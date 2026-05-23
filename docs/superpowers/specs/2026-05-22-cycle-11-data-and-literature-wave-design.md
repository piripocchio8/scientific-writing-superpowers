---
sws_artifact: cycle-11-spec
artifact_version: 0.1
locked: 2026-05-22
title: "Cycle #11 — Data + literature wave (4 agents: data-curator, plot-maker, literature-searcher, bibliography-curator; 4 skills; 3 external-API scripts; locks the Zenodo_db/ layout). xlsx-as-data-authority with fail-loud on un-cached formula cells; matplotlib figures sized from the journal-style overlay with opt-in VLM self-check; MCP-aversion external wiring (Semantic Scholar / CrossRef / OpenAlex via scripts, PubMed via existing MCP, Zotero via existing skill)."

cycle_index: 11
original_roadmap_index: 9
predecessor: cycle-10-style-calibration
banner_after_completion: null            # banner stays 🧪 v0.1 alpha; v0.1 flip is the dedicated NLM cycle (#13)
version_after_completion: "0.1.0-alpha"

sources:
  architecture_sketch: "docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §7 cycle table line 490 (Data + literature wave (4 agents): plot-maker + optional VLM, data-curator Zenodo/xlsx + formula resolution, literature-searcher, bibliography-curator; wires Semantic Scholar / PubMed / Zotero / CrossRef / OpenAlex; locks Zenodo_db/ layout); §Zenodo_db layout lines 168-171"
  prior_cycle_anchors:
    - "cycle-07 D22: sws_read_xlsx.py / sws_read_docx.py I/O wrappers — data-curator reads xlsx through sws_read_xlsx.py, never ad-hoc openpyxl"
    - "cycle-07: sws_extract_zotero_manifest.py + /sws:prepare-lit-context — literature-searcher builds on the Zotero manifest extraction"
    - "cycle-07 status note: editorial dropped its caption-writer/data-curator/plot-maker activation entries — preserved here"
    - "cycle-09 D8: claim-verifier's nlm-librarian consumer wiring deferred to the NLM cycle; same deferral applies to literature-searcher + bibliography-curator here (D9)"
    - "cycle-09 D13 / risk R1: Semantic Scholar rate-limit + caching/backoff discipline — reused for the 3 external-API scripts"
  related_memory:
    - "claude_memory/project_roster_v0.1.md (#17 plot-maker, #18 data-curator, #5 literature-searcher, #19 bibliography-curator — all Sonnet 4.6 high)"
    - "claude_memory/feedback_openpyxl_formulas.md (data_only=True returns None unless cached; resolve formula cells to plain numbers; the basis for the fail-loud decision D4)"
    - "claude_memory/reference_external_tools.md (MCP-aversion: CLI/WebFetch+scripts over MCP; PubMed kept as MCP exception; Zotero-first fallback chain)"
    - "claude_memory/feedback_subagent_dispatch.md (phase-sequential, within-phase parallel dispatch)"
    - "claude_memory/feedback_integration_smoke.md (smoke_cycle_11.sh = canonical final verification)"
    - "claude_memory/feedback_lean_deliverables.md (frontmatter = dictionary, body = orientation)"

