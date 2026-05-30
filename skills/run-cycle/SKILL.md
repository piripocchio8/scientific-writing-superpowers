---
name: run-cycle
description: |
  Master orchestrator. Runs the full SWS pipeline end-to-end: outline → draft →
  revise → review → cover-letter → ai-disclosure → response-to-reviewers.
  Each step is skipped when its artifacts already exist (D9 idempotency).
  Supports --dry-run (plan only) and --only=<csv> (subset). Writes a single
  passport entry with phase=submit summarising the steps dispatched.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:run-cycle

End-to-end SWS pipeline driver. Re-run safely — completed steps are skipped.

## Usage

```
/sws:run-cycle                                  # full pipeline
/sws:run-cycle --dry-run                        # plan only, no dispatch
/sws:run-cycle --only=cover-letter,disclosure   # subset
```

## Step plan (D9)

| Step | Name          | Skill dispatched             | Skip condition                                              |
|------|---------------|------------------------------|-------------------------------------------------------------|
| 1    | outline       | /sws:outline-paper           | outline.md exists                                           |
| 2    | draft         | /sws:draft-paper             | _drafts/*.md non-empty                                      |
| 3    | revise        | /sws:revise-paper            | _drafts/*.revised.md newer than canonical drafts            |
| 4    | review        | /sws:review-paper            | all 3 _review/<agent>/report.md present                     |
| 5    | cover-letter  | /sws:write-cover-letter      | _submission/cover-letter.md exists OR not required          |
| 6    | disclosure    | /sws:disclose-ai-usage       | _submission/ai-disclosure.md exists OR not required         |
| 7    | response      | /sws:respond-to-reviewers    | no pending _review/round-<N>/reviewer-comments.md           |

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Parse `--dry-run` and `--only=<csv>` flags.
3. Compute the step plan:
   ```
   ${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" \
       ${CLAUDE_PLUGIN_ROOT}/scripts/sws_run_cycle.py \
       --paper-root "$PAPER_ROOT" --dry-run --json [--only=<csv>]
   ```
   Capture the JSON plan; print a human-readable summary to the user.
4. If `--dry-run` was passed, exit 0 here.
5. Otherwise, iterate the planned steps in order. For each step with
   `should_run: true`:
   - Determine dispatch kind by step name:
     ```
     case "$step_name" in
       outline|draft|revise|review|cover-letter|response)
           # Agent-backed step — emit MANUAL directive for the user-context
           # to dispatch the matching skill. The orchestrating context
           # (typically Claude Code in the user's session) reads the
           # directive and invokes the skill.
           echo "MANUAL: dispatch ${skill_name} (${step_name})"
           ;;
       disclosure)
           # Deterministic script — dispatch directly.
           ${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" \
               ${CLAUDE_PLUGIN_ROOT}/scripts/sws_disclosure_writer.py \
               --paper-root "$PAPER_ROOT"
           ;;
     esac
     ```
6. After all dispatchable steps complete, append a single passport history
   entry with:
   - `phase: submit`
   - `venue: <target_journal>` (from marker)
   - `round: <N>` (only when the response step was dispatched)
   - `change_summary`: comma-separated list of step names dispatched
   - `next_step`: "ready for upload" if all required artifacts exist, else
     a short TODO list (e.g. "fill {EDITOR_NAME} in cover-letter.md").
7. Print a final summary listing each step's outcome (RUN | SKIPPED | MANUAL).

## Stale-detection (R4, D10)

When `_submission/cover-letter.md` predates a `_drafts/*.md` source file by
more than 5 seconds, the planner flags the step as `stale`. The orchestrator
prints a notice but does NOT auto-regenerate — the user re-runs the specific
skill if they want a refresh.

## Profile gating

Steps 5 (cover-letter) and 7 (response) check both the
`RESOLVED_COVER_LETTER_REQUIRED` / `RESOLVED_DISCLOSURE_REQUIRED` resolver
fields and the active profile's agent-activation list before dispatch (D8).

## Spec source of truth

`docs/superpowers/specs/2026-05-30-cycle-12-submission-orchestration-design.md`
— D2, D9, D10, D14, R4.
