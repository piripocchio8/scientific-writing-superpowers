---
sws_artifact: cycle-06-spec
artifact_version: 0.1
locked: 2026-05-12
title: "Cycle #6 — Profile system + journal-style/call-rules overlay layer"

cycle_index: 6
original_roadmap_index: 4
predecessor: cycle-05-hooks-and-passport
banner_after_completion: "🚧 v0.1 in design"

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §4 Profile system + journal-style + call-rules"
  brainstorm_confirm: "2026-05-12 user approved all 6 design sections in this brainstorm"
  related_memory:
    - "claude_memory/project_profiles.md (9 profiles + journal-style flow)"
    - "claude_memory/project_roster_v0.1.md (24 agents)"
    - "claude_memory/project_cycle_execution_status.md (cycles #3–#5 patterns)"

deliverables:
  code_changes:
    - scripts/resolve_overlay.py
    - scripts/sws_python.sh
    - scripts/agent_prelude.sh
    - scripts/sws_install_deps.sh
    - scripts/sws_hook_session_start.py   # extended for missing-profile nudge
  profile_files:
    - profiles/full-article.md
    - profiles/communication.md
    - profiles/perspective.md
    - profiles/review-paper.md
    - profiles/mini-review.md
    - profiles/editorial.md
    - profiles/methodological-paper.md
    - profiles/commentary-reply.md
    - profiles/funding-proposal.md
  requirements:
    - requirements/sws-deps.txt
  skills:
    - skills/set-profile/SKILL.md
    - skills/resolve-journal-style/SKILL.md
    - skills/resolve-call-rules/SKILL.md
    - skills/install-deps/SKILL.md
  init_project_extension:
    - skills/init-project/SKILL.md  # adds --c7 flag + NL parsing + venv bootstrap
  test_changes:
    - tests/test_resolve_overlay.py
    - tests/test_set_profile.py
    - tests/test_resolve_journal_style.py
    - tests/test_resolve_call_rules.py
    - tests/test_agent_prelude.py
    - tests/fixtures/papers/dummy_paper/
    - tests/fixtures/journal_pages/   # canned guide-for-authors HTML
    - tests/fixtures/calls/           # PDF/DOCX/MD/TXT/HTML call fixtures
    - tests/fixtures/agent_activation_matrix.yaml
    - tests/smoke_cycle_06.sh

