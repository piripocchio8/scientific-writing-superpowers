---
sws_artifact: voice-profile-schema
artifact_version: 0.1
used_by: agents/style-calibrator.md, agents/drafter-flagship.md, agents/drafter-fast.md, agents/reviser-full.md, agents/reviser-fast.md, agents/humanizer.md
---

# Voice profile schema (`_voice/profile.md`, v0.1)

`profile.md` is the file the drafters/revisers/humanizer consume. It is a NEW
input on the VOICE axis, SEPARATE from the journal-style/constraints overlay
(D13): it does NOT pass through `resolve_overlay.py`.

## Frontmatter (machine-readable feature targets)

```yaml
---
sws_artifact: voice-profile
artifact_version: 0.1
calibrated: <ISO-date>
recent_weighted: true
feature_targets:
  sentence_len_mean: { target: 24.0, band: [20.0, 28.0] }
  sentence_len_sd: { target: 9.0, band: [6.0, 12.0] }
  hedge_density: { target: 1.8, band: [1.0, 2.6] }
  connective_density: { target: 2.2, band: [1.4, 3.0] }
  passive_ratio: { target: 0.35, band: [0.2, 0.5] }
  lexical_diversity: { target: 0.52, band: [0.46, 0.58] }
  fp_plural_rate: { target: 1.6, band: [0.9, 2.3] }
convergence:
  self_band: [0.74, 0.91]
  gamma: 0.42
  alpha: 0.58   # stylometric-channel weight (clipped-Fisher k_stylo)
  beta: 0.42    # Haiku-channel weight; alpha + beta = 1
sections: [global, introduction, results, discussion, methods, abstract]
---
```

`self_band` is the band over the COMBINED score `S = alpha*k_stylo +
beta*haiku_sim` across same-author pairs, not a single-channel similarity. `alpha`
/ `beta` are the fitted channel mix (see `references/stylometry-features.md`): the
stylometric channel uses clipped Fisher weights over standardized squared feature
differences wrapped in the RBF kernel; the Haiku channel is a real Haiku judge's
voice similarity. A constant Haiku value collapses that channel, so `beta -> 0` and
the score reduces to the stylometric kernel — a real judge is required. The
baseline is enriched (same-author incl. peer-self vs different-author incl.
peer×peer) so the mix is fitted on a robust separation.

`feature_targets` keys are a subset of `FEATURE_ORDER` (the 7 stylometric
features; function-word freqs are summarized in prose, not pinned numerically).
Every `band` is `[lo, hi]` with `lo <= target <= hi`.

## Body contract

The body has ONE global voice block followed by PER-SECTION delta blocks.

```markdown
# Voice profile

## Global voice
<2–4 paragraphs: sentence rhythm, hedging/stance, connective habits,
register, signposting, recurring phrasings. No AI-writing tells.>

## Section deltas

### Introduction
<how the register shifts here vs the global block>

### Results
<...>

### Discussion
<...>

### Methods
<convention-bound; minimal personal voice>

### Abstract
<...>
```

Required headings: `## Global voice` and `## Section deltas`, with at least
`### Introduction`, `### Results`, `### Discussion` present. The drafters read the
global block always, plus the per-section delta for the section being written.
Absent `_voice/profile.md` -> agents behave exactly as today (graceful degrade).

## Related artifacts (written by style-calibrator, not consumed by drafters)

- `_voice/field-profile.md` — one-shot subfield conventions (D5; no per-section breakdown).
- `_voice/style-evolution.md` — diachronic feature x year/era table + reading (D7).
- `_voice/sources.json` — `[{zotero_key, title, year, author_position, has_pdf, role: train|heldout, recency_weight}]` + fitted clipped-weights snapshot + channel mix `{alpha, beta, gamma}` + self-band.
- `_voice/convergence.md` — per round, per section: distance, RBF sim, Haiku median, what changed, why, seed prompt + candidate text (D11).
- `_voice/_archive/` — prior `profile.md` versions, timestamped, on re-run.