scope:
  deliverable: "First usable data + literature wave. data-curator ingests the Zenodo_db/ xlsx as the data authority (fail-loud on un-cached formula cells) and emits a tidy data manifest; plot-maker generates publication figures from curated data via co-located fit/plot scripts, sized from the resolved journal-style overlay, with an opt-in VLM self-check; literature-searcher DISCOVERS new relevant sources (Zotero-first, then PubMed/Semantic Scholar) for a topic or section; bibliography-curator AUDITS the manuscript's EXISTING citations (resolve/dedup/fix DOIs, format to the journal refs_style, Zotero-first with CrossRef/OpenAlex fallback). The Zenodo_db/ layout (data/, scripts/, figures/, manifest.json, _archive/) is locked. After this cycle a paper's data, figures, literature discovery, and citation hygiene are all SWS-managed."
  not_in_scope:
    - "nlm-librarian agent + NLM consumer wiring for literature-searcher / bibliography-curator — DEFERRED to the dedicated NLM cycle (current #13, the roadmap's 'NLM integration, last'). v0.1 agents degrade gracefully without NLM (D9). NOTE numbering ambiguity flagged for user confirmation at the spec-review gate."
    - "Automated Zenodo deposition / DOI minting / dataset upload — v0.2. The Zenodo_db/ folder is the LOCAL data-authority layout only; actual Zenodo API deposition is future work."
    - "Python-side formula EVALUATION (formulas/pycel) or LibreOffice-headless recalc — rejected (D4). v0.1 reads cached values and fails loud."
    - "VLM verification as a separate rostered vision agent — v0.2. v0.1 VLM self-check is plot-maker reading its own rendered PNG via the native multimodal Read tool, opt-in (D7)."
    - "LaTeX/TikZ figure output — v0.2. v0.1 plot-maker emits raster + vector (PNG/PDF/SVG) via matplotlib."
    - "Paid literature APIs (iThenticate, Dimensions, Web of Science) — out of scope; v0.1 uses free tiers of Semantic Scholar / CrossRef / OpenAlex + PubMed + Zotero."
    - "Embedding-based semantic literature ranking — v0.2. v0.1 ranking is title/abstract relevance + citation-count + recency heuristics."

