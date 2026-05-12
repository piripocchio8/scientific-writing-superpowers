---
sws_artifact: cycle-03-spec
artifact_version: 0.1
locked: 2026-05-12
title: "Cycle #3 — init-project C4 append (smart-merge promote from v0.2)"

cycle_index: 3
predecessor: cycle-02-init-project
successors: [cycle-04-profiles]
banner_after_completion: "🚧 v0.1 in design"

sources:
  beta_test_finding: "2026-05-12 beta test: binary [replace, skip] for C4 forces users to lose either hand-curated CLAUDE.md content or SWS cross-refs. Append was always the right default for the common case."
  cycle_2_spec: docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md
  v02_backlog_origin: claude_memory/project_v02_backlog.md (entry: "init-project smart-merge, deferred 2026-05-12")

deliverables:
  code_changes:
    - scripts/sws_init_project.py
  skill_changes:
    - skills/init-project/SKILL.md
  test_changes:
    - tests/test_init_project.py

locked_decisions:
  D1_merge_location:
    choice: utility-layer (scripts/sws_init_project.py)
    rationale: unit-testable, rollback-safe, consistent with cycle-#2 pattern. Skill stays prose-only.

  D2_idempotency:
    choice: HTML-comment markers
    open_marker: "<!-- SWS-managed start: do not hand-edit between the markers below -->"
    close_marker: "<!-- SWS-managed end -->"
    behavior: "On re-run: if both markers present, replace between them. If one or neither marker present (E2), append fresh at end."
    rationale: "Plain text delimiters survive any editor, git diff cleanly, require no YAML parsing of user content."

  D3_section_content:
    choice: cross-refs only
    canonical_metadata: .sws-project.local.md (not injected into user CLAUDE.md)
    rationale: "User's CLAUDE.md is their space. SWS injects only the pointers agents need to find the marker file and canonical references. No per-paper notes placeholder — user has their own."

  D4_rollback:
    choice: in-memory original content
    mechanism: "_execute_op stores pre-append content in op.extra[\"_original_content\"]; _rollback_op restores it via target.write_text(original)."
    rationale: "Same undo-log pattern as cycle #2. No temp files, no backup-on-disk."

  D5_v02_still_deferred:
    items:
      - C5 move (rotate claude_memory/ to _archive/)
      - frontmatter merge for user-existing YAML in CLAUDE.md
      - content-aware section placement
    rationale: "These require YAML parsing of user content or more complex placement logic. Not needed to solve the beta-test complaint."

edge_cases:
  E1_no_claude_md:
    case: "CLAUDE.md missing at append-time"
    action: "FileNotFoundError; rollback executes. Defensive — C4 only fires when CLAUDE.md is present, so this should not reach production unless plan is mis-constructed."
  E2_partial_markers:
    case: "Only one of the two markers present (corrupted prior run)"
    action: "Treat as no-markers; append fresh at end. Produces a duplicate section if the open-marker is present but close-marker is missing — accepted v0.1 limitation."
  E3_marker_in_user_content:
    case: "Marker string appears in user content above the SWS section"
    action: "Between-marker content gets clobbered. Accepted v0.1 limitation. v0.2 could use content-hash markers."
  E4_rerun_different_handle:
    case: "Re-run with a different short_handle"
    action: "Markers detected; section replaced. Old short_handle reference is gone. Marker file is the canonical source."

v02_backlog_status:
  c4_append: shipped_in_cycle_03 (2026-05-12)
  c5_move: still_v02
  frontmatter_merge: still_v02
  content_aware_placement: still_v02
---

# Cycle #3 — init-project C4 append

Frontmatter above is the source of truth. This body is orientation only.

## Why

Beta test on 2026-05-12 confirmed the cycle-#2 binary (`[replace, skip]`) is wrong for the common case: a researcher running `/sws:init-project` in a folder that already has a hand-curated CLAUDE.md. `replace` destroys their notes; `skip` leaves agents without SWS context. The append option was always planned (see cycle-#2 spec `Q1` detection set, which listed `[a]ppend` alongside `[r]eplace`) but was deferred to v0.2 to keep cycle #2 scope tight.

## What ships

A single new op kind `append_sws_section` in `scripts/sws_init_project.py`. When C4 resolution is `append`, `build_plan` emits this op instead of a `render_template` op for `CLAUDE.md`. The `_execute_op`/`_rollback_op` pair handles it atomically: store the pre-append content, write the merged file, record undo. On re-run, HTML-comment markers let the code replace the existing SWS section in place rather than duplicating it.

`scan_conflicts` gains a third option (`append`) in C4's option list. `SKILL.md` Step c gains the full `[r]eplace / [a]ppend / [s]kip` description.

Six new unit tests cover: no-marker append, idempotent marker replace, rollback, missing-file error, C4-options-include-append, build-plan-emits-append-op.

## What stays v0.2

C5 `[m]ove`, frontmatter merge for existing YAML in user CLAUDE.md, content-aware section placement. See `v02_backlog_status` in frontmatter.
