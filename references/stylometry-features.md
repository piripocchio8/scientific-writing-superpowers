---
sws_artifact: stylometry-features
artifact_version: 0.1
used_by: scripts/sws_stylometry.py, agents/style-calibrator.md
---

# Stylometry features (v0.1)

`sws_stylometry.py` extracts a fixed 17-dimensional feature vector per text. The
keys, in `FEATURE_ORDER`:

| # | key | definition | scale |
|---|---|---|---|
| 1 | sentence_len_mean | mean tokens per sentence | tokens |
| 2 | sentence_len_sd | population sd of sentence length | tokens |
| 3 | hedge_density | hedge tokens per 100 tokens | per-100 |
| 4 | connective_density | connective tokens per 100 tokens | per-100 |
| 5 | passive_ratio | be-aux + nearby -ed events per sentence | per-sentence |
| 6 | lexical_diversity | type/token ratio | 0–1 |
| 7 | fp_plural_rate | first-person-plural pronouns per 100 tokens | per-100 |
| 8–17 | fw_the … fw_as | relative frequency of each tracked function word | 0–1 |

Tracked function words (order fixed): `the, of, and, to, in, that, we, is, for, as`.

## Word lists (mirror the script constants)

- **HEDGES:** may, might, could, possibly, perhaps, likely, suggest, suggests, appear, appears, seem, seems, indicate, indicates, probably, presumably, arguably, relatively
- **CONNECTIVES:** however, moreover, therefore, thus, furthermore, nevertheless, consequently, hence, accordingly, additionally, whereas, although
- **FP_PLURAL:** we, us, our, ours, ourselves
- **PASSIVE_AUX:** was, were, is, are, been, be, being (passive proxy = aux followed within 2 tokens by an `-ed` word)

Empty text returns the zero vector (every feature 0.0). Short text never crashes.

## Scoring math (D8/D8a/D10 + voice-metric correction)

The metric has TWO channels, combined at the SIMILARITY level — never folded
into one squared distance. (The earlier design folded the Haiku term into the
distance as a linear `w_h(1-sim)` while fitting it as squared `(1-sim)^2`, with
no per-term weight clipping; a real-Haiku validation showed that blend
anti-correlated with voice. The corrected metric below tracks voice.)

**Standardization.** Each feature is standardized to mean 0 / sd 1 across the
anchor set before weighting (sd floored to 1.0 when ~0), so squared differences
across features are comparable.

**Stylometric channel — distance.** `D_stylo(x,y) = SUM_i w_i (z_x_i - z_y_i)^2`
on standardized features. Stylometric only; the Haiku term is NOT in here.

**Clipped Fisher weights.** Per term, `fisher_i = between_var_i / max(within_var_i,
1e-6)`, where within-variance is the mean squared standardized difference over
POSITIVE pairs (same-author) and between-variance over NEGATIVE pairs
(different-author). Shrink toward uniform `w = (1-lambda)*fisher + lambda*uniform`
(default lambda 0.3) and normalize, THEN per-term CLIP each weight to
`[clip_lo*u, clip_hi*u]` (u = 1/len(FEATURE_ORDER); defaults clip_lo 0.4,
clip_hi 2.5) and renormalize, iterating clip+renormalize ~8 times to converge.
Clipping stops any single feature (e.g. `fw_and`) from running away. Constraints:
`w_i >= 0`, `SUM(w_i) ~= 1`. A within-variance floor prevents division blow-ups on
a tiny corpus. The Haiku channel is fitted separately (below), not here.

**RBF kernel.** `k_stylo(x,y) = exp(-gamma * D_stylo(x,y))`, bounded in (0,1],
saturating under large drift. `gamma = 1 / median(D_stylo over same-author pairs)`
(median heuristic), guarded when the median is ~0.

**Haiku channel.** A pairwise voice similarity in [0,1] supplied by a REAL Haiku
judge (the style-calibrator dispatches it with a fixed rubric, median of 3). A
constant value collapses this channel — it carries no separation, so the fit
hands all weight to the stylometric channel. A real judge is required for the
Haiku channel to contribute.

**Fitted channel mix.** Combine the two channels as `S(x,y) = alpha*k_stylo(x,y) +
beta*haiku_sim(x,y)`, with the mix fitted by how well each channel separates
same-author from different-author pairs: `sep_s = mean(k_stylo on pos) -
mean(k_stylo on neg)`, `sep_h = mean(haiku on pos) - mean(haiku on neg)`, each
clamped to >= 1e-6; `alpha = sep_s/(sep_s+sep_h)`, `beta = sep_h/(sep_s+sep_h)`
(so `alpha+beta = 1`). The channel that separates better gets the larger weight.
`S` increases monotonically with `haiku_sim` (others fixed); this is the
anti-correlation fix.

**Enriched baseline.** The anchor set is enriched beyond author-vs-field:
POSITIVE = same-author pairs (author-self AND peer-self); NEGATIVE = different-
author pairs (author×peer AND peer×peer-of-other). The richer between-class makes
both the Fisher weights and the channel separations more robust.

**Self-similarity band (the stopping target, D10).** Compute the combined score
`S` for every intra-author pair (using the supplied per-pair Haiku sims); the band
is `mean +/- sd`. The calibration loop stops a section type when its
generated-vs-held-out combined score enters the band — you cannot be more like
yourself than your own papers already are. Backstops: keep-best-so-far (revert any
worsening edit; monotone per section), a plateau rule (relative improvement <
epsilon), and a hard round cap N.
