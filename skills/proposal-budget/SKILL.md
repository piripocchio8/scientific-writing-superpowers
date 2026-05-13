---
name: proposal-budget
description: "This skill should be used when the user invokes /sws:proposal-budget, says 'suggest the budget', 'help me draft the budget', 'budget breakdown for the proposal' — and the active profile is funding-proposal with a resolved call-rules overlay. Dispatches proposal-budget-helper to produce _proposal/budget-suggestions.md."
version: 0.1.0
---

# /sws:proposal-budget — Get budget line-item suggestions

Dispatches `proposal-budget-helper`. First run runs an interactive Q&A and caches answers to `_proposal/budget-context.yaml`; subsequent runs read the cache and the resolved call overlay.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check. If absent, print "not an SWS project (no .sws-project.local.md found)" and exit.
2. **Verify profile = funding-proposal.** Run:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
       "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
       --paper "$PAPER_ROOT"
   ```
   If `profile_id != funding-proposal`, print "this skill only runs for funding-proposal profile; current is <id>" and exit.
3. **Verify call-rules overlay exists.** Check `${PAPER_ROOT}/Manuscript/_call/`. If empty, print "no call-rules overlay — run /sws:resolve-call-rules first" and exit.
4. **Verify outline exists.** Check `${PAPER_ROOT}/_outline/outline.md`. If missing, print "no outline yet — run /sws:outline-paper first" and exit.
5. **Dispatch proposal-budget-helper** via the Task tool. Pass `PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT` in env. On first invocation the agent runs the interactive Q&A (PhD/postdoc gross, equipment hourly rates, consumables baseline, currency) and caches the answers to `_proposal/budget-context.yaml`.
6. **Hand back to user.** Agent prints the path to `${PAPER_ROOT}/_proposal/budget-suggestions.md` and a one-line summary (total + sanity check vs call cap).

## When to invoke

- Explicit `/sws:proposal-budget`.
- User triggers from the description above.
- Do NOT invoke without a marker, without funding-proposal profile, without a call-rules overlay, or without an outline.
