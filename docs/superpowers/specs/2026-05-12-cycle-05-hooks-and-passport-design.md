---
sws_artifact: cycle-05-spec
artifact_version: 0.1
locked: 2026-05-12
title: "Cycle #5 — Three MVP hooks + passport.json schema"

cycle_index: 5
original_roadmap_index: 3
predecessor: cycle-04-auto-resolve-defaults
banner_after_completion: "🚧 v0.1 in design"

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §5 Hooks and external integrations"
  brainstorm_confirm: "2026-05-12 user approval: I agree on all 6. execute"

deliverables:
  code_changes:
    - scripts/sws_hook_utils.py
    - scripts/sws_hook_pre_edit_backup.py
    - scripts/sws_hook_stop_passport.py
    - scripts/sws_hook_session_start.py
  hook_config:
    - hooks/hooks.json
  test_changes:
    - tests/test_sws_hook_utils.py
    - tests/test_sws_hook_pre_edit_backup.py
    - tests/test_sws_hook_stop_passport.py
    - tests/test_sws_hook_session_start.py

locked_decisions:
  D1_passport_schema_minimal:
    choice: "5 fields per entry: cycle, agent, file, change_summary, next_step"
    rationale: "Submission-phase fields (journal slug, DOI, submission date) come in original cycle #10 (now renumbered)."

  D2_state_model_append_only:
    choice: "Each Stop adds a new entry to data['history']. 'Where you left off' = last entry."
    rationale: "Append-only history is safe on concurrent re-init; no entry is ever overwritten."
    stub_written_by: "cycle-#2 init: {\"sws_version\": \"0.1\", \"cycle\": 0, \"history\": []}"

  D3_stop_trigger_files_only:
    choice: "Stop hook appends only when at least one file was modified during the turn."
    rationale: "Empty turns produce no passport entry. Avoids spurious entries for query-only sessions."

  D4_implementation_language:
    choice: "Python 3.9+ stdlib. Each hook is scripts/sws_hook_<purpose>.py."
    constraint: "Pure stdlib only. No pyyaml. Marker frontmatter parsed with minimal regex/key-value scanner."

  D5_marker_scoping_shared_helper:
    choice: "scripts/sws_hook_utils.py exposes check_marker(cwd: Path) -> dict | None"
    behavior: "Returns parsed marker dict if SWS is active in cwd; None for silent no-op."
    every_hook: "calls check_marker() first and early-returns on None"

  D6_backup_failure_mode_block:
    choice: "If backup shutil.copy2() raises, hook exits non-zero → Claude Code blocks the Edit/Write call."
    rationale: "The whole point is data-loss safety. Failing open would defeat it."

passport_schema:
  fields:
    cycle:
      type: integer
      description: "Monotonically increasing cycle counter. Starts at 1 for the first real entry (stub is cycle 0)."
    timestamp:
      type: string
      format: "ISO 8601 UTC (Z suffix)"
      description: "When the Stop hook fired."
    agent:
      type: "string | null"
      description: "Null in v0.1; reserved for agent-driven cycles in v0.2."
    file:
      type: "array[string]"
      description: "Sorted unique relative paths of all files modified during the turn."
    change_summary:
      type: "string | null"
      description: "Null in v0.1; agent fills this in v0.2."
    next_step:
      type: "string | null"
      description: "Null in v0.1; agent fills this in v0.2."

hook_inventory:
  hook_a:
    name: sws_hook_pre_edit_backup.py
    trigger: "PreToolUse matching Edit|Write"
    behavior: |
      Creates <filename>.backup_pre_<event>.<ext> via shutil.copy2 before docx (always)
      or *.{tex,bib,cls} (when marker format: latex). No-op if target file does not
      exist yet (nothing to back up).
    failure_mode: "exit non-zero to block the tool call; prints clear error to stderr"

  hook_b:
    name: sws_hook_stop_passport.py
    trigger: "Stop"
    behavior: |
      Extracts modified-file paths from the session's tool-use history (Edit/Write/MultiEdit).
      If no files modified, exits 0 with no write. Otherwise appends a new entry to
      claude_memory/passport.json history list.
    failure_mode: "exit 0 on missing/corrupt passport (don't crash the session)"

  hook_d:
    name: sws_hook_session_start.py
    trigger: "SessionStart"
    behavior: |
      Reads last passport history entry; prints one line: cycle summary.
      If article_type != funding-proposal AND no journal-style overlay is cached,
      prints a nudge to run /sws:resolve-journal-style.
    failure_mode: "silent on all read/parse errors; never blocks session start"

