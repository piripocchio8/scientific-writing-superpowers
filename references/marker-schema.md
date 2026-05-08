---
sws_artifact: marker-schema
artifact_version: 0.1
locked: 2026-05-06
file_path_in_manuscript_project: <paper-root>/.sws-project.local.md
sources:
  - docs/superpowers/specs/2026-05-08-architecture-sketch-design.md
  - claude_memory/project_decisions_so_far.md (2026-05-06 entries "Hook scoping rule", Section 2 revisions)

schema_version_field: sws_version    # bump on additive minor changes
schema:
  sws_version:
    required: true
    type: string
    valid: ["0.1"]
    default: "0.1"
  active_profile:
    required: true
    type: string
    valid: [full-article, communication, perspective, review-paper, mini-review, editorial, methodological-paper, commentary-reply, funding-proposal]
    default: null   # /sws:init-project asks
  language:
    required: true
    type: string
    valid: [en, it]
    default: en
    note: opt-in to it; other languages = v0.2+
  format:
    required: true
    type: string
    valid: [docx, latex]
    default: docx
    note: one active format per project; docx + main.tex never coexist
  target_journal:
    required: false
    type: "string | null"
    valid: lowercase slug, no spaces (e.g. chembiochem)
    default: null
    populated_by: /sws:resolve-journal-style
  target_call:
    required: false
    type: "string | null"
    valid: lowercase slug, no spaces
    default: null
    populated_by: /sws:resolve-call-rules
  notebooklm.enabled:
    required: true
    type: bool
    valid: [true, false]
    default: false
    when_true_activates: [refs/nlm_uploads/, nlm-librarian agent]
  created:
    required: true
    type: string
    format: ISO 8601 with timezone
    populated_by: /sws:init-project

conditional_triggers:
  call/_directory: { when: "active_profile == funding-proposal", persists_across_profile_change: true }
  refs/nlm_uploads/: { when: "notebooklm.enabled == true" }
  format_aware_agents_use_latex: { when: "format == latex", consumers: [drafter, reviser, style-enforcer, format-checker, table-formatter, equation-handler, figure-caption-writer] }
  pre_edit_backup_extends_to_tex_bib_cls: { when: "format == latex" }

example: |
  ---
  sws_version: 0.1
  active_profile: communication
  language: en
  format: docx
  target_journal: chembiochem
  target_call: null
  notebooklm:
    enabled: false
  created: 2026-05-08T00:00:00Z
  ---

  # free-form notes about this paper-project (preserved across regenerations)

validation_rules:
  - missing_required_field_or_wrong_type → hook prints single warning, falls back to no-op (never crashes session)
  - rewriting_existing_marker_via_init_project → requires --force flag

consumers:
  hooks: [pre-edit backup (a), Stop passport-write (b), SessionStart passport-reload (d)]
  hook_scoping_rule: "every script's first ~3 lines check for marker presence; absent = silent no-op"
  agents: format-aware agents (read format), language-aware agents (read language)
  skills: [/sws:init-project, /sws:resolve-journal-style, /sws:resolve-call-rules]
---

# Marker Schema

Schema for `<paper-root>/.sws-project.local.md`, the file every SWS hook checks before doing anything substantive. Absent marker = silent no-op (microseconds, zero output).

The frontmatter is the source of truth for the schema, the conditional triggers, the example, the validation rules, and the consumer mapping. This body is orientation only; rationale lives in the design doc.

New marker fields land via additive minor-version bumps (`sws_version: 0.2` etc.) with backward-compatible defaults.
