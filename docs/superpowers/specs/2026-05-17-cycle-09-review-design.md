---
sws_artifact: cycle-09-spec
artifact_version: 0.1
locked: 2026-05-17
title: "Cycle #9 — Review (3 agents, 4 skills, 2 scripts, 1 reference doc, banner flip to 🧪 v0.1 alpha)"

cycle_index: 9
original_roadmap_index: 7
predecessor: cycle-08-revising
banner_after_completion: "🧪 v0.1 alpha"
version_after_completion: "0.1.0-alpha"

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §7 cycle table line 488 (Review phase = 3 new agents + banner flip)"
  prior_cycle_anchors:
    - "cycle-07 D17: citation-key plain-bracket format — claim-verifier reads the same keys"
    - "cycle-08 D9: _review/ established as the SWS-managed review directory; consistency-checker writes there"
    - "cycle-08 D12: section-router action axis (5 actions: draft|revise|consistency|style|lint) — cycle #9 adds a 6th (review)"
  related_memory:
    - "claude_memory/project_roster_v0.1.md (peer-reviewer Opus 4.7 max; claim-verifier + plagiarism-screener Sonnet 4.6 high)"
    - "claude_memory/reference_external_tools.md (Semantic Scholar = primary citation graph; PubMed via MCP; user's peer-review skill wrapped end-to-end)"
    - "claude_memory/feedback_subagent_dispatch.md (sequential dispatch with explicit arg-passing this cycle, not fan-out)"
    - "claude_memory/feedback_integration_smoke.md (smoke_cycle_09.sh = the canonical task-13 verification)"

scope:
  deliverable: "First usable review pipeline. End of cycle: a user who has revised a paper via /sws:revise-paper (cycle #8) can run /sws:review-paper to take the final .docx through claim-verifier → plagiarism-screener → peer-reviewer in sequence, producing one report per agent in _review/<agent>/, with the peer-reviewer explicitly receiving the prior two reports as input. Banner and plugin version bump to alpha. Full writing+review track is usable end-to-end."
  not_in_scope:
    - "Sprint-contracts paper-blind phase for peer-reviewer (deferred to cycle #9.1 follow-up per user instruction 2026-05-17)"
    - "Concession-threshold scoring (dormant until response-to-reviewers ships in cycle #10)"
    - "Text-similarity plagiarism detection (n-gram fuzzy match, embedding similarity) — v0.2 backlog; v0.1 plagiarism-screener is stub-only"
    - "Self-plagiarism check against user's prior Zotero items — v0.2 backlog"
    - "NLM-grounded claim verification — claim-verifier uses Semantic Scholar + PubMed + Zotero only in v0.1; NLM consumer wiring deferred to cycle #11"
    - "Inline docx-comment annotations from any of the 3 reviewers (report files only; mirrors cycle-08 D15)"
    - "EIC + 3 reviewers + DA multi-persona Imbad0202 pattern as separate agents — peer-reviewer encodes all four personas in a single agent prompt for v0.1"
    - "VLM figure verification (cycle #11 / plot-maker territory)"
    - "Funding-proposal review (claim-verifier + plagiarism-screener inactive in funding-proposal; peer-reviewer active everywhere — proposal review handled via /sws:peer-review on the proposal narrative)"

