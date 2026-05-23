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

## Scoring math (D8/D8a/D10)

**Standardization.** Each feature is standardized to mean 0 / sd 1 across the
anchor set before weighting (sd floored to 1.0 when ~0), so squared differences
across features are comparable.

**Distance.** `D(x,y) = SUM_i w_i (x_i - y_i)^2 + w_h (1 - haiku_sim(x,y))` on
standardized features. The Haiku voice-similarity term is a pairwise dissimilarity
that enters directly (it cannot be differenced).

**Fisher weights.** Per term, `fisher_i = between_var_i / max(within_var_i, 1e-6)`,
where within-variance is the mean squared standardized difference over POSITIVE
pairs (author,author) and between-variance over NEGATIVE pairs (author,field).
`w_h` is fitted identically from a Haiku sample on the same anchor pairs.
Constraints: `w_i >= 0`, `SUM(w_i) + w_h = 1`. Regularization: shrink toward
uniform `w = (1-lambda) * fisher + lambda * uniform` (default lambda 0.3), with a
within-variance floor to prevent division blow-ups on a tiny corpus.

**RBF kernel.** `k(x,y) = exp(-gamma * D(x,y))`, bounded in (0,1], saturating under
large drift. `gamma = 1 / median(intra-author weighted distances)` (median
heuristic), guarded when the median is ~0.

**Self-similarity band (the stopping target, D10).** Compute RBF similarity for
every intra-author pair; the band is `mean +/- sd`. The calibration loop stops a
section type when its generated-vs-held-out similarity enters the band — you
cannot be more like yourself than your own papers already are. Backstops:
keep-best-so-far (revert any worsening edit; monotone per section), a plateau rule
(relative improvement < epsilon), and a hard round cap N.
