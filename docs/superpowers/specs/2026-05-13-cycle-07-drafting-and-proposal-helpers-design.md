---
sws_artifact: cycle-07-spec
artifact_version: 0.1
locked: 2026-05-13
title: "Cycle #7 — Drafting + funding-proposal helpers (6 agents, 7 files)"

cycle_index: 7
original_roadmap_index: 5
predecessor: cycle-06.1-cleanup
banner_after_completion: "🚧 v0.1 in design"

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §3 (roster) + §7 (cycle order)"
  brainstorm_confirm: "2026-05-13 user approved all 6 design sections in this brainstorm"
  related_memory:
    - "claude_memory/project_roster_v0.1.md (24 agents, original to SWS)"
    - "claude_memory/project_decisions_so_far.md (recycled-from-superpowers + adapted-from-andrehuang/Imbad0202 attribution rule)"
    - "claude_memory/project_urgent_deadlines.md (perspective transformation 2026-05-09; funding proposal May 2026)"
    - "claude_memory/feedback_ai_writing_tells.md (seed dictionary for ai-writing-tells.md)"
    - "claude_memory/feedback_subagent_dispatch.md (parallelization preference)"
    - "claude_memory/feedback_integration_smoke.md (final task = real e2e smoke)"
    - "$HOME/.claude/projects/.../user_address_no_default_gender.md (no gender-default in user address)"

scope:
  deliverable: "First usable proposal/perspective writing capability. End of cycle: a user with profile=perspective or funding-proposal can run /sws:outline-paper, /sws:draft-section, /sws:draft-paper, and (funding-proposal only) /sws:proposal-budget + /sws:proposal-compliance to produce first-draft sections grounded by the resolved overlay and (opt-in) by their Zotero library."
  not_in_scope:
    - "references/chemistry-formatting.md (italic species, sub/superscripts, Latin abbreviations) — cycle #8 reviser/style-enforcer (Q6=c)"
    - "Alt-text for figures (Q6=A locked: caption text only)"
    - "xlsx-budget-template auto-fill (Q7=A locked: markdown suggestions only)"
    - "nlm-librarian + NLM-grounded compliance/grounding — cycle #11"
    - "PubMed-expanded-over-Zotero literature search — cycle #11 literature-searcher"
    - "Inline docx-comment compliance annotations — never (Q8=b is final, report file only)"
    - "Italian section of ai-writing-tells.md — v0.2+ (Q3=B locked English-only)"
    - "format: latex deep handling — v0.2 format-translator agent (cycle-#7 agents read marker but generate markdown only)"

deliverables:
  reference_docs:
    - references/agent-contract.md          # the 5 cross-cutting constraints + structure pattern + AI-tells link + attribution rule
    - references/ai-writing-tells.md        # English, 40–60 tells structured by category, severity block/warn

  scripts:
    - scripts/agent_should_run.sh           # thin wrapper over resolve_overlay.py --agent <id>; checks agents_active/agents_inactive
    - scripts/sws_extract_zotero_manifest.py # invoked by /sws:prepare-lit-context; wraps user's zotero skill output
    - scripts/sws_read_docx.py
    - scripts/sws_read_xlsx.py

  agents:
    - agents/outline-architect.md           # Sonnet 4.6 high
    - agents/drafter-flagship.md            # Opus 4.7 xhigh
    - agents/drafter-fast.md                # Sonnet 4.6 high
    - agents/methods-writer.md              # Sonnet 4.6 high
    - agents/caption-writer.md              # Haiku 4.5 medium (text only, no docx edit)
    - agents/proposal-budget-helper.md      # Sonnet 4.6 high
    - agents/proposal-compliance-helper.md  # Sonnet 4.6 high

  skills:
    - skills/outline-paper/SKILL.md         # /sws:outline-paper
    - skills/draft-section/SKILL.md         # /sws:draft-section <section>
    - skills/draft-paper/SKILL.md           # /sws:draft-paper (drafter-flagship orchestrator mode)
    - skills/prepare-lit-context/SKILL.md   # /sws:prepare-lit-context (Zotero manifest export, opt-in)
    - skills/proposal-budget/SKILL.md       # /sws:proposal-budget
    - skills/proposal-compliance/SKILL.md   # /sws:proposal-compliance

  profile_updates:
    - profiles/full-article.md              # agents_active/agents_inactive updated for cycle-#7 agents
    - profiles/communication.md
    - profiles/perspective.md
    - profiles/review-paper.md
    - profiles/mini-review.md
    - profiles/editorial.md
    - profiles/methodological-paper.md
    - profiles/commentary-reply.md
    - profiles/funding-proposal.md

  test_changes:
    - tests/test_agent_should_run.py
    - tests/test_outline_baseline.py
    - tests/test_citation_key_parser.py
    - tests/test_zotero_manifest_export.py
    - tests/test_section_to_agent_map.py
    - tests/test_profile_agent_activation.py
    - tests/fixtures/cycle_07_paper/       # minimal SWS-initialized perspective profile
    - tests/fixtures/zotero_collections/   # canned zotero exports
    - tests/fixtures/figures/              # 1–2 PNG fixtures for caption-writer
    - tests/smoke_cycle_07.sh              # full 6-agent e2e walkthrough