deliverables:
  reference_docs:
    - references/peer-review-rubric.md          # EIC + 3 reviewers + DA template, MIT-attributed to Imbad0202; profile-aware section weights
  scripts:
    - scripts/sws_claim_extract.py              # text-internal claim extraction from _drafts/*.md → claims.json (assertion + citation_keys[] + section)
    - scripts/sws_plagiarism_overlap.py         # stub plagiarism check: paragraph-level verbatim search against Semantic Scholar abstracts of cited papers via DOI
  agents:
    - agents/peer-reviewer.md                   # Opus 4.7 max — wraps user's peer-review skill end-to-end; encodes EIC/3-reviewer/DA in one prompt
    - agents/claim-verifier.md                  # Sonnet 4.6 high — runs sws_claim_extract.py, then verifies each claim against Semantic Scholar / PubMed / Zotero
    - agents/plagiarism-screener.md             # Sonnet 4.6 high — runs sws_plagiarism_overlap.py, interprets findings, writes report
  skills:
    - skills/peer-review/SKILL.md               # /sws:peer-review (standalone or single-section via --section arg)
    - skills/verify-claims/SKILL.md             # /sws:verify-claims (standalone; runs claim-verifier on _drafts/*.md or a final .docx)
    - skills/check-plagiarism/SKILL.md          # /sws:check-plagiarism (standalone; runs plagiarism-screener on a final .docx)
    - skills/review-paper/SKILL.md              # /sws:review-paper (sequential orchestrator: claim → plagiarism → peer; passes prior report paths into peer-reviewer)
  profile_updates:
    - profiles/full-article.md                  # agents_active picks up [peer-reviewer, claim-verifier, plagiarism-screener]
    - profiles/communication.md
    - profiles/perspective.md
    - profiles/review-paper.md
    - profiles/mini-review.md
    - profiles/editorial.md
    - profiles/methodological-paper.md
    - profiles/commentary-reply.md
    - profiles/funding-proposal.md              # peer-reviewer active; claim-verifier + plagiarism-screener INACTIVE (D10)
  reference_updates:
    - references/agent-contract.md              # R3 I/O inventory extended with _review/peer-reviewer/, _review/claim-verifier/, _review/plagiarism-screener/ shapes
  router_updates:
    - scripts/sws_section_router.py             # 6th action axis: review
  memory_updates:
    - claude_memory/project_v02_backlog.md      # 5 new entries per D13
    - claude_memory/project_cycle_execution_status.md  # cycle #9 → merged at end of PR
  banner_updates:
    - README.md                                 # 🚧 v0.1 in design → 🧪 v0.1 alpha
    - .claude-plugin/plugin.json                # version 0.0.1 → 0.1.0-alpha
  tests:
    - tests/test_claim_extract.py
    - tests/test_plagiarism_overlap.py
    - tests/test_section_router_review_action.py
    - tests/test_profile_activation_review_agents.py
    - tests/smoke_cycle_09.sh                   # 16-step e2e against the cycle-08 fixture, extended