locked_decisions:
  D1_profile_selection_three_entries:
    choice: "Profile is set via (a) /sws:init-project --c7=<name>, (b) /sws:set-profile <name>, or (c) left null + nudged"
    rationale: "init handles happy path; set-profile handles changes; null + nudge handles legacy / unset cases without destructive defaulting"

  D2_journal_style_trigger:
    choice: "/sws:resolve-journal-style <slug> slash command, never SessionStart hook"
    rationale: "WebFetch is slow; surprising a session-start with 10s stalls is bad UX. User controls when to fetch."

  D3_call_rules_trigger:
    choice: "/sws:resolve-call-rules slash command. Pre-step scans Manuscript/call/ for non-underscore PDF/DOCX/MD/TXT/HTML; parses if found, else Q&A wizard."
    rationale: "Symmetric with journal-style. Pre-step honors the user's existing call/ workflow."

  D4_overlay_file_format:
    choice: "Markdown + YAML frontmatter (same shape as profile files)"
    rationale: "Frontmatter = machine contract; body = free-form notes captured during synthesis (e.g., 'evaluators emphasize novelty')"

  D5_overlay_storage_path:
    choice: "Two parallel dirs under the user paper: <paper>/Manuscript/_journal-style/<slug>.md and <paper>/Manuscript/_call/<slug>.md"
    rationale: "_call/ already houses the uploaded call source; overlay living next to its source is intuitive. Self-documenting via directory name."

  D6_cache_freshness:
    choice: "No auto-refresh. Re-run the slash command to refresh."
    rationale: "Journal guidelines change rarely; user controls the moment. Matches cycle #5 deterministic-hooks discipline."

  D7_missing_profile_fallback:
    choice: "Soft-fail with contract. SessionStart hook prints one-line nudge; resolver emits profile_set: false; agents abort cleanly via prelude check."
    rationale: "Q8=C. Non-blocking, informative. No destructive auto-default — mis-defaulting between full-article and funding-proposal would silently activate the wrong agent set."

  D8_profile_body_loading:
    choice: "Frontmatter is the contract for all agents. Body is read only by the drafter (and any agent that explicitly opts in for prose context)."
    rationale: "Q9=B. Token-efficient. Most agents (style-enforcer, peer-reviewer, methods-writer) only need machine fields."

  D9_agent_runtime_discovery:
    choice: "Helper script scripts/resolve_overlay.py returns merged JSON. Agents shell out; no agent walks the 3 layers itself."
    rationale: "Q10=A. Single source of truth. Adding a v0.2 overlay layer means updating the resolver, not 24 agents."

  D10_call_rules_qa_scope:
    choice: "Minimal locked set: program name, deadline, page limit, required sections (multi-select from standard set), language. 5 fields. Free-form notes added by post-write body edit."
    rationale: "Q11=A. Wizards bloat fast; body is editable for everything else."

  D11_set_profile_mechanics:
    choice: "/sws:set-profile <name> rewrites the profile field in .sws-project.local.md frontmatter. Existing overlays are NOT invalidated."
    rationale: "Q12=A. Overlays are keyed by journal/call slug, not by profile. Switching from full-article to funding-proposal makes the journal overlay irrelevant rather than wrong."

  D12_init_project_c7_hybrid:
    choice: "init-project writes profile field only if --c7=<name> flag is explicit or NL parser matches. Otherwise marker writes profile: null and the SessionStart nudge fires on first session."
    rationale: "Q13=C. No destructive defaulting. Mis-defaulting between full-article and funding-proposal would silently activate the wrong agent set."

  D13_call_rules_uploaded_source_parser:
    choice: "Hybrid B+C: regex/heuristic extractor first (deadline, page limit, budget patterns), LLM fills gaps, then user-confirm pass on every field the LLM flags as uncertain."
    rationale: "Q14=B+C. Funding proposals fail on technicalities (wrong page limit, missed section). Confirm-on-uncertain is cheap insurance."

  D14_merge_list_semantics_replace:
    choice: "List-typed fields (sections, agents_active, agents_inactive): overlay replaces profile list entirely."
    rationale: "Q15=A. Simpler resolver. Patch-by-id deferred to v0.2 once we have 3+ real journal overlays to see what patterns emerge."

  D15_overlay_archive_on_re_resolve:
    choice: "When /sws:resolve-journal-style or /sws:resolve-call-rules overwrites an existing overlay, the prior file is copied to _archive/<slug>-YYYYMMDD-HHMMSS.md first."
    rationale: "Q15-addition. History-preserving, recoverable. Matches cycle-#2 style-calibrator's _archive/ pattern."

  D16_overlay_diff_summary:
    choice: "After overwriting, resolver prints a one-block diff summary: 'sections changed: +Discussion, -Results and Discussion; word_total: null → 4000; ref_cap: 80 → 50'."
    rationale: "Q15-addition. User sees exactly what shifted before any agent acts on it."

  D17_merge_explicit_null_drops:
    choice: "Overlay key present (including explicit null) wins. Overlay key absent = inherit from profile. Explicit null means 'rule dropped'."
    rationale: "User correction during Section 4. Silent inheritance is wrong when a journal genuinely removes a rule. Synthesizer asks for user confirmation on every field where the source is silent."

  D18_synthesizer_confirm_on_uncertain:
    choice: "Both resolve-journal-style and resolve-call-rules use the same hybrid-B-C pattern: emit only fields the user actively confirmed or the source actively stated. Don't write fields that 'match the profile' by default."
    rationale: "User correction during Section 4. Overlay file is concise (only diffs from profile + user-confirmed drops); merge is unambiguous; user is in the loop for any rule that falls."

  D19_venv_discipline_no_dev_env_name_in_published_code:
    choice: "Plugin scripts never reference the dev mamba env. Init-project creates <paper>/.venv/ at bootstrap and installs requirements/sws-deps.txt. All plugin Python invokes via $PAPER_ROOT/.venv/bin/python through scripts/sws_python.sh wrapper."
    rationale: "User correction during Section 4. the dev mamba env is the dev's internal env; published code must be portable. Existing Claude-environment capabilities (Read for DOCX/PDF text) used first; venv covers what Read cannot."

  D20_venv_per_paper:
    choice: "Per-paper <paper>/.venv/, not plugin-global. Each paper isolates its own deps. Already in .gitignore per CLAUDE.md."
    rationale: "User instruction during Section 4. Avoids cross-paper contamination; matches per-paper isolation principle."