locked_decisions:
  D1_agent_file_structure_shared_scaffold:
    choice: "Shared scaffold + per-agent specialization (Q1=B). Each agent file is ~15 lines: frontmatter + agent-specific prompt + reference to references/agent-contract.md."
    rationale: "Cycle #6 already proved the prelude pattern. Future cross-cutting fixes touch one reference doc, not 7 agent files."

  D2_outline_md_format:
    choice: "Markdown + YAML frontmatter at <paper>/_outline/outline.md. Frontmatter = machine-readable (sections dict, figures dict). Body = prose-y narrative arc per section. (Q2=C)"
    rationale: "Mirrors profile/overlay file shape and the project's lean-deliverables pattern. One file serves both downstream agents (frontmatter) and the user (body)."

  D3_outline_overwrite_policy_warn_on_user_edits:
    choice: "outline-architect writes <paper>/_outline/.outline-baseline.sha256 sidecar after generation. Re-runs compare current outline.md hash to baseline; if different (user hand-edits), architect stops, shows diff of would-be-lost content, asks before overwriting. (Q2 sub-question)"
    rationale: "User feedback overrides automatic assignment, but the architect must surface lossy operations before doing them."

  D4_no_passport_log_for_outline_edits:
    choice: "outline.md edits are NOT specially logged in passport.json. Cycle-#5 Stop-hook already records one passport entry per agent run (agent=outline-architect, file=_outline/outline.md). No further per-edit tracking needed. Downstream agents read outline.md directly, never consult passport.json to find the latest outline. (Q2 sub-question)"
    rationale: "Outline is meant to be self-consistent for the architect; downstream dispatches read it directly. Per-edit logging adds tokens with no consumer."

  D5_ai_writing_tells_comprehensive_english_only:
    choice: "references/ai-writing-tells.md = comprehensive catalog (40–60 tells) structured by category (lexical, syntactic, structural, hedging-patterns, transitions). Each tell: pattern, example-bad, example-fix, severity (block/warn). English only in v0.1. Italian section deferred to v0.2+. (Q3=B + sub-question)"
    rationale: "Minimal seed (10–15 tells) too thin to be useful; would get reopened in cycle #8. Linter (option C) defers to cycle #8 once we have real false-positive data."

  D6_drafter_split_two_files:
    choice: "drafter splits into agents/drafter-flagship.md (Opus 4.7 xhigh, Intro/Discussion/Conclusion/Abstract) and agents/drafter-fast.md (Sonnet 4.6 high, Results + journal-defined narrative non-Methods sections like Theoretical Background, Limitations, Significance). (Q4=A)"
    rationale: "One model field per agent file. Two-file split is cheaper and more legible than invocation-time override or internal sub-dispatch. Future re-tier touches 2 small files."

  D7_first_draft_abstract_routes_to_flagship:
    choice: "drafter-flagship handles the FIRST abstract draft. The cycle-#8 abstract-writer agent is for refinement (word-count tightening, polish), not first draft. (Q4 sub-question)"

  D8_methods_writer_publication_only:
    choice: "methods-writer owns Materials + Methods + Statistical + Computational details + Software + Data availability when journal places them in the Experimental Section. Funding-proposal Methodology/Approach prose routes to drafter-flagship instead (it's rationale-prose, not procedural). (Q5=C + sub-question)"
    rationale: "Keeps cycle #7 at 6 agents (locked roster count). Methods-writer stays sharp. Proposal methodology rhetoric is closer to Discussion than to procedural Methods."

  D9_methodological_paper_profile_does_not_auto_route:
    choice: "Profile=methodological-paper does NOT auto-route everything to methods-writer. Profiles control section list, word budgets, agents_active, agents_inactive — never the section→agent map. A methodological paper still has Intro/Results/Discussion drafted by drafter-* as usual; methods-writer just gets a bigger Methods word-budget."
    rationale: "User correction during Q5. Profile sets WHAT KIND of paper; section→agent map is constant."

  D10_caption_writer_text_only_no_alt:
    choice: "caption-writer produces caption text only, written into outline.md frontmatter under each figure entry (figures: { f1: { caption: '<text>', file: ..., supports: ... } }). No alt-text. No docx editing. (Q6=A)"
    rationale: "User confirmed: never used alt-text; captions should be self-explanatory. Locked rule 'never Haiku for docx XML' rules out C."

  D11_chemistry_formatting_deferred_to_cycle_08:
    choice: "references/chemistry-formatting.md does NOT ship in cycle #7. Cycle-#7 agents produce drafts in plain prose; cycle-#8 reviser/style-enforcer handles italic species, sub/superscripts in formulae, italic Latin abbreviations, bold figure-label prefix. (Q6=c)"
    rationale: "User accepted that first draft is plain; polish is a downstream pass. Keeps cycle #7 scope tight."

  D12_proposal_budget_helper_suggest_only:
    choice: "proposal-budget-helper produces markdown line-item suggestions at <paper>/_proposal/budget-suggestions.md. Does NOT fill xlsx templates. User transcribes into the call's actual template manually. (Q7=A)"
    rationale: "Universally useful across any call format. Avoids xlsx formula-cell risk (CLAUDE.md item #4)."

  D13_budget_context_interactive_qa_cached:
    choice: "On first invocation, proposal-budget-helper runs an interactive Q&A (lab's PhD/postdoc gross/year, equipment hourly rates, consumables baseline) and caches answers to <paper>/_proposal/budget-context.yaml. Subsequent runs read the cache. User edits YAML to update. (Q7=a)"
    rationale: "Cost magnitudes vary by country/institution/lab. Asking once + caching is the cheapest accurate path."

  D14_proposal_compliance_helper_overlay_plus_pdf:
    choice: "proposal-compliance-helper reads the call-rules overlay (call/_call-style/<slug>.md) for structured rules, then uses Claude's built-in PDF/DOCX skill on call/<source>.pdf for ambiguity resolution. When nlm-librarian ships in cycle #11, this agent is upgraded to delegate PDF reading to NLM (cheaper grounded queries); cycle-#7 contract stays the same from the user's POV. (Q8=B)"
    rationale: "Mirrors how humans check proposals. Doesn't depend on cycle-#11 NLM."

  D15_compliance_report_standalone_file:
    choice: "Compliance output = standalone <paper>/_proposal/compliance-report.md with pass/fail per rule, line/section pointers into the proposal, suggested fixes. No inline docx-comment annotations (rejected as fragile). (Q8=b)"

  D16_drafter_grounding_zotero_manifest_pre_step:
    choice: "Before drafter runs, /sws:prepare-lit-context invokes the user's zotero skill and writes <paper>/_lit/zotero-manifest.md (per-item: zotero key, first-author, year, title, doi, key_claims digest). Drafter reads the manifest and cites from it. Items not in the manifest get [CITATION_NEEDED]. literature-searcher (cycle #11) later resolves keys to full bib entries and fills placeholder gaps. Manifest is opt-in; degradation chain: zotero (recommend install) → PubMed MCP fallback → placeholders. (Q9=B + degradation chain)"
    rationale: "Pure placeholders produce unusable May-deadline drafts. Live Zotero queries are heavy and assume the user has the zotero skill. Manifest pre-step uses what's available, falls back gracefully."

  D17_citation_key_format_explicit_prefix:
    choice: "Citation keys in drafted prose use form [Smith2023; doi:10.xxxx] or [Smith2023; zotero:ABCDEFGH]. Always first-author + year + explicit prefix (doi: or zotero:) + unique identifier. Placeholders use [CITATION_NEEDED: <claim being made>]. (Q9=c)"
    rationale: "Explicit prefix removes ambiguity for downstream parser. Author+year keeps it readable inline."

  D18_pubmed_expanded_zotero_search_deferred:
    choice: "PubMed-expanded-over-Zotero search (especially for peer-reviewer feedback flows) deferred to cycle #11 literature-searcher. Cycle #7 only does the Zotero-manifest pre-step + PubMed MCP fallback for known-missing items. (Q9 user note)"

  D19_testing_fixture_plus_structural_assertions:
    choice: "Unit tests cover deterministic scaffolding (prelude sourcing, profile resolution, format branching, should_run check, citation-key parsing, manifest export). Structural assertion tests on agent outputs: file exists, word-count under budget, AI-tells grep-pass = zero high-severity, citation keys parse. Integration smoke = tests/smoke_cycle_07.sh on tests/fixtures/cycle_07_paper/. No golden snapshot diffs (too brittle for LLM prose). (Q10=B)"

  D20_beta_integration_perspective_intro_paragraph:
    choice: "Cycle-#7 phase-2 mid-cycle gate = beta-test against a real in-progress perspective manuscript's introduction. The manuscript file is read READ-ONLY via Claude's built-in DOCX skill. Sandbox lives at this plugin repo's _perspective_beta/ (gitignored alongside claude_memory/), NOT in the actual paper folder. (Q11=B)"
    target_manuscript: "$TARGET_MANUSCRIPT"   # local path, kept out of version control; never commit a real path
    test_focus: "A subsection of the current intro is missing a relevant framing reference. Drafter-flagship is prompted with this gap; output compared side-by-side to the original."
    safety: "Manuscript file MUST NOT be written to. DOCX skill opens read-only. Sandbox sits inside this plugin repo so beta artifacts never pollute the actual paper directory."

  D21_phasing_internal_to_one_PR:
    choice: "Cycle #7 ships as one PR with four internal phases (Q11=C/build-strategy=C). Phase 1: scaffolding + outline-architect + drafter-flagship + minimal skills. Phase 2: beta-test gate against the beta-test perspective. Phase 3: remaining 5 agents (parallel subagent dispatch) + orchestrator mode + remaining skills. Phase 4: end-to-end smoke."
    rationale: "Captures vertical-slice beta-value-early without splitting the roadmap. Mid-cycle smoke catches scaffolding flaws before they propagate to 4 more agents."

  D22_io_wrapper_layer:
    choice: "Cycle #7 ships scripts/sws_read_docx.py + scripts/sws_read_xlsx.py wrappers (python-docx + openpyxl-based) because native Read tool fails on DOCX/XLSX. R3 in references/agent-contract.md updated to reflect: native Read for PDF + images; SWS wrappers for DOCX + XLSX. WRITE wrappers deferred to cycle #8 (reviser + style-enforcer needs)."
    rationale: "Discovered during phase-2 beta-test on the the beta-test perspective .docx. Contract was honest-broken — agents would either fail on the binary or silently fall back to ad-hoc python-docx installs. Ship the wrappers + fix the contract in the same PR so phase-3 agent prompts can reference them correctly from day one."