locked_decisions:
  D1: |
    3 new agents: peer-reviewer (Opus 4.7 max), claim-verifier (Sonnet 4.6 high), plagiarism-screener (Sonnet 4.6 high).
    All three diagnose-only per Review-Then-Act. No writes to manuscript .docx.
    Rationale: locked by roster v0.1 + arch sketch §7.

  D2: |
    4 skills: /sws:peer-review, /sws:verify-claims, /sws:check-plagiarism, /sws:review-paper (sequential orchestrator).
    Mirrors cycle-#8 pattern (3 atomic + 1 orchestrator).
    Rationale: orchestrator gives ergonomic single-command review; atomics give flexibility for paragraph-level concerns.

  D3: |
    Orchestrator order in /sws:review-paper: claim-verifier → plagiarism-screener → peer-reviewer, fully sequential.
    Orchestrator MUST pass prior report paths to peer-reviewer via explicit CLI args
    (--claim-report _review/claim-verifier/report.md --plagiarism-report _review/plagiarism-screener/report.md).
    peer-reviewer does NOT autoscan _review/.
    Rationale: user instruction 2026-05-17 — autoscan is unreliable; explicit arg-passing matches subagent-dispatch principle of "light context, explicit input".

  D4: |
    _review/ directory layout (extends cycle-08 _review/consistency-report.md):
      _review/peer-reviewer/report.md
      _review/peer-reviewer/rubric.md            # populated when sprint-contracts ship in cycle-#9.1; placeholder absent in v0.1
      _review/claim-verifier/report.md
      _review/claim-verifier/claims.json         # machine-readable: [{section, claim, citation_keys[], verification_status, source_match[]}]
      _review/plagiarism-screener/report.md
      _review/plagiarism-screener/flags.json     # machine-readable: [{paragraph_id, section, overlap_text, source_doi, similarity_method}]
    Gitignored in user paper-project templates (already present in templates/ since cycle #8).
    Rationale: matches existing convention; per-agent subdir prevents collision; JSON sidecars enable downstream R&R Traceability Matrix in cycle #10.

  D5: |
    peer-reviewer wraps user's peer-review skill end-to-end. Single agent encodes all four Imbad0202 personas
    (EIC, Reviewer 1, Reviewer 2, Reviewer 3, Decision Authority) in one prompt — NOT split into 5 separate agents.
    Rationale: avoids 5x token overhead; user's peer-review skill already structures the review; multi-agent split is v0.2+ territory once we have feedback on the single-prompt approach.

  D6: |
    No sprint-contracts paper-blind Phase 1 in v0.1. peer-reviewer reads the paper directly and produces report.
    Sprint-contracts (paper-blind rubric.md commit BEFORE reading paper, with timestamp gate) deferred to cycle-#9.1 follow-up.
    Rationale: user instruction 2026-05-17 — ship the basic pipeline first; add discipline layer once we have feedback on real reviews.

  D7: |
    No concession-threshold scoring in v0.1. The 1–5 rebuttal scoring loop is meaningful only when response-to-reviewers
    (cycle #10) replies to peer-reviewer findings. Until then it's machinery without a counterparty.
    Rationale: arch sketch §1 explicitly bundles concession-threshold with response-to-reviewers; cycle #10 will wire both.

  D8: |
    claim-verifier text-internal claim extraction. sws_claim_extract.py parses _drafts/*.md (citation-key format per cycle-07 D17),
    extracts assertion sentences with attached citation keys, emits claims.json. Agent then verifies each via:
      1. Zotero first (user's curated corpus, highest quality)
      2. Semantic Scholar / PubMed (fill gaps)
      3. nlm-librarian — DEFERRED to cycle #11 (degrades gracefully when absent in v0.1)
    Rationale: arch sketch §5 consumption order; NLM consumer wiring isolated to cycle #11.

  D9: |
    plagiarism-screener is STUB-ONLY in v0.1. sws_plagiarism_overlap.py extracts paragraphs from the final .docx
    (via sws_read_docx.py) and does exact-string search against Semantic Scholar abstracts of papers cited in the
    bibliography (resolved via DOI). Flags any paragraph with verbatim overlap ≥ 25 contiguous words.
    Text-similarity (fuzzy n-gram, embeddings), self-plagiarism (Zotero own-corpus check) → v0.2 backlog.
    Rationale: user instruction 2026-05-17 — honest about what we can ship without paid API; v0.2 entry tracks the upgrade.

  D10: |
    Per-profile agent activation matrix (extends cycle-#8 matrix):
      - peer-reviewer:        ACTIVE in all 9 profiles (already locked by cycle-#7 test).
      - claim-verifier:       ACTIVE in [full-article, communication, perspective, review-paper, mini-review,
                                          editorial, methodological-paper, commentary-reply].
                              INACTIVE in [funding-proposal] — proposals have unverified-by-design forward-looking claims.
      - plagiarism-screener:  same as claim-verifier (active 8 / inactive funding-proposal).
    Rationale: funding proposals describe planned work; "verifying" forward-looking claims is category-mismatched.
    Proposal review goes through /sws:peer-review on the narrative.

  D11: |
    Banner flip ships in the same PR as the review work.
      README.md:        🚧 v0.1 in design — code starts <date>  →  🧪 v0.1 alpha — usable end-to-end writing+review track
      plugin.json:      "version": "0.0.1"  →  "version": "0.1.0-alpha"
    No tagged release created in this cycle — user does git tag + GitHub release as a separate action post-merge.
    Rationale: arch sketch §7 line 488 names end-of-#9 as the banner-flip milestone.

  D12: |
    I/O wrappers: all 3 review agents are prose-only diagnostic agents. They use existing sws_read_docx.py to read
    the manuscript .docx. They DO NOT write to the manuscript. They write only to _review/<agent>/ (plain markdown + JSON).
    No new wrapper scripts needed beyond the two domain scripts (sws_claim_extract.py, sws_plagiarism_overlap.py).
    Rationale: minimizes ad-hoc python deps; honors agent-contract R3 from cycle #7.

  D13: |
    v0.2 backlog additions (5 entries):
      1. Text-similarity plagiarism (n-gram fuzzy match + embedding similarity against Semantic Scholar full corpus)
      2. Self-plagiarism detection against user's own Zotero items
      3. Sprint-contracts paper-blind enforcement for peer-reviewer (Phase 1 rubric commit before Phase 2 paper read)
      4. Concession-threshold scoring for response-to-reviewers (1–5 scoring; concessions ≥4; no consecutive concessions)
      5. NLM consumer wiring for claim-verifier (delegate grounded RAG to nlm-librarian when notebooklm.enabled=true)
    Rationale: explicit deferrals captured for future-self; prevents scope creep within cycle #9.

  D14: |
    section-router 6th action axis: review. Maps {section, action=review} → {agent: peer-reviewer (single-section mode)}.
    Single-section review only routes to peer-reviewer (not claim-verifier / plagiarism-screener) because claim and
    plagiarism checks are paper-wide by nature; per-section limits would give false confidence.
    Rationale: matches /sws:review-paper full-paper orchestration; single-section is a peer-reviewer-only concern.

  D15: |
    Smoke test smoke_cycle_09.sh extends the cycle-08 fixture. 16 steps:
      1–8: cycle-08 baseline reproducible (drafts → consistency → revise → style → final .docx)
      9:   /sws:verify-claims → _review/claim-verifier/{report.md, claims.json}
      10:  /sws:check-plagiarism → _review/plagiarism-screener/{report.md, flags.json}
      11:  /sws:peer-review → _review/peer-reviewer/report.md (no rubric.md in v0.1)
      12:  /sws:review-paper (orchestrator) → all three reports populated in one run
      13:  assert peer-reviewer received --claim-report and --plagiarism-report args (via mock-args trace)
      14:  assert claim-verifier degrades gracefully when notebooklm.enabled=false (no errors, no NLM calls)
      15:  assert profile activation: claim-verifier exits 0 with v0.1-unsupported message in funding-proposal
      16:  assert README banner string matches 🧪 v0.1 alpha + plugin.json version 0.1.0-alpha
    Rationale: feedback_integration_smoke.md — every multi-step plan's final task = real e2e smoke.

  D16: |
    Profile-aware peer-review rubric. references/peer-review-rubric.md ships per-profile section weights:
      - full-article:        introduction 15%, methods 25%, results 30%, discussion 20%, references 10%
      - communication:       intro 30%, methods 20%, results 40%, references 10%  (no separate discussion)
      - review-paper:        coverage 35%, synthesis 30%, critical evaluation 25%, references 10%
      - mini-review:         same shape as review-paper, halved word budgets
      - perspective:         framing 30%, argumentation 40%, novelty 20%, references 10%
      - editorial:           argument 50%, voice 30%, brevity 20%
      - methodological-paper: novelty 20%, methods 40%, validation 30%, references 10%
      - commentary-reply:    fidelity-to-original 30%, argument 40%, civility 20%, references 10%
      - funding-proposal:    feasibility 25%, novelty 25%, impact 25%, team 15%, budget 10%
    Rationale: one rubric file, profile-keyed sections; peer-reviewer reads the section matching the resolved profile.
    Imbad0202 EIC structure preserved as the outer narrative shape; section weights are SWS-specific.

  D17: |
    Subagent dispatch policy for /sws:review-paper orchestrator. Each of the 3 review agents runs as a separate
    subagent dispatch (not parallel — sequential per D3). peer-reviewer dispatch passes:
      --claim-report ${PAPER_ROOT}/_review/claim-verifier/report.md
      --plagiarism-report ${PAPER_ROOT}/_review/plagiarism-screener/report.md
      --manuscript ${PAPER_ROOT}/Manuscript/<active-docx>
    peer-reviewer reads all three explicitly. Orchestrator does NOT read agent outputs and pass them inline — peer-reviewer
    reads from the filesystem given the paths. This matches cycle-#8 /sws:revise-paper pattern.
    Rationale: keeps orchestrator stateless; agent outputs are durable on filesystem; matches feedback_subagent_dispatch.md.

testing:
  unit_tests:
    - test_claim_extract.py            # parsing _drafts/*.md → claims.json, citation-key resolution, edge cases (no citations, multi-citation, footnotes)
    - test_plagiarism_overlap.py       # paragraph extraction, exact-string match logic, DOI resolution failure handling, empty bibliography
    - test_section_router_review_action.py  # review action routes only to peer-reviewer (not claim/plagiarism for single section)
    - test_profile_activation_review_agents.py  # peer-reviewer active in 9/9, claim+plagiarism inactive in funding-proposal only
  smoke:
    - tests/smoke_cycle_09.sh          # 16 steps per D15
  regression:
    - tests/smoke_cycle_07.sh          # re-baseline if router changes
    - tests/smoke_cycle_08.sh          # re-baseline if router changes; ensure consistency-checker still writes _review/consistency-report.md (paths unchanged)
  total_target: "~40 new unit tests; cycle baseline rises from ~390 to ~430"

risks:
  R1: |
    Semantic Scholar rate limits. claim-verifier and plagiarism-screener both hit S2.
    Mitigation: aggressive caching at sws_claim_extract.py output level + per-DOI memoization across the run; exponential backoff on 429.

  R2: |
    Plagiarism-screener stub may produce false-confidence ("no plagiarism found" when only exact-string overlap was checked).
    Mitigation: report.md MUST include a prominent "v0.1 LIMITATION" header stating only verbatim ≥25-word overlap is detected; text-similarity is v0.2.
    User instruction: be honest about what we can ship.

  R3: |
    peer-reviewer (Opus 4.7 max) is the most expensive agent in the plugin. A single /sws:review-paper run = ~one Opus max invocation.
    Mitigation: doc the cost in skill README; users who only want quick checks can run /sws:verify-claims and /sws:check-plagiarism without peer-reviewer.

  R4: |
    Banner flip in same PR couples two unrelated concerns (review work + version milestone).
    Mitigation: separate commit for the banner change within the PR so it can be reverted independently if needed.

execution:
  approach: "Same dispatch flow as cycles #7 and #8: user approves spec → planner skill writes implementation plan → subagent-driven execution → PR opened, user merges."
  parallelism: "Tasks within phases parallelizable per feedback_subagent_dispatch.md. Phases sequential (refs → scripts → agents → skills → profiles → router → tests → smoke → banner)."
  expected_pr_size: "Larger than cycle #8 (~25–35 commits, ~3000–4500 LoC added). 3 agents + 4 skills + 2 scripts + rubric + 9 profile updates + ~40 tests + smoke + banner."
  beta_test_phase: "Optional phase-2.5 against the Procentese perspective fixture (cycle #7 phase-2 sandbox) — run /sws:review-paper end-to-end on the existing fixture. User-approved before phase-3 implementation completion."
---

# Cycle #9 — Review

End-of-cycle goal: a user who has completed cycle-#8 revising (`/sws:revise-paper` → final `.docx`) can run `/sws:review-paper` to take that `.docx` through three diagnostic reviewers in sequence — `claim-verifier` → `plagiarism-screener` → `peer-reviewer` — with each report persisted under `_review/<agent>/` and the peer-reviewer explicitly receiving the prior two reports' paths as input. End-of-cycle banner flips to `🧪 v0.1 alpha` and `plugin.json` version bumps to `0.1.0-alpha`.

This spec follows the same dispatch flow as cycles #7 and #8. All locked decisions are in the frontmatter `locked_decisions:` block above (D1–D17). The body of this document is orientation only — frontmatter is the project-memory dictionary.

## What ships

Three diagnostic-only agents, four user-facing slash commands, two helper scripts, one rubric reference, and a profile-activation update across all nine profiles. Plus the visible alpha milestone: README banner + version bump.

Per arch-sketch §7, this is the cycle that makes the writing+review track usable end-to-end. After cycle #9 merges, the plugin can take a paper from outline → draft → revise → review without leaving SWS slash commands.

## Why these scope cuts

Three substantial features get explicit deferral, all per user instruction 2026-05-17:

1. **Sprint-contracts paper-blind Phase 1** for peer-reviewer (rubric committed before reading paper, with timestamp gate). Ship the basic pipeline first; add the discipline layer in cycle #9.1 once we have feedback on real reviews.
2. **Text-similarity plagiarism detection** (n-gram fuzzy match, embedding similarity, self-plagiarism). The v0.1 plagiarism-screener is a stub that catches only verbatim ≥25-word overlap against cited papers' abstracts. The report file states this limitation prominently. Honest about what we can ship without a paid API.
3. **NLM consumer wiring** for claim-verifier. The agent uses Zotero + Semantic Scholar + PubMed in v0.1 and degrades gracefully without NLM. NLM wiring happens in cycle #11 where `nlm-librarian` ships.

These deferrals are tracked as explicit entries in `claude_memory/project_v02_backlog.md` per D13.

## Cross-cutting compliance

- **Review-Then-Act:** all 3 agents diagnose only; no writes to manuscript `.docx`.
- **Agent-contract R1:** each agent sources `scripts/agent_prelude.sh` and calls `agent_should_run.sh <id>` before doing work.
- **Agent-contract R3:** I/O wrappers — agents call `sws_read_docx.py` via `sws_python.sh` to read manuscript; agents write plain markdown + JSON to `_review/<agent>/`.
- **Agent-contract R5:** no gender-default in user address, baked into all 3 agent prompts.
- **MCP-aversion principle:** Semantic Scholar via WebFetch + small utility scripts; PubMed via the existing `claude_ai_PubMed` MCP (the documented v0.1 exception); no new MCP servers.
- **Profile-aware activation:** peer-reviewer everywhere; claim-verifier + plagiarism-screener inactive in funding-proposal (D10).

## Banner change exact strings

- `README.md` banner line:
  - Before: `🚧 v0.1 in design — code starts 2026-05-08`
  - After: `🧪 v0.1 alpha — usable end-to-end writing+review track (drafting, revising, review)`
- `.claude-plugin/plugin.json`:
  - Before: `"version": "0.0.1"`
  - After: `"version": "0.1.0-alpha"`

Banner change is its own commit within the PR for revertability (R4).
