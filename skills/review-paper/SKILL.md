---
name: review-paper
description: |
  Sequential orchestrator that runs the SWS review pipeline end-to-end: /sws:verify-claims → /sws:check-fidelity → /sws:peer-review. Passes report paths from the first two into peer-reviewer via explicit CLI args (no autoscan). Propagates SWS_FIDELITY_STATUS to peer-reviewer so the peer-review report transparently notes when fidelity was skipped. Inactive in funding-proposal profile (component skills' profile gates also fire individually).
allowed-tools: Bash, Read, Write, Glob, WebFetch
---

# /sws:review-paper

Run the full SWS review pipeline on the active manuscript.

## Usage

```
/sws:review-paper                          # full pipeline
```

## Pipeline order (sequential per D3)

1. **claim-verifier** — text-internal claims first.
2. **bibliography-fidelity-checker** — Zotero-corpus overlap second. Always exits 0; may skip with a documented reason.
3. **peer-reviewer** — receives both prior report paths via explicit CLI args.

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh review-paper`.
3. Run `/sws:verify-claims`. Wait for completion. Capture exit status. (Skipped silently if profile is funding-proposal.)
4. Run `/sws:check-fidelity`. Wait for completion. Read `_review/bibliography-fidelity-checker/status.json` to determine `SWS_FIDELITY_STATUS`. (Skipped silently if profile is funding-proposal.)
5. Run `/sws:peer-review --claim-report ${PAPER_ROOT}/_review/claim-verifier/report.md --fidelity-report ${PAPER_ROOT}/_review/bibliography-fidelity-checker/report.md` with `SWS_FIDELITY_STATUS` exported. If the fidelity report file does not exist (e.g. D9c hard skip), omit `--fidelity-report` and still export `SWS_FIDELITY_STATUS=skipped:no-zotero-installation-detected`.
6. After peer-reviewer returns, print summary of all three reports.

## Profile gate

If `RESOLVED_PROFILE_ID == funding-proposal`, run peer-reviewer only (claim-verifier and fidelity-checker exit 0 with v0.1-unsupported messages, which is acceptable behavior — orchestrator does not error).

## Spec source of truth

`docs/superpowers/specs/2026-05-17-cycle-09-review-design.md` — D2, D3, D17.
