---
name: audit-bibliography
description: |
  Audit the manuscript's existing citations: resolve DOIs, deduplicate, flag format
  deviations vs the resolved refs_style. Writes _review/bibliography-audit/{report.md,
  fixes.json}. Fixes are PROPOSALS — not applied to the .docx (Review-Then-Act).
  Zotero -> CrossRef -> OpenAlex fallback chain. NLM deferred (D9).
  Active in all 9 profiles. Dispatches the bibliography-curator agent.
allowed-tools: Bash, Read, Write, Glob, WebFetch
---

# /sws:audit-bibliography

Audit the manuscript bibliography for resolution, duplication, and format compliance.

## Usage

```
/sws:audit-bibliography                        # audit full bibliography
/sws:audit-bibliography --doi-only             # only check DOI resolution (skip format)
/sws:audit-bibliography --format-only          # only check format vs refs_style
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Locate the manuscript `.docx` in `${PAPER_ROOT}/Manuscript/` (or as specified in the marker).
3. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh bibliography-curator`.
4. Check `RESOLVED_OK`; if 0, print the prelude's message and exit 0.
   (bibliography-curator is active in all 9 profiles, so this should always pass.)
5. Dispatch the `bibliography-curator` agent with any mode flags.
6. After the agent returns, print summary:
   - N citations audited / N resolved / N unresolved DOIs / N duplicates / N format deviations.
7. Point the user at `${PAPER_ROOT}/_review/bibliography-audit/report.md` and `fixes.json`.
   Remind the user: "fixes.json contains proposals only — apply manually or via /sws:apply-fixes (future v0.2)."

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md` — D3, D8, D9, D11.
