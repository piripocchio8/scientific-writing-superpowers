---
name: curate-data
description: |
  Ingest Zenodo_db/data/*.xlsx as the data authority. Reads values via sws_xlsx_resolve.py
  (data_only; fail-loud on un-cached formula cells). Writes Zenodo_db/manifest.json
  atomically. Dispatches the data-curator agent.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:curate-data

Ingest the Zenodo_db/ xlsx files as the data authority and emit a traceable manifest.

## Usage

```
/sws:curate-data                     # ingest all .xlsx in Zenodo_db/data/
/sws:curate-data --check             # run manifest orphan check only (no ingestion)
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Verify `${PAPER_ROOT}/Zenodo_db/data/` exists and contains at least one `.xlsx`.
   If not, print: "No xlsx files found in Zenodo_db/data/. Add your data spreadsheet and re-run."
3. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh data-curator`.
4. Check `RESOLVED_OK`; if 0, print the prelude's message and exit 0.
5. If `--check` flag: run `sws_data_manifest.py <zenodo_db> --check` and report results.
6. Otherwise: dispatch the `data-curator` agent.
7. After the agent returns, print summary: N datasets resolved, N manifest entries, any orphans.
8. Point the user at `${PAPER_ROOT}/Zenodo_db/manifest.json`.

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md` — D4, D5, D11.
