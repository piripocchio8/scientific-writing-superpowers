---
sws_artifact: cycle-08-spec
artifact_version: 0.1
locked: 2026-05-14
title: "Cycle #8 — Revising (5 agents, 5 skills, 3 wrapper scripts, 1 reference doc, 1 linter)"

cycle_index: 8
original_roadmap_index: 6
predecessor: cycle-07-drafting-and-proposal-helpers
banner_after_completion: "🚧 v0.1 in design"

autonomous_run_caveat: |
  This spec was authored autonomously overnight on 2026-05-14 with the user's
  explicit grant of authority ("run everything in cycle 8 that does not need
  my intervention. Go with recommended options and then I'll revise this
  tomorrow"). Every locked decision below carries a one-line `rationale` so
  the user can re-decide each in the morning before the PR merges. The PR is
  opened in draft state to make tomorrow's revision low-friction.

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §3 (roster lines 237–240) + §7 (cycle order line 487)"
  prior_cycle_deferrals:
    - "cycle-07 D5: linter for AI-tells deferred to cycle #8 once we have real false-positive data"
    - "cycle-07 D11: references/chemistry-formatting.md (italic species, sub/superscripts, italic Latin abbreviations, bold figure-label prefix) deferred to cycle #8"
    - "cycle-07 D22: WRITE wrappers for DOCX/XLSX deferred to cycle #8 (reviser + style-enforcer needs)"
  related_memory:
    - "claude_memory/project_roster_v0.1.md (reviser=Opus/Sonnet split, humanizer=Haiku, style-enforcer=Sonnet bumped from Haiku for docx XML risk, consistency-checker=Sonnet)"
    - "claude_memory/feedback_docx_typography.md (Arial-based custom-style canon)"
    - "references/docx-style.md (YAML canon for SWS-Body/H1/H2/Caption/References)"
    - "claude_memory/feedback_ai_writing_tells.md (seed for the linter rules)"
    - "claude_memory/feedback_subagent_dispatch.md (parallel dispatch)"
    - "claude_memory/feedback_integration_smoke.md (final task = real e2e smoke)"

scope:
  deliverable: "First usable revising pipeline. End of cycle: a user who has drafted a paper or proposal via /sws:draft-paper (cycle #7) can run /sws:revise-paper to take the assembled markdown drafts through consistency check → reviser → humanizer → style-enforcer and out as a final .docx with SWS style canon and chemistry formatting applied."
  not_in_scope:
    - "abstract-writer agent (D7 of cycle #7 places abstract REFINEMENT in cycle #8; reviser-full is sufficient — no dedicated abstract-writer agent. Spec D2 below)"
    - "xlsx WRITE wrapper (proposal-budget xlsx auto-fill deferred to cycle #10 per v0.2 backlog)"
    - "Italian section of ai-writing-tells.md / chemistry-formatting.md (Italian opt-in deferred to v0.2+ per cycle-07 D5 lock)"
    - "format: latex deep handling (style-enforcer skips when format=latex per docx-style.md rule 4)"
    - "Inline docx-comment annotations from consistency-checker (report file only, mirrors cycle-07 D15 for proposal-compliance-helper)"
    - "Per-coauthor voice profiles for the reviser (style calibration ships in cycle #10 — reviser reads _voice/profile.md if present, ignores it otherwise)"
    - "NLM-grounded claim verification (claim-verifier is cycle #9; consistency-checker in cycle #8 stays text-internal — refs/figs/abbreviations, no external lookup)"

deliverables:
  reference_docs:
    - references/chemistry-formatting.md       # cycle-07 D11 — italic species, sub/superscripts, Latin abbrevs, bold figure-label prefix
  scripts:
    - scripts/sws_write_docx.py                # markdown → .docx with SWS style canon (WRITE wrapper, cycle-07 D22)
    - scripts/sws_restyle_docx.py              # re-apply SWS styles to an existing .docx (style-enforcer's hammer)
    - scripts/sws_apply_chemistry_format.py    # apply chemistry-formatting patterns to a .docx (italic species, sub/super, etc.)
    - scripts/sws_lint_ai_tells.py             # context-aware AI-tells linter (cycle-07 D5)
    - scripts/sws_consistency_check.py         # static-analysis core of consistency-checker (parses markdown drafts, returns findings JSON)
  agents:
    - agents/reviser-full.md                   # Opus 4.7 xhigh — full-paper passes
    - agents/reviser-fast.md                   # Sonnet 4.6 high — single-section / paragraph passes
    - agents/humanizer.md                      # Haiku 4.5 medium — AI-tells cleanup, sentence-level polish
    - agents/style-enforcer.md                 # Sonnet 4.6 high — produces the final .docx (chemistry + style canon)
    - agents/consistency-checker.md            # Sonnet 4.6 high — refs/figs/abbreviations/citation-key uniqueness
  skills:
    - skills/revise-paper/SKILL.md             # /sws:revise-paper (sequential orchestrator)
    - skills/revise-section/SKILL.md           # /sws:revise-section <section> (single-section reviser-fast pass)
    - skills/enforce-style/SKILL.md            # /sws:enforce-style (style-enforcer on a single .docx)
    - skills/check-consistency/SKILL.md        # /sws:check-consistency (consistency-checker standalone)
    - skills/lint-ai-tells/SKILL.md            # /sws:lint-ai-tells <file> (linter standalone)
  profile_updates:
    - profiles/full-article.md                 # agents_inactive list extended for cycle-#8 agents
    - profiles/communication.md
    - profiles/perspective.md
    - profiles/review-paper.md
    - profiles/mini-review.md
    - profiles/editorial.md
    - profiles/methodological-paper.md
    - profiles/commentary-reply.md
    - profiles/funding-proposal.md
  reference_updates:
    - references/agent-contract.md             # I/O wrapper inventory extended with WRITE wrappers (cycle 8); D5 linter section refreshed
  router_updates:
    - scripts/sws_section_router.py            # add revising-action routes (consistency/style/lint) — section→agent map gets a `revising` axis
  test_changes:
    - tests/test_write_docx.py
    - tests/test_restyle_docx.py
    - tests/test_apply_chemistry_format.py
    - tests/test_lint_ai_tells.py
    - tests/test_consistency_check.py
    - tests/test_chemistry_formatting_catalog.py
    - tests/test_revising_section_router.py
    - tests/test_revising_agent_activation.py
    - tests/fixtures/cycle_08_paper/           # builds on cycle_07_paper with assembled markdown drafts in _drafts/
    - tests/fixtures/manuscripts/styled_ok.docx        # a clean SWS-styled docx fixture for restyle tests
    - tests/fixtures/manuscripts/word_default.docx     # a Word-default-styled docx (Heading 1/2) for restyle tests
    - tests/smoke_cycle_08.sh                  # full revise-paper e2e walkthrough on cycle_08_paper fixture

locked_decisions:
  D1_reviser_split_two_files:
    choice: "reviser splits into agents/reviser-full.md (Opus 4.7 xhigh, full-paper passes) and agents/reviser-fast.md (Sonnet 4.6 high, single-section or single-paragraph passes). Mirrors cycle-#7 D6 drafter split. One model field per agent file."
    rationale: "Same logic as the drafter split — keeps the model assignment legible in the agent file, makes future re-tiering a 2-file change instead of an invocation-time override."

  D2_no_dedicated_abstract_writer_agent:
    choice: "No separate abstract-writer agent in cycle #8. The reviser-full prompt explicitly handles abstract refinement (word-count tightening, polish) as part of a full-paper pass. Cycle-#7 D7 noted 'cycle-#8 abstract-writer agent' but locked roster count (24) does not include one — re-reading the roster confirms no abstract-writer slot."
    rationale: "Adding a 25th agent breaks the locked roster. Reviser-full owns abstract refinement; the user can also call /sws:revise-section abstract to invoke reviser-fast on the abstract specifically. v0.2 can promote abstract-writer to a real agent if usage shows it warranted."

  D3_skill_surface_five_skills:
    choice: "Five skills ship: /sws:revise-paper (sequential orchestrator), /sws:revise-section <section> (single-section reviser-fast), /sws:enforce-style (style-enforcer on a single .docx), /sws:check-consistency (consistency-checker standalone), /sws:lint-ai-tells <file> (linter standalone). The humanizer agent is reachable through /sws:revise-paper and via direct agent dispatch — no dedicated /sws:humanize skill in v0.1."
    rationale: "Reviser-paper covers the common case. Standalone skills exist for the three diagnostic passes the user might want without re-revising the whole paper. Skipping a humanize-only skill keeps the surface small; promote in v0.2 if asked for."

  D4_orchestrator_sequential_not_parallel:
    choice: "/sws:revise-paper runs the four passes sequentially: consistency-checker → reviser-full (or reviser-fast for short profiles) → humanizer → style-enforcer. Each pass consumes the previous pass's output written to disk. No parallel fan-out — these are pipeline passes, not independent fragments."
    rationale: "Reviser cannot run until consistency-checker has surfaced cross-section issues. Humanizer cannot run until reviser has produced a stable draft. Style-enforcer cannot run until the prose is final. Sequential preserves correctness; the cycle-#7 drafter-flagship orchestrator was parallel because sections are independent — passes are not."
    short_profile_carve_out: "When resolved word_total < 1500 (editorial, communication, mini-review, commentary-reply), the orchestrator dispatches reviser-fast instead of reviser-full. Decision lives in the skill, not in the agent prompts."

  D5_three_write_wrappers_no_xlsx:
    choice: "Cycle #8 ships three WRITE-side scripts: scripts/sws_write_docx.py (markdown → fresh .docx with SWS canon), scripts/sws_restyle_docx.py (re-style an existing .docx — handles Word Heading 1/2 → SWS-H1/SWS-H2 conversion, strips Title/Subtitle), scripts/sws_apply_chemistry_format.py (italic/sub/super patterns from references/chemistry-formatting.md applied to runs in an existing .docx). XLSX writes deferred — proposal-budget auto-fill stays markdown-only per cycle-#7 D12, cycle #10 revisits."
    rationale: "Three focused scripts beat one polyfunctional one. Each maps to one agent capability: write_docx is style-enforcer's primary, restyle_docx is style-enforcer's tool for user-supplied legacy docs, apply_chemistry_format runs as a post-pass on either above. XLSX writes have no consumer in cycle #8 — defer."

  D6_chemistry_formatting_reference_yaml_catalog:
    choice: "references/chemistry-formatting.md ships as a YAML-frontmatter catalog. Categories: (a) Latin-abbreviation italicization (et al., e.g., i.e., in vitro, in vivo, ex vivo, vs., versus, in silico, ad hoc, a priori), (b) chemical-formula sub/superscript patterns (H2O→H₂O, CO2→CO₂, NaCl, K+, Ca2+, SO4^2-), (c) species-name italicization (Genus species pattern: capital-letter word followed by lowercase species epithet, also abbreviated genus E. coli / S. cerevisiae), (d) gene-name italicization (HUGO convention: gene symbols italicized, protein names plain — pattern: 3-5 uppercase letters NOT inside formula context), (e) bold non-italic figure/table label prefix (e.g., 'Figure 1.' becomes bold, italic stripped from the label even if the surrounding caption is italic). Each pattern: regex, replacement strategy (italic / sub / super / bold), severity (auto / suggest), example_before, example_after, why."
    rationale: "Mirrors the structure of references/ai-writing-tells.md — patterns + severity + examples. YAML frontmatter makes the catalog machine-parseable for sws_apply_chemistry_format.py. Severity=auto means the script applies the change unconditionally; severity=suggest means the change is flagged for user review (catches ambiguous cases like 'NaCl' which could be a chemical formula or a variable name)."

  D7_chemistry_formatting_scope_docx_only:
    choice: "Chemistry formatting applies ONLY when marker has format: docx. When format: latex, sws_apply_chemistry_format.py exits 0 with a no-op (the journal's .cls file handles typography per docx-style.md rule 4). The Latin-abbreviation italicization catalog stays language-agnostic between en and it (et al. / e.g. / i.e. / in vitro are the same in both)."
    rationale: "LaTeX class files own typography for LaTeX projects — overriding them would corrupt the journal-specific template. Italian opt-in does not change the Latin-abbreviation list itself."

  D8_ai_tells_linter_three_context_rules:
    choice: "scripts/sws_lint_ai_tells.py implements three context-aware refinements on top of the cycle-#7 grep-pass: (1) PARAGRAPH-COUNT — for warn-severity tells with a `linter_rule: min_count_per_paragraph: N` frontmatter field, the linter flags only when the pattern fires ≥N times in the same paragraph (e.g., em-dash warn fires only when ≥3 em-dashes appear in one paragraph); (2) CODE-FENCE SKIP — text inside ``` fences and inline `code` is excluded from matching; (3) CITATION-PLACEHOLDER SKIP — text inside [CITATION_NEEDED: ...] is excluded (placeholder content is metadata, not prose). Output is structured: per-finding line number, column, snippet, pattern, severity, why. Exit code 0 if no block-severity hits, 1 otherwise. JSON output via --json flag for agent consumption."
    rationale: "Three rules cover the obvious false-positive sources from the cycle-#7 grep-pass without requiring an LLM in the loop. The `linter_rule:` schema is forward-compatible — additional rules (min_count_per_section, ignore_in_caption, etc.) can be added without breaking existing tells."
    optional_field: "The `linter_rule:` field is OPTIONAL in references/ai-writing-tells.md. Tells without it behave exactly like the cycle-#7 grep-pass. Initial linter ships with this field on ~3 patterns (em-dash overuse, sentence-initial 'Furthermore/Moreover', stacked compound adjectives) — the patterns whose cycle-#7 grep regex already encodes 'count-or-distance' implicitly."

  D9_consistency_checker_text_internal_only:
    choice: "consistency-checker stays text-internal in cycle #8 — no external citation lookup. Checks: (1) figure references in prose (Fig. N, Figure N, Figures N+M) match figures dict in _outline/outline.md; (2) table references similarly; (3) section list in the assembled draft matches profile's required sections; (4) citation keys parse via scripts/sws_citation_key.py and are uniquely-formatted (no key written twice with different DOIs); (5) abbreviations introduced on first use (regex: '(?<full>[A-Z][a-z].+) \\((?<abbr>[A-Z]{2,})\\)' on first occurrence; subsequent occurrences must match an introduced abbreviation); (6) terminology uniformity (case-sensitive: 'thrombin' / 'Thrombin' / 'THROMBIN' mixed in the same draft = a finding). Output: <paper>/_review/consistency-report.md per-finding with line/section pointers and suggested fix. claim-verifier (cycle #9) and NLM-grounded compliance (cycle #11) cover external-source verification — out of scope here."
    rationale: "Six text-internal checks all run in scripts/sws_consistency_check.py without external API calls or LLM judgment, so the agent is fast and deterministic. External claim verification needs a different infrastructure (cycle #9 with literature-searcher / cycle #11 with nlm-librarian)."

  D10_style_enforcer_owns_final_docx:
    choice: "style-enforcer is the only cycle-#8 agent that produces the final .docx. Pipeline: (1) read all _drafts/<section>.md files in profile section order (or read a user-supplied stitched markdown file); (2) call sws_write_docx.py to generate <paper>/Manuscript/<paper-name>.docx with SWS style canon; (3) call sws_apply_chemistry_format.py to apply chemistry patterns; (4) print summary (sections written, words, chemistry patterns applied, AI-tells block hits if any leaked through earlier). The PreToolUse backup hook (cycle #5) writes <paper>.backup_pre_style_enforcer.docx before the write."
    rationale: "Single agent owns the docx-output bottleneck. Other agents stay markdown-only — easier to test, easier to dispatch in parallel for future cycles."

  D11_no_chemistry_in_markdown_drafts:
    choice: "Drafter / reviser / humanizer agents all stay in plain markdown — no chemistry formatting in intermediate drafts. Chemistry formatting is applied ONLY at style-enforcer time, on the .docx file. Drafted markdown uses plain ASCII (H2O, CO2, NaCl, et al., E. coli). The chemistry pass converts on write."
    rationale: "Markdown is the lossless source-of-truth for prose. Applying chemistry formatting in markdown means defining a markdown italic / sub / super dialect that does not round-trip cleanly. Better: keep markdown plain, apply formatting once on docx generation. Mirrors how LaTeX users let pandoc handle character-level typography."

  D12_revising_section_router_axis:
    choice: "scripts/sws_section_router.py gets a second axis: `action`. Existing cycle-#7 routes (intro → drafter-flagship, methods → methods-writer, etc.) live under action=draft. Cycle-#8 adds action=revise (intro → reviser-fast, results → reviser-fast, full → reviser-full when invoked from /sws:revise-paper), action=consistency (everything → consistency-checker), action=style (everything → style-enforcer), action=lint (everything → no agent — the linter is a script, not an agent — but the router knows to point /sws:lint-ai-tells at scripts/sws_lint_ai_tells.py instead of an agent dispatch)."
    rationale: "Keeps section routing in one place. The action axis is forward-compatible with cycle-#9 review and cycle-#10 submission orchestration. Avoids inventing a parallel router file."

  D13_profile_activation_all_five_active_everywhere:
    choice: "All five cycle-#8 agents are listed as agents_active for every profile (no per-profile blocking). Short-form profiles (editorial, communication, mini-review, commentary-reply) get the size-aware dispatch from D4 (reviser-fast instead of reviser-full) — this lives in the /sws:revise-paper skill, not in the profile."
    rationale: "Per-profile agents_inactive carries semantic meaning (e.g., funding-proposal blocks methods-writer because proposals do not have an Experimental Section). For revising agents, the profile does not change WHAT the user wants — they want their paper revised. Size-aware behavior belongs in the orchestrator. Keeps the matrix simple. Per-profile blocking re-evaluated in cycle #12 (NLM integration) when real usage data exists."

  D14_phasing_three_phases_one_PR:
    choice: "Cycle #8 ships as one PR with three internal phases: Phase 1 = foundation (3 wrapper scripts + chemistry-formatting reference + AI-tells linter + their unit tests, dispatched in parallel since the scripts are independent). Phase 2 = 5 agent files + 5 skills + agent-contract update + section-router update + revising-axis tests (parallel subagent dispatch). Phase 3 = profile updates (parallel) + e2e smoke + agent-matrix migration tests + smoke_cycle_07 regression check."
    rationale: "No mid-cycle beta-test against a real manuscript this cycle — the cycle-#7 phase-2 beta exposed the WRITE-wrapper gap (D22 emerged from it). Now that wrappers ship, cycle #8 is mechanically lower-risk. Parallel dispatch is safe within each phase because the deliverables are independent (different files, no shared edits)."

  D15_test_strategy_extension_of_cycle07:
    choice: "Tests: ~80 new tests across the 5 cycle-#8 test files. Smoke = tests/smoke_cycle_08.sh exercising /sws:revise-paper on a cycle_08_paper fixture that already has _drafts/<section>.md files seeded (so we are not running the cycle-#7 drafter, just the cycle-#8 revising chain). Re-run tests/smoke_cycle_07.sh to ensure cycle-#8 changes (router action axis, profile updates, agent-contract update) did not break the drafting pipeline."
    rationale: "Smoke-on-fresh-fixture isolates cycle-#8 logic. Cycle-#7 smoke regression test catches matrix-drift bugs (we have history of this — cycle-07 had to adapt smoke_cycle_06 when the drafter split landed)."

  D16_backup_discipline_via_existing_hook:
    choice: "No new backup logic in cycle #8. The cycle-#5 PreToolUse backup hook already fires on Edit/Write of .docx, producing <paper>.backup_pre_<tool>_<timestamp>.docx. Style-enforcer writes via the Write tool route through sws_write_docx.py — backup runs automatically. Verify the hook recognizes the wrapper-mediated write path (it should: the hook hooks the tool call, not the script)."
    rationale: "Cycle #5 already shipped this safety net. Adding cycle-specific backup logic would duplicate the contract."

  D17_agent_color_palette:
    choice: "Colors: reviser-full=red, reviser-fast=pink, humanizer=cyan-bright (distinct from drafter-fast's cyan), style-enforcer=brown, consistency-checker=gray. All distinct from cycle-#7 palette (blue, cyan, orange, yellow, green, purple, teal)."
    rationale: "Color is a UX cue in the agent picker. Distinct colors per agent reduce mispick."

  D18_no_separate_revise_section_skill_for_full_reviser:
    choice: "/sws:revise-section <section> always dispatches reviser-fast. To run reviser-full on a single (very long) section, the user invokes /sws:revise-paper and the orchestrator dispatches reviser-full on the assembled draft. There is no /sws:revise-section --full flag in v0.1."
    rationale: "Reviser-full is intended for cross-section reasoning (redundancy across Intro/Discussion, citation deduplication across sections). Running it on a single section wastes the model's strength. If a section is genuinely huge, the user can copy it into a fresh paper folder; cycle #8 does not optimize for this edge case."

  D19_consistency_checker_publication_only_in_v0_1:
    choice: "consistency-checker checks (figure refs, table refs, citation keys, abbreviations, terminology, section list) apply to PUBLICATION profiles only. funding-proposal profile uses a different set of checks (WP cross-references, deliverable IDs, milestone IDs) that ship later in cycle #10 (submission orchestration). v0.1 consistency-checker on funding-proposal returns 'profile not supported for consistency check; manual review required' and exits 0."
    rationale: "Proposal consistency is structurally different (WP-Dxx.y, M-N labels, Gantt-row indices). Designing it now without real proposal data risks the same false-positive trap as cycle-#7 D5 warned about for ai-tells. Defer to cycle #10."

  D20_lint_ai_tells_uses_existing_reference:
    choice: "scripts/sws_lint_ai_tells.py reads references/ai-writing-tells.md (cycle #7 shipped). No new reference doc for the linter. The linter's three context rules are encoded as Python logic; the optional linter_rule: field in the YAML frontmatter steers per-tell behavior."
    rationale: "Cycle-#7 D5 locked references/ai-writing-tells.md as the source-of-truth. Adding a second reference for the linter would split the catalog. Per-tell linter_rule lets the existing catalog evolve in place."

cross_cutting:
  agent_contract_changes:
    section_to_modify: "I/O wrapper inventory (R3 in references/agent-contract.md)"
    diff_summary: |
      Add three WRITE wrapper entries to the inventory table:
      | scripts/sws_write_docx.py             | Write markdown → .docx with SWS style canon              | 8 |
      | scripts/sws_restyle_docx.py           | Re-apply SWS styles to an existing .docx                 | 8 |
      | scripts/sws_apply_chemistry_format.py | Apply chemistry-formatting patterns to an existing .docx | 8 |
      | scripts/sws_lint_ai_tells.py          | Context-aware AI-tells linter (vs grep-pass)             | 8 |
      Update R3 closing sentence: "Cycle #7 ships READ wrappers only. WRITE wrappers ship in cycle #8" → "Cycle #7 ships READ wrappers; cycle #8 ships WRITE wrappers (sws_write_docx / sws_restyle_docx / sws_apply_chemistry_format) and the AI-tells linter (sws_lint_ai_tells)."
    no_other_R_changes: "R1–R2, R4–R5 unchanged. Token discipline + filesystem frugality + no-gender-default still apply verbatim."

  revising_pipeline_artifact_paths:
    consistency_report: "<paper>/_review/consistency-report.md (consistency-checker output)"
    revision_notes_section: "<paper>/_review/revision-notes-<section>.md (reviser-fast per-section side-by-side)"
    revision_notes_full: "<paper>/_review/revision-notes-full.md (reviser-full whole-paper notes)"
    humanized_drafts: "<paper>/_drafts/<section>-humanized.md (humanizer output; overwrites cycle to cycle)"
    revised_drafts: "<paper>/_drafts/<section>-revised.md (reviser output; consumed by humanizer, then by style-enforcer)"
    lint_report: "<paper>/_review/lint-report-<file>.md (lint-ai-tells output when invoked standalone via /sws:lint-ai-tells)"
    final_docx: "<paper>/Manuscript/<paper-name>.docx (style-enforcer output — single source of truth)"

  section_router_action_axis:
    new_actions: [draft, revise, consistency, style, lint]
    routes_draft_unchanged: "All cycle-#7 routes (intro → drafter-flagship, methods → methods-writer, etc.) live under action=draft. Default action when omitted = draft (backwards-compat)."
    routes_revise:
      intro: reviser-fast
      introduction: reviser-fast
      abstract: reviser-fast
      discussion: reviser-fast
      conclusion: reviser-fast
      conclusions: reviser-fast
      methods: reviser-fast
      experimental: reviser-fast
      "experimental section": reviser-fast
      results: reviser-fast
      "results and discussion": reviser-fast
      figure_caption: reviser-fast
      full: reviser-full        # special: dispatched by /sws:revise-paper only
    routes_consistency:
      "*": consistency-checker
    routes_style:
      "*": style-enforcer
    routes_lint:
      "*": "(script, not agent — sws_lint_ai_tells.py)"

orchestration_model:
  /sws:revise-paper:
    description: "Full revision pipeline. Sequential, not parallel."
    steps:
      - "1. Resolve overlay; read resolved word_total."
      - "2. Locate _drafts/<section>.md files. Bail if none found (user must draft first)."
      - "3. Dispatch consistency-checker. Write _review/consistency-report.md. If block-severity findings exist, print summary to user and ASK whether to proceed (skill ack — agent does not auto-block)."
      - "4. Decide reviser tier from word_total (< 1500 → reviser-fast; ≥ 1500 → reviser-full). Dispatch the chosen reviser; it writes _drafts/<section>-revised.md per section plus _review/revision-notes-full.md (full) or _review/revision-notes-<section>.md (fast)."
      - "5. Dispatch humanizer on the revised drafts (one section at a time, or all at once — humanizer is Haiku, fast). Humanizer writes _drafts/<section>-humanized.md."
      - "6. Dispatch style-enforcer on the humanized drafts (or on revised if humanizer was skipped). Style-enforcer reads section order from profile, calls sws_write_docx.py, then sws_apply_chemistry_format.py, writes Manuscript/<paper-name>.docx."
      - "7. Final summary: number of consistency findings, reviser revisions applied, humanizer changes, AI-tells block hits caught, docx path."

  /sws:revise-section:
    description: "Single-section reviser-fast pass."
    args: "<section-id> [--no-humanize]"
    steps:
      - "1. Resolve overlay."
      - "2. Read _drafts/<section>.md."
      - "3. Dispatch reviser-fast on it (writes _drafts/<section>-revised.md + _review/revision-notes-<section>.md)."
      - "4. Unless --no-humanize: dispatch humanizer (writes _drafts/<section>-humanized.md)."
      - "5. Print summary."

  /sws:enforce-style:
    description: "Style-enforcer standalone — produces the final .docx from existing markdown drafts."
    args: "[--from <markdown-file>] [--restyle <existing-docx>]"
    steps:
      - "1. Resolve overlay."
      - "2. If --restyle <file>: run sws_restyle_docx.py on it (legacy docx → SWS canon)."
      - "3. Else: read _drafts/<section>-humanized.md (or -revised.md if no humanized version) per profile section order; call sws_write_docx.py to generate Manuscript/<paper-name>.docx."
      - "4. Call sws_apply_chemistry_format.py on the result (skipped if format=latex)."
      - "5. Print summary."

  /sws:check-consistency:
    description: "Consistency-checker standalone."
    steps:
      - "1. Resolve overlay; if profile=funding-proposal, print v0.1 unsupported message and exit 0 (D19)."
      - "2. Run sws_consistency_check.py on _drafts/ (or on a stitched markdown if drafts are not assembled)."
      - "3. Dispatch consistency-checker agent only if findings are ambiguous (e.g., possible abbreviation collisions). For purely deterministic checks (ref number mismatch, citation duplication) the script suffices."
      - "4. Write _review/consistency-report.md and print summary."

  /sws:lint-ai-tells:
    description: "AI-tells linter standalone — script-only, no agent."
    args: "<file.md> [--severity block|warn|all] [--json]"
    steps:
      - "1. Run sws_lint_ai_tells.py with the given file."
      - "2. Print findings (or JSON if --json)."
      - "3. Exit code 0 if no block-severity, 1 if any block."

auxiliary_file_shapes:
  consistency_report:
    path: "<paper>/_review/consistency-report.md"
    schema: |
      ---
      generated_at: <iso8601>
      profile: <id>
      checked_files: [<path>, ...]
      findings_count: int
      findings_by_severity:
        block: int
        warn: int
      ---
      # Consistency report
      ## block — <category> — <line ref>
        - what: <one-line description>
        - where: <file>:<line>:<column>
        - context: <snippet ~120 chars>
        - suggested_fix: <one-line>

  revision_notes:
    path_full: "<paper>/_review/revision-notes-full.md"
    path_section: "<paper>/_review/revision-notes-<section>.md"
    schema: |
      ---
      reviser: reviser-full | reviser-fast
      target: full | <section-id>
      generated_at: <iso8601>
      word_count_before: int
      word_count_after: int
      changes_summary:
        redundancy_cuts: int
        consecutio_rewrites: int
        claim_grounding_flags: int
        ai_tells_blocked: int
      ---
      # Revision notes
      ## Cut — redundancy — <section> §<n>
        - before: "<snippet>"
        - after: "<snippet>"
        - why: "<one-line reason>"

  chemistry_formatting_catalog:
    path: "references/chemistry-formatting.md"
    schema_summary: |
      ---
      sws_artifact: chemistry-formatting
      artifact_version: 0.1
      categories:
        latin_abbreviations:
          - pattern: "\\b(et al|e\\.g|i\\.e|in vitro|in vivo|ex vivo|in silico|vs|versus|ad hoc|a priori)\\b"
            apply: italic
            severity: auto
        chemical_formulae:
          - pattern: "(?<=[A-Z][a-z]?)(\\d+)(?![A-Za-z])"
            apply: subscript
            severity: auto
            example_before: "H2O"
            example_after: "H₂O"
          - pattern: "([A-Z][a-z]?)(\\d*)\\^?(\\d*)([+-])"
            apply: superscript
            severity: auto
            example_before: "Ca2+"
            example_after: "Ca²⁺"
        species_names:
          - pattern: "\\b([A-Z][a-z]+)\\s([a-z]{4,})\\b"
            apply: italic
            severity: suggest    # ambiguous — could be "John Smith" not "Genus species"
        species_abbreviated:
          - pattern: "\\b([A-Z])\\.\\s([a-z]{4,})\\b"
            apply: italic
            severity: auto       # "E. coli" pattern is unambiguous in scientific context
        gene_names:
          - pattern: "\\b([A-Z][A-Z0-9]{2,5})\\b"
            apply: italic
            severity: suggest    # could be acronyms not gene names — flag for review
        figure_label_prefix:
          - pattern: "^(Figure|Fig\\.|Table|Tab\\.)\\s(\\d+|S\\d+)([.:])"
            apply: bold
            severity: auto
        ---
        # Chemistry formatting
        Frontmatter is source of truth.

phasing:
  phase_1_foundation:
    description: "WRITE wrappers, chemistry-formatting reference, AI-tells linter — parallel subagent dispatch since deliverables are independent."
    parallel_subagent_tasks:
      A: references/chemistry-formatting.md + tests/test_chemistry_formatting_catalog.py
      B: scripts/sws_write_docx.py + tests/test_write_docx.py + tests/fixtures/manuscripts/styled_ok.docx generation helper
      C: scripts/sws_restyle_docx.py + tests/test_restyle_docx.py + tests/fixtures/manuscripts/word_default.docx generation helper
      D: scripts/sws_apply_chemistry_format.py + tests/test_apply_chemistry_format.py (depends on A — dispatch second wave)
      E: scripts/sws_lint_ai_tells.py + tests/test_lint_ai_tells.py
      F: scripts/sws_consistency_check.py + tests/test_consistency_check.py
    gate_criteria:
      - "All scripts ship with --help text"
      - "All test files reach 100% pass on `pytest`"
      - "references/agent-contract.md updated with new wrapper rows"

  phase_2_agents_and_skills:
    description: "5 agent files + 5 skills + section-router action axis."
    parallel_subagent_tasks:
      G: agents/reviser-full.md
      H: agents/reviser-fast.md
      I: agents/humanizer.md
      J: agents/style-enforcer.md
      K: agents/consistency-checker.md
      L: skills/revise-paper/SKILL.md
      M: skills/revise-section/SKILL.md
      N: skills/enforce-style/SKILL.md
      O: skills/check-consistency/SKILL.md
      P: skills/lint-ai-tells/SKILL.md
      Q: scripts/sws_section_router.py (action axis) + tests/test_revising_section_router.py
    gate_criteria:
      - "Every agent file references references/agent-contract.md and sources scripts/agent_prelude.sh"
      - "Every skill file references the resolver and the agent it dispatches"
      - "Router test asserts all five action axes return the right agent/script"

  phase_3_profiles_and_smoke:
    description: "Profile updates + end-to-end smoke + cycle-#7 regression check."
    parallel_subagent_tasks:
      R: profiles/*.md updates (one parallel task per profile group: publication + funding-proposal)
      S: tests/test_revising_agent_activation.py
      T: tests/fixtures/cycle_08_paper/ skeleton + seeded _drafts/<section>.md files
      U: tests/smoke_cycle_08.sh
      V: re-run tests/smoke_cycle_07.sh to ensure no regression; adjust assertions if router action axis touched anything
    gate_criteria:
      - "smoke_cycle_08 walks: /sws:check-consistency → /sws:revise-section results → /sws:revise-paper → /sws:enforce-style and ends with a Manuscript/cycle_08_paper.docx"
      - "smoke_cycle_07 still passes 14/14"
      - "AI-tells linter exits 0 on all phase-3 fixtures (no block-severity hits)"

testing:
  unit_target: "~80 new tests"
  smoke_target: "tests/smoke_cycle_08.sh covers ~12 steps; tests/smoke_cycle_07.sh stays 14/14 (regression)"
  fixtures:
    - "tests/fixtures/manuscripts/styled_ok.docx — clean SWS-styled docx, used as input for restyle (should be no-op) and write-equivalence checks"
    - "tests/fixtures/manuscripts/word_default.docx — a docx with Word's built-in Heading 1/2 styles, used as restyle input"
    - "tests/fixtures/cycle_08_paper/ — extends cycle_07_paper with _drafts/<section>.md files pre-seeded (intro, results, discussion, conclusion); chemistry-formatting trigger words embedded (H2O, et al., E. coli, Figure 1.)"

what_stays_v02_or_later:
  - "abstract-writer dedicated agent — v0.2 if usage data justifies it (D2)"
  - "/sws:humanize standalone skill — v0.2 if asked for (D3)"
  - "Italian section of ai-writing-tells.md / chemistry-formatting.md — v0.2+"
  - "format: latex deep handling of chemistry / style enforcement — v0.2 format-translator"
  - "Per-coauthor voice profiles for the reviser — cycle #10 style calibration"
  - "Funding-proposal-specific consistency checks (WP/D/M refs) — cycle #10 (D19)"
  - "xlsx WRITE wrapper — cycle #10 with proposal-budget auto-fill"
  - "Multi-rule linter_rule schema (min_count_per_section, ignore_in_caption, etc.) — v0.2"
  - "External-source claim verification in consistency-checker — cycle #9 claim-verifier handles"

risks:
  R1_chemistry_pattern_false_positives:
    risk: "species_names pattern (Capital + lowercase) catches person names (John Smith). gene_names pattern (3–5 uppercase) catches acronyms (NMR, HPLC, DOI)."
    mitigation: "Both ship as severity=suggest, not auto. style-enforcer flags suggestions in its summary; user reviews in the docx. Auto-apply only the unambiguous patterns (abbreviated species like E. coli; chemical formulae like H2O; Latin abbreviations)."

  R2_restyle_docx_loses_user_intent:
    risk: "User's existing .docx may have intentional non-SWS styles (highlighted passages, comment-marker color) that sws_restyle_docx.py erases when normalizing to the canon."
    mitigation: "Restyle preserves direct character formatting (bold, italic, underline) — it ONLY rewrites paragraph-style assignments and font/size/family. Highlight color and comment markers stay. Document this behavior in the script --help. Add a test that a pre-styled run with explicit italic survives restyle."

  R3_consistency_checker_abbreviation_false_negatives:
    risk: "Abbreviations defined across sections (introduced in Methods, used in Results without re-definition) flag as 'never introduced' if the checker reads sections in isolation."
    mitigation: "Consistency-checker reads ALL section drafts in profile order before scanning for abbreviation introductions. First-occurrence-in-document is what counts, not first-occurrence-in-section. Add a test that covers this."

  R4_revise_paper_orchestrator_loses_user_edits_between_passes:
    risk: "User hand-edits _drafts/<section>-revised.md between reviser and humanizer passes. Humanizer overwrites those edits."
    mitigation: "Humanizer ALWAYS reads -humanized.md if it exists. If user wants to keep humanizer from running, they can: pass --skip-humanize to /sws:revise-paper; or write a sentinel <section>-humanized.md by hand (humanizer detects and skips). Document in the skill."

  R5_section_router_action_axis_breaks_cycle_07_calls:
    risk: "Adding the action axis to scripts/sws_section_router.py changes its CLI signature; cycle-#7 callers that pass section only (no action) break."
    mitigation: "Backwards-compatible: omitted action defaults to 'draft'. Existing /sws:draft-section + /sws:draft-paper callers keep working without change. Test asserts router with no action arg returns the cycle-#7 draft agent."

  R6_lint_ai_tells_too_strict_blocks_user_writes:
    risk: "Linter shipped on day 1 with the cycle-#7 ~50-tell catalog may over-trigger on legitimate scientific text, blocking style-enforcer pipeline."
    mitigation: "Linter only RUNS automatically inside the humanizer agent's prompt (which can resolve flagged tells via rewrite). The standalone /sws:lint-ai-tells skill reports without blocking. style-enforcer does not gate on linter exit code — it gates on its own internal checks only (style canon applied, chemistry pass complete). User can disable the linter pass entirely via /sws:revise-paper --skip-lint."

---

# Cycle #8 — Revising

Frontmatter is the source of truth. This body is orientation only.

## Why

Cycle #7 produced first-draft prose. Cycle #8 turns drafts into something a journal will accept: cross-section consistency, AI-tells removed, chemistry typography correct, SWS docx canon applied. Without cycle #8, every cycle-#7 draft still needs hours of manual polish before submission. Cycle #8 is also the cycle that finally moves SWS from "produces markdown" to "produces the actual .docx the user submits" — the WRITE wrappers shipped here (deferred from cycle #7 D22) make every later cycle's docx work possible.

## What ships

One reference doc (`chemistry-formatting.md`), five wrapper scripts (3 docx WRITE wrappers + the AI-tells linter + the consistency-check static-analysis core), five agent files (`reviser-full`, `reviser-fast`, `humanizer`, `style-enforcer`, `consistency-checker`), five skills (`/sws:revise-paper`, `/sws:revise-section`, `/sws:enforce-style`, `/sws:check-consistency`, `/sws:lint-ai-tells`), updates to all nine profile files for the cycle-#8 agent activation matrix, an action-axis extension to `sws_section_router.py`, and a regression-safe e2e smoke that exercises the full revision pipeline.

## How it ships

One PR, three phases (D14). No mid-cycle beta-test against a real manuscript this cycle — the cycle-#7 phase-2 beta exposed the WRITE-wrapper gap that this cycle closes; further beta work waits until cycle #9 review agents land. Phases dispatch parallel subagents where deliverables are independent (six tasks in phase 1, eleven in phase 2, five in phase 3).

## What stays for cycles #9 / #10 / #11 / v0.2

See `what_stays_v02_or_later` in frontmatter.

## Autonomous-run caveat (for user review tomorrow)

This spec was authored autonomously overnight. Every locked decision (D1–D20) carries a one-line rationale. The PR is opened in draft state so revisions before merge are friction-free. Most likely candidates for user revision:
- D2 (no abstract-writer): roster says no, but cycle-#7 D7 implied yes — confirm.
- D3 (5 skills, no /sws:humanize): possible user preference to add it.
- D6 (chemistry-formatting auto vs suggest severity per category): species_names + gene_names are flagged as suggest because false positives — confirm.
- D13 (all five agents active everywhere): vs per-profile blocking for editorial / mini-review.
- D17 (color palette): purely cosmetic; user may want different choices.
