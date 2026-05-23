---
sws_artifact: cycle-09-spec
artifact_version: 0.1
locked: 2026-05-17
title: "Cycle #9 — Review (3 agents, 4 skills, 2 scripts, 1 reference doc, banner flip to 🧪 v0.1 alpha). Plagiarism-screener refocused to bibliography-fidelity-checker per user instruction 2026-05-17."

cycle_index: 9
original_roadmap_index: 7
predecessor: cycle-08-revising
banner_after_completion: "🧪 v0.1 alpha"
version_after_completion: "0.1.0-alpha"

autonomous_run_caveat: |
  Cycle #9 implementation was executed autonomously overnight on 2026-05-17 with the user's explicit
  grant of authority ("move on and run as many agents in parallel to finish cycle 9 overnight unattended").
  Every locked decision (D1–D17, D9a–D9c) carries a rationale so the user can re-decide any of them in the
  morning before the PR merges. The PR is opened in DRAFT state to make tomorrow's revision low-friction.
  Mirrors the cycle-08 autonomous-execution pattern.

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §7 cycle table line 488 (Review phase = 3 new agents + banner flip)"
  prior_cycle_anchors:
    - "cycle-07 D17: citation-key plain-bracket format — claim-verifier reads the same keys"
    - "cycle-08 D9: _review/ established as the SWS-managed review directory; consistency-checker writes there"
    - "cycle-08 D12: section-router action axis (5 actions: draft|revise|consistency|style|lint) — cycle #9 adds a 6th (review)"
  related_memory:
    - "claude_memory/project_roster_v0.1.md (peer-reviewer Opus 4.7 max; claim-verifier + bibliography-fidelity-checker Sonnet 4.6 high; roster #16 renamed 2026-05-17)"
    - "claude_memory/reference_external_tools.md (Semantic Scholar = primary citation graph; PubMed via MCP; user's peer-review skill wrapped end-to-end)"
    - "claude_memory/feedback_subagent_dispatch.md (sequential dispatch with explicit arg-passing this cycle, not fan-out)"
    - "claude_memory/feedback_integration_smoke.md (smoke_cycle_09.sh = the canonical task-13 verification)"

scope:
  deliverable: "First usable review pipeline. End of cycle: a user who has revised a paper via /sws:revise-paper (cycle #8) can run /sws:review-paper to take the final .docx through claim-verifier → bibliography-fidelity-checker → peer-reviewer in sequence, producing one report per agent in _review/<agent>/, with the peer-reviewer explicitly receiving the prior two reports as input (and a skip-state env var when fidelity is inert because the user has no zotero skill or empty Zotero library). Banner and plugin version bump to alpha. Full writing+review track is usable end-to-end."
  not_in_scope:
    - "Sprint-contracts paper-blind phase for peer-reviewer (deferred to cycle #9.1 follow-up per user instruction 2026-05-17)"
    - "Concession-threshold scoring (dormant until response-to-reviewers ships in cycle #10)"
    - "Unbounded-corpus plagiarism detection (Crossref Similarity Check / iThenticate paid API, Google Programmable Search opt-in) — v0.2 backlog. v0.1 bibliography-fidelity-checker only searches the user's Zotero full-text index, not the open web."
    - "Embedding-similarity / SPECTER2 paraphrase detection — v0.2 backlog. v0.1 fidelity-check is exact-string overlap only (≥15 contiguous words)."
    - "NLM-grounded claim verification — claim-verifier uses Semantic Scholar + PubMed + Zotero only in v0.1; NLM consumer wiring deferred to cycle #11"
    - "Inline docx-comment annotations from any of the 3 reviewers (report files only; mirrors cycle-08 D15)"
    - "EIC + 3 reviewers + DA multi-persona Imbad0202 pattern as separate agents — peer-reviewer encodes all four personas in a single agent prompt for v0.1"
    - "VLM figure verification (cycle #11 / plot-maker territory)"
    - "Funding-proposal review (claim-verifier + bibliography-fidelity-checker inactive in funding-proposal; peer-reviewer active everywhere — proposal review handled via /sws:peer-review on the proposal narrative)"

