---
name: draft-section
description: "This skill should be used when the user invokes /sws:draft-section <section>, says 'draft the intro', 'write the introduction', 'draft section X', or similar — and the cwd is an SWS project with an outline at _outline/outline.md. Routes the request to the right primary agent (drafter-flagship for Intro/Discussion/Conclusion/Abstract; methods-writer for Materials/Experimental subsections; drafter-fast for Results and other narrative; caption-writer for figure_caption; proposal-budget-helper / proposal-compliance-helper for funding-proposal special sections)."
version: 0.1.0
---

# /sws:draft-section — Draft a single section

Maps a section id to the right primary agent and dispatches it. The full map is documented in `docs/superpowers/specs/2026-05-13-cycle-07-drafting-and-proposal-helpers-design.md` (`section_to_agent_map`).

## Routing (full)

The skill picks the right map based on the resolved profile id.

### Publication-profile sections (intro, methods, results, etc.)

| Section id (lowercased, hyphens or spaces both accepted) | Agent |
|---|---|
| intro, introduction, abstract, discussion, conclusion, conclusions | drafter-flagship |
| methods, experimental, "experimental section", materials, "statistical analysis", "computational details", software, "data availability" | methods-writer |
| results | drafter-fast |
| "results and discussion" | drafter-flagship (joint section: rationale wins) |
| figure_caption | caption-writer |
| (other narrative section ids) | drafter-fast (fallback) |

### Funding-proposal sections

| Section id | Agent |
|---|---|
| "state of the art", "state-of-the-art", vision, objectives, workplan, methodology, approach, impact, "risk management", deliverables, timeline | drafter-flagship |
| budget | proposal-budget-helper (special: writes budget-suggestions.md, not a drafted section) |
| compliance | proposal-compliance-helper (special: writes compliance-report.md) |
| figure_caption | caption-writer |
| (other section ids) | drafter-flagship (fallback) |

The single source of truth for routing is `scripts/sws_section_router.py` — the tables above mirror its `_PUBLICATION_MAP` and `_FUNDING_PROPOSAL_MAP` dicts.

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
4. **Resolve the section→agent route.** Run:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" -c \
       "from sws_section_router import route_section; print(route_section('<section-id>', '<profile-id>'))"
   ```
   The router lowercases the section id, accepts both `state-of-the-art` and `state of the art`, and falls back to `drafter-fast` (publication) or `drafter-flagship` (funding-proposal) on unknown ids.
5. **Dispatch the agent** via the Task tool (or the plugin's agent-dispatch convention). Pass `PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT` in the env, plus the requested `--section <id>` argument. The agent's own `agent_should_run.sh` check enforces the per-profile activation matrix — if the chosen agent is in `agents_inactive`, the dispatch silently no-ops and the skill prints "agent <id> is inactive for profile <id>; nothing drafted".
6. **Hand back to user.** The agent writes the draft to `_drafts/<section-id>.md` and prints the path.

## When to invoke

- Explicit `/sws:draft-section <section>`.
- User says "draft the <section>", "write the <section>", etc. — with a valid SWS marker.

Do NOT invoke when the marker is missing or the profile is unset.
