---
sws_artifact: cycle-12-spec
artifact_version: 0.1
locked: 2026-05-30
title: "Cycle #12 — Submission orchestration (2 agents: cover-letter-writer, response-to-reviewers; 4 skills incl. /sws:run-cycle master orchestrator; venue-specific AI-disclosure; .review/round-N persistence pattern; passport submission-phase fields)."

cycle_index: 12
original_roadmap_index: 10
predecessor: cycle-11-data-and-literature-wave
banner_after_completion: null            # banner stays 🧪 v0.1 alpha; v0.1 flip is cycle-13 (NLM)
version_after_completion: "0.1.0-alpha"

autonomous_run_caveat: |
  Cycle #12 was executed autonomously on 2026-05-30 with the user's explicit grant of authority
  ("conclude unattended all the cycles remaining until full 0.1 deploy"). Every locked decision
  carries a rationale so the user can re-decide any of them before the PR merges. The PR is
  opened in READY (not draft) state since the user has asked for end-to-end deploy preparation;
  the user merges manually per established cycle-#3-onwards pattern.

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §7 cycle table line 491 ('Cycle + submission orchestration': /sws:run-cycle skill, cover-letter-writer, response-to-reviewers with R&R Traceability Matrix, Disclosure-mode slash command, passport submission-phase fields, .review/ persistence pattern)."
  prior_cycle_anchors:
    - "cycle-05: passport.json schema (cycle, agent, file, change_summary, next_step) — cycle-12 extends with optional submission-phase fields"
    - "cycle-06: resolve_overlay.py + agent_prelude.sh expose RESOLVED_DISCLOSURE_REQUIRED + RESOLVED_COVER_LETTER_REQUIRED — cycle-12 consumes them"
    - "cycle-07 D17 / cycle-09: citation-key bracket format — response-to-reviewers preserves them"
    - "cycle-08 D9: _review/ established as the SWS-managed review directory — cycle-12 adds _review/round-<N>/ sub-folders for externally-received reviewer comments + the R&R matrix"
    - "cycle-08 D12 / cycle-09: section-router action axis already 6-deep (draft|revise|consistency|style|lint|review) — cycle-12 adds a 7th: submit"
    - "cycle-09: peer-reviewer + claim-verifier + bibliography-fidelity-checker outputs sit under _review/<agent>/ — that layout is preserved untouched; new submission artifacts sit under _review/round-<N>/ which never collides"
  related_memory:
    - "claude_memory/project_roster_v0.1.md (#20 cover-letter-writer Sonnet 4.6 high; #21 response-to-reviewers Opus 4.7 xhigh)"
    - "claude_memory/project_profiles.md + the 9 profile files (disclosure_required, cover_letter_required already in frontmatter)"
    - "claude_memory/feedback_ai_writing_tells.md (cover-letter prose must grep-pass the AI-tells linter)"
    - "claude_memory/feedback_subagent_dispatch.md (phase-sequential, within-phase parallel — /sws:run-cycle orchestrator follows phase order)"
    - "claude_memory/feedback_integration_smoke.md (smoke_cycle_12.sh = canonical e2e verification)"
    - "claude_memory/feedback_lean_deliverables.md (frontmatter = dictionary, body = orientation)"

