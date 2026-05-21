---
name: check-fidelity
description: |
  Run the SWS bibliography-fidelity-checker on the active .docx to find verbatim ≥15-word overlaps against the user's Zotero corpus. Renamed from /sws:check-plagiarism on 2026-05-17 — the v0.1 scope is bounded-corpus fidelity, not unbounded plagiarism. Four code paths (D9 happy, D9a Zotero-desktop-only recommendation, D9b small/unresponsive library, D9c no-Zotero neutral). Writes _review/bibliography-fidelity-checker/{report.md, flags.json, status.json}. Inactive in funding-proposal profile.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:check-fidelity

Check the manuscript for verbatim overlaps against papers in your Zotero library — catches accidental copy-paste from sources you have read.

## Usage

```
/sws:check-fidelity                          # full paper, default .docx
/sws:check-fidelity --docx <path>            # explicit docx
/sws:check-fidelity --probe-zotero           # print probe state JSON only
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh bibliography-fidelity-checker`.
3. If `RESOLVED_PROFILE_ID == funding-proposal`, print the v0.1-unsupported message and exit 0.
4. Dispatch the `bibliography-fidelity-checker` agent. The agent runs `sws_bibliography_fidelity.py` which always exits 0 and writes a `status.json` indicating which code path was taken.
5. After the agent returns, read `status.json` and print:
   - if `ran == true`: "Fidelity check complete: N flag(s) across M sections. See _review/bibliography-fidelity-checker/report.md."
   - if `ran == false` and `skip_reason == zotero-desktop-detected-but-claude-skill-missing`: "Skipped — Zotero detected at <path> but the Claude Code zotero skill is not installed. See report for installation guidance."
   - if `ran == false` and `skip_reason == no-zotero-installation-detected`: "Skipped — no Zotero installation detected. The fidelity check is Zotero-only in v0.1; see report for v0.2 alternatives."
   - other skip reasons: print the specific reason from status.json.

## What this is NOT

Bibliography-fidelity is a *fidelity* check ("did I accidentally copy from a paper I've read?"), not an unbounded-corpus *plagiarism* check ("was this text published anywhere first?"). The latter requires paid APIs (Crossref Similarity Check / iThenticate) or scraping (Google Programmable Search opt-in), both v0.2 backlog.

## Spec source of truth

`docs/superpowers/specs/2026-05-17-cycle-09-review-design.md` — D1, D2, D9, D9a, D9b, D9c, D10, D13.