deliverables:
  scripts:
    - scripts/sws_semantic_scholar.py      # WebFetch/curl + parser. title-fuzzy-match (Levenshtein >=0.70), DOI verify, citation-graph traversal, abstract fetch. Caching + 429 backoff (cycle-09 R1 discipline).
    - scripts/sws_crossref.py              # CrossRef DOI resolver + metadata; fallback for bibliography-curator
    - scripts/sws_openalex.py              # OpenAlex metadata; non-CS-friendly alternative to Semantic Scholar
    - scripts/sws_data_manifest.py         # build/update Zenodo_db/manifest.json (dataset -> script -> figure provenance); atomic write
    - scripts/sws_xlsx_resolve.py          # wraps sws_read_xlsx.py; reads cached values; FAIL-LOUD with actionable message when a formula cell has no cached value (D4)
    - scripts/sws_plot_runner.py           # injects rcParams (>=8pt font floor + column-width figsize), execs the user's plot script unmodified, introspects the figure for font-floor + width-bounds compliance, saves to figures/, records width+min-font in manifest (D6a)
  references:
    - references/zenodo-db-layout.md       # the locked Zenodo_db/ layout + manifest.json schema (dataset->script->figure)
    - references/literature-sources.md     # the 5-source fallback chain + which agent uses which + rate-limit/caching policy
  agents:
    - agents/data-curator.md               # Sonnet 4.6 high (roster #18). Ingests Zenodo_db/ xlsx via sws_xlsx_resolve.py; emits the data manifest; never re-derives formulas.
    - agents/plot-maker.md                 # Sonnet 4.6 high (roster #17). Generates figures via co-located scripts; sizes from journal-style overlay; opt-in --verify VLM self-check.
    - agents/literature-searcher.md        # Sonnet 4.6 high (roster #5). DISCOVERY: find new sources. Zotero-first -> PubMed/Semantic Scholar. NLM deferred (D9).
    - agents/bibliography-curator.md       # Sonnet 4.6 high (roster #19). AUDIT: validate existing citations; dedup; fix DOIs; format to refs_style. Zotero-first; CrossRef/OpenAlex fallback.
  skills:
    - skills/curate-data/SKILL.md          # /sws:curate-data
    - skills/make-figure/SKILL.md          # /sws:make-figure  (--verify for VLM self-check)
    - skills/search-literature/SKILL.md    # /sws:search-literature
    - skills/audit-bibliography/SKILL.md   # /sws:audit-bibliography
  profile_updates:
    - profiles/full-article.md             # data-curator + plot-maker + literature-searcher + bibliography-curator ACTIVE
    - profiles/communication.md            # data-curator + plot-maker + literature-searcher + bibliography-curator ACTIVE
    - profiles/methodological-paper.md     # all 4 ACTIVE
    - profiles/review-paper.md             # plot-maker (schematic/summary figs) + literature-searcher + bibliography-curator ACTIVE; data-curator INACTIVE (reviews don't curate raw data)
    - profiles/mini-review.md              # same as review-paper
    - profiles/perspective.md              # literature-searcher + bibliography-curator ACTIVE; data-curator + plot-maker INACTIVE
    - profiles/editorial.md                # literature-searcher + bibliography-curator ACTIVE; data-curator + plot-maker INACTIVE (preserves cycle-07 drop)
    - profiles/commentary-reply.md         # bibliography-curator ACTIVE; literature-searcher exec-tunable; data-curator + plot-maker INACTIVE
    - profiles/funding-proposal.md         # literature-searcher + bibliography-curator ACTIVE; data-curator + plot-maker INACTIVE (preliminary-data figures handled manually in v0.1)
  reference_updates:
    - references/agent-contract.md         # R3 I/O inventory: Zenodo_db/{data,scripts,figures,manifest.json,_archive}/ shapes; refs/_lit-search/ + _review/bibliography-audit/ outputs
  memory_updates:
    - claude_memory/project_v02_backlog.md          # new entries: Zenodo deposition/DOI minting, VLM vision agent, LaTeX/TikZ figures, embedding lit-ranking, paid APIs
    - claude_memory/project_cycle_execution_status.md  # cycle #11 -> merged at end of PR
  tests:
    - tests/test_xlsx_resolve.py           # cached-value read; FAIL-LOUD on un-cached formula cell (asserts the actionable message verbatim)
    - tests/test_data_manifest.py          # manifest round-trip; dataset->script->figure linkage; atomic update
    - tests/test_plot_runner.py            # D6a: rcParams font floor applied; figure <8pt text -> FAIL with offending elements; width outside {7.5cm | 12-16cm} -> FAIL; valid figure -> PASS + width/min-font recorded
    - tests/test_semantic_scholar.py       # parser vs captured fixture responses (NO live network); fuzzy-match threshold; backoff path
    - tests/test_crossref.py               # DOI resolve vs captured fixtures
    - tests/test_openalex.py               # metadata parse vs captured fixtures
    - tests/test_bibliography_refs_format.py  # format to a journal refs_style; dedup; flag unresolved DOIs
    - tests/test_profile_activation_data_lit.py  # the 4-agent activation matrix across 9 profiles
    - tests/smoke_cycle_11.sh              # curate-data -> make-figure -> search-literature -> audit-bibliography against the fixture