scope:
  deliverable: "First usable submission orchestration. End of cycle: a user with a reviewed paper (cycle #9 outputs in _review/<agent>/) can run /sws:write-cover-letter to draft a journal-specific cover letter, /sws:respond-to-reviewers (reading _review/round-1/reviewer-comments.md provided by the user) to produce a Response-to-Reviewers document + R&R Traceability Matrix JSON, /sws:disclose-ai-usage to produce a venue-specific AI-usage statement, and /sws:run-cycle as the master orchestrator that runs the entire SWS pipeline (outline → draft → revise → review → submission artifacts) in one invocation, idempotently skipping steps whose outputs already exist. Passport entries gain optional submission-phase fields (phase, venue, round). The complete v0.1-alpha pipeline now has a single entry point."
  not_in_scope:
    - "Actual submission to the journal portal (Wiley/Elsevier/RSC/ACS submission systems) — manual user step; v0.2+ for any portal automation"
    - "OCR / parsing of reviewer comments from PDF — v0.1 expects user to convert reviewer PDF to markdown manually (or paste into _review/round-N/reviewer-comments.md). v0.2 may add /sws:ingest-reviewer-pdf"
    - "Multi-round response automation (round 2, round 3 of revisions) — schema supports round-<N> folders; v0.1 covers the workflow once, the user just reruns for subsequent rounds. No new tooling required."
    - "Inline docx-comment threading from reviewer-quote → paragraph-changed — v0.2 (mirrors cycle-09 docx-comment exclusion)"
    - "Sprint-contracts / concession-threshold automation triggered by response-to-reviewers — the rubric structure is encoded in the agent prompt, but no automated escalation. v0.2"
    - "Disclosure language for venues we don't have an overlay for — /sws:disclose-ai-usage falls back to a generic ICMJE-style statement and surfaces a TODO; per-venue language requires the journal overlay to populate disclosure.template_id (v0.2 expands the catalog)"
    - "NLM-grounded response-to-reviewers (e.g., feeding the reviewer comments through nlm-librarian) — deferred to cycle #13"
    - "/sws:run-cycle does not modify _voice/, _drafts/, or final .docx files itself — it dispatches the existing skills; orchestration is the new value-add, not new write logic"
    - "Funding-proposal cover-letter generation — cover-letter-writer is INACTIVE in funding-proposal (D8); proposals have their own submission artifacts (proposal-budget, proposal-compliance) which already shipped in cycle-#7"

deliverables:
  scripts:
    - scripts/sws_response_matrix.py     # parses _review/round-<N>/reviewer-comments.md into a structured JSON matrix (reviewer × comment → status/response/edits); deterministic, no LLM call (D5)
    - scripts/sws_disclosure_writer.py   # composes a venue-specific AI-usage statement from journal-overlay disclosure.template_id + RESOLVED_DISCLOSURE_REQUIRED; falls back to ICMJE-style on miss
    - scripts/sws_run_cycle.py           # orchestration driver: enumerates planned steps based on profile/marker/existing artifacts, prints a step plan, dispatches sub-skills in phase order, writes a single cycle-summary passport entry at the end
    - scripts/sws_review_round.py        # init / find / inventory _review/round-<N>/ folders; idempotent
  references:
    - references/submission-artifacts.md  # the 3 submission artifact formats (cover letter, response-to-reviewers, AI-disclosure) + the _review/round-<N>/ folder schema + venue-template-id mapping
  agents:
    - agents/cover-letter-writer.md       # Sonnet 4.6 high (roster #20). Reads resolved journal-style overlay (target_journal, editor_address, requested_format) + the paper's abstract + the profile to draft a venue-appropriate cover letter. Never invents the editor's name; uses {EDITOR_NAME} placeholder.
    - agents/response-to-reviewers.md     # Opus 4.7 xhigh (roster #21). Reads _review/round-<N>/reviewer-comments.md + the paper drafts/.docx + (optionally) the cycle-09 peer-review report for cross-checks. Produces a Response-to-Reviewers .md following the R&R Traceability Matrix structure (one row per comment: id, severity, status (accepted/partial/rejected), edits_made, response_text, line_refs). Concession-threshold rubric encoded in prompt (concessions only when reviewer score >=4).
  skills:
    - skills/write-cover-letter/SKILL.md          # /sws:write-cover-letter
    - skills/respond-to-reviewers/SKILL.md        # /sws:respond-to-reviewers --round <N>
    - skills/disclose-ai-usage/SKILL.md           # /sws:disclose-ai-usage
    - skills/run-cycle/SKILL.md                   # /sws:run-cycle (master orchestrator)
  profile_updates:
    - profiles/full-article.md                    # agents_active picks up [cover-letter-writer, response-to-reviewers]
    - profiles/communication.md                   # same
    - profiles/perspective.md                     # cover-letter-writer ACTIVE; response-to-reviewers ACTIVE (perspectives go through review)
    - profiles/review-paper.md                    # same
    - profiles/mini-review.md                     # same
    - profiles/methodological-paper.md            # same
    - profiles/editorial.md                       # cover-letter-writer ACTIVE; response-to-reviewers INACTIVE (editorials are invited, no peer-review rounds in v0.1)
    - profiles/commentary-reply.md                # cover-letter-writer ACTIVE; response-to-reviewers ACTIVE
    - profiles/funding-proposal.md                # both INACTIVE — proposals use proposal-budget-helper + proposal-compliance-helper from cycle-#7; no cover-letter, no R&R (D8)
  reference_updates:
    - references/agent-contract.md                # R3 I/O inventory extended with _review/round-<N>/ shape + submission artifacts/ output dir
    - references/marker-schema.md                 # additive: target_journal already supports the editor_name optional sub-field via journal overlay (no marker change), but add note that disclosure template id is overlay-resolved
  router_updates:
    - scripts/sws_section_router.py               # 7th action axis: submit (maps "cover-letter" + "response" + "disclosure" routes to the three new skills)
  passport_updates:
    - scripts/sws_hook_stop_passport.py           # add optional fields to passport entry schema: phase (plan|draft|revise|review|submit), venue (slug from target_journal), round (int). All optional; older entries remain valid.
  memory_updates:
    - claude_memory/project_v02_backlog.md        # 5 new entries (per-portal submission automation, OCR-ingest reviewer PDF, multi-round automation, inline docx-comment threading, disclosure-catalog expansion)
    - claude_memory/project_cycle_execution_status.md  # cycle #12 → merged at end of PR
  tests:
    - tests/test_response_matrix.py               # parser unit tests (markdown → matrix JSON); round-trip; severity inference; status state machine
    - tests/test_disclosure_writer.py             # venue-specific template render; ICMJE fallback; resolver-disabled (RESOLVED_DISCLOSURE_REQUIRED=false) → exits cleanly with "not required"
    - tests/test_review_round.py                  # init creates _review/round-1/; find returns highest existing N; inventory lists artifacts
    - tests/test_run_cycle.py                     # plans correct step set for each profile; idempotent skip when artifact exists; final passport entry written
    - tests/test_section_router_submit_action.py  # 7th action axis routes correctly
    - tests/test_profile_activation_submission.py # the 2-agent activation matrix across 9 profiles
    - tests/test_passport_submission_fields.py    # entries with phase|venue|round validate; older entries without them validate too
    - tests/smoke_cycle_12.sh                     # end-to-end: cover-letter → respond-to-reviewers → disclose-ai-usage → run-cycle dry-run on fixture

