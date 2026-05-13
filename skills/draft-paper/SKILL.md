---
name: draft-paper
description: "This skill should be used when the user invokes /sws:draft-paper, says 'draft the whole paper', 'draft all sections', 'draft the proposal', 'draft the perspective end to end' — and the cwd is an SWS project with an outline at _outline/outline.md. Dispatches drafter-flagship in orchestrator mode, which fans out section drafting in parallel."
version: 0.1.0
---

# /sws:draft-paper — Draft all profile-required sections in parallel

Invokes `drafter-flagship` in orchestrator mode. The flagship reads the outline frontmatter, dispatches section agents (drafter-flagship for narrative-heavy, drafter-fast for Results, methods-writer for Methods, caption-writer for figures) in parallel, and assembles the result into `_drafts/draft-paper-<timestamp>.md`.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check. If absent, print "not an SWS project (no .sws-project.local.md found)" and exit.
2. **Resolve profile.** Run:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
       "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
       --paper "$PAPER_ROOT"
   ```
   If `profile_set: false`, print "no profile set — run /sws:set-profile <name> first" and exit.
3. **Verify outline exists.** Check `${PAPER_ROOT}/_outline/outline.md`. If missing, print "no outline yet — run /sws:outline-paper first" and exit.
4. **Recommend zotero manifest.** If `${PAPER_ROOT}/_lit/zotero-manifest.md` is missing, print: "consider running /sws:prepare-lit-context first to ground citations from your Zotero library" — then proceed regardless (drafter falls back to `[CITATION_NEEDED:]`).
5. **Dispatch drafter-flagship in orchestrator mode** via the Task tool with `--mode=orchestrator`. Pass `PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT` in env. The orchestrator reads the outline frontmatter and fans out parallel subagent dispatches per the section→agent map (see `scripts/sws_section_router.py`).
6. **Hand back to user.** Flagship's summary (section count, word count, placeholder count, AI-tells hits) is the user-visible output. The assembled draft lands at `${PAPER_ROOT}/_drafts/draft-paper-<timestamp>.md`.

## When to invoke

- Explicit `/sws:draft-paper`.
- User triggers from the description above.
- Do NOT invoke without a marker, without a set profile, or without an outline.