locked_decisions:
  D1: |
    One PR, all 4 rostered agents (data-curator #18, plot-maker #17, literature-searcher #5, bibliography-curator #19),
    all Sonnet 4.6 high. Matches the roadmap's "Data + literature wave (4 agents)" bundle and is within cycle-#7 (7 agents) /
    cycle-#8 (5 agents) sizes.
    Rationale: user instruction 2026-05-22 — keep the wave as one cycle/PR/spec/smoke; the data/literature seam does not justify
    the overhead of splitting into 11a/11b.

  D2: |
    4 skills: /sws:curate-data, /sws:make-figure (--verify opt-in VLM), /sws:search-literature, /sws:audit-bibliography.
    All atomic; no orchestrator this cycle (the wave's steps are independent utilities, unlike the revise/review pipelines).
    Rationale: these agents serve different phases (Data, Data, Plan, Submit); an orchestrator would force an unnatural ordering.

  D3: |
    literature-searcher vs bibliography-curator boundary (no overlap):
      literature-searcher = DISCOVERY. Find NEW relevant sources for a topic/section (input to drafting). Plan phase.
        Output: refs/_lit-search/<slug>.md — ranked candidates with title/authors/year/DOI/abstract + why-relevant.
      bibliography-curator = AUDIT. Validate the manuscript's EXISTING citations (pre-submission hygiene). Submit phase.
        Output: _review/bibliography-audit/{report.md, fixes.json} — unresolved DOIs, duplicates, format deviations vs refs_style.
    Rationale: discovery and hygiene are distinct jobs at opposite ends of the workflow; conflating them produces a vague agent.

  D4: |
    data-curator xlsx formula resolution = READ CACHED, FAIL LOUD. sws_xlsx_resolve.py (wrapping cycle-#7 sws_read_xlsx.py)
    reads the value the spreadsheet app last cached (openpyxl data_only). If a formula cell has NO cached value, the script STOPS
    with an actionable message: "Cell <sheet>!<ref> is a formula with no cached value. Open and save this workbook in Excel or
    LibreOffice so values cache, then re-run /sws:curate-data." NEVER re-derive or guess. Honors xlsx-as-data-authority.
    Rejected: Python evaluation (formulas/pycel — incomplete Excel-function coverage, silent wrong numbers on scientific data);
    LibreOffice-headless recalc (heavy/fragile external dep).
    Rationale: user instruction 2026-05-22 + feedback_openpyxl_formulas.md — a wrong number in scientific data is catastrophic;
    the spreadsheet is authoritative and we must not silently re-compute it.

  D5: |
    Zenodo_db/ layout LOCKED:
      Zenodo_db/data/        # source xlsx (the data authority) + raw exports
      Zenodo_db/scripts/     # fit + plot scripts, co-located with the data they consume
      Zenodo_db/figures/     # plot-maker outputs (PNG/PDF/SVG), regenerable
      Zenodo_db/manifest.json # provenance spine: each entry links dataset file -> script -> figure(s)
      Zenodo_db/_archive/    # superseded data/figure versions, timestamped
    Marker-scoped; writes pass through the cycle-#5 backup hook. manifest.json is the single source of figure provenance — a
    figure is always traceable to its data + the script that made it.
    Rationale: arch sketch §Zenodo_db (lines 168-171) extended with figures/ + manifest.json for reproducibility/traceability.

  D6: |
    plot-maker: matplotlib in the per-paper venv. Reads the RESOLVED journal-style overlay for figure dimensions, format, and
    font constraints — NO hardcoded sizes. Fit + plot scripts are CO-LOCATED in Zenodo_db/scripts/ and recorded in manifest.json,
    NEVER inlined into the agent prompt (so they are re-runnable and version-controllable by the user).
    Rationale: figures must meet journal specs (which live in the overlay) and stay reproducible from committed scripts.

  D6a: |
    FIGURE-READABILITY RULE (always enforced, self-checked) — user instruction 2026-05-23:
      (a) FONT FLOOR: every text element (axis labels, tick labels, legend, annotations, titles) >= 8 pt; target 9 pt.
          Enforced via an rcParams floor applied before the user's plot script runs.
      (b) WIDTH: single-column = 7.5 cm, OR double-column = 12-16 cm (16 cm hard max). Converted to inches for figsize
          (7.5 cm = 2.953 in; 12 cm = 4.724 in; 16 cm = 6.299 in). Height is free (respect the script's aspect ratio).
      The resolved journal-style overlay may specify exact column widths; when present they WIN, but must still fall within
      these bounds (1-col ~ 7.5 cm; 2-col 12-16 cm) and the >= 8 pt font floor ALWAYS applies regardless of overlay.
    Mechanism — scripts/sws_plot_runner.py (NEW, makes the rule unit-testable, closes the cycle-11 plan flag):
      - Injects rcParams (font floor + chosen figsize width) then runs the user's co-located plot script via exec (the script
        is NOT modified on disk — the runner sets the environment around it).
      - After the figure is built, INTROSPECTS it: asserts figure width is in the allowed set/bounds and that every text
        artist's effective font size >= 8 pt. Returns a machine-readable pass/fail + the offending elements.
      - Saves the figure to Zenodo_db/figures/ and records the width + min-font in the manifest entry.
    Rationale: paper figures are unreadable when text shrinks on column-fit or when widths are arbitrary; a deterministic
    runner enforces the floor + width bounds reproducibly and makes the check testable without the agent runtime.

  D7: |
    plot-maker optional VLM self-check (opt-in via --verify). After rendering, the agent reads the PNG back via the NATIVE
    multimodal Read tool and self-checks: axis labels present, no overlapping elements, legend correct, data matches the manifest
    entry. The DETERMINISTIC font-floor + width checks from D6a run ALWAYS (independent of --verify); --verify adds the
    qualitative VLM pass on top. No extra dependency; no separate vision agent. --verify OFF by default.
    Rationale: arch sketch names "optional VLM verification"; native Read makes it dependency-free; opt-in keeps the default path
    cheap. The D6a numeric checks are cheap + deterministic so they are never gated behind --verify. A dedicated vision agent is v0.2.

  D8: |
    External wiring (MCP-aversion honored). New scripts via WebFetch/curl + parsers: sws_semantic_scholar.py, sws_crossref.py,
    sws_openalex.py. PubMed stays on the existing claude_ai_PubMed MCP (the documented v0.1 exception — no first-class CLI).
    Zotero via the existing zotero skill. Fallback chain (reference_external_tools.md): Zotero first -> Semantic Scholar / PubMed
    -> (NLM deferred, D9); CrossRef / OpenAlex for DOI + metadata gaps. All scripts cache aggressively + back off on 429
    (cycle-#9 R1 discipline).
    Rationale: prefer zero-context-cost CLI/Bash paths over MCP token overhead; reuse the locked fallback chain.

  D9: |
    NLM consumer wiring DEFERRED. nlm-librarian (roster #22, Infra) and the NLM grounded-RAG path for literature-searcher and
    bibliography-curator do NOT ship in this cycle. The roadmap places NLM integration LAST (current cycle #13). Both agents
    degrade gracefully without NLM (use Zotero/PubMed/Semantic Scholar/CrossRef/OpenAlex only; never fail).
    LOCKED 2026-05-23 (user confirmation): NLM/nlm-librarian ships in CURRENT cycle #13 (the roadmap's "NLM integration, last"),
    NOT here. The cycle-#9 spec prose that said "NLM in cycle #11" used the ORIGINAL roadmap numbering (original #11 = current #13).
    Rationale: conservative alignment with the roadmap's "NLM integration, last"; avoids shipping the infra agent early.

  D10: |
    Per-profile activation matrix for the 4 agents (extends cycle-#7/#8/#9 matrices). Defaults (exec-tunable):
      data-curator + plot-maker:   ACTIVE in [full-article, communication, methodological-paper]; plot-maker ALSO active in
                                   [review-paper, mini-review] for schematic/summary figures (data-curator inactive there);
                                   BOTH inactive in [perspective, editorial, commentary-reply, funding-proposal].
      literature-searcher:         ACTIVE in [full-article, communication, perspective, review-paper, mini-review,
                                   methodological-paper, editorial, funding-proposal]; exec-tunable in [commentary-reply].
      bibliography-curator:        ACTIVE in all 9 (every profile has a bibliography to audit).
    Rationale: data curation/plotting belong to data-bearing profiles; reviews remake summary figures but don't curate raw data;
    literature discovery is broadly useful; citation hygiene is universal. Preserves the cycle-#7 editorial drop.

  D11: |
    I/O contract (agent-contract R3 extension):
      data-curator   READS Zenodo_db/data/*.xlsx via sws_xlsx_resolve.py; WRITES Zenodo_db/manifest.json via sws_data_manifest.py.
      plot-maker     READS curated data + Zenodo_db/scripts/*; WRITES Zenodo_db/figures/* + updates manifest.json atomically.
      literature-searcher  READS Zotero (skill) + PubMed/S2; WRITES refs/_lit-search/<slug>.md.
      bibliography-curator READS the manuscript bibliography + Zotero/CrossRef/OpenAlex; WRITES _review/bibliography-audit/{report.md, fixes.json}.
    No agent writes the manuscript .docx (Review-Then-Act — these are diagnostic/asset agents). bibliography-curator proposes
    fixes in fixes.json; applying them to the .docx is a style-enforcer/reviser concern, not this cycle.
    Rationale: keeps assets + reports durable on the filesystem; preserves the write-boundary discipline.

  D12: |
    Testing (honors feedback_integration_smoke.md):
      Unit: xlsx fail-loud (verbatim message); manifest round-trip + linkage; plot-runner font-floor + width-bounds (D6a);
            the 3 API parsers vs CAPTURED fixture responses (no live network); refs formatting to a journal refs_style + dedup +
            unresolved-DOI flagging; activation matrix.
      Fixtures: a tiny Zenodo_db/ with one xlsx (cached values + ONE un-cached formula cell to trigger fail-loud) and one fit
            script; a plot script that draws a labelled figure; captured JSON for Semantic Scholar / CrossRef / OpenAlex; a small Zotero export.
      tests/smoke_cycle_11.sh: curate-data -> make-figure -> search-literature -> audit-bibliography against the fixture; assert
            manifest links data->script->figure, fail-loud fires on the un-cached cell, a figure file is produced with all text
            >= 8 pt and width in {7.5cm | 12-16cm} (D6a), and the bibliography audit resolves/flags DOIs.
    Rationale: captured fixtures keep the smoke offline + reproducible while exercising every code path.

  D13: |
    v0.2 backlog additions: (1) automated Zenodo deposition / DOI minting; (2) VLM verification as a separate rostered vision
    agent; (3) LaTeX/TikZ figure output; (4) embedding/SPECTER2 semantic literature ranking; (5) paid literature APIs (Dimensions,
    Web of Science) opt-in; (6) auto-apply bibliography-curator fixes to the .docx via style-enforcer.
    Rationale: explicit deferrals captured for future-self; prevents scope creep within cycle #11.

risks:
  R1: |
    External API rate limits (Semantic Scholar / CrossRef / OpenAlex free tiers).
    Mitigation: aggressive per-DOI/per-query caching + exponential backoff on 429 (cycle-#9 R1 discipline); Zotero-first means
    most lookups never hit the network; captured fixtures keep tests offline.
  R2: |
    matplotlib figures may have quality defects (overlapping labels, wrong sizing) that pass silently without VLM.
    Mitigation: --verify opt-in VLM self-check (D7); journal-overlay-driven sizing (D6) removes the most common spec violations;
    document that --verify is recommended before submission.
  R3: |
    Fail-loud on un-cached formula cells could frustrate users with formula-heavy workbooks.
    Mitigation: the message is specific (names the cell + the exact fix) and one open-save resolves the whole workbook; this is
    strictly safer than silently shipping a wrong number. Documented in the skill README.
  R4: |
    manifest.json drift — figures regenerated but provenance stale, or scripts edited out-of-band.
    Mitigation: make-figure ALWAYS updates manifest.json atomically in the same step; sws_data_manifest.py validates linkage and
    flags orphaned figures/scripts.
  R5: |
    NLM numbering ambiguity (D9) could cause the executor to ship nlm-librarian early or omit a wiring the user expected.
    Mitigation: D9 flags it explicitly for user confirmation at the spec-review gate before the plan is written.

execution:
  approach: "Same dispatch flow as cycles #7-#10: user approves spec -> planner skill writes implementation plan -> subagent-driven execution -> PR opened, user merges."
  parallelism: "Phases sequential (scripts+references -> agents -> skills -> profiles -> tests -> smoke). Within phases, independent files parallelizable: the 3 external-API scripts, the 4 agents, the 4 skills, the 9 profile edits."
  expected_pr_size: "Comparable to cycle #9 (~25-35 commits). 4 agents + 4 skills + 5 scripts + 2 references + 9 profile edits + ~45 unit tests + smoke."
  beta_test_phase: "Optional: run /sws:curate-data + /sws:make-figure against a real Zenodo_db from a prior manuscript to validate the fail-loud path and journal-overlay sizing on genuine data. User-approved before treating the wave as production-ready."
---

# Cycle #11 — Data + literature wave

End-of-cycle goal: a paper's data, figures, literature discovery, and citation hygiene are all SWS-managed. `data-curator` makes the `Zenodo_db/` xlsx the data authority (refusing to guess at un-cached formulas), `plot-maker` turns curated data into journal-sized figures from co-located scripts, `literature-searcher` finds new sources, and `bibliography-curator` audits the existing bibliography for resolution, duplication, and format compliance.

This spec follows the cycle-#7/#8/#9/#10 dispatch flow. All locked decisions live in the frontmatter `locked_decisions:` block (D1–D13). The body is orientation only — the frontmatter is the project-memory dictionary.

## The two seams that shape the cycle

**Data authority.** The spreadsheet is the source of truth, and SWS must never silently re-derive it. `data-curator` reads the values the spreadsheet app cached; if a formula cell has no cached value, it stops and tells the user exactly which cell and exactly how to fix it (open + save). A wrong number in a chemistry manuscript is worse than a halt. `plot-maker` then draws only from curated data, through scripts that live next to that data in `Zenodo_db/scripts/` and are recorded in `manifest.json`, so every figure is reproducible and traceable to its source.

**Discovery vs hygiene.** `literature-searcher` and `bibliography-curator` sit at opposite ends of the workflow and never overlap: the first *finds new sources* to inform drafting; the second *validates the citations already in the manuscript* before submission. Keeping them distinct keeps each agent sharp.

## External wiring without MCP bloat

Three small scripts (`sws_semantic_scholar.py`, `sws_crossref.py`, `sws_openalex.py`) reach the web sources via WebFetch/curl + parsing, honoring the MCP-aversion principle. PubMed stays on its existing MCP (the documented exception — no first-class CLI), and Zotero stays first in the fallback chain so most lookups never touch the network. All scripts cache and back off, reusing the cycle-#9 rate-limit discipline.

## One thing to confirm before planning

The memory has a numbering ambiguity about `nlm-librarian`: the cycle-#9 spec prose said NLM wiring lands "in cycle #11," but that used the original roadmap numbering, where NLM was original-#11 = **current #13** (the roadmap's explicit "NLM integration, last"). This spec keeps `nlm-librarian` and NLM grounded-RAG OUT of cycle 11 and lets `literature-searcher` / `bibliography-curator` degrade gracefully without it (D9). If you intended NLM to ship here instead, that's the one decision to flip at the review gate.

## Cross-cutting compliance

- **Agent-contract R1:** each agent sources `agent_prelude.sh` + calls `agent_should_run.sh <id>`.
- **Agent-contract R3:** xlsx via `sws_xlsx_resolve.py`/`sws_read_xlsx.py`; figures + manifest written under `Zenodo_db/`; lit-search + audit outputs under `refs/_lit-search/` and `_review/bibliography-audit/`. No agent writes the manuscript `.docx`.
- **Agent-contract R5:** no gender-default in user address.
- **MCP-aversion:** Semantic Scholar / CrossRef / OpenAlex via scripts; PubMed via the existing MCP; no new MCP server.
- **Profile-aware activation:** the 4-agent matrix per D10; preserves the cycle-#7 editorial drop.
- **Review-Then-Act:** these are diagnostic/asset agents; bibliography fixes are proposed in `fixes.json`, not applied to the manuscript.
