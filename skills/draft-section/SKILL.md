---
name: draft-section
description: "This skill should be used when the user invokes /sws:draft-section <section>, says 'draft the intro', 'write the introduction', 'draft section X', or similar — and the cwd is an SWS project with an outline at _outline/outline.md. Routes the request to the right primary agent (drafter-flagship for Intro/Discussion/Conclusion/Abstract). Phase-1 ships with intro routing only; remaining sections wired in phase 3."
version: 0.1.0
---

# /sws:draft-section — Draft a single section

Maps a section id to the right primary agent and dispatches it. The full map is documented in `docs/superpowers/specs/2026-05-13-cycle-07-drafting-and-proposal-helpers-design.md` (`section_to_agent_map`).

## Phase-1 routing (in this version)

| Section id | Agent |
|---|---|
| intro, introduction | drafter-flagship |
| (everything else)   | (not yet wired — print "section <id> not yet supported in this build; coming in phase 3") |

Phase 3 extends this map with the full publication and funding-proposal section lists.

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
4. **Look up section id in the map** above. If not in the map, print the phase-3 message and exit.
5. **Dispatch the agent** via the Task tool (or the plugin's agent-dispatch convention). Pass `PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT` in the env, plus the requested `--section <id>` argument.
6. **Hand back to user.** The agent writes the draft to `_drafts/<section-id>.md` and prints the path.

## When to invoke

- Explicit `/sws:draft-section <section>`.
- User says "draft the <section>", "write the <section>", etc. — with a valid SWS marker.

Do NOT invoke when the marker is missing or the profile is unset.
