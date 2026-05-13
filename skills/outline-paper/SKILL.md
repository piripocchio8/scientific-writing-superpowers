---
name: outline-paper
description: "This skill should be used when the user invokes /sws:outline-paper, says 'build the outline', 'structure the paper', 'plan the sections', 'draft an outline', or similar. Validates that the cwd is an SWS project with a profile set, then dispatches the outline-architect agent to produce _outline/outline.md."
version: 0.1.0
---

# /sws:outline-paper — Build a structured outline for the current paper

This skill triggers the `outline-architect` agent. The architect reads the resolved profile + journal/call overlay, scans the figures directory, and writes `<paper>/_outline/outline.md` (markdown + YAML frontmatter) plus a `.outline-baseline.sha256` sidecar.

## When to invoke

- User explicitly types `/sws:outline-paper`.
- User says "build the outline", "structure this paper", "plan the sections", "let's outline first" — and the cwd contains a valid `.sws-project.local.md` marker.

Do NOT invoke when:
- The cwd has no marker. Print "not an SWS project (no .sws-project.local.md found)" and exit.
- The marker has `profile: null`. Print "no profile set — run /sws:set-profile <name> first" and exit.

## Steps

1. **Resolve `$PAPER_ROOT`.** Current working directory must contain `.sws-project.local.md`. If absent, print the not-an-SWS-project line and exit.

2. **Check profile is set.** Run:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
       "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
       --paper "$PAPER_ROOT"
   ```
   Parse the JSON; if `profile_set: false`, print the no-profile-set line and exit.

3. **Dispatch outline-architect.** Use the Task tool with `subagent_type=outline-architect` (or invoke the agent file directly per the plugin's agent-dispatch convention). Pass `PAPER_ROOT=$PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}` in the env.

4. **Hand back to the user.** The agent writes the outline plus sidecar and prints the path. No further model action needed.

## Re-run behavior

If `_outline/outline.md` already exists, the agent compares its current hash to `.outline-baseline.sha256`. On mismatch (user hand-edits since the last architect run), the agent stops, shows a diff of the would-be-lost content, and asks before overwriting. The safety prompt is opt-out via `--force`.