frontmatter_schema_final:
  description: "Final schema for profiles/<id>.md and for overlay files in _journal-style/<slug>.md and _call/<slug>.md."
  fields:
    profile:
      type: string
      enum: [full-article, communication, perspective, review-paper, mini-review, editorial, methodological-paper, commentary-reply, funding-proposal]
      required: true
      where: "profile files only; overlays omit this field"
    inherits:
      type: "string | null"
      default: null
      v01_constraint: "Always null in v0.1. Reserved for v0.2 profile inheritance."
    sections:
      type: array
      element_shape: "{ id: string, label: string, word_limit: int | null, required: bool }"
      v01_constraint: "id is the canonical section key (stable across journals); label is the heading text written to the docx (overridable by journal overlay); word_limit: null means uncapped."
    ref_cap:
      type: "int | null"
      description: "Maximum number of references. null = uncapped."
    word_total:
      type: "int | null"
      description: "Total manuscript word cap. null = uncapped."
    figures_max:
      type: "int | null"
    tables_max:
      type: "int | null"
    abstract_style:
      type: string
      enum: [structured, unstructured, graphical, none]
    disclosure_required:
      type: bool
    cover_letter_required:
      type: bool
    supplementary_allowed:
      type: bool
    refs_style:
      type: string
      enum: [numbered, author-year, footnote]
    agents_active:
      type: "array[string]"
      description: "Agent ids from the locked 24-agent roster (project_roster_v0.1.md). Replaces profile-level list when set in overlay."
    agents_inactive:
      type: "array[string]"
      description: "Agent ids that should NOT run for this profile. Resolver emits should_run: false for any agent in this list (regardless of agents_active)."

agent_activation_matrix:
  description: "Initial per-profile agent activation. Refinable as profiles are exercised on real papers. Tested by tests/fixtures/agent_activation_matrix.yaml."
  default_active: "all 24 agents except where listed below"
  per_profile_inactive:
    full-article: [proposal-budget-helper, proposal-compliance-helper]
    communication: [proposal-budget-helper, proposal-compliance-helper]
    perspective: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator, plot-maker]
    review-paper: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator]
    mini-review: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator]
    editorial: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator, plot-maker, caption-writer]
    methodological-paper: [proposal-budget-helper, proposal-compliance-helper]
    commentary-reply: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator]
    funding-proposal: [response-to-reviewers]

resolve_overlay_contract:
  invocation: "python ${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py --paper $PAPER_ROOT [--agent <agent-id>]"
  output_format: JSON on stdout
  output_fields:
    profile_set:
      type: bool
      description: "False if marker has profile: null or no marker found."
    profile_id:
      type: "string | null"
    profile_path:
      type: "string | null"
      description: "Absolute path to plugin's profiles/<id>.md"
    journal_overlay_path:
      type: "string | null"
      description: "Absolute path to <paper>/Manuscript/_journal-style/<slug>.md if present"
    call_overlay_path:
      type: "string | null"
    resolved_frontmatter:
      type: "object | null"
      description: "Merged frontmatter (schema defaults < profile < overlay) following the schema above."
    should_run:
      type: "bool | null"
      description: "Null unless --agent passed. True if agent is in agents_active and not in agents_inactive."
    diagnostics:
      type: object
      shape: "{ warnings: [string], missing_journal_overlay: bool, missing_call_overlay: bool }"
  exit_codes:
    0: "OK (whether profile_set is true or false)"
    2: "Profile file not found"
    3: "Malformed YAML / schema violation in profile or overlay (with line number)"
    4: "Marker not found (not an SWS project)"