deliverables:
  reference_docs:
    - references/peer-review-rubric.md          # EIC + 3 reviewers + DA template, MIT-attributed to Imbad0202; profile-aware section weights
  scripts:
    - scripts/sws_claim_extract.py              # text-internal claim extraction from _drafts/*.md → claims.json (assertion + citation_keys[] + section)
    - scripts/sws_bibliography_fidelity.py      # verbatim-overlap check: paragraphs vs Zotero full-text index. Wraps the zotero skill's full-text search API. Has --probe mode to detect whether zotero skill + non-empty library are available.
  agents:
    - agents/peer-reviewer.md                   # Opus 4.7 max — wraps user's peer-review skill end-to-end; encodes EIC/3-reviewer/DA in one prompt
    - agents/claim-verifier.md                  # Sonnet 4.6 high — runs sws_claim_extract.py, then verifies each claim against Semantic Scholar / PubMed / Zotero
    - agents/bibliography-fidelity-checker.md   # Sonnet 4.6 high — RENAMED from plagiarism-screener (roster v0.1 #16). Runs sws_bibliography_fidelity.py, interprets hits, writes report. Degrades gracefully when zotero skill absent or library empty.
  skills:
    - skills/peer-review/SKILL.md               # /sws:peer-review (standalone or single-section via --section arg)
    - skills/verify-claims/SKILL.md             # /sws:verify-claims (standalone; runs claim-verifier on _drafts/*.md or a final .docx)
    - skills/check-fidelity/SKILL.md            # /sws:check-fidelity (standalone; runs bibliography-fidelity-checker on a final .docx). RENAMED from /sws:check-plagiarism.
    - skills/review-paper/SKILL.md              # /sws:review-paper (sequential orchestrator: claim → fidelity → peer; passes prior report paths into peer-reviewer)
  profile_updates:
    - profiles/full-article.md                  # agents_active picks up [peer-reviewer, claim-verifier, bibliography-fidelity-checker]
    - profiles/communication.md
    - profiles/perspective.md
    - profiles/review-paper.md
    - profiles/mini-review.md
    - profiles/editorial.md
    - profiles/methodological-paper.md
    - profiles/commentary-reply.md
    - profiles/funding-proposal.md              # peer-reviewer active; claim-verifier + bibliography-fidelity-checker INACTIVE (D10)
  reference_updates:
    - references/agent-contract.md              # R3 I/O inventory extended with _review/peer-reviewer/, _review/claim-verifier/, _review/bibliography-fidelity-checker/ shapes
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
    - tests/test_bibliography_fidelity.py       # RENAMED from test_plagiarism_overlap.py. Covers zotero-available path, zotero-skill-absent path, zotero-installed-but-empty-library path.
    - tests/test_section_router_review_action.py
    - tests/test_profile_activation_review_agents.py
    - tests/smoke_cycle_09.sh                   # 17-step e2e against the cycle-08 fixture, extended (17 steps after adding the zotero-absent fallback assertion)