cross_cutting_agent_contract:
  description: "Content for references/agent-contract.md. Linked from every cycle-#7 agent file. Future agents (cycles #8–#11) inherit the same rules."
  rules:
    R1_python_frugality:
      rule: "Reuse <paper>/.venv/. No new pip installs unless the task genuinely requires it."
      why: "Per-paper venv discipline (cycle #6 D19/D20). New deps add maintenance burden and bootstrap time."

    R2_filesystem_frugality:
      rule: "Prefer scripts/sws_fs_index.py manifest + the Explore tool over Bash/ls/find. Reach for shell only when no alternative exists."
      why: "Long sessions burn tokens on repeated directory walks. The fs-index utility (cycle #1) was built specifically for this."

    R3_built_in_skill_preference:
      rule: "Use Claude's native PDF/DOCX reading and image viewing for paper figures, manuscript PNG/TIF/JPEG files, and PDF figures rather than spawning external tools or Python parsers."
      why: "Native skills are token-efficient and don't require new pip installs. Marker rule R1 reinforces."

    R4_token_discipline:
      rule: "Concise thinking and concise user-facing chatter. DRAFTED PROSE IS EXEMPT (the user controls voice via _voice/ and proposal-/perspective-style guides)."
      why: "Long sessions; many parallel agents; user wants the budget spent on output, not narration."

    R5_no_gender_default_in_user_address:
      rule: "Before adopting any pronoun, honorific, or gendered descriptor when addressing or referring to the user, read the user's memory/profile (e.g., $HOME/.claude/projects/<project>/memory/user_*.md). If pronouns are unknown, use the user's first name or neutral phrasing ('you', 'the user'). Do not guess."
      why: "Locked from user instruction 2026-05-13. LLMs frequently slip into he/him/Mr. defaults; this rule prevents it across all SWS agents."

  ai_tells_link: "All agents grep their drafts against references/ai-writing-tells.md before returning. Block-severity tells abort the response with a fix suggestion; warn-severity tells get flagged in the agent's reply."

  attribution_pattern: "Agent files whose prompts are adapted from MIT-licensed prior art carry a one-line header: # Adapted from <plugin-url> (MIT). Survey targets: andrehuang/academic-writing-agents, Imbad0202/academic-research-skills. Roster (names/scopes/models) is original to SWS; only prompt content adapts."

  agent_file_template:
    description: "What every cycle-#7 agent file looks like. ~15 lines."
    structure: |
      ---
      name: <agent-id>
      description: <one-line trigger description>
      model: <opus-4-7 | sonnet-4-6 | haiku-4-5>
      color: <pick from existing palette>
      ---

      # Adapted from <plugin-url> (MIT)   # only if applicable

      <Agent-specific 5-10 line prompt focused on the agent's narrow job>

      Follow the SWS agent contract: source ${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh, then ${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh <agent-id> before doing any work. See ${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md for the full contract.

orchestration_model:
  primary_agents: [outline-architect, drafter-flagship, drafter-fast, methods-writer, caption-writer, proposal-budget-helper, proposal-compliance-helper]
  service_agents_v01: [nlm-librarian]   # cycle #11; not built yet
  rules:
    user_to_skill_to_agent: "Standard path. User invokes a /sws:* skill; skill dispatches the right primary agent. The section→agent map lives in /sws:draft-section as a literal dictionary."
    primary_to_service: "Allowed. drafter-flagship, proposal-compliance-helper, etc. call nlm-librarian when it ships (cycle #11) for narrow capability (grounded literature lookup, call-PDF reading). Cycle-#7 versions degrade gracefully when nlm-librarian is absent."
    primary_to_primary_safety_net: "Allowed only as a misroute safety net. If user invokes drafter directly on a section it doesn't own (most likely 'draft the Methods'), drafter detects the mismatch and delegates to the right primary agent. Not a multi-agent orchestration pattern — just a UX backstop."
    whole_paper_orchestration: "drafter-flagship in orchestrator mode (when invoked via /sws:draft-paper). Reads outline frontmatter, dispatches in PARALLEL: itself for each Opus-tier section, drafter-fast for each Sonnet-tier narrative section, methods-writer for Methods, caption-writer for each figure. Reconciliation = drafter-flagship collects results into the docx. Cross-section issues are cycle-#8 reviser's job."

section_to_agent_map:
  description: "Authoritative routing for /sws:draft-section. Used by /sws:draft-paper as well. Methods/Experimental routes apply only to PUBLICATION profiles; for funding-proposal, methods-writer is in agents_inactive (D8), so the should_run check blocks it even if a user types `/sws:draft-section methods` — proposal Methodology routes to drafter-flagship via the explicit proposal-section entries below."
  map_publication:
    intro:        drafter-flagship
    introduction: drafter-flagship
    abstract:     drafter-flagship
    discussion:   drafter-flagship
    conclusion:   drafter-flagship
    conclusions:  drafter-flagship
    methods:      methods-writer
    experimental: methods-writer
    "experimental section": methods-writer
    materials:    methods-writer
    "statistical analysis": methods-writer
    "computational details": methods-writer
    software:     methods-writer
    "data availability": methods-writer
    results:      drafter-fast
    "results and discussion": drafter-flagship  # joint section: rationale wins → flagship
    figure_caption: caption-writer
  map_funding_proposal:
    "state of the art": drafter-flagship
    "state-of-the-art": drafter-flagship
    vision: drafter-flagship
    objectives: drafter-flagship
    workplan: drafter-flagship
    methodology: drafter-flagship          # proposal methodology = rationale prose (D8)
    approach: drafter-flagship
    impact: drafter-flagship
    "risk management": drafter-flagship
    deliverables: drafter-flagship
    timeline: drafter-flagship
    budget: proposal-budget-helper         # special: not a drafting agent; produces budget-suggestions.md
    compliance: proposal-compliance-helper # special: produces compliance-report.md
    figure_caption: caption-writer
  fallback:
    "*": drafter-fast                      # for unrecognized narrative section ids in publication profiles
  resolver: "Skill reads marker → resolved profile_id. If profile_id == funding-proposal: use map_funding_proposal. Else: use map_publication. Unmapped section_id in either map → fall back to drafter-fast (publication) or drafter-flagship (proposal)."

agent_activation_matrix_cycle_07_updates:
  description: "Cycle-#7 agents land in the agents_active/agents_inactive lists per profile. Cycle-#6 baseline preserved; only cycle-#7 agent IDs added below."
  invariant_caption_writer_always_active: "caption-writer is ACTIVE for every profile (user instruction 2026-05-13). Do not add it to any profile's agents_inactive list."
  per_profile_inactive_additions:
    full-article: []
    communication: [methods-writer, drafter-fast]   # short-form; intro/discussion/conclusion + caption-writer for the typical 1-2 figures
    perspective: [proposal-budget-helper, proposal-compliance-helper, methods-writer]   # narrative + figures (concept schemas, classification trees, overviews) — caption-writer ACTIVE
    review-paper: [proposal-budget-helper, proposal-compliance-helper, methods-writer]
    mini-review: [proposal-budget-helper, proposal-compliance-helper, methods-writer]
    editorial: [proposal-budget-helper, proposal-compliance-helper, methods-writer, drafter-fast]   # short-form opinion; caption-writer ACTIVE per user instruction (caption-writer is always active across all profiles)
    methodological-paper: [proposal-budget-helper, proposal-compliance-helper]
    commentary-reply: [proposal-budget-helper, proposal-compliance-helper, methods-writer]   # rebuttal text; figures rare but allowed — caption-writer ACTIVE
    funding-proposal: [methods-writer, drafter-fast]                # methodology routes through drafter-flagship per D8

auxiliary_file_shapes:
  outline_md:
    path: "<paper>/_outline/outline.md"
    written_by: outline-architect
    figure_discovery: "outline-architect scans <paper>/figures/ (or the canonical figures directory per references/folder-topology.md) for image files (PNG/TIF/JPEG/SVG) and seeds the figures dict in the frontmatter. Per-figure caption stays empty until caption-writer runs. The user edits the `supports:` field (which section the figure supports) and may delete or reorder figures in the frontmatter before caption-writer runs."
    schema: |
      ---
      profile: <id>
      generated_at: <iso8601>
      sections:
        intro:    { word_target: int, status: planned|drafted|revised, key_claims: [string], figs: [string], cites: [string] }
        methods:  { ... }
        results:  { ... }
        ...
      figures:
        f1: { caption: "", file: "figures/Fig1.png", supports: "Results §1" }
        f2: { ... }
      ---
      # Outline narrative
      ## Intro
      <prose-y narrative arc per section: hook, gap, contribution, roadmap>

  outline_baseline:
    path: "<paper>/_outline/.outline-baseline.sha256"
    written_by: outline-architect
    purpose: "Detect user hand-edits before architect overwrites on re-run (D3)."

  zotero_manifest:
    path: "<paper>/_lit/zotero-manifest.md"
    written_by: "/sws:prepare-lit-context (wrapping user's zotero skill)"
    schema: |
      ---
      exported_from: zotero://library/collection/<id>
      exported_at: <iso8601>
      item_count: int
      cap_token_budget: int   # opt-in cap; truncate beyond this
      ---
      - key: ABCDEFGH
        first_author: Smith
        year: 2023
        title: "..."
        doi: 10.xxxx
        key_claims: "Showed that X under condition Y..."
      - ...
    degradation:
      - "If user's zotero skill is not installed: print 'install the zotero skill for citation grounding; falling back to PubMed MCP / placeholders' and continue."
      - "If PubMed MCP is unavailable too: drafter writes [CITATION_NEEDED: <claim>] placeholders for any cite-needing claim."

  budget_context:
    path: "<paper>/_proposal/budget-context.yaml"
    written_by: proposal-budget-helper (Q&A on first run)
    schema: |
      phd_gross_per_year: int
      postdoc_gross_per_year: int
      consumables_per_project_year: int
      equipment_hourly_rates: { instrument_X: int, ... }
      currency: <ISO 4217>
      last_updated: <date>

  budget_suggestions:
    path: "<paper>/_proposal/budget-suggestions.md"
    written_by: proposal-budget-helper
    shape: "Markdown breakdown by WP. Per-WP: line items, magnitudes, rationale, total. Final total + sanity check vs call's budget cap (from call-rules overlay)."

  compliance_report:
    path: "<paper>/_proposal/compliance-report.md"
    written_by: proposal-compliance-helper
    shape: "Per-rule pass/fail. Pointer (proposal section + line range) for each fail. Suggested fix for each fail. Summary header with rule-pass count."

  perspective_beta_sandbox:
    path: "<plugin-repo>/_perspective_beta/   # NOT in user paper folder"
    gitignore_status: "gitignored alongside claude_memory/"
    contents:
      - source-snapshot.md     # extracted scope + intro from real manuscript (read-only DOCX skill)
      - outline.md             # sandbox outline frontmatter for the perspective profile
      - draft-intro-v1.md      # drafter-flagship output
      - comparison.md          # side-by-side original vs draft

phasing:
  phase_1_scaffolding_plus_first_slice:
    description: "Build shared scaffolding + outline-architect + drafter-flagship (single-section mode only) + minimal skills."
    deliverables:
      - references/agent-contract.md
      - references/ai-writing-tells.md
      - scripts/agent_should_run.sh
      - agents/outline-architect.md
      - agents/drafter-flagship.md   # single-section mode only in this phase
      - skills/outline-paper/SKILL.md
      - skills/draft-section/SKILL.md   # intro routing only
      - skills/prepare-lit-context/SKILL.md
      - scripts/sws_extract_zotero_manifest.py
      - tests/test_agent_should_run.py
      - tests/test_outline_baseline.py
      - tests/test_citation_key_parser.py
      - tests/test_zotero_manifest_export.py

  phase_2_beta_gate:
    description: "Mid-cycle beta-test against the beta-test perspective intro (D20). User reviews. Proceed only on acceptable result."
    artifacts:
      - _perspective_beta/source-snapshot.md
      - _perspective_beta/outline.md
      - _perspective_beta/draft-intro-v1.md
      - _perspective_beta/comparison.md
    gate_criteria:
      - "Drafter-flagship intro addresses the Semaglutide-driven peptide-revival gap"
      - "Output stays within the perspective profile's intro word_target"
      - "AI-tells grep returns zero block-severity hits"
      - "User finds the draft preferable or comparable to current"

  phase_3_remaining_agents:
    description: "Parallel subagent dispatch (per feedback_subagent_dispatch.md) for the 5 remaining agents + drafter-flagship orchestrator extension + remaining skills."
    deliverables:
      - agents/drafter-fast.md
      - agents/methods-writer.md
      - agents/caption-writer.md
      - agents/proposal-budget-helper.md
      - agents/proposal-compliance-helper.md
      - agents/drafter-flagship.md   # extended with orchestrator mode
      - skills/draft-section/SKILL.md   # extended with full section→agent map
      - skills/draft-paper/SKILL.md
      - skills/proposal-budget/SKILL.md
      - skills/proposal-compliance/SKILL.md
      - profiles/*.md   # agent_activation_matrix_cycle_07_updates applied
      - tests/test_section_to_agent_map.py
      - tests/test_profile_agent_activation.py

  phase_4_e2e_smoke_and_pr:
    description: "End-to-end smoke + PR open."
    deliverables:
      - tests/fixtures/cycle_07_paper/
      - tests/fixtures/zotero_collections/
      - tests/fixtures/figures/
      - tests/smoke_cycle_07.sh
    smoke_steps:
      - "1. /sws:set-profile perspective on fixture paper"
      - "2. /sws:resolve-journal-style chembiochem (using cycle-06 fixture HTML)"
      - "3. /sws:prepare-lit-context (canned zotero collection)"
      - "4. /sws:outline-paper → outline.md + .outline-baseline.sha256 written"
      - "5. /sws:draft-section intro → drafter-flagship draft, citations from manifest"
      - "6. Switch fixture to funding-proposal profile, drop call/test-call.pdf"
      - "7. /sws:resolve-call-rules"
      - "8. /sws:proposal-budget → first-run Q&A scripted, budget-context.yaml + budget-suggestions.md written"
      - "9. /sws:proposal-compliance → compliance-report.md written"
      - "10. /sws:draft-paper on the perspective fixture (multiple sections + figures) → drafter-flagship orchestrator-mode parallel fan-out: itself for intro/discussion/conclusion/abstract, drafter-fast for results, caption-writer for each figure. Result: all sections drafted into _drafts/ in one orchestrator call."
      - "11. AI-tells grep on all phase-4 outputs returns zero block-severity"

testing:
  unit_target: "~80 tests across cycle-#7 deliverables"
  test_files:
    - "tests/test_agent_should_run.py — gating against agents_active/agents_inactive for all 9 profiles + cycle-#7 agents"
    - "tests/test_outline_baseline.py — sidecar write/compare/diff; modification detection; new-file vs re-run"
    - "tests/test_citation_key_parser.py — [Author Year; doi:...] / [...; zotero:...] / [CITATION_NEEDED: ...] all parse; malformed rejected"
    - "tests/test_zotero_manifest_export.py — empty collection; missing DOI; missing first-author; token-budget cap; unavailable zotero skill graceful degradation"
    - "tests/test_section_to_agent_map.py — section→agent routing for all locked sections + fallback"
    - "tests/test_profile_agent_activation.py — agent_activation_matrix_cycle_07_updates applied correctly per profile"
  integration_smoke: "tests/smoke_cycle_07.sh per phase_4 spec above"

what_stays_v02_or_later:
  - "references/chemistry-formatting.md — cycle #8 reviser/style-enforcer pass (D11)"
  - "Alt-text for figures — never planned for v0.1; revisit only if accessibility lobbying emerges"
  - "xlsx-budget-template auto-fill — cycle #10 or v0.2; needs real call-template corpus first"
  - "nlm-librarian + NLM-grounded behaviors — cycle #11"
  - "literature-searcher (PubMed-expanded-over-Zotero) — cycle #11"
  - "Inline docx-comment compliance annotations — never (D15 is final)"
  - "Italian section of ai-writing-tells.md — v0.2+"
  - "format: latex deep handling — v0.2 format-translator"
  - "Live Zotero queries from drafter (vs manifest pre-step) — re-evaluate after cycle #11 literature-searcher exists"
  - "Linter for AI-tells (vs grep-pass) — cycle #8 once we have false-positive data"

risks:
  R1_andrehuang_imbad_too_latex_coupled:
    risk: "Prior-art prompts may be so LaTeX-coupled that adaptation cost ≈ fresh-write."
    mitigation: "Survey-then-decide per agent during phase 3. If adaptation < 30% of prompt, header attribution + fresh-write the rest. If 0%, don't add the header."

  R2_zotero_manifest_token_blowup:
    risk: "Large Zotero collections produce manifests that consume > target token budget, crowding out drafter context."
    mitigation: "Manifest export caps total tokens (default 15k); user can tune via cap_token_budget frontmatter. Truncation strategy: most recent N items by date_added; user can re-run /sws:prepare-lit-context with a tighter collection scope."

  R3_outline_baseline_collision_with_user_workflow:
    risk: "User edits outline.md, runs architect again later, gets prompted for diff — annoying if frequent."
    mitigation: "Baseline check is opt-out via /sws:outline-paper --force. Default is the safety prompt."

  R4_caption_writer_haiku_image_quality:
    risk: "Haiku 4.5 may produce thin captions on technical figures (microscopy, chromatograms, kinetics plots)."
    mitigation: "Caption-writer prompt explicitly asks for description grounded in the section's key_claims (from outline frontmatter), not just visual description. If beta surfaces caption-quality issues, fall back to Sonnet for caption-writer in cycle #8."

  R5_proposal_compliance_call_pdf_too_big:
    risk: "Some call PDFs (ERC, MSCA) are 100+ pages; Claude built-in PDF skill may struggle with whole-doc context."
    mitigation: "Compliance helper reads the overlay (already digested) FIRST; only opens the PDF for specific ambiguity resolution (passes a targeted question + relevant page range). Falls back to user-supplied excerpt if PDF skill fails."

  R6_beta_test_manuscript_accidental_write:
    risk: "Misconfigured agent or skill writes to the actual beta-test manuscript file."
    mitigation: "Beta sandbox lives at THIS plugin repo's _perspective_beta/, not in the user paper folder. DOCX skill is opened in read-only mode. Tests for the beta path assert no writes outside _perspective_beta/."

---

# Cycle #7 — Drafting + funding-proposal helpers (6 agents, 7 files)

Frontmatter above is the source of truth. This body is orientation only.

## Why

Cycle #6 shipped the profile + overlay layer; cycle #5 shipped hooks + passport. Cycle #7 is the first cycle where SWS produces actual prose. The deliverable — first usable proposal/perspective writing capability — directly serves the user's near-term deadlines (perspective transformation, May 2026 funding proposal). Until cycle #7 lands, SWS is infrastructure with no end-user output.

## What ships

Two reference docs (`agent-contract.md`, `ai-writing-tells.md`), 7 agent files (drafter splits into flagship + fast), 6 new skills (`/sws:outline-paper`, `/sws:draft-section`, `/sws:draft-paper`, `/sws:prepare-lit-context`, `/sws:proposal-budget`, `/sws:proposal-compliance`), one new helper script (`agent_should_run.sh`), one new utility script (`sws_extract_zotero_manifest.py`), updates to all 9 profile files for the new agent_activation_matrix entries.

## How it ships (phasing)

One PR, four phases. Phase 2 is a real mid-cycle beta-test against the user's actual perspective intro (read-only) before building the remaining 5 agents. See `phasing` in frontmatter for full per-phase deliverable lists.

## What stays for cycles #8 / #11 / v0.2

See `what_stays_v02_or_later` in frontmatter.