skill_inventory:
  set_profile:
    invocation: "/sws:set-profile <name>"
    validates: "name in 9 locked ids"
    writes: ".sws-project.local.md profile field"
    leaves_alone: "_journal-style/, _call/, all other marker fields"
    prints: "profile: <new> (was: <old>)"

  resolve_journal_style:
    invocation: "/sws:resolve-journal-style <journal-slug>"
    requires: "profile_set: true (else abort)"
    steps:
      - "1. Read marker; abort if profile unset"
      - "2. Resolve guide-for-authors URL from hardcoded slug→URL map (initial 8 journals: chembiochem, jacs, chem-sci, ang-chem, nat-comm, j-chem-inf-mod, biochem-and-biophys-acta, chemistry-european)"
      - "3. WebFetch the page"
      - "4. Subagent (Sonnet) extracts frontmatter following the schema; flags every field where source is silent and profile has a non-default value"
      - "5. User-confirm pass on each flagged field"
      - "6. Validate emitted frontmatter against schema"
      - "7. If overlay exists, archive to _archive/<slug>-YYYYMMDD-HHMMSS.md"
      - "8. Write new overlay; print diff summary if overwriting"
    no_auto_refresh: true

  resolve_call_rules:
    invocation: "/sws:resolve-call-rules"
    requires: "profile == funding-proposal (else abort)"
    pre_step: "Scan <paper>/Manuscript/call/ for non-underscore *.{pdf,docx,md,txt,html}"
    pre_step_found:
      - "Show file list; user confirms source"
      - "Hybrid B+C parser: regex/heuristic extracts (deadline, page limit, budget); LLM fills gaps; user-confirm pass on uncertain fields"
    pre_step_not_found:
      - "Q&A wizard: program name, deadline, page limit, required sections (multi-select), language"
    common_tail:
      - "Validate, archive existing (if any), write to _call/<slug>.md, print diff"

  install_deps:
    invocation: "/sws:install-deps"
    purpose: "Bootstrap or re-bootstrap <paper>/.venv/ with requirements/sws-deps.txt"
    called_by: "init-project on first run; user can re-run manually if deps drift"

  init_project_extension:
    new_flag: "--c7=<profile-name>"
    nl_parse: "Recognize phrases like 'for a Communication paper', 'this is a funding proposal'"
    venv_bootstrap: "If <paper>/.venv/ doesn't exist, run /sws:install-deps inline"
    marker_field: "profile: <name> or profile: null"

requirements_sws_deps:
  description: "Default v0.1 Python deps installed into <paper>/.venv/ at init time. LaTeX-specific deps only added if marker says format: latex."
  default:
    - "PyYAML>=6.0       # frontmatter parsing"
    - "python-docx>=1.1  # docx read/write/edit"
    - "pdfplumber>=0.10  # PDF structural inspection"
    - "lxml>=5.0         # XML for docx and HTML parsing"
    - "openpyxl>=3.1     # Excel data tables (per feedback_openpyxl_formulas.md)"
    - "pytest>=8.0       # for plugin's own test suite if user runs locally"
  latex_optional:
    - "pylatexenc>=2.10  # if format: latex"

