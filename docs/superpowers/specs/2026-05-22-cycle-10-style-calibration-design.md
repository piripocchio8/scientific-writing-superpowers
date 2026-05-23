---
sws_artifact: cycle-10-spec
artifact_version: 0.1
locked: 2026-05-22
title: "Cycle #10 — Style calibration (1 agent, 1 skill, 1 stylometry script, _voice/ folder). Iterative held-out voice-matching loop with a Fisher-weighted linear combination of stylometric features + a Haiku voice-similarity term, wrapped in an RBF kernel, stopped at the author's self-similarity band. Plus a one-shot diachronic style-evolution analysis."

cycle_index: 10
original_roadmap_index: 8
predecessor: cycle-09-review
banner_after_completion: null            # no banner flip this cycle (alpha set at cycle #9; v0.1 set at cycle #13)
version_after_completion: "0.1.0-alpha"  # unchanged

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §7 cycle table line 489 (Style calibration = /sws:calibrate-style + style-calibrator + _voice/, Zotero ingestion via user's zotero skill); §_voice folder layout lines 174-178"
  prior_cycle_anchors:
    - "cycle-06 D14/D17: resolve_overlay.py 3-layer merge — voice profile is a SEPARATE axis from the journal-style/constraints overlay; it does not pass through resolve_overlay.py"
    - "cycle-07 D22: native Read tool (with pages param for >10pp PDFs) reads PDF; sws_read_docx.py / sws_read_xlsx.py for DOCX/XLSX. No ad-hoc python-docx PDF installs"
    - "cycle-07 agent-contract R1: agents source agent_prelude.sh + call agent_should_run.sh <id>"
    - "cycle-09 D9a/D9c: zotero-probe pattern (skill-present vs desktop-detected vs absent) — reused for the calibrator's no-corpus fallback"
  related_memory:
    - "claude_memory/project_roster_v0.1.md (#4 style-calibrator Sonnet 4.6 high, Zotero, writes _voice/{profile.md,sources.json,field-profile.md,_archive/}); roster stays at 24 — the Haiku scorer is an internal dispatched step, not a new rostered agent"
    - "claude_memory/reference_external_tools.md (zotero skill = corpus source; Zotero-first principle)"
    - "claude_memory/project_v02_backlog.md ('Author personal-skill lookup' deferred — v0.1 calibrates fresh; 'HTML-format memory/overlay files' deferred — voice files stay md)"
    - "claude_memory/feedback_ai_writing_tells.md (generated calibration prose must pass the AI-tells grep; the voice profile is not an excuse to reintroduce tells)"
    - "claude_memory/feedback_integration_smoke.md (smoke_cycle_10.sh = canonical final verification)"
    - "claude_memory/feedback_lean_deliverables.md (this spec: frontmatter = dictionary, body = orientation)"

scope:
  deliverable: "An author can run /sws:calibrate-style to build a reusable, evidence-backed voice profile from their own papers in Zotero. The calibrator name-searches the library, ranks hits by authorship position, presents a flagging list the author curates, auto-holds-out 1-2 recent first-author papers as a hidden test target, then runs an iterative loop: draft a candidate profile.md (global voice block + per-section deltas), generate held-out-section prose on the held-out paper's own content (content-controlled so only voice varies), score generated-vs-real via a Fisher-weighted stylometric distance + a Haiku voice-similarity term wrapped in an RBF kernel, diagnose the gap, edit the profile, repeat until the score enters the author's own self-similarity band or plateaus. Writes _voice/{profile.md, field-profile.md, style-evolution.md, sources.json, convergence.md, _archive/}. The drafter/reviser/humanizer agents consume profile.md as a new voice axis. This cycle also dogfoods the calibration mechanism end-to-end — the held-out split IS the real-world test of 'can SWS set an author's voice.'"
  not_in_scope:
    - "Author personal-skill lookup (pre-existing hand-written voice SKILL.md) — v0.2 backlog. v0.1 always calibrates fresh."
    - "HTML rendering of voice files / _archive comparison viewer — v0.2 backlog. All voice files ship as md + YAML frontmatter."
    - "Multiple-kernel learning (MKL) / learned non-diagonal Mahalanobis metric / string-kernel on syntactic shape — v0.2. v0.1 uses a diagonal Fisher metric wrapped in a single RBF."
    - "Year-trend detrending of within-author variance before the kernel — considered and deferred (D16). Revisit in v0.2 ONLY IF style-evolution.md on real corpora shows drift large enough to inflate within-author variance. Not pre-built."
    - "Per-section deltas for field-profile.md — field profile is a single global descriptive characterization, no per-section breakdown, no loop (D5)."
    - "Drafter-in-the-loop realism test (using the production drafter as the in-loop generator) — Approach B, rejected. Production-consumer validation is a post-calibration concern, not part of the loop (D1)."
    - "Inline application of the voice profile to an existing manuscript — calibration produces the profile; drafting/revising consume it (cycle #7/#8 agents). This cycle does not rewrite any manuscript prose."

deliverables:
  scripts:
    - scripts/sws_stylometry.py            # stdlib + venv, NO NLTK/spaCy. Modes: --vector <text> -> feature JSON; --distance <vecA> <vecB> [--weights w.json] -> {distance, per_feature_contrib}; --fit-weights <pos-pairs> <neg-pairs> -> diagonal-Fisher weights JSON (regularized); --rbf <D> --gamma <g> -> similarity in [0,1]; --self-band <author-vectors> -> the intra-author self-similarity band (mean/sd). Bundled function-word + hedge + connective lists live in references/.
  references:
    - references/stylometry-features.md    # the canonical feature list + the function-word/hedge/connective word-lists the script reads; the Fisher-weight + RBF + self-band math, documented so the numbers are reproducible and auditable
    - references/voice-profile-schema.md    # frontmatter schema for _voice/profile.md (machine-readable feature targets) + the global-block / per-section-delta body contract
  agents:
    - agents/style-calibrator.md           # Sonnet 4.6 high (roster #4). Orchestrates the 5 phases + the loop; dispatches the Haiku scoring step; reads sws_stylometry.py JSON (never invents a score); diagnoses gaps; edits profile.md; writes the _voice/ artifacts.
  skills:
    - skills/calibrate-style/SKILL.md      # /sws:calibrate-style. Phase driver: discover -> flag&split -> extract -> (3.5 evolution) -> calibrate-loop -> write&report. Holds the loop defaults (epsilon, max-rounds, blend/regularization params).
  profile_updates:
    - profiles/full-article.md             # style-calibrator default-active
    - profiles/communication.md            # default-active
    - profiles/perspective.md              # default-active
    - profiles/review-paper.md             # default-active
    - profiles/mini-review.md              # default-active
    - profiles/methodological-paper.md     # default-active
    - profiles/funding-proposal.md         # default-active
    - profiles/editorial.md                # default-INACTIVE (exec-tunable; short, may skip calibration) per D14
    - profiles/commentary-reply.md         # default-INACTIVE (exec-tunable) per D14
  consumer_updates:
    - agents/drafter-flagship.md           # reads _voice/profile.md (global + per-section delta) when present; graceful degrade when absent
    - agents/drafter-fast.md
    - agents/reviser-full.md
    - agents/reviser-fast.md
    - agents/humanizer.md                  # humanize TOWARD the author's voice, not generic, when profile present
  shared_helper_updates:
    - scripts/agent_prelude.sh             # export VOICE_PROFILE (path to _voice/profile.md if present, else empty) for the 5 consumer agents
  reference_updates:
    - references/agent-contract.md         # R3 I/O inventory: add _voice/ shapes (calibrator WRITES _voice/*; the 5 consumers READ _voice/profile.md)
  memory_updates:
    - claude_memory/project_v02_backlog.md          # new entries: MKL/learned-kernel, detrending (conditional), drafter-in-loop realism test
    - claude_memory/project_cycle_execution_status.md  # cycle #10 -> merged at end of PR
  tests:
    - tests/test_stylometry_vector.py      # feature extraction determinism; empty/short text edge cases; section-pooling
    - tests/test_stylometry_fisher.py      # Fisher weights recover a KNOWN separation on synthetic data; constraints w>=0 / sum=1; regularization shrink + within-var floor; w_h (Haiku term) fitted alongside feature weights
    - tests/test_stylometry_kernel.py      # RBF bounds in [0,1]; gamma median-heuristic; self-similarity band math; monotonic keep-best behavior
    - tests/test_voice_profile_schema.py   # profile.md frontmatter validation; global + per-section delta blocks present and well-formed
    - tests/test_profile_activation_calibrator.py  # style-calibrator active in 7 / inactive in editorial + commentary-reply
    - tests/smoke_cycle_10.sh              # full /sws:calibrate-style against a fixture corpus; Haiku stubbed via test-mode env var

locked_decisions:
  D1: |
    Approach A — single agent + objective script. style-calibrator (Sonnet 4.6 high, roster #4) runs the entire loop:
    corpus discovery (via the zotero skill), PDF reading (native Read tool), candidate-profile drafting, held-out generation,
    gap diagnosis, and profile editing. scripts/sws_stylometry.py supplies the OBJECTIVE numbers (feature vectors, fitted
    weights, distance, RBF similarity, self-similarity band). A Haiku 4.5 voice-similarity call is dispatched as an INTERNAL
    scoring step BY style-calibrator — it is NOT a new rostered agent. Roster stays at 24.
    Rejected: Approach B (drafter-in-the-loop as generator — Opus-per-round too expensive, needs a judge agent the roster
    lacks; production-consumer validation belongs AFTER calibration). Approach C (script-only — can't generate prose, kills
    refinement quality).
    Rationale: A is the cheapest path that keeps an objective stopping rule, fits the locked 1-agent roster slot, and the
    stylometry script + held-out target prevent the agent from self-grading its own output.

  D2: |
    Five phases driven by /sws:calibrate-style, plus a Phase 3.5 diachronic analysis:
      1. Discover  — confirm author name variants once; name-search the whole Zotero library; rank hits by authorship position.
      2. Flag&Split — present the flagging list; author curates; auto-hold-out 1-2 papers as the hidden test target.
      3. Extract   — read training PDFs (native Read, pages for >10pp); slice into sections; pool each section type across papers.
      3.5 Evolution — fingerprint every flagged paper, order by year, detect per-feature trends; write style-evolution.md (one-shot).
      4. Calibrate loop — per section type: draft candidate -> generate held-out prose (content-controlled) -> score -> diagnose -> edit -> repeat until self-band or plateau.
      5. Write&Report — persist _voice/ artifacts; rotate prior profile.md into _archive/; print the convergence report.
    Rationale: clean phase boundaries; the evolution pass is cheap (reuses the per-text feature vectors) and informs nothing in
    the loop, so it sits before calibration as a descriptive side-output.

  D3: |
    Corpus discovery (Phase 1-2). Author confirms their name variants once (e.g. "Surname I", "I. Surname", "Firstname Surname").
    Calibrator name-searches the WHOLE library (not a single named collection), then RANKS hits by authorship position:
    first / last / corresponding = strong voice signal; second = good; middle author = dropped (weak voice signal).
    Presents a flagging list: [title, year, author_position, has_full_text_pdf]. The author flags which to include (curation gate
    — removes minor co-authorships and off-voice items). From the confirmed set the calibrator AUTO-holds-out 1-2 items
    (preferring a RECENT first-author paper with a full-text PDF) as the hidden test target; the remainder is the training corpus.
    Rationale: user instruction 2026-05-22 — name-search with position-preference + a human flagging gate beats both a blind
    author-scan (pulls minor co-authorships) and a named-collection requirement (setup friction). Author-position is the voice-
    weight signal: first author wrote it, last/corresponding shaped it, middle contributed weakly.

  D4: |
    Per-section voice deltas. profile.md = a GLOBAL voice block + PER-SECTION delta blocks for Introduction / Results /
    Discussion / Methods / Abstract ("here your register shifts to X"). Per-section deltas are learned by POOLING each section
    type across the included training papers (so a handful of papers yields enough per-section signal). The held-out comparison
    in the loop runs PER SECTION TYPE — generate each section type in the candidate voice, score against the real held-out
    section of that type.
    Rationale: user instruction 2026-05-22 — voice is not uniform across a paper (Methods is convention-bound; Intro/Discussion
    carry personal voice). Per-section fidelity is worth the heavier corpus slicing.

  D5: |
    field-profile.md is a ONE-SHOT descriptive characterization of the author's subfield conventions (typical structure,
    citation density, hedging norms, terminology), built from a SECOND corpus of field papers the author flags. It is NOT in
    the calibration loop and gets NO per-section breakdown — there is nothing to "match closest" for descriptive field norms.
    The drafter consults it as a reference alongside profile.md.
    Rationale: user instruction 2026-05-22 — field norms are descriptive, not a personal target. Looping them is overkill.

  D6: |
    Target voice = RECENT-WEIGHTED CURRENT voice. profile.md captures who the author writes like NOW: the training corpus
    weights recent papers higher (recency_weight in sources.json), and the held-out target is a recent first-author paper.
    style-evolution.md remains a SEPARATE descriptive artifact showing the full arc; it does not feed profile.md.
    Rationale: user instruction 2026-05-22 — drafting today's manuscript should match today's voice, not a career-average
    composite the author has partly outgrown.

  D7: |
    Diachronic style analysis (Phase 3.5). For every flagged paper, sws_stylometry.py emits its feature vector; order by
    publication year, bucket into eras when the span is long, detect per-feature trends (mean sentence length, hedge density,
    first-person-plural rate, connective style, lexical diversity, passive ratio). Output _voice/style-evolution.md = a
    feature x year/era table + style-calibrator's prose reading of WHAT shifted, WHEN, and likely inflection points
    (first independent papers, PI transition). Written once; not part of the loop. The flagging list already carries year,
    so no extra corpus work.
    Rationale: user instruction 2026-05-22 — "grasp if and how my style changed over the years." Reuses the loop's own
    stylometry primitive.

  D8: |
    Scoring — ONE unified weighted distance, fitted from boundary conditions, wrapped in an RBF kernel.
      D(x,y) = SUM_i w_i * (x_i - y_i)^2  +  w_h * (1 - haiku_sim(x,y))
    The stylometric features x_i are per-text (differenced); the Haiku term is a PAIRWISE dissimilarity that enters directly
    (it cannot be differenced). All terms are standardized to comparable scale BEFORE weighting. The weights {w_i, w_h} are
    fitted by the DIAGONAL FISHER RATIO from two boundary conditions (D8a). The kernel is k(x,y) = exp(-gamma * D(x,y)),
    bounded in [0,1] and saturating under large drift, with gamma from the median heuristic on weighted intra-author distances.
    Rationale: user instructions 2026-05-22 — (1) "take into account a linear combination of vector features first" -> the
    weighted-squared-difference sum; (2) "optimize the combinatorial constants based on boundary conditions" -> Fisher fit;
    (3) "Haiku output baked within the linear combination" -> w_h as a fitted term, removing any hand-set blend constant;
    (4) "kernel function more than just a vector" -> RBF wrap for bounded, smooth, drift-tolerant similarity. The earlier
    hand-set 0.5/0.5 blend is DROPPED — the blend is now learned.

  D8a: |
    Fisher weight fitting. Boundary conditions:
      POSITIVE pairs = (author paper, author paper)  -> distance should be SMALL ("this is me").
      NEGATIVE pairs = (author paper, field paper)    -> distance should be LARGE (separation).
    Per term, w ∝ between-class-variance / within-author-variance (classic diagonal Fisher ratio). Constraints: w_i >= 0,
    SUM(w_i) + w_h = 1. Regularization (mandatory — only 4-6 author papers): shrink toward uniform,
    w = (1 - lambda) * fisher + lambda * uniform; floor the within-author variance to avoid division blow-ups. To fit w_h,
    Haiku is run once on a sample of the anchor pairs (positive + negative) to get its own within/between variance, exactly like
    any other term. Near-closed-form: no optimizer, no heavy dep — fits stdlib/venv.
    Rationale: well-posed supervised metric learning that REUSES the field corpus already collected for field-profile.md.
    Discriminative features (stable within the author, separating from the field) get the most weight; noisy/generic features
    get suppressed. Regularization prevents overfitting to a tiny author corpus.

  D9: |
    Haiku 4.5 voice-similarity judge — strict prompt contract. Context given to Haiku: "two excerpts of the SAME section type
    from chemistry manuscripts; A is the human author, B is a machine imitation of that author's VOICE; both cover similar
    content, so do NOT reward topic/content/citation overlap." Similarity defined explicitly = sentence rhythm and length
    variation, hedging/stance, connective and transition habits, register/formality, signposting, idiosyncratic phrasings.
    ANCHORED RUBRIC supplied identically every call: 0.9-1.0 stylistically indistinguishable; 0.7-0.9 same hand, minor tells;
    0.5-0.7 related register, different hand; <0.5 clearly different voice. Output forced JSON {"voice_similarity": x, "note": "..."}.
    Low temperature; run x3; take the MEDIAN to damp variance. Dispatched as an internal step by style-calibrator (not a rostered agent).
    Rationale: user instruction 2026-05-22 — "prompt haiku the right way; define exactly the similarity concept and the overall
    context." The fixed anchored rubric makes scores comparable across rounds; the voice-not-content framing prevents the judge
    from rewarding the content-controlled overlap.

  D10: |
    Convergence — the author's SELF-SIMILARITY BAND. The stopping target is the score the author's OWN papers achieve against
    each other (sws_stylometry.py --self-band on the author vectors). The loop stops for a section type when its generated-vs-
    held-out score enters that band — you cannot be more like yourself than your own papers already are. Backstops:
    keep-best-so-far (an edit that WORSENS a section's score is reverted, so the loop is monotonic per section), a plateau rule
    (relative improvement < epsilon between rounds), and a hard round cap N. Defaults (epsilon, N, lambda, blend params) live in
    the skill (initial: epsilon=5% relative, N=4, lambda=0.3).
    Rationale: user concern 2026-05-22 — a raw cosine with significant drift could recycle forever in a non-convex/non-derivable
    edit space. The self-similarity band gives a PRINCIPLED ceiling; keep-best + plateau + cap are belt-and-suspenders against
    oscillation.

  D11: |
    Content-control. Each loop round feeds the generation step the held-out section's ACTUAL outline/claims, so the only free
    variable is voice. The stylometric distance and the Haiku score therefore measure voice divergence, not topic divergence.
    convergence.md records the seed prompt + the candidate text per round (the script is deterministic; generation is not), so
    every round is inspectable even though regeneration is not byte-identical.
    Rationale: isolates the quantity we actually want to minimize.

  D12: |
    _voice/ output schema:
      _voice/profile.md         # YAML frontmatter (recent-weighted feature targets: sentence-length band, hedge density,
                                #   passive ratio, connective prefs, lexical signatures, first-person-plural rate) + body:
                                #   GLOBAL voice block then PER-SECTION delta blocks. THE file drafters/revisers consume.
      _voice/field-profile.md   # one-shot subfield conventions (D5)
      _voice/style-evolution.md # diachronic trajectory table + reading (D7)
      _voice/sources.json       # [{zotero_key, title, year, author_position, has_pdf, role: train|heldout, recency_weight}] + fitted weights snapshot + gamma + self-band
      _voice/convergence.md     # per round, per section: distance, RBF sim, Haiku median, what changed, why, seed prompt + candidate text
      _voice/_archive/          # prior profile.md versions, timestamped, on re-run
    All writes are marker-scoped and pass through the cycle-#5 PreToolUse backup hook.
    Rationale: matches the arch-sketch _voice/ layout (lines 174-178) extended with convergence.md (dogfooding evidence) and
    style-evolution.md (D7); the underscore-prefix metadata convention (cycle-#6).

  D13: |
    Consumption. _voice/profile.md is a NEW input on the VOICE axis, SEPARATE from the journal-style/constraints overlay
    (which stays numeric: word caps, sections, refs_style). It does NOT pass through resolve_overlay.py. drafter-flagship,
    drafter-fast, reviser-full, reviser-fast, and humanizer read it WHEN PRESENT — the global block always, plus the per-section
    delta for the section being written (the section-router already knows the section). agent_prelude.sh exports VOICE_PROFILE
    (path if _voice/profile.md exists, else empty). Absent _voice/ -> agents behave exactly as today (graceful degrade). Marker-scoped.
    Rationale: voice is orthogonal to journal constraints; layering it into resolve_overlay.py would conflate two axes. Reading
    it via a prelude-exported path keeps the wiring uniform with the rest of the plugin.

  D14: |
    Per-profile activation matrix for style-calibrator (extends the cycle-#7/#8 matrix):
      DEFAULT-ACTIVE: full-article, communication, perspective, review-paper, mini-review, methodological-paper, funding-proposal.
      DEFAULT-INACTIVE (exec-tunable): editorial, commentary-reply (short, fast-turnaround; calibration may be skipped).
    style-calibrator is a Plan-phase agent run once to build _voice/; "active" means the profile expects a voice-calibration step.
    Rationale: as approved 2026-05-22. Editorial/commentary-reply default-off to avoid forcing a full calibration on short pieces;
    exec can flip them on if the author wants voice there too.

  D15: |
    Testing (honors feedback_integration_smoke.md):
      Unit: feature-vector determinism + edge cases; Fisher weights recover a KNOWN separation on synthetic data (incl. w_h);
            constraint + regularization behavior; RBF bounds + gamma + self-band; profile.md schema; activation matrix.
      Fixture: a tiny FAKE author corpus as plain-text files (3 "author" + 2 "field" + 1 held-out) so no live Zotero/network is
            needed; the Haiku call is STUBBED via the existing test-mode env-var pattern returning fixed scores.
      tests/smoke_cycle_10.sh: run the full /sws:calibrate-style flow against the fixture; assert _voice/ files exist,
            sources.json has the train/heldout split + recency weights, convergence.md shows monotonic (keep-best) improvement,
            profile.md has a global block + per-section delta blocks.
    Rationale: the loop is deterministic except for generation + Haiku; stubbing Haiku and using a fixed fixture makes the smoke
    reproducible while still exercising every code path (discover-skip via fixture sources, fit, loop, write).

  D16: |
    Detrending considered, DEFERRED. Year-trend detrending of within-author variance would only help the Fisher weights (not
    profile.md, which is already recency-targeted per D6), and only IF drift is large. Whether drift is large is unknown until
    style-evolution.md runs on a real corpus. So detrending is data-driven v0.2 work, not pre-built. One v0.2-backlog entry.
    Rationale: user instruction 2026-05-22 — "no note, no need... explain if it's worth in v0.2." Honest answer: one narrow
    benefit, speculative until we see real drift magnitude. YAGNI.

  D17: |
    No-corpus fallback (reuses the cycle-#9 zotero-probe pattern). If the zotero skill is absent:
      - Zotero DESKTOP detected on host (sqlite probe) -> nudge: recommend installing the Claude Code zotero plugin, name the
        detected path, exit without calibrating.
      - No Zotero at all -> neutral note; offer the manual path: drop chosen PDFs into _voice/sources/ and re-run with
        --sources _voice/sources/ (the manual path is the documented fallback, never the default).
    If the zotero skill is present but returns too few of the author's papers to split (< 3 includable items after flagging),
    the calibrator stops with a clear message rather than calibrating on an unusably small corpus.
    Rationale: consistency with cycle-#9 graceful-degradation UX; calibration fundamentally needs a corpus, so fail honestly with
    an actionable path rather than producing a hollow profile.

risks:
  R1: |
    Tiny author corpus (4-6 papers) makes per-feature within/between variance noisy -> unstable Fisher weights.
    Mitigation: D8a regularization (shrink-to-uniform lambda + within-variance floor); the self-similarity band (D10) is itself
    estimated from the same small corpus, so the stopping target scales with the available evidence rather than demanding an
    unrealistic match.
  R2: |
    Haiku sycophancy / variance could inflate voice_similarity and let the loop stop early.
    Mitigation: median of x3 low-temp calls (D9); the Haiku term is only ONE weighted component (w_h fitted from data, D8a) — if
    Haiku fails to separate author-from-field on the anchor pairs, Fisher down-weights it automatically. The stylometric terms
    and the self-band provide an objective floor Haiku cannot override alone.
  R3: |
    Non-convex / non-derivable edit space -> oscillation or never-ending recycling (user's explicit concern).
    Mitigation: keep-best-so-far makes the loop monotonic per section; plateau + hard round cap bound iterations; the RBF +
    self-similarity band give a principled, reachable target instead of an unbounded distance to chase.
  R4: |
    Generated calibration prose could reintroduce AI-writing tells while chasing a stylometric target.
    Mitigation: the AI-tells grep-pass (cycle-#7) runs on generated prose before scoring; style-evolution and profile body must
    not encode tells. The voice profile describes the AUTHOR's habits, which are tell-free by construction.
  R5: |
    Voice profile could leak into the public repo or be applied silently.
    Mitigation: _voice/ is gitignored in user paper-project templates (per the underscore-metadata convention); profile.md is
    consumed transparently (agents state when a voice profile is active); nothing in _voice/ is pushed to the SWS plugin repo.

execution:
  approach: "Same dispatch flow as cycles #7-#9: user approves spec -> planner skill writes implementation plan -> subagent-driven execution -> PR opened, user merges."
  parallelism: "Phases sequential (script+references -> agent -> skill -> consumer wiring -> profiles -> tests -> smoke). Within phases, independent files parallelizable per feedback_subagent_dispatch.md (e.g., the 5 consumer-agent edits, the 9 profile edits)."
  expected_pr_size: "Comparable to cycle #8 (~20-30 commits). 1 agent + 1 skill + 1 script + 2 references + 5 consumer-agent edits + prelude export + 9 profile edits + ~40 unit tests + smoke."
  beta_test_phase: "Optional dogfood: run /sws:calibrate-style against the maintainer's REAL Zotero (the genuine end-to-end test of 'can SWS set an author's voice'). Run locally only; no corpus, author identity, or publication detail is committed. User-approved before treating the convergence report as evidence the mechanism works. This is the real-scenario test that motivated the cycle."
---

# Cycle #10 — Style calibration

End-of-cycle goal: an author runs `/sws:calibrate-style` and gets a reusable, evidence-backed voice profile built from their own papers in Zotero, produced by an iterative held-out loop that converges to the author's own self-similarity band. The drafter, reviser, and humanizer then consume that profile so SWS writes in the author's voice rather than a generic one.

This spec follows the cycle-#7/#8/#9 dispatch flow. All locked decisions live in the frontmatter `locked_decisions:` block (D1–D17, with D8a). The body is orientation only — the frontmatter is the project-memory dictionary.

## The core idea

The calibrator does not one-shot a voice description. It runs a measured loop: hold out one of the author's own recent papers, generate that paper's sections in a candidate voice **on the paper's real content** (so only voice varies), score how close the generated prose is to the real held-out prose, diagnose the gap, edit the profile, and repeat until the generated prose is as similar to the held-out paper as the author's own papers are to each other. That self-similarity band is the honest ceiling: you cannot imitate an author more closely than the author imitates themselves across papers.

This doubles as the real-world test of the mechanism. If the loop converges into the band on a real author's Zotero corpus (run locally during dogfooding), that is direct evidence SWS can set an author's voice — the scenario the cycle was requested to validate. No corpus or identity detail from that run is committed.

## Why the scoring design is shaped this way

The score is one fitted quantity, not a hand-tuned blend. Stylometric features (sentence-length distribution, function-word frequencies, hedge/connective density, passive ratio, lexical diversity, first-person-plural rate) enter as a weighted sum of squared differences; the Haiku voice-similarity judge enters as one more weighted term. The weights are learned from boundary conditions the project already has data for — the author's papers should look alike, and should look different from the field corpus — via a diagonal Fisher ratio. The whole distance is wrapped in an RBF kernel so similarity is bounded in `[0,1]`, smooth, and tolerant of large drift (it saturates instead of exploding). This directly answers the convergence worry: a bounded kernel plus a self-similarity-band target plus keep-best-so-far cannot recycle forever in the non-derivable edit space.

## What the author sees

A flagging list of their own papers (ranked by authorship position), a held-out split chosen for them, a convergence report showing the per-section trajectory round by round, a `style-evolution.md` reading of how their voice changed over the years, and a `profile.md` the rest of SWS consumes. Everything stays under `_voice/`, marker-scoped and gitignored — never pushed to the public plugin.

## Cross-cutting compliance

- **Agent-contract R1:** style-calibrator sources `agent_prelude.sh` and calls `agent_should_run.sh style-calibrator`.
- **Agent-contract R3:** calibrator WRITES `_voice/*`; the five consumer agents READ `_voice/profile.md`; PDFs read via native Read (pages for >10pp), no ad-hoc python-docx.
- **Agent-contract R5:** no gender-default in user address.
- **MCP-aversion:** corpus access via the existing `zotero` skill; no new MCP server. Haiku scoring is an internal model dispatch, not a tool/MCP.
- **Voice ≠ constraints:** `profile.md` is a separate axis from the `resolve_overlay.py` journal-style/constraints overlay (D13).
- **AI-tells:** generated prose passes the cycle-#7 AI-tells grep before scoring (R4).
