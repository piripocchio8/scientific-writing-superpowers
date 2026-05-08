---
sws_artifact: cycle-02-spec
artifact_version: 0.1
locked: 2026-05-08
title: "Cycle #2 — /sws:init-project and the 3 templates"

cycle_index: 2
predecessor: cycle-01-foundation
successors: [cycle-03-hooks, cycle-04-profiles]
banner_after_completion: "🚧 v0.1 in design"   # transitions to alpha only after cycle #7

sources:
  architecture_sketch: docs/superpowers/specs/2026-05-08-architecture-sketch-design.md
  decisions_log: claude_memory/project_decisions_so_far.md (2026-05-08 cycle-#2 brainstorm entry)
  marker_schema: references/marker-schema.md
  folder_topology: references/folder-topology.md
  typography_canon: claude_memory/feedback_docx_typography.md
  cycle_1_plan: docs/superpowers/plans/2026-05-08-cycle-01-foundation.md   # reference only — historical

deliverables:
  slash_commands:
    - "/sws:init-project"
  skills:
    - skills/init-project/SKILL.md
  templates:
    - templates/sws-project-marker.template     # → <paper-root>/.sws-project.local.md
    - templates/manuscript-claude-md.template   # → <paper-root>/CLAUDE.md (per-paper)
    - templates/manuscript-memory-md.template   # → <paper-root>/claude_memory/MEMORY.md (per-paper)
  references:
    - references/docx-style.md   # typography canon; consumed by docx-touching agents from cycle #5+
    - references/python-env.md   # Python env policy + skill preflight pattern
  scripts:
    - scripts/sws_render_template.py
  tests:
    - tests/test_render_template.py
    - tests/test_init_project_planner.py
    - tests/test_python_env.py

locked_decisions:
  Q1_existing_files_behavior:
    choice: smart-merge
    detection_set:
      C1: "root *.docx → suggest move to Manuscript/"
      C2: "loose Figures/*.{png,jpg,svg,pdf} (no main/ or SI/ subdir) → suggest move to Figures/main/"
      C3: "claude_material/ (legacy hDF-style) → suggest rename to scratch/"
      C4: "existing root CLAUDE.md → [r]eplace / [a]ppend (under '## SWS-managed' section) / [s]kip"
      C5: "existing claude_memory/ → [k]eep / [m]ove to _archive/ / [r]eplace"
      C6: "existing .sws-project.local.md → re-init flow: load existing values, prompt edits, write merged"
    interaction: per-conflict prompts with suggested-default ([Y/n/skip/manual])
    fallthrough: CWDs with files but zero class matches → fresh-init mode (skip §c)

  Q2_input_gathering:
    choice: args-plus-interactive-fill-in
    waterfall: [named_args, "$ARGUMENTS natural-language parse", interactive_prompts]
    defaults_from: references/marker-schema.md

  Q3_what_init_produces:
    choice: minimal-plus-initial-state-files
    artifacts:
      - folder topology (per references/folder-topology.md base_layout, conditional on marker fields)
      - 3 templated files (marker, per-paper CLAUDE.md, per-paper MEMORY.md)
      - claude_memory/passport.json (cycle: 0 stub)
      - claude_memory/fs_index.json (initial snapshot via scripts/sws_fs_index.py)
    deferred_to_cycle_5:
      - "Manuscript/<short_handle>.docx (or .tex) skeleton — drafter generates with article_type sections + SWS styles"
    excluded_v0_1:
      - per-paper .gitignore   # uneven adoption; potential confusion

  Q4_smart_merge_scope:
    choice: detection-plus-suggested-default
    set_size: 6
    set_reference: locked_decisions.Q1_existing_files_behavior.detection_set

  Q5_input_set:
    user_provided:
      article_type: { type: enum, options: 9-profile-set, required: true }
      language: { type: enum, options: [en, it], default: en }
      format: { type: enum, options: [docx, latex], default: docx }
      target_journal: { type: slug, required_when: "article_type != funding-proposal" }
      target_call: { type: slug, required_when: "article_type == funding-proposal" }
      first_author: { type: string, required: true, slugified: true }
      year: { type: int, default: system_date_year, override_allowed: true }
      co_authors_present: { type: bool, required: true }
      notebooklm.enabled: { type: bool, default: false }
    computed:
      short_handle: '<first_author_slug> + ("_et_al_" if co_authors_present else "_") + <year>'
      manuscript_filename_default: 'Manuscript/<short_handle>.<docx|tex>'
    dropped:
      paper_title: "changes during refinement; not stable enough to template against"

  Q5b_field_naming:
    choice: rename-active-profile-to-article-type
    landed_in_commit: 8e4378e
    rationale: matches every journal-portal terminology; no consumer depends on field yet

  Q6_atomicity:
    choice: plan-then-apply
    apply_engine: in-memory undo log; reverse on per-op failure or ctrl-C or disk-full
    user_files_safety: only ops user approved at §c can touch user-pre-existing files

  custom_typography:
    spec_location: references/docx-style.md
    canonical_styles: [SWS-Body, SWS-H1, SWS-H2, SWS-Caption, SWS-References]
    forbidden_word_styles: [Heading 1, Heading 2, Heading 3, Title, Subtitle]
    consumers_first_cycle: 5
    rationale_memory: claude_memory/feedback_docx_typography.md

  python_env_policy:
    spec_location: references/python-env.md
    min_version: "3.9"
    deps_state_v0_1: stdlib-only through cycle #4
    first_real_dep: cycle #5 (likely python-docx)
    preflight_pattern: |
      python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' \
        || { echo "SWS requires Python ≥ 3.9. Activate or install a compatible env, then re-run."; exit 1; }

template_substitution:
  engine: string.Template (Python stdlib)
  mode: substitute (strict; missing variable raises KeyError)
  syntax: ${var}
  utility: scripts/sws_render_template.py
  cli_signature: "python sws_render_template.py --template <path> --vars-file <vars.json> --out <path>"
  rationale: consistent with cycle #1 sws_fs_index.py — pure stdlib, model-orchestrated, deterministic substitution

orchestration_steps:
  a: argument-resolution (3-tier waterfall — named args → $ARGUMENTS NL parse → interactive prompts)
  b: detection-scan (one-shot walk for the 6 classes)
  c: per-conflict-prompts (suggested-default UX)
  d: plan-assembly (ordered op list — mkdir → mv → render_template → write_json)
  e: plan-presentation (numbered list, [apply/cancel])
  f: apply-with-rollback (undo log)
  g: post-apply (write passport.json cycle 0; run sws_fs_index.py; print summary)

edge_cases:
  E1_unsafe_cwd: { case: "CWD is $HOME / / read-only / no write perm", action: "refuse before §a" }
  E2_arg_mismatch_journal: { case: "article_type != funding-proposal AND --target-call given", action: "error: arg mismatch; suggest --target-journal" }
  E3_funding_proposal_no_call: { case: "article_type == funding-proposal AND no target_call in args/NL", action: "interactive prompt for target_call" }
  E4_unicode_first_author: { case: "first_author has Unicode/punctuation (Müller, O'Brien, Søren)", action: "slugify: NFD-decompose → drop-non-ASCII → lowercase → strip-apostrophes/hyphens. Müller→muller, O'Brien→obrien" }
  E5_empty_first_author: { case: "first_author empty/whitespace", action: "re-prompt" }
  E6_implausible_year: { case: "year integer-but-far-from-current (e.g. 1899, 2099)", action: "accept; user knows best" }
  E7_partial_nl_parse: { case: "NL parse can't extract a required field", action: "fill what extracts; interactive-prompt the rest" }
  E8_malformed_existing_marker: { case: "existing .sws-project.local.md has unparseable YAML or missing required fields", action: "parse what's possible; prompt for missing/invalid fields; write merged; never crash" }
  E9_cancel_at_plan: { case: "user types 'cancel' at §e", action: "exit cleanly; no disk writes" }
  E10_failure_mid_apply: { case: "ctrl-C / disk-full / perm-denied during §f", action: "reverse undo log; print rollback summary" }

cycle_5_followups:
  manuscript_skeleton_generator:
    cycle: 5
    consumer: drafter agent
    behavior: "generates Manuscript/<short_handle>.docx with article_type-specific section structure + SWS custom styles applied per references/docx-style.md"
  python_dep_infrastructure:
    cycle: 5
    artifacts: [requirements.txt at repo root, scripts/sws_setup_env.sh]
    trigger: "first real Python dep (likely python-docx for OOXML)"

v02_backlog_from_this_brainstorm:
  - "Heavy content-aware smart-merge (parse manuscript metadata, detect figure caption styles)"
  - "--root <path> arg (invoke against explicit dir, not CWD)"
  - "Stage-and-swap atomicity (Q6 option d) for high-stakes existing manuscripts"
  - "LaTeX-specific smart-merge classes (main.tex at root, .bib at root) when format=latex"
  - "Dedicated /sws:migrate slash command for heavy legacy-project restructuring"
---

# Cycle #2 — /sws:init-project and the 3 templates

The frontmatter is the source of truth. This body is orientation only — architectural rationale lives in the architecture-sketch design doc; constitutional rules in `claude_memory/feedback_*`; per-decision history in the decisions log.

## §1 Scope, entry point, inputs

`/sws:init-project` is a Claude-Code-native slash command + skill: takes optional named args, parses `$ARGUMENTS` natural-language input for any unset args, then interactively prompts for the remaining required fields. Defaults pulled from `references/marker-schema.md`.

The 9 user inputs and the computed `short_handle` are in `locked_decisions.Q5_input_set`. The `active_profile → article_type` rename landed in commit `8e4378e`. Refusal cases: `edge_cases.E1_unsafe_cwd`.

## §2 Smart-merge + plan-then-apply

7-step orchestration in `orchestration_steps` (a–g). Six conflict classes in `Q1_existing_files_behavior.detection_set` with suggested-default actions. Plan is assembled before any disk write; user confirms a numbered plan; apply executes with in-memory undo-log rollback on failure or interrupt. CWDs with files but zero class matches fall through to fresh-init mode.

## §3 Templates + render utility + style canon

Three `.template` files (consumed by init), one reference doc (consumed from cycle #5+), one Python utility:

- **Marker template**: 8 marker schema fields only; lean.
- **Per-paper CLAUDE.md template**: full project metadata (12 keys) in YAML frontmatter — canonical lookup for any agent that needs paper metadata. Body is ~15 lines of cross-refs to plugin canonical references.
- **Per-paper MEMORY.md template**: empty index; two bootstrap pointers.
- **`references/docx-style.md`**: typography canon spec (the 5 SWS- named styles, forbidden Word built-ins). Cross-refs `feedback_docx_typography.md` for rationale.
- **`scripts/sws_render_template.py`**: stdlib `string.Template` renderer; CLI in `template_substitution.cli_signature`.

## §4 Edge cases, tests, follow-ups

10 edge cases enumerated in `edge_cases`. TDD pattern matches cycle #1: 3 test files cover the deterministic Python concerns (`test_render_template.py`, `test_init_project_planner.py`, `test_python_env.py`). Orchestration is model-driven and gets a manual smoke test post-implementation.

`cycle_5_followups` lists items deferred to cycle #5 (still v0.1): manuscript-skeleton generator + Python-dep infrastructure. `v02_backlog_from_this_brainstorm` lists the genuinely-deferred features that don't ship in any v0.1 cycle.
