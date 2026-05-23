---
name: calibrate-style
description: |
  Build a reusable, evidence-backed voice profile from the author's own papers in Zotero. Runs the style-calibrator agent's 5-phase iterative held-out loop and writes _voice/{profile.md, field-profile.md, style-evolution.md, sources.json, convergence.md}. The drafters/revisers/humanizer then write in the author's voice. Default-inactive in editorial and commentary-reply profiles.
allowed-tools: Bash, Read, Write, Glob, Task
---

# /sws:calibrate-style

Build the author's voice profile from their own papers, with an objective stopping rule (the author's own self-similarity band).

## Usage

```
/sws:calibrate-style                      # discover via the zotero skill
/sws:calibrate-style --sources _voice/sources/   # manual fallback: pre-dropped PDFs (D17)
```

## Loop defaults (D8a / D10)

- `epsilon = 0.05` (5% relative improvement — below this counts as a plateau)
- `max_rounds N = 4` per section type
- `lambda = 0.3` (Fisher shrink-to-uniform)
- Haiku scoring: x3 calls, low temperature, take the median (D9)

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh style-calibrator`.
3. If `agent_should_run.sh style-calibrator` exits non-zero (editorial / commentary-reply default-inactive), print "style-calibrator is default-inactive for this profile; flip it on in the profile's agents_active if you want voice calibration here." and exit 0.
4. Dispatch the `style-calibrator` agent. It runs the 5 phases: discover -> flag&split -> extract -> (3.5 evolution) -> calibrate-loop -> write&report.
5. After the agent returns, print a one-line summary: per-section convergence (entered-band / plateau / cap), training/heldout counts.
6. Point the author at `${PAPER_ROOT}/_voice/profile.md` and `${PAPER_ROOT}/_voice/convergence.md`.

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-10-style-calibration-design.md` — D1, D2, D8, D8a, D9, D10, D11, D12, D17.