session_start_hook_extension:
  description: "Cycle #5's sws_hook_session_start.py gets a new branch."
  new_branch: |
    Read marker. If profile field is null:
      print: "No profile set — run /sws:set-profile <name> (e.g. communication, full-article, funding-proposal). Agents are paused until set."
    Else:
      (existing cycle-#5 behavior: passport summary + journal-style nudge if applicable)

edge_cases:
  E1_unknown_profile_name_in_marker:
    case: "Marker has profile: <name> where <name> is not one of the 9 ids"
    action: "Resolver exits 3 with schema-violation error; SessionStart hook prints the same."
  E2_journal_slug_not_in_url_map:
    case: "User runs /sws:resolve-journal-style with a slug not in the hardcoded map"
    action: "Skill prompts: 'No URL on file for <slug>. Enter the guide-for-authors URL:' and proceeds with the user-supplied URL."
  E3_call_dir_missing:
    case: "/sws:resolve-call-rules runs but no Manuscript/call/ directory"
    action: "Skill creates the directory then proceeds to Q&A wizard (no source files to check)."
  E4_call_dir_has_only_underscore_files:
    case: "Manuscript/call/ has _scratch.md or _archive/ but no non-underscore source"
    action: "Treated as empty; proceeds to Q&A wizard."
  E5_venv_missing_at_agent_runtime:
    case: "Agent runs but <paper>/.venv/ doesn't exist (user deleted it or never ran init)"
    action: "sws_python.sh exits non-zero with one-line instruction: 'run /sws:install-deps to bootstrap deps'."
  E6_overlay_present_for_unset_profile:
    case: "Marker has profile: null but _journal-style/chembiochem.md exists"
    action: "Resolver emits profile_set: false and ignores the overlay. SessionStart nudge fires."
  E7_two_overlays_same_slug:
    case: "_journal-style/chembiochem.md and _archive/chembiochem-20260101-000000.md both exist"
    action: "Archive is informational only; resolver always reads the live file. No automatic 'restore from archive' in v0.1."
  E8_synthesizer_extracts_invalid_yaml:
    case: "Sonnet subagent emits malformed YAML"
    action: "Skill catches the parse error, retries the synthesizer once with the error message, then errors out cleanly if still invalid. User can re-run."
  E9_user_aborts_confirm_pass:
    case: "User Ctrl-Cs during confirm-on-uncertain pass"
    action: "Skill exits without writing the overlay. Existing overlay (if any) is preserved."
  E10_agents_active_or_inactive_omitted_in_overlay:
    case: "Journal overlay omits agents_active and agents_inactive fields"
    action: "Inherit from profile (standard merge). Overlays should not need to override agent activation — that's a profile-level concern."

testing:
  unit_target: "~100 tests for resolve_overlay.py"
  unit_coverage:
    - "Merge logic: 3 layers, all 9 profiles, scalar precedence, list-replace, explicit-null-drops"
    - "Validation: schema errors with line numbers; enum violations rejected; unknown fields warned"
    - "should_run matrix: every agent × every profile, driven by tests/fixtures/agent_activation_matrix.yaml"
    - "Edge cases E1–E10 above"
  skill_tests:
    - "set-profile: valid/invalid/missing-marker"
    - "resolve-journal-style: canned guide-for-authors HTML fixtures (chembiochem, jacs, nat-comm); archive on re-run; diff summary; user-confirm via scripted answers"
    - "resolve-call-rules: with uploaded source (PDF + DOCX fixtures); without source (Q&A wizard with scripted answers)"
  e2e_smoke: tests/smoke_cycle_06.sh
  smoke_steps:
    - "1. /sws:set-profile communication → marker updated"
    - "2. /sws:resolve-journal-style chembiochem (fixture HTML) → overlay written, archive empty, diff summary printed"
    - "3. Re-run with different fixture HTML → overlay overwritten, archive populated, diff printed"
    - "4. Dummy agent sources agent_prelude.sh → RESOLVED_OK=1, RESOLVED_REF_CAP=50 from overlay"
    - "5. Agent gated by activation matrix → exits 'not active for <profile>' or runs per matrix"
    - "6. Set profile: null → any agent run → aborts with missing-profile nudge"
    - "7. /sws:set-profile funding-proposal; drop fixture call PDF in call/; /sws:resolve-call-rules → overlay produced via uploaded-source path"

what_stays_v02:
  - "HTML-format memory/overlay files for rich state inspection (user suggestion during brainstorm)"
  - "Patch-by-id merge for list-typed fields (D14 says replace in v0.1; revisit once 3+ real journal overlays exist)"
  - "Profile inheritance via inherits field (D1 frontmatter reserves it as null)"
  - "WebFetch path for /sws:resolve-call-rules (architecture sketch §4: call-rules v0.1 = Q&A + uploaded source only)"
  - "Optional comprehensive Q&A scope for call-rules (D10 = minimal locked set in v0.1)"
  - "TTL / auto-refresh for journal-style overlays (D6 = no auto-refresh in v0.1)"
  - "Quarterly staleness nudge for overlays"
---

# Cycle #6 — Profile system + journal-style/call-rules overlay layer

Frontmatter above is the source of truth. This body is orientation only.

## Why

Profiles are how SWS knows what kind of paper the user is writing — full article vs communication vs funding proposal — and that decision controls which of the 24 agents run and with what constraints (word limits, ref caps, required sections). Journal-style overlays then specialize the profile for a target journal (ChemBioChem's 250-word abstract vs JACS's 150-word). Call-rules overlays do the same for funding-proposal profiles against a specific call.

Without this layer, every agent would have to embed hardcoded constraints, and switching journals would require code changes. Cycle #6 is the first cycle where the 3-layer contract (schema defaults < profile < overlay) goes live; cycles #7–#9 (drafting / revising / review agents) consume it.

## What ships

9 profile files. 3 new slash commands (`/sws:set-profile`, `/sws:resolve-journal-style`, `/sws:resolve-call-rules`) plus 1 supporting (`/sws:install-deps`). Extended `/sws:init-project` (new `--c7` flag, NL parse, venv bootstrap). One Python resolver (`scripts/resolve_overlay.py`) that all agents consume via the shared `agent_prelude.sh`. Per-paper `.venv/` discipline with `requirements/sws-deps.txt`. Extended cycle-#5 SessionStart hook for the missing-profile nudge.

Tests: ~100 unit + 3 skill tests + 1 e2e smoke against a fixture paper.

## What stays v0.2

See `what_stays_v02` in frontmatter.
