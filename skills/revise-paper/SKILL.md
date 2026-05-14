---
name: sws:revise-paper
description: "This skill should be used when the user invokes /sws:revise-paper, says 'revise the paper', 'polish the draft', 'run the revision pipeline', 'prepare the final docx', or similar — and the cwd is an SWS project with drafted sections at _drafts/<section>.md. Runs a sequential four-pass pipeline: consistency-checker → reviser (full or fast) → humanizer → style-enforcer, producing Manuscript/<paper-name>.docx."
---

# /sws:revise-paper — Full revision pipeline (sequential orchestrator)

Runs the four pipeline passes in strict order: consistency check → reviser → humanizer → style-enforcer. Each pass reads the previous pass's output from disk. This is sequential by design (D4): passes are not independent, so the cycle-#7 parallel fan-out pattern does not apply here.

## Flags

- `--skip-humanize` — skip the humanizer pass; style-enforcer reads `-revised.md` files directly.
- `--skip-lint` — skip the AI-tells linter that runs inside the humanizer agent. The linter is informational (R6): it does not gate the pipeline, but disabling it skips the cleanup nudge entirely.
- `--skip-style` — skip style-enforcer; pipeline ends after humanizer. No `.docx` is produced. Use when you only want polished markdown.

## Steps

### 1. Resolve marker and overlay

Check `$PAPER_ROOT/.sws-project.local.md`. If absent, print "not an SWS project (no .sws-project.local.md found)" and exit.

Run the overlay resolver:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
    "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
    --paper "$PAPER_ROOT"
```

If `profile_set: false`, print "no profile set — run /sws:set-profile <name> first" and exit. Read `RESOLVED_WORD_TOTAL` from the resolved overlay for the tier decision in step 4.

### 2. Locate draft files

Glob `${PAPER_ROOT}/_drafts/<section>.md` (plain drafts, not `-revised` or `-humanized` suffixed). If none found, print:

```
no draft files found in _drafts/ — run /sws:draft-paper or /sws:draft-section first
```

and exit. List the found files so the user knows what will be revised.

### 3. Dispatch consistency-checker

Dispatch the `consistency-checker` agent via the Task tool. Pass `PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT` in env. The agent:

- reads all `_drafts/<section>.md` files in profile section order
- runs `scripts/sws_consistency_check.py`
- writes `${PAPER_ROOT}/_review/consistency-report.md`

**If block-severity findings exist:** print a summary of the findings (count by category, first three excerpts) and ask the user:

```
Consistency check found <N> block-severity issue(s). Continue with revision? [y/n]
```

Do not auto-proceed. Wait for explicit user confirmation before continuing. Warn-severity findings are logged to the report but do not pause the pipeline.

Note: if `profile == funding-proposal`, consistency-checker prints "profile not supported for consistency check in v0.1; manual review required" and exits 0 (D19). The pipeline continues.

### 4. Decide reviser tier and dispatch

Read `RESOLVED_WORD_TOTAL` from the overlay:

- `RESOLVED_WORD_TOTAL < 1500` → dispatch `reviser-fast` (per-section passes; writes `_drafts/<section>-revised.md` + `_review/revision-notes-<section>.md` per section).
- `RESOLVED_WORD_TOTAL >= 1500` → dispatch `reviser-full` (whole-paper pass; writes `_drafts/<section>-revised.md` for all sections + `_review/revision-notes-full.md`).

The tier decision is made here in the skill, not inside the agent prompts (D4 short_profile_carve_out). Profiles that naturally fall below 1500 words (editorial, communication, mini-review, commentary-reply) get reviser-fast automatically. Dispatch via the Task tool; wait for completion before proceeding.

### 5. Dispatch humanizer

Unless `--skip-humanize` is set: dispatch `humanizer` agent on the revised drafts (`_drafts/<section>-revised.md`). The humanizer:

- reads each `-revised.md` file
- runs the AI-tells linter (`scripts/sws_lint_ai_tells.py`) internally (unless `--skip-lint` was passed to this skill, in which case `--skip-lint` is forwarded to the humanizer)
- rewrites flagged tells via sentence-level polish
- writes `_drafts/<section>-humanized.md`

Important: humanizer skips a section if `<section>-humanized.md` already exists and is newer than `<section>-revised.md`. This preserves any hand-edits the user made to a previous humanized draft (R4).

The linter is informational only inside this pipeline (R6). It does not gate the humanizer or the skill — the humanizer resolves flagged tells via rewrite and moves on. To view raw linter output without running the full pipeline, use `/sws:lint-ai-tells <file>`.

### 6. Dispatch style-enforcer

Unless `--skip-style` is set: dispatch `style-enforcer` agent. It reads humanized drafts (or revised drafts if `--skip-humanize`) in profile section order and:

1. calls `scripts/sws_write_docx.py` to generate `${PAPER_ROOT}/Manuscript/<paper-name>.docx` with SWS style canon
2. calls `scripts/sws_apply_chemistry_format.py` on the result (skipped automatically if `format: latex`)

**Backup discipline:** the cycle-#5 PreToolUse hook fires automatically before style-enforcer's docx write, producing `<paper-name>.backup_pre_style_enforcer_<timestamp>.docx`. No additional backup logic is needed here (D16).

### 7. Final summary

Print a structured summary:

```
/sws:revise-paper complete
  consistency:  <N> block, <M> warn — see _review/consistency-report.md
  reviser:      <tier> — <words before> → <words after> words
  humanizer:    <N> sections polished, <K> AI-tells resolved  [skipped if --skip-humanize]
  style:        SWS canon applied, chemistry pass done        [skipped if --skip-style]
  output:       Manuscript/<paper-name>.docx
```

If `--skip-style`, omit the docx line and note that no `.docx` was written.

## When to invoke

- Explicit `/sws:revise-paper`.
- User triggers from the description above.
- Do NOT invoke without a marker, without a set profile, or without at least one `_drafts/<section>.md` file.
