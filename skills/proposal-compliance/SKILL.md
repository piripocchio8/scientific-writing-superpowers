---
name: proposal-compliance
description: "This skill should be used when the user invokes /sws:proposal-compliance, says 'check compliance', 'verify the proposal against the call', 'audit the proposal', 'check rules' — and the active profile is funding-proposal with both a resolved call-rules overlay and at least one drafted proposal section. Dispatches proposal-compliance-helper to produce _proposal/compliance-report.md."
version: 0.1.0
---

# /sws:proposal-compliance — Check the proposal against call rules

Dispatches `proposal-compliance-helper`. The agent reads the call overlay (structured rules) first, then opens the call PDF (native Read) or DOCX (sws_read_docx.py wrapper) for ambiguity resolution, and produces a compliance report at `_proposal/compliance-report.md`.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check. If absent, print "not an SWS project (no .sws-project.local.md found)" and exit.
2. **Verify profile = funding-proposal.** Run the resolver as in `/sws:proposal-budget` step 2. If `profile_id != funding-proposal`, print "this skill only runs for funding-proposal profile; current is <id>" and exit.
3. **Verify call-rules overlay exists.** Check `${PAPER_ROOT}/Manuscript/_call/`. If empty, print "no call-rules overlay — run /sws:resolve-call-rules first" and exit.
4. **Verify proposal drafts exist.** Check `${PAPER_ROOT}/_drafts/` is non-empty OR a docx file exists in `${PAPER_ROOT}/Manuscript/`. If neither, print "nothing to check — draft proposal sections first via /sws:draft-paper or /sws:draft-section" and exit.
5. **Dispatch proposal-compliance-helper** via the Task tool. Pass `PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT` in env. The agent reads the overlay, the drafts (and any DOCX in `Manuscript/` via `sws_read_docx.py`), and the call PDF when ambiguity needs resolving (native Read with `pages` parameter for PDFs over 10 pages).
6. **Hand back to user.** Agent prints the path to `${PAPER_ROOT}/_proposal/compliance-report.md` and a one-line summary (X of N rules pass).

## When to invoke

- Explicit `/sws:proposal-compliance`.
- User triggers from the description above.
- Do NOT invoke without a marker, without funding-proposal profile, without a call-rules overlay, or without at least one drafted proposal section.
