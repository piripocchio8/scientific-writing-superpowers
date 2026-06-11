---
name: write-cover-letter
description: |
  Dispatch the SWS cover-letter-writer agent (Sonnet 4.6) to draft a venue-
  specific cover letter at _submission/cover-letter.md. Reads the resolved
  journal-style overlay (target_journal in the marker, or --venue override
  per D18) + the paper's abstract. Never fabricates the editor name (D11).
  Accepts --force to overwrite an existing cover-letter.md. Active in 8/9
  profiles; gated on RESOLVED_COVER_LETTER_REQUIRED.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:write-cover-letter

Draft a journal-upload cover letter for the active manuscript.

## Usage

```
/sws:write-cover-letter                         # use marker's target_journal
/sws:write-cover-letter --venue chembiochem     # override target journal (D18)
/sws:write-cover-letter --force                 # overwrite existing cover-letter.md
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists. If not, exit with the
   standard "not an SWS project" message and instruct the user to run
   `/sws:init-project` first.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh cover-letter-writer`
   to load `RESOLVED_*` env vars.
3. If `RESOLVED_COVER_LETTER_REQUIRED` is not `true`, exit cleanly with:
   "Cover letter is not required for the active profile."
4. Parse the optional `--venue <slug>` and `--force` flags. Export
   `SWS_VENUE_OVERRIDE` (if `--venue` given) and `SWS_COVER_LETTER_FORCE`
   (if `--force` given) so the agent picks them up.
5. Dispatch the `cover-letter-writer` agent.
6. After the agent returns, print the one-line summary it produced (path +
   word count + grep-pass status).
7. Point the user at `${PAPER_ROOT}/_submission/cover-letter.md`.

## V0.1 limitations

- The cover-letter-writer never invents the editor name. When the overlay
  lacks `editor_name`, the output carries `Dear {EDITOR_NAME},` with a TODO
  marker. The user fills it in before upload.
- No automated suggested-editors list. The overlay must populate
  `suggested_handling_editors` to surface them.

## Spec source of truth

`docs/superpowers/specs/2026-05-30-cycle-12-submission-orchestration-design.md`
— D2, D11, D16, D18.