locked_decisions:
  D1: |
    3 new agents: peer-reviewer (Opus 4.7 max), claim-verifier (Sonnet 4.6 high), bibliography-fidelity-checker (Sonnet 4.6 high).
    All three diagnose-only per Review-Then-Act. No writes to manuscript .docx.
    bibliography-fidelity-checker is the renamed roster v0.1 agent #16 (was "plagiarism-screener"). Renamed per user instruction 2026-05-17
    after the abstract-only stub was judged not useful enough to ship under the plagiarism name. The agent's actual job is checking
    for verbatim overlap with papers in the user's Zotero corpus, not unbounded-corpus plagiarism detection.
    Roster file (claude_memory/project_roster_v0.1.md, gitignored) MUST be updated as a side-effect of this cycle.
    Rationale: locked by roster v0.1 (#13/#15/#16) + arch sketch §7 with the #16 rename approved 2026-05-17.

  D2: |
    4 skills: /sws:peer-review, /sws:verify-claims, /sws:check-fidelity, /sws:review-paper (sequential orchestrator).
    /sws:check-fidelity is renamed from the originally-planned /sws:check-plagiarism, matching the D1 agent rename.
    Mirrors cycle-#8 pattern (3 atomic + 1 orchestrator).
    Rationale: orchestrator gives ergonomic single-command review; atomics give flexibility for paragraph-level concerns.

  D3: |
    Orchestrator order in /sws:review-paper: claim-verifier → bibliography-fidelity-checker → peer-reviewer, fully sequential.
    Orchestrator MUST pass prior report paths to peer-reviewer via explicit CLI args
    (--claim-report _review/claim-verifier/report.md --fidelity-report _review/bibliography-fidelity-checker/report.md).
    peer-reviewer does NOT autoscan _review/. If bibliography-fidelity-checker skipped (no Zotero), --fidelity-report is omitted and
    peer-reviewer is told via env-var SWS_FIDELITY_STATUS=skipped:<reason> so its report can note the missing input.
    Rationale: user instruction 2026-05-17 — autoscan is unreliable; explicit arg-passing matches subagent-dispatch principle of
    "light context, explicit input". Skip-state propagation prevents peer-reviewer from waiting on a file that will never exist.

  D4: |
    _review/ directory layout (extends cycle-08 _review/consistency-report.md):
      _review/peer-reviewer/report.md
      _review/peer-reviewer/rubric.md                       # populated when sprint-contracts ship in cycle-#9.1; absent in v0.1
      _review/claim-verifier/report.md
      _review/claim-verifier/claims.json                    # machine-readable: [{section, claim, citation_keys[], verification_status, source_match[]}]
      _review/bibliography-fidelity-checker/report.md
      _review/bibliography-fidelity-checker/flags.json      # machine-readable: [{paragraph_id, section, overlap_text, zotero_item_id, zotero_collection, page_hint}]
      _review/bibliography-fidelity-checker/status.json     # zotero detection state: {zotero_skill_available: bool, library_item_count: int, ran: bool, skip_reason: "..."}
    Gitignored in user paper-project templates (already present in templates/ since cycle #8).
    Rationale: matches existing convention; per-agent subdir prevents collision; JSON sidecars enable downstream R&R Traceability Matrix in cycle #10.
    status.json on fidelity-checker side gives a machine-readable skip-state for the orchestrator and for the smoke test.

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
    bibliography-fidelity-checker scope: verbatim-overlap detection against the user's Zotero full-text index.
    sws_bibliography_fidelity.py extracts paragraphs from the final .docx (via sws_read_docx.py) and queries the user's
    Zotero library via the existing zotero skill. For each paragraph, generates candidate ≥15-word substrings and
    submits them as exact-string queries to Zotero's full-text search. Flags any match. Reports hits with:
      - the overlapping passage (≥15 contiguous words),
      - the Zotero item that matched (title, authors, year, item key, collection),
      - a page hint when Zotero's index returns one.
    Corpus priority (mirrors arch sketch §5 "Zotero first"):
      1. Papers cited in the manuscript bibliography (DOI/citation-key match) — the highest-risk set.
      2. All other items in the same Zotero collection as the cited papers — catches "read but didn't cite" reproductions.
      3. (v0.2+) Nearest-neighbor expansion via Semantic Scholar references — out of scope for v0.1.
    Why ≥15 words (not 25): Zotero's index supports phrase search; 15-word phrases are long enough to suppress false positives
    from common scientific phrasing ("we performed differential expression analysis") but short enough to catch the actual
    accidental-paste error class.
    Limitations in v0.1 (must be stated in every report.md): exact-string only — paraphrase / synonym substitution / sentence
    reordering will not be caught. Unbounded corpus (open web, paywalled papers not in user's Zotero) not searched.
    Rationale: user instruction 2026-05-17 — the original abstract-only stub against Semantic Scholar was theater; full-text
    against the user's actual reading corpus (where the accidental copy-paste actually happens) is the honest useful check.

  D9a: |
    Fallback path A: zotero skill NOT installed in Claude Code, BUT Zotero desktop IS installed on the user's system.
    Detection logic (sws_bibliography_fidelity.py --probe-zotero):
      Step 1 — probe Claude Code zotero skill: check .claude/plugins/cache for the zotero plugin AND query
               `claude --list-skills 2>/dev/null` if available AND check whether the user's CLAUDE.md / global config
               references the zotero skill.
      Step 2 — probe Zotero desktop: check for the canonical Zotero SQLite at the common paths
               (~/Zotero/zotero.sqlite on macOS/Linux; %USERPROFILE%/Zotero/zotero.sqlite on Windows;
               also ~/.zotero/zotero/*/zotero.sqlite for older Zotero versions on Linux). Path found = Zotero desktop installed.
    Behavior when zotero_skill_available=false AND zotero_desktop_detected=true (Fallback A):
      - Agent exits 0 (skip is not an error).
      - Writes _review/bibliography-fidelity-checker/status.json with:
        {zotero_skill_available: false, zotero_desktop_detected: true, zotero_sqlite_path: "<detected path>",
         ran: false, skip_reason: "zotero-desktop-detected-but-claude-skill-missing"}.
      - Writes report.md leading with an ACTIONABLE RECOMMENDATION (verbatim wording, per user instruction 2026-05-17):
        "We detected a Zotero installation at <path>. If you use Zotero to manage references for this manuscript,
         we recommend installing the zotero plugin in Claude Code to enable the bibliography-fidelity check.
         Install with: /plugin install zotero (or your equivalent). After installation, re-run /sws:check-fidelity
         to verify your manuscript against your Zotero corpus."
      - Orchestrator propagates SWS_FIDELITY_STATUS=skipped:zotero-desktop-detected-but-claude-skill-missing to peer-reviewer.
    Rationale: detecting Zotero on the host system lets us make the recommendation conditional and useful instead of
    generic. Many users have Zotero installed but haven't realized the Claude Code zotero skill exists; a targeted nudge
    converts that gap into a one-command fix.

  D9c: |
    Fallback path C: NO Zotero installation detected on the user's system at all.
    Detection: Step 1 returned zotero_skill_available=false AND Step 2 (D9a's probe of common SQLite paths) returned
    zotero_desktop_detected=false.
    Behavior:
      - Agent exits 0.
      - Writes status.json with:
        {zotero_skill_available: false, zotero_desktop_detected: false, ran: false,
         skip_reason: "no-zotero-installation-detected"}.
      - Writes report.md with a neutral note (no recommendation to install Zotero — that's a workflow choice):
        "No Zotero installation detected on this system. The bibliography-fidelity check is Zotero-only in v0.1.
         If you use a different reference manager (Mendeley, EndNote, Papers, plain BibTeX), this check is not
         available in v0.1. Manual proofreading remains the recommended workaround. See v0.2 backlog for planned
         unbounded-corpus alternatives (Crossref Similarity Check, Google Programmable Search opt-in)."
      - Orchestrator propagates SWS_FIDELITY_STATUS=skipped:no-zotero-installation-detected to peer-reviewer.
    Rationale: distinguishing "you have Zotero but lack the skill" from "you don't use Zotero" is important UX —
    the first deserves a recommendation, the second deserves respect for the user's actual workflow.
    Splitting D9a into two sub-cases per user instruction 2026-05-17.

  D9b: |
    Fallback path: zotero skill installed but library is empty or unusable.
    Detection: probe call returns zotero_skill_available=true but the user's Zotero library has fewer than 10 items
    OR fails to respond within 30s OR returns a permission error.
    Behavior when unusable:
      - Agent exits 0.
      - Writes status.json with {zotero_skill_available: true, library_item_count: <n>, ran: false, skip_reason: "zotero library too small to be a useful fidelity corpus" | "zotero skill unresponsive" | "zotero permission denied"}.
      - Writes report.md with a note explaining what was skipped and what threshold was applied.
      - Orchestrator propagates SWS_FIDELITY_STATUS=skipped:<reason> to peer-reviewer.
    The 10-item threshold is a sanity floor — fewer than 10 items is essentially "no curated corpus" and any hit would be misleading.
    Rationale: same graceful-degradation principle as D9a. The 10-item floor is conservative and clearly stated so the user
    can override via the v0.2 backlog if they want stricter or laxer thresholds.

  D10: |
    Per-profile agent activation matrix (extends cycle-#8 matrix):
      - peer-reviewer:                    ACTIVE in all 9 profiles (already locked by cycle-#7 test).
      - claim-verifier:                   ACTIVE in [full-article, communication, perspective, review-paper, mini-review,
                                                     editorial, methodological-paper, commentary-reply].
                                          INACTIVE in [funding-proposal] — proposals have unverified-by-design forward-looking claims.
      - bibliography-fidelity-checker:    same as claim-verifier (active 8 / inactive funding-proposal).
                                          The fidelity check is meaningful only when the manuscript has a bibliography; funding
                                          proposals do reference some published work but the corpus risk profile is different
                                          and the v0.1 check would mostly fire on standard methodological boilerplate.
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
    No new wrapper scripts needed beyond the two domain scripts (sws_claim_extract.py, sws_bibliography_fidelity.py).
    Rationale: minimizes ad-hoc python deps; honors agent-contract R3 from cycle #7.

  D13: |
    v0.2 backlog additions (7 entries):
      1. Unbounded-corpus plagiarism detection — proper Crossref Similarity Check / iThenticate API integration (paid; opt-in via marker).
      2. Google Programmable Search Engine opt-in path for users without Zotero (free tier 100/day; user provides API key + cx).
      3. Embedding / SPECTER2 paraphrase detection on top of bibliography-fidelity-checker (catches reworded copy, not just verbatim).
      4. Nearest-neighbor corpus expansion for fidelity-checker (Semantic Scholar references of cited papers — broader corpus when user opts in).
      5. Sprint-contracts paper-blind enforcement for peer-reviewer (Phase 1 rubric commit before Phase 2 paper read).
      6. Concession-threshold scoring for response-to-reviewers (1–5 scoring; concessions ≥4; no consecutive concessions).
      7. NLM consumer wiring for claim-verifier (delegate grounded RAG to nlm-librarian when notebooklm.enabled=true).
    Rationale: explicit deferrals captured for future-self; prevents scope creep within cycle #9.

  D14: |
    section-router 6th action axis: review. Maps {section, action=review} → {agent: peer-reviewer (single-section mode)}.
    Single-section review only routes to peer-reviewer (not claim-verifier / bibliography-fidelity-checker) because claim and
    fidelity checks are paper-wide by nature; per-section limits would give false confidence.
    Rationale: matches /sws:review-paper full-paper orchestration; single-section is a peer-reviewer-only concern.

  D15: |
    Smoke test smoke_cycle_09.sh extends the cycle-08 fixture. 18 steps across 4 fixture variants:
      1–8: cycle-08 baseline reproducible (drafts → consistency → revise → style → final .docx)
      9:   /sws:verify-claims → _review/claim-verifier/{report.md, claims.json}
      10:  /sws:check-fidelity on Variant 1 (NO zotero skill, NO Zotero desktop on system):
            asserts D9c — status.json.ran == false, skip_reason == "no-zotero-installation-detected",
            report.md contains the neutral "no Zotero detected" message.
      11:  /sws:check-fidelity on Variant 2 (NO zotero skill, Zotero desktop mocked at fixture ~/Zotero/zotero.sqlite):
            asserts D9a — status.json.zotero_desktop_detected == true, status.json.zotero_sqlite_path is set,
            skip_reason == "zotero-desktop-detected-but-claude-skill-missing", report.md leads with the
            ACTIONABLE RECOMMENDATION (verbatim string match against the D9a-locked wording).
      12:  /sws:check-fidelity on Variant 3 (zotero skill mocked-available + library < 10 items):
            asserts D9b — status.json.ran == false, skip_reason == "zotero-library-too-small",
            status.json.library_item_count is set.
      13:  /sws:check-fidelity on Variant 4 (zotero skill mocked-available + library populated + seeded fidelity-violation):
            asserts D9 happy-path — status.json.ran == true, flags.json contains ≥1 flag for the seeded paragraph,
            report.md has the V0.1 LIMITATION header.
      14:  /sws:peer-review → _review/peer-reviewer/report.md (no rubric.md in v0.1)
      15:  /sws:review-paper (orchestrator) on Variant 1 → all three reports populated;
            assert peer-reviewer received --claim-report and SWS_FIDELITY_STATUS=skipped:no-zotero-installation-detected;
            peer-review report.md contains the one-line note that fidelity was skipped.
      16:  assert claim-verifier degrades gracefully when notebooklm.enabled=false (no errors, no NLM calls).
      17:  assert profile activation: claim-verifier + fidelity-checker exit 0 with v0.1-unsupported message in funding-proposal.
      18:  assert README banner string matches 🧪 v0.1 alpha + plugin.json version 0.1.0-alpha.
    Rationale: feedback_integration_smoke.md — every multi-step plan's final task = real e2e smoke.
    Four fixture variants (no-zotero-at-all, zotero-desktop-only, skill+empty-library, skill+populated+violation) cover all four
    fidelity-checker code paths end-to-end. Variant 2 specifically asserts the verbatim wording of the D9a recommendation
    so future edits to the message can't silently drift.

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
      --fidelity-report ${PAPER_ROOT}/_review/bibliography-fidelity-checker/report.md   # OMITTED if status.json.ran=false
      --manuscript ${PAPER_ROOT}/Manuscript/<active-docx>
    Plus environment variable SWS_FIDELITY_STATUS, one of:
      - "ran"
      - "skipped:zotero-desktop-detected-but-claude-skill-missing"   (D9a — actionable recommendation in report)
      - "skipped:no-zotero-installation-detected"                    (D9c — neutral note in report)
      - "skipped:zotero-library-too-small"                           (D9b)
      - "skipped:zotero-unresponsive"                                (D9b)
      - "skipped:zotero-permission-denied"                           (D9b)
    peer-reviewer reads the report files from the filesystem given the paths. When SWS_FIDELITY_STATUS != "ran", peer-reviewer's
    report.md includes a one-line note that the fidelity check was skipped and why, so the user knows that branch of the review
    was not exercised. Orchestrator does NOT read agent outputs and pass them inline. Matches cycle-#8 /sws:revise-paper pattern.
    Rationale: keeps orchestrator stateless; agent outputs are durable on filesystem; matches feedback_subagent_dispatch.md.
    Explicit skip-state communication prevents silent "I checked everything" claims when one of the checks was inert.

testing:
  unit_tests:
    - test_claim_extract.py                  # parsing _drafts/*.md → claims.json, citation-key resolution, edge cases (no citations, multi-citation, footnotes)
    - test_bibliography_fidelity.py          # paragraph extraction, ≥15-word substring generation, exact-string match logic. Four primary fixtures + two error fixtures:
                                             #   (a) zotero skill mocked-available + library populated → flags seeded fidelity violation (D9 happy path)
                                             #   (b) zotero skill mocked-available + library has <10 items → exit 0, skip_reason="zotero-library-too-small" (D9b)
                                             #   (c) zotero skill absent + NO Zotero desktop on system → exit 0, skip_reason="no-zotero-installation-detected" (D9c, neutral)
                                             #   (d) zotero skill absent + Zotero desktop SQLite mocked → exit 0, skip_reason="zotero-desktop-detected-but-claude-skill-missing" (D9a, asserts ACTIONABLE RECOMMENDATION verbatim)
                                             #   (e) zotero-unresponsive timeout → exit 0, skip_reason="zotero-unresponsive"
                                             #   (f) zotero permission denied → exit 0, skip_reason="zotero-permission-denied"
    - test_section_router_review_action.py   # review action routes only to peer-reviewer (not claim/fidelity for single section)
    - test_profile_activation_review_agents.py  # peer-reviewer active in 9/9, claim+fidelity inactive in funding-proposal only
  smoke:
    - tests/smoke_cycle_09.sh                # 17 steps per D15 (two fixture variants: no-zotero default + mocked-zotero)
  regression:
    - tests/smoke_cycle_07.sh                # re-baseline if router changes
    - tests/smoke_cycle_08.sh                # re-baseline if router changes; ensure consistency-checker still writes _review/consistency-report.md (paths unchanged)
  total_target: "~50 new unit tests (10 extra for the 4 primary + 2 error fallback fixtures in test_bibliography_fidelity.py, including the verbatim-message assertion for the D9a recommendation); cycle baseline rises from ~390 to ~440"

risks:
  R1: |
    Semantic Scholar rate limits. claim-verifier hits S2 (and PubMed) heavily; bibliography-fidelity-checker does NOT
    use S2 in v0.1 (queries Zotero full-text only) so the risk is now localized to claim-verifier.
    Mitigation: aggressive caching at sws_claim_extract.py output level + per-DOI memoization across the run; exponential backoff on 429.

  R2: |
    Bibliography-fidelity-checker may produce false-confidence ("no overlap found" when only exact-string ≥15-word match
    against Zotero corpus was checked, and only that corpus). Paraphrase / synonym substitution / sentence reordering will
    not be caught. Sources outside the user's Zotero (open web, papers they haven't read) are not checked at all.
    Mitigation: report.md MUST include a prominent "v0.1 LIMITATION" header stating exactly what was checked, what threshold
    was applied, how many Zotero items formed the corpus, and what was NOT checked (paraphrase, open web, paywalled). The
    bibliography-fidelity-checker is a *fidelity* check ("did I accidentally copy from a paper I've read?"), not an
    unbounded-corpus *plagiarism* check ("was this text published anywhere first?"). Tool name and report framing both
    enforce this distinction.

  R5: |
    Detecting "zotero skill installed in Claude Code" AND "Zotero desktop installed on host system" both have edge cases.
    For the skill: different installation paths (user plugin, project plugin, marketplace, manual). For the desktop: custom
    data-directory paths (Zotero users can move their library), Zotero 7 vs older Zotero 5 path conventions, missing-but-
    referenced installations (uninstalled but cache left behind).
    False-negatives in either probe would degrade UX:
      - Missing skill probe = run the check anyway and fail downstream (worse than skipping).
      - Missing desktop probe in D9a = give the neutral D9c message when the actionable D9a recommendation was warranted.
    Mitigation: sws_bibliography_fidelity.py --probe-zotero tries multiple signals for each layer:
      Skill: (1) .claude/plugins/cache presence, (2) `claude --list-skills` if CLI available, (3) user CLAUDE.md reference.
      Desktop: (1) ~/Zotero/zotero.sqlite, (2) %USERPROFILE%/Zotero/zotero.sqlite, (3) ~/.zotero/zotero/*/zotero.sqlite,
               (4) honor $ZOTERO_DATA_DIR env-var override for users with custom paths.
    Status.json records WHICH probe signal succeeded (or all-failed reason for each layer). User can override with
    --force-zotero / --no-zotero / --zotero-sqlite=<path> flags. All probe paths covered in test_bibliography_fidelity.py
    fixtures (a)–(f).

  R3: |
    peer-reviewer (Opus 4.7 max) is the most expensive agent in the plugin. A single /sws:review-paper run = ~one Opus max invocation.
    Mitigation: doc the cost in skill README; users who only want quick checks can run /sws:verify-claims and /sws:check-fidelity without peer-reviewer.

  R4: |
    Banner flip in same PR couples two unrelated concerns (review work + version milestone).
    Mitigation: separate commit for the banner change within the PR so it can be reverted independently if needed.

execution:
  approach: "Same dispatch flow as cycles #7 and #8: user approves spec → planner skill writes implementation plan → subagent-driven execution → PR opened, user merges."
  parallelism: "Tasks within phases parallelizable per feedback_subagent_dispatch.md. Phases sequential (refs → scripts → agents → skills → profiles → router → tests → smoke → banner)."
  expected_pr_size: "Larger than cycle #8 (~25–35 commits, ~3000–4500 LoC added). 3 agents + 4 skills + 2 scripts + rubric + 9 profile updates + ~40 tests + smoke + banner."
  beta_test_phase: "Optional phase-2.5 against the the beta-test perspective fixture (cycle #7 phase-2 sandbox) — run /sws:review-paper end-to-end on the existing fixture. User-approved before phase-3 implementation completion."
---

# Cycle #9 — Review

End-of-cycle goal: a user who has completed cycle-#8 revising (`/sws:revise-paper` → final `.docx`) can run `/sws:review-paper` to take that `.docx` through three diagnostic reviewers in sequence — `claim-verifier` → `bibliography-fidelity-checker` → `peer-reviewer` — with each report persisted under `_review/<agent>/` and the peer-reviewer explicitly receiving the prior two reports' paths as input (plus a skip-state env var when fidelity is inert). End-of-cycle banner flips to `🧪 v0.1 alpha` and `plugin.json` version bumps to `0.1.0-alpha`.

This spec follows the same dispatch flow as cycles #7 and #8. All locked decisions are in the frontmatter `locked_decisions:` block above (D1–D17, with D9a + D9b + D9c for the three fidelity-checker fallback paths). The body of this document is orientation only — frontmatter is the project-memory dictionary.

## What ships

Three diagnostic-only agents, four user-facing slash commands, two helper scripts, one rubric reference, and a profile-activation update across all nine profiles. Plus the visible alpha milestone: README banner + version bump.

Per arch-sketch §7, this is the cycle that makes the writing+review track usable end-to-end. After cycle #9 merges, the plugin can take a paper from outline → draft → revise → review without leaving SWS slash commands.

## Why these scope cuts

Four substantial features get explicit deferral, all per user instructions on 2026-05-17:

1. **Sprint-contracts paper-blind Phase 1** for peer-reviewer (rubric committed before reading paper, with timestamp gate). Ship the basic pipeline first; add the discipline layer in cycle #9.1 once we have feedback on real reviews.
2. **Unbounded-corpus plagiarism detection.** The original cycle-#9 design proposed a plagiarism-screener checking ≥25-word overlap against Semantic Scholar abstracts of cited papers. User judgment 2026-05-17: abstract-only is theater (Google Scholar searches full text; our API doesn't), so the agent was refocused — renamed to `bibliography-fidelity-checker` and rescoped to verbatim ≥15-word overlap against the user's Zotero full-text index. This catches the real common error (accidentally reproducing text from a paper you actually read), not unbounded-corpus plagiarism. The unbounded check (Crossref Similarity Check API, Google Programmable Search opt-in, embedding paraphrase detection) is in the v0.2 backlog per D13.
3. **Concession-threshold scoring.** Dormant until response-to-reviewers ships in cycle #10.
4. **NLM consumer wiring** for claim-verifier. The agent uses Zotero + Semantic Scholar + PubMed in v0.1 and degrades gracefully without NLM. NLM wiring happens in cycle #11 where `nlm-librarian` ships.

These deferrals are tracked as explicit entries in `claude_memory/project_v02_backlog.md` per D13.

## Bibliography-fidelity-checker — what "fidelity" actually means

Naming this agent precisely is load-bearing. **Plagiarism** = "this text appeared somewhere before, even if you've never seen it." Detecting that requires unbounded-corpus search (industry tools: iThenticate, Crossref Similarity Check). **Fidelity** = "this text accidentally reproduces a passage from a paper that's in your reading history." Detecting that requires only the user's Zotero corpus — bounded, curated, and openly accessible via the `zotero` skill's full-text index.

The fidelity check is the right scope for v0.1 because: (a) the user's Zotero is the most common source of accidental copy-paste errors during writing; (b) we can do it confidently with the tools we already have; (c) we don't pretend to be doing more than we are. The report-file framing reinforces this — every report leads with "V0.1 LIMITATION: this is a fidelity check against your Zotero library only, not unbounded-corpus plagiarism detection."

Three fallback paths handle users who can't run the check, distinguished by what we actually detect on their system:

- **D9a** — Zotero desktop is installed on the host (`~/Zotero/zotero.sqlite` or equivalent) but the Claude Code `zotero` skill is not installed. Report leads with an ACTIONABLE RECOMMENDATION naming the detected install path and suggesting the user install the zotero plugin in Claude Code. Most useful UX: tells Zotero users about a one-command fix they probably didn't know existed.
- **D9b** — `zotero` skill is installed and responsive, but the library is too small (< 10 items), unresponsive, or permission-denied. Report explains the threshold or the specific failure.
- **D9c** — neither the `zotero` skill nor Zotero desktop is detected. Report is neutral — no recommendation to install Zotero, since that's a workflow choice. Notes that v0.1 fidelity-checker is Zotero-only and points to the v0.2 backlog for alternative-corpus paths (Crossref Similarity Check, Google Programmable Search opt-in).

All three exit 0 with a clear `status.json` skip-state and an informative `report.md`. The orchestrator propagates the specific skip-reason to `peer-reviewer` via `SWS_FIDELITY_STATUS` so the peer-review report can transparently note which path was taken — never silent failure, never false confidence, and a useful nudge when (and only when) a nudge is warranted.

## Cross-cutting compliance

- **Review-Then-Act:** all 3 agents diagnose only; no writes to manuscript `.docx`.
- **Agent-contract R1:** each agent sources `scripts/agent_prelude.sh` and calls `agent_should_run.sh <id>` before doing work.
- **Agent-contract R3:** I/O wrappers — agents call `sws_read_docx.py` via `sws_python.sh` to read manuscript; agents write plain markdown + JSON to `_review/<agent>/`.
- **Agent-contract R5:** no gender-default in user address, baked into all 3 agent prompts.
- **MCP-aversion principle:** Semantic Scholar via WebFetch + small utility scripts; PubMed via the existing `claude_ai_PubMed` MCP (the documented v0.1 exception); no new MCP servers.
- **Profile-aware activation:** peer-reviewer everywhere; claim-verifier + bibliography-fidelity-checker inactive in funding-proposal (D10).

## Banner change exact strings

- `README.md` banner line:
  - Before: `🚧 v0.1 in design — code starts 2026-05-08`
  - After: `🧪 v0.1 alpha — usable end-to-end writing+review track (drafting, revising, review)`
- `.claude-plugin/plugin.json`:
  - Before: `"version": "0.0.1"`
  - After: `"version": "0.1.0-alpha"`

Banner change is its own commit within the PR for revertability (R4).
