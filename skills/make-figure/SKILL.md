---
name: make-figure
description: |
  Generate publication figures from co-located Zenodo_db/scripts/ via the per-paper venv.
  Sizes figures from the resolved journal-style overlay. Updates manifest.json atomically.
  Opt-in VLM self-check via --verify (native multimodal Read). Dispatches plot-maker agent.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:make-figure

Generate journal-compliant publication figures from curated data.

## Usage

```
/sws:make-figure                        # regenerate all figures in manifest.json
/sws:make-figure --entry <dataset>      # regenerate figures for one manifest entry
/sws:make-figure --verify               # regenerate + VLM self-check each output PNG
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Verify `${PAPER_ROOT}/Zenodo_db/manifest.json` exists.
   If not, print: "No manifest.json found. Run /sws:curate-data first."
3. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh plot-maker`.
4. Check `RESOLVED_OK`; if 0, print the prelude's message and exit 0.
5. Read the resolved journal-style overlay for figure constraints (width, dpi, font).
6. Dispatch the `plot-maker` agent, passing `--verify` flag if given.
7. After the agent returns, print summary: N figures generated, manifest updated.
   If `--verify`: print VLM self-check findings per figure.
8. Point the user at `${PAPER_ROOT}/Zenodo_db/figures/`.

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md` — D6, D7, D11.
