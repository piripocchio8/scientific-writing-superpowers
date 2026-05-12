---
sws_artifact: cycle-04-spec
artifact_version: 0.1
locked: 2026-05-12
title: "Cycle #4 — Auto-resolve safe defaults + post-apply summary"

cycle_index: 4
predecessor: cycle-03-claude-md-append
banner_after_completion: "🚧 v0.1 in design"

sources:
  beta_test_finding: "2026-05-12 follow-up: cycle #3 shipped C4=append but still prompts per conflict. Per-conflict prompts are friction. Safe defaults exist for all 6 classes; auto-resolve silently and surface decisions at the single plan-presentation step."
  cycle_3_spec: docs/superpowers/specs/2026-05-12-cycle-03-claude-md-append-design.md

deliverables:
  code_changes:
    - scripts/sws_init_project.py
  skill_changes:
    - skills/init-project/SKILL.md
  test_changes:
    - tests/test_init_project.py

locked_decisions:
  D1_auto_resolve_all_six:
    choice: auto-resolve all 6 conflict classes with safe defaults; no per-conflict prompts
    rationale: "Plan-presentation step (Step e) is the single consolidated review + cancel point. Safe defaults are data-loss-safe for all classes."

  D2_safe_defaults_never_destructive:
    choice: "accept/append/keep/proceed only; replace never defaults"
    rationale: "C4=replace and C5=replace destroy user content. They only fire on explicit user opt-in (CLI flag or unambiguous NL signal)."

  D3_override_mechanism:
    choice: CLI flags + NL parse signals
    cli_flags: [--c1, --c2, --c3, --c4, --c5, --c6]
    flag_values: "each flag takes a string matching the conflict's options list"
    nl_parse_signals:
      - '"overwrite my CLAUDE.md" / "replace existing CLAUDE.md" → c4=replace'
      - '"skip the docx move" / "leave paper.docx where it is" → c1=skip'
      - '"replace my memory" / "overwrite claude_memory" → c5=replace'
      - '"skip the claude_material rename" → c3=skip'

  D4_helper_in_utility_layer:
    choice: "SAFE_DEFAULTS dict + default_resolutions() pure function in scripts/sws_init_project.py"
    rationale: "Single source of truth for the safe-default table; unit-testable; skill stays prose-only."

  D5_defaults_cli_subcommand:
    choice: "new subcommand: python3 sws_init_project.py defaults --conflicts <conflicts.json>"
    rationale: "Cleaner than embedding Python -c calls in the skill prose. Skill calls scan → defaults → (apply overrides) → plan."

  D6_plan_presentation_shows_auto_resolutions:
    format: |
      Detected N conflicts; auto-resolved with safe defaults:
        C4=append (preserves your CLAUDE.md; appends SWS-managed section)
        C1=accept (moves paper.docx → Manuscript/paper.docx)
        C3=accept (renames claude_material/ → scratch/)

      [If any user-supplied overrides:]
      User-supplied overrides:
        C4=replace (will overwrite your CLAUDE.md — confirm in plan below)

      Plan (N ops):
        ...

      Apply? [apply/cancel]

  D7_post_apply_user_file_summary:
    choice: "New section 'What SWS did with your existing files' in Step g"
    format: "One line per user-pre-existing file touched; omit section entirely if no user files were touched."

safe_defaults_table:
  C1: {default: accept, rationale: "mv to Manuscript/<filename> — reversible"}
  C2: {default: accept, rationale: "mv loose figs to Figures/main/ — reversible"}
  C3: {default: accept, rationale: "rename claude_material/ to scratch/ — reversible"}
  C4: {default: append, rationale: "preserve CLAUDE.md verbatim; append SWS-managed section — non-destructive"}
  C5: {default: keep, rationale: "leave claude_memory/ untouched — SWS does not write MEMORY.md or passport.json"}
  C6: {default: proceed, rationale: "re-init flow: load existing marker values as defaults, write merged marker"}

override_mechanism:
  cli_flags:
    - --c1 (accepts: accept, skip)
    - --c2 (accepts: accept, skip)
    - --c3 (accepts: accept, skip)
    - --c4 (accepts: replace, append, skip)
    - --c5 (accepts: keep, replace)
    - --c6 (accepts: proceed, abort)
  nl_parse_signals:
    c4_replace: ['"overwrite my CLAUDE.md"', '"replace existing CLAUDE.md"', '"replace my CLAUDE.md"']
    c1_skip: ['"skip the docx move"', '"leave paper.docx where it is"']
    c5_replace: ['"replace my memory"', '"overwrite claude_memory"', '"replace existing memory"']
    c3_skip: ['"skip the claude_material rename"']
  validation: "If override value not in conflict.options → abort before plan with clear message naming invalid value and valid options."
  destructive_guard: "c4=replace and c5=replace MUST NOT default; only fire on explicit opt-in."

edge_cases:
  E1_invalid_override_value:
    case: "User supplies --c4=foobar (not in C4.options)"
    action: "Skill validates and errors out before calling plan with: Error: --c4=foobar is not a valid override. Valid options for C4: [replace, append, skip]."
  E2_override_for_absent_conflict:
    case: "User supplies --c4=replace but no CLAUDE.md exists (C4 not detected)"
    action: "Skill silently ignores the override. Accepted v0.1 behavior; documented."
  E3_new_class_no_default:
    case: "A new conflict class added in v0.2 is not in SAFE_DEFAULTS"
    action: "default_resolutions() omits it from result; caller should escalate to prompt for that class only."
  E4_only_destructive_options:
    case: "A future conflict class has only destructive options (e.g., delete X)"
    action: "SAFE_DEFAULTS returns None or skip for that class; skill defers to user. Documentary only."

what_stays_v02:
  - "--interactive flag to opt back into per-conflict prompts"
  - "utility-level validate_resolutions(conflicts, resolutions) for stronger checking"
  - "C5 move (rotate claude_memory/ to _archive/) — still v0.2"
  - "frontmatter merge for existing YAML in user CLAUDE.md"
  - "content-aware section placement"
---

# Cycle #4 — Auto-resolve safe defaults + post-apply summary

Frontmatter above is the source of truth. This body is orientation only.

## Why

Beta-test follow-up (2026-05-12): cycle #3 shipped C4=append, but the skill still prompts the user once per conflict. With 3 or 6 conflicts, that is 3-6 sequential prompts before anything happens. All 6 defaults are data-loss-safe, so auto-resolving silently at this point is strictly better UX. The single consolidated review at the plan-presentation step (Step e) already gives the user a cancel point before any disk write.

## What ships

`SAFE_DEFAULTS` dict and `default_resolutions(conflicts)` pure function added to `scripts/sws_init_project.py`. New `defaults` CLI subcommand reads a conflicts JSON file and prints the safe-default resolution dict. Skill Step c is rewritten to call `defaults` and merge user overrides instead of prompting per conflict. Step e gains an auto-resolutions header. Step g gains a "What SWS did with your existing files" section.

Six new `--c1`..`--c6` flags added to the skill's Step a named-arg list with NL-parse counterparts. Validation aborts early if an override value is not in the conflict's options list.

## What stays v0.2

See `what_stays_v02` in frontmatter.