locked_decisions:
  D1: |
    One PR. 2 agents (#20 cover-letter-writer Sonnet 4.6 high; #21 response-to-reviewers Opus 4.7 xhigh) + 4 skills.
    Matches the roadmap line 491 bundle exactly.
    Rationale: cover-letter and response-to-reviewers are the two submission artifacts the architecture sketch
    locked in §7; they ship together because they share the _review/round-<N>/ folder schema and the passport
    submission-phase fields.

  D2: |
    Three artifact skills (write-cover-letter, respond-to-reviewers, disclose-ai-usage) + one orchestrator
    skill (run-cycle).
    Rationale: each artifact has independent value (a user with no reviewer comments yet still wants to draft
    a cover letter). run-cycle adds end-to-end value: outline → draft → revise → review → submission artifacts
    in one invocation, idempotent on re-run.

  D3: |
    _review/round-<N>/ folder schema (mirrors _drafts/, _voice/, _lit-search/ — underscore prefix, not dot).
    Contents:
      _review/round-1/
        reviewer-comments.md         # USER-PROVIDED (parsed from journal email/portal; v0.1 expects markdown)
        response-matrix.json         # scripts/sws_response_matrix.py output (deterministic parse)
        response-to-reviewers.md     # response-to-reviewers agent output (the prose document)
        edits-summary.md             # optional, agent-generated list of edits made per comment
    Subsequent rounds use round-2, round-3, etc.
    Rationale: matches the existing underscore-prefix SWS convention (cycle-08 D9, cycle-10 _voice/, cycle-07
    _lit-search/). Architecture sketch said ".review/" but underscore is the de-facto pattern across all other
    SWS-managed folders, and dot-prefixed folders are reserved for .sws-project.local.md and .venv/.

  D4: |
    Passport schema extension is ADDITIVE ONLY. New optional fields: phase (enum: plan|draft|revise|review|submit),
    venue (string, copied from target_journal), round (int, only set when phase==submit and a round-<N> applies).
    Older entries without these fields validate; the JSON-schema version stays at the cycle-05 schema (no bump
    required for additive-optional changes).
    Rationale: cycle-05 D-locked the 5-field core schema; the architecture sketch said "final maturation with
    submission-phase fields" — additive is the cheapest path that doesn't break the cycle-05 contract.

  D5: |
    sws_response_matrix.py is DETERMINISTIC, no LLM call. It parses reviewer-comments.md (markdown headings
    Reviewer 1/2/3 + numbered bullets) into a JSON matrix (reviewer × comment → {id, text, severity_inferred,
    status: "pending", response_text: "", edits_made: [], line_refs: []}). The response-to-reviewers AGENT
    fills the status/response_text/edits_made fields by editing the JSON and rendering the .md.
    Rationale: parsing structured markdown is well within a Python script's range and removes LLM-call costs
    from a step the user will run on every revision round. The expensive Opus reasoning is reserved for the
    response prose, where it matters.

  D6: |
    Reviewer-comments.md input format is LIBERAL — accepts any of:
      (a) "## Reviewer 1" headings with numbered or bulleted comments
      (b) flat numbered list with implicit single-reviewer
      (c) "R1.1:" / "R2.3:" prefixed lines (per Imbad0202 convention)
    Parser detects the shape and routes to the right strategy; unknown shape → exit-3 with an explicit error
    message and an inline example of the three accepted shapes.
    Rationale: reviewer comments arrive in heterogeneous formats from journal portals. Hardline-rejecting on
    a minor formatting variant would make the tool annoying to use; the deterministic parser absorbs the
    variation.

  D7: |
    /sws:disclose-ai-usage produces a single statement file at _submission/ai-disclosure.md.
    Venue language is keyed by journal_overlay.disclosure.template_id; valid template_ids ship a body in
    references/submission-artifacts.md disclosure_templates.{template_id}. v0.1 ships 4 templates:
      - "icmje"      (default ICMJE-style language; covers most clinical / biomedical journals)
      - "wiley"      (Wiley AI/genAI policy as of 2026)
      - "rsc"        (Royal Society of Chemistry policy)
      - "acs"        (American Chemical Society policy)
    Journal overlays for chembiochem, jacs, chemsci, chemcomm, ic, etc. set disclosure.template_id to one
    of these 4. Missing template_id → fallback to "icmje" with a surfaced TODO.
    Rationale: the v0.1 journal-url-map has 8 slugs; mapping each to one of 4 publisher families covers them
    cleanly. Catalog expansion is v0.2 (project_v02_backlog).

  D8: |
    Profile activation matrix:
      cover-letter-writer:
        ACTIVE in: full-article, communication, perspective, review-paper, mini-review, methodological-paper,
                   editorial (invited cover note), commentary-reply
        INACTIVE in: funding-proposal (proposals don't have cover letters in v0.1; proposal-compliance-helper
                     covers the equivalent)
      response-to-reviewers:
        ACTIVE in: full-article, communication, perspective, review-paper, mini-review, methodological-paper,
                   commentary-reply
        INACTIVE in: editorial (invited, no peer-review rounds), funding-proposal (proposals don't go through
                     R&R; rebuttal at re-submission is its own beast deferred to v0.2)
    Rationale: cover letters apply to almost everything (8/9 profiles); R&R applies to 7/9 (editorial +
    funding-proposal opt out, both for the same reason — different submission workflow).

  D9: |
    /sws:run-cycle orchestrator step plan (idempotent on re-run; skips any step whose artifacts already
    exist on disk):
      Step 1 — outline       (skip if outline.md exists)
      Step 2 — draft         (skip if _drafts/*.md exist and pass agent-contract R3 inventory)
      Step 3 — revise        (skip if revise-paper has produced revised drafts; sentinel = passport
                              entry with phase==revise within last 24h OR _drafts/*.revised.md timestamps
                              newer than _drafts/*.md)
      Step 4 — review        (skip if _review/{peer-reviewer,claim-verifier,bibliography-fidelity-checker}/
                              all populated; otherwise dispatches /sws:review-paper)
      Step 5 — cover letter  (skip if _submission/cover-letter.md exists; conditional on
                              RESOLVED_COVER_LETTER_REQUIRED + cover-letter-writer active in profile)
      Step 6 — disclosure    (skip if _submission/ai-disclosure.md exists; conditional on
                              RESOLVED_DISCLOSURE_REQUIRED)
      Step 7 — response      (only if _review/round-<N>/reviewer-comments.md exists for any N; skip if
                              response-to-reviewers.md exists for that round; conditional on
                              response-to-reviewers active in profile)
    Final action: write ONE passport entry with phase==submit, change_summary listing the steps run,
    next_step indicating any TODOs surfaced.
    Rationale: idempotency is critical because users will rerun /sws:run-cycle after every round of edits;
    re-doing completed steps would waste tokens and risk overwriting good work.

  D10: |
    /sws:run-cycle is ADVISORY when an artifact is stale (e.g., source draft modified after the
    cover-letter was generated). It prints a "stale: cover-letter.md predates current draft" warning and
    surfaces the choice to the user — it does NOT auto-regenerate. The user re-runs the specific skill
    if they want the artifact refreshed.
    Rationale: silent regeneration of a hand-edited cover letter would destroy the user's polish work.
    Stale-detection is a notice, not a trigger.

  D11: |
    Cover-letter-writer NEVER invents an editor name. It reads journal_overlay.editor_name if present, or
    emits {EDITOR_NAME} placeholder with an explicit TODO in the output for the user to fill manually.
    Rationale: editor identity is venue-specific, time-varying, and easily wrong. A fabricated editor name
    would be embarrassing. The journal-style overlay can populate it when known.

  D12: |
    Response-to-reviewers concession threshold is encoded in the agent prompt only — no automated scoring.
    The prompt instructs: "Score each reviewer comment for soundness 1-5. Accept (concede) ONLY when
    score ≥ 4 AND the requested change would not contradict your manuscript's thesis or evidence base.
    Otherwise: push back with evidence, or partial-accept with explicit scope."
    Rationale: codifying a manual rubric in the prompt is the v0.1 commitment (Imbad0202 pattern). Automated
    scoring is v0.2; cycle-09 D-locked sprint-contracts + concession-scoring as deferred.

  D13: |
    No new external API integrations. Cover-letter, response-to-reviewers, and disclosure are all local
    document-generation tasks. Existing wired-up tools (Zotero, Semantic Scholar via cycle-09/11 scripts)
    are not needed.
    Rationale: scope discipline. The submission artifacts are about marshalling already-known facts (the
    paper, the journal style, the reviewer comments), not gathering new ones.

  D14: |
    /sws:run-cycle accepts an optional --dry-run flag that prints the step plan without executing.
    It also accepts --only=<step1,step2,...> to run a subset (e.g., --only=cover-letter,disclosure).
    Rationale: dry-run lets users sanity-check before kicking off a long orchestration; --only supports
    the common case of "I just need the submission artifacts, the paper is already revised and reviewed."

  D15: |
    Submission artifacts land in _submission/ (new SWS-managed dir):
      _submission/cover-letter.md
      _submission/ai-disclosure.md
      _submission/response-to-reviewers-round-<N>.md   # one per round, linked to _review/round-<N>/
    Rationale: keeps the "what gets uploaded to the journal" set in one folder, separate from the SWS-internal
    _review/round-<N>/ machinery. Mirrors _drafts/ (working) vs final .docx (output).

  D16: |
    All cycle-12 prose outputs (cover-letter, response-to-reviewers, ai-disclosure) MUST grep-pass the
    AI-tells linter (sws_lint_ai_tells.py from cycle-08) before being written. Agent prompts include the
    R5 (cycle-07 agent-contract) gender-neutral rule and the R6 AI-tells-grep-pass-before-return rule.
    Rationale: editor-facing prose is the highest-stakes output in the entire SWS workflow; AI-tells in a
    cover letter or response-to-reviewers would torpedo the submission's credibility. The existing linter
    catches the 55 English tells.

  D17: |
    Section-router 7th action axis "submit" routes:
      cover-letter  → /sws:write-cover-letter
      response      → /sws:respond-to-reviewers
      disclosure    → /sws:disclose-ai-usage
    Rationale: section-router is the canonical dispatcher; adding the axis keeps the dispatch table single-
    sourced. Mirrors cycle-09's "review" axis addition.

  D18: |
    --venue flag override on /sws:write-cover-letter and /sws:disclose-ai-usage allows the user to write
    a cover letter or disclosure for a target_journal different from the one in the marker (e.g., when
    submitting elsewhere after rejection). Default: read target_journal from marker.
    Rationale: rejection-redirect is a common reality; forcing the user to edit the marker first is friction.

  D19: |
    No code-reviewer agent dispatched on this cycle's outputs by default. The /sws:run-cycle orchestrator
    does NOT call code-reviewer on the cover-letter / response / disclosure outputs (they are not code;
    code-reviewer evaluates code). The cycle-09 review pipeline (peer-reviewer + claim-verifier +
    bibliography-fidelity-checker) handles paper-text quality and runs upstream of step 5.
    Rationale: avoids redundant invocation. The review pipeline already covered the manuscript itself
    before /sws:run-cycle reaches the submission step.

  D20: |
    smoke_cycle_12.sh test corpus uses fixture/sample-cycle-12/ with:
      - a 4-line outline.md (skip-step-1 sentinel)
      - 3 minimal _drafts/*.md files (skip-step-2 sentinel)
      - 3 minimal _review/<agent>/report.md files (skip-step-4 sentinel)
      - a _review/round-1/reviewer-comments.md with 2 reviewers × 3 comments each (drives step 7)
      - .sws-project.local.md with cover_letter_required + disclosure_required true, article_type=full-article,
        target_journal=chembiochem
    Smoke runs in DRY-RUN first (step plan printed), then in actual mode but with --only=cover-letter,
    disclosure to keep the smoke deterministic (no LLM calls; uses the deterministic disclosure_writer +
    a captured-fixture cover-letter response).
    Rationale: matches the smoke discipline of cycles #6-#11 (the smoke catches integration breaks without
    blowing tokens on full agent calls).

risks_and_mitigations:
  R1: |
    Risk: response-to-reviewers (Opus 4.7 xhigh) is expensive. A user running it speculatively on every
    edit would burn budget.
    Mitigation: the skill prompt explicitly says "Run only after a finalized revision and after receiving
    actual reviewer comments." /sws:run-cycle only triggers it if _review/round-<N>/reviewer-comments.md
    exists. README + SKILL.md call out the cost explicitly.

  R2: |
    Risk: cover-letter-writer fabricates a positive editorial decision history ("In our recent JACS paper...").
    Mitigation: agent prompt forbids referencing the user's prior work unless given explicit input. Cover
    letter scope: this manuscript's significance + fit to scope + suggested handling editors (if specified
    in journal overlay).

  R3: |
    Risk: response-matrix.json schema drift if user edits reviewer-comments.md and reruns the parser.
    Mitigation: sws_response_matrix.py is idempotent on re-parse and preserves existing
    {status, response_text, edits_made, line_refs} fields when a comment's id is unchanged. New comments
    appended; deleted comments removed. Field-preservation is unit-tested.

  R4: |
    Risk: /sws:run-cycle's stale-detection heuristics (mtime comparison) produces false positives on
    file systems with imprecise mtime (HFS+, network mounts).
    Mitigation: stale-detection has a 5-second tolerance window. False positives produce a notice, not an
    auto-action (D10), so the cost is only a user noticing a spurious warning.

  R5: |
    Risk: profile activation matrix gets out of sync between profile files and the activation test.
    Mitigation: test_profile_activation_submission.py reads all 9 profile YAML frontmatters directly and
    asserts the matrix; profile-file edits that drift will break the test. Same pattern as cycles #9/#11.

  R6: |
    Risk: disclosure templates contain venue-specific URLs or policy clauses that become stale (e.g.,
    Wiley updates its AI policy).
    Mitigation: each disclosure_template carries a `policy_url` field and a `last_verified` date in
    references/submission-artifacts.md. /sws:disclose-ai-usage prints the template's last_verified date
    so the user knows when to re-check. v0.2 may add a freshness-check WebFetch.

smoke:
  script: tests/smoke_cycle_12.sh
  step_count: 12
  fixtures: tests/fixtures/sample-cycle-12/
  dependencies: cycle-11 smoke + cycle-09 review fixtures already in tests/fixtures/

unit_test_count_target: ~60-70 new tests (parser + matrix preservation + 9-profile activation + router axis + passport extension + disclosure render + run-cycle planner). Total post-cycle target: ~750.

handoff_to_planner: |
  Hand off to superpowers:writing-plans for cycle-12. Plan should structure as:
    Phase 1 — Foundations (3 scripts: response_matrix, disclosure_writer, review_round). Stdlib-only.
    Phase 2 — Submission references doc + run_cycle planner + section-router axis + passport extension.
    Phase 3 — Two agents (cover-letter-writer, response-to-reviewers).
    Phase 4 — Four skills (write-cover-letter, respond-to-reviewers, disclose-ai-usage, run-cycle).
    Phase 5 — Profile activation matrix updates (all 9 profiles).
    Phase 6 — Memory/status updates + tests + smoke.
  Within-phase parallelism is fine (multiple subagents); between-phase is sequential (later phases consume
  earlier deliverables). Plan should be subagent-driven per cycle-09/11/feedback_subagent_dispatch.md.
---

# Cycle #12 — Submission Orchestration

This body is orientation only; **all decisions, scope, deliverables, risks, and the smoke plan live in the frontmatter dictionary above** and are the source of truth.

## What this cycle is

The first end-to-end submission workflow. Until cycle #12, an SWS-managed paper went outline → draft → revise → review and then the user had to assemble the cover letter, AI disclosure, and response-to-reviewers by hand. Cycle #12 adds those three artifacts as first-class SWS outputs, plus a master orchestrator (`/sws:run-cycle`) that drives the entire pipeline idempotently from a single command.

## Why these two agents

`cover-letter-writer` (roster #20, Sonnet 4.6 high) and `response-to-reviewers` (roster #21, Opus 4.7 xhigh) are the two locked submission-phase agents. The architecture sketch §7 named them as the cycle's deliverable along with `/sws:run-cycle` and the disclosure-mode slash command. Their model assignments come from the v0.1 roster (locked) — Opus for R&R because the reasoning load is highest there (rebuttal arguments, evidence cross-references, concession scoring).

## Why `_review/round-<N>/` and not `.review/`

The architecture sketch wrote `.review/` but every other SWS-managed folder uses the underscore-prefix convention (`_drafts/`, `_voice/`, `_lit-search/`, `_review/` from cycle-08 D9). Dot-prefixed folders are reserved for the marker file and the per-paper venv. `_review/round-<N>/` slots cleanly alongside the existing `_review/<agent>/` outputs from cycle-09; the two never collide because `<agent>` names are known (peer-reviewer, claim-verifier, bibliography-fidelity-checker) and don't start with "round-".

## Why a deterministic response-matrix parser

The reviewer-comments → response-matrix JSON conversion is structural markdown parsing — no judgement required. Keeping it deterministic means the user can rerun it cheaply after editing the comments file, and the expensive Opus call is reserved for the prose-generation step where reasoning actually matters (D5).

## How `/sws:run-cycle` interacts with what already shipped

`/sws:run-cycle` is a thin orchestrator that dispatches existing skills in phase order:
`/sws:outline-paper` → `/sws:draft-paper` → `/sws:revise-paper` → `/sws:review-paper` → `/sws:write-cover-letter` → `/sws:disclose-ai-usage` → `/sws:respond-to-reviewers` (only if a `_review/round-<N>/reviewer-comments.md` exists).

Each step is skipped when its artifacts already exist (D9). The orchestrator writes a single passport entry summarising what it did, tagged `phase: submit`. Re-running on a fresh checkout produces the same final state.

## Banner stays at `🧪 v0.1 alpha`

Cycle #12 does NOT flip the banner. Cycle #13 (NLM integration) is the last cycle of v0.1 and owns the banner flip per architecture sketch §7 line 492.

## Cross-cutting constraints honored

- All cycle-12 agents source `scripts/agent_prelude.sh` and call `scripts/agent_should_run.sh <id>` before doing work (agent-contract R1).
- All prose outputs grep-pass `sws_lint_ai_tells.py` before write (D16).
- No new external API dependencies (D13).
- Passport schema extension is additive-only (D4).
- Profile activation matrix updated for all 9 profiles (D8) and tested (R5).
- `R5 — no gender-default in user address` baked into both agent prompts.
- Cover-letter editor name never fabricated (D11); placeholder + TODO instead.