marker_scoping:
  helper: "sws_hook_utils.check_marker(cwd: Path) -> dict | None"
  marker_filename: ".sws-project.local.md"
  contract: "Returns None if marker absent; returns parsed top-level scalar dict if present."
  parser: "Minimal regex/key-value scanner; handles string, bool, int, null scalars only at top level."
  nested_keys: "Nested keys (e.g., notebooklm.enabled) are NOT parsed; hooks don't need them in v0.1."

edge_cases:
  E1_new_file:
    case: "Target file doesn't exist yet (first Write to a new path)"
    action: "Hook (a) no-op — nothing to back up."
  E2_unknown_format:
    case: "Marker has format value other than docx or latex"
    action: "Hook (a) treats as docx-only (default behavior — backs up .docx only)."
  E3_missing_corrupt_passport:
    case: "passport.json is missing or corrupt"
    action: "Hook (b) exits 0 quietly; doesn't crash the session."
  E4_multiple_files:
    case: "Multiple files modified in one turn"
    action: "Hook (b) deduplicates and sorts before writing the entry."
  E5_tool_history_field_variation:
    case: "Tool-use history field name differs across Claude Code versions"
    action: "Hook (b) probes multiple likely fields (tool_uses, tool_calls, transcript); falls back to empty list."
  E6_missing_journal_style_dir:
    case: "Manuscript/_journal-style/ directory doesn't exist yet"
    action: "Hook (d) treats as 'no overlay' and prints the nudge."
  E7_backup_write_fails:
    case: "Backup write fails (disk full, permission denied)"
    action: "Hook (a) exits non-zero to block the tool call; prints clear error to stderr."
  E8_backup_already_exists:
    case: "Backup file already exists from a prior edit in the same session"
    action: "Hook (a) overwrites it (no rotation in v0.1; user prunes manually)."

what_stays_v02:
  - "Hook (c): PostToolUse docx write — validate schema compliance after each write (architecture sketch §5)"
  - "Hook (e): UserPromptSubmit — inject journal-style overlay as system context when present (architecture sketch §5)"
  - "Richer passport schema for cycle #10 (submission-phase fields: journal slug, DOI, submission date)"
  - "agent field populated by agent-driven cycles"
  - "change_summary and next_step filled by agent at cycle close"
---

# Cycle #5 — Three MVP hooks + passport.json schema

Frontmatter above is the source of truth. This body is orientation only.

## Why

Cycle-memory hooks were listed as a SWS differentiator from the architecture sketch onward.
They are the mechanism that lets a fresh session pick up without burning tokens on re-discovery.
The backup hook is the data-loss safety net that makes docx editing safe inside Claude Code.

## What ships

Four Python scripts (pure stdlib) under `scripts/`:
`sws_hook_utils.py` — shared marker-scoping helper used by all three hooks.
`sws_hook_pre_edit_backup.py` — PreToolUse: backs up docx (and latex sources) before every edit.
`sws_hook_stop_passport.py` — Stop: appends a history entry to `claude_memory/passport.json`.
`sws_hook_session_start.py` — SessionStart: prints cycle summary + journal-style nudge.

Hook config at `hooks/hooks.json` (plugin wrapper format confirmed by `plugin-dev:hook-development`).

Four new test modules (~25 tests total). Full suite expected at ~101 tests.

## What stays v0.2

See `what_stays_v02` in frontmatter.
