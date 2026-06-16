---
sws_artifact: cycle-13-spec
artifact_version: 0.1
locked: 2026-05-30
title: "Cycle #13 — NLM integration (nlm-librarian agent #22 Sonnet 4.6 high; sws_nlm.sh CLI wrapper for jacob-bd/notebooklm-mcp-cli — NEVER as MCP; notebooklm.enabled marker-flag wiring; 5 consumer agents updated to dispatch when enabled + degrade gracefully when disabled; final v0.1 banner flip). LAST CYCLE of v0.1."

cycle_index: 13
original_roadmap_index: 11
predecessor: cycle-12-submission-orchestration
banner_after_completion: "v0.1"
version_after_completion: "0.1.0"

autonomous_run_caveat: |
  Cycle #13 was executed autonomously on 2026-05-30 with the user's explicit grant of authority
  ("conclude unattended all the cycles remaining until full 0.1 deploy"). Every locked decision
  carries a rationale so the user can re-decide any of them before the PR merges. The PR is
  opened in READY (not draft) state since this is the final v0.1 cycle and the user has
  asked for end-to-end deploy preparation; the user merges manually per established cycle-#3-onwards
  pattern.

sources:
  architecture_sketch: |
    docs/superpowers/specs/2026-05-08-architecture-sketch-design.md §7 cycle table line 492 ('NLM integration (opt-in, last)':
    nlm-librarian agent, CLI invocation pattern (Bash tool, not MCP), notebooklm.enabled marker-flag wiring,
    verification that all 5 consumer agents degrade gracefully when disabled. End-of-#11/cycle becomes 'v0.1' banner).
    Also §Zenodo_db / refs/ layout line 184 (refs/nlm_uploads/ — curated corpus for nlm-librarian ingestion).
    Also §External integrations line 380 (notebooklm-mcp-cli — invoked as CLI binary via Bash, gated by
    notebooklm.enabled marker flag; MCP-aversion principle).
  prior_cycle_anchors:
    - "cycle-02 marker schema: notebooklm.enabled boolean field already present (default false)"
    - "cycle-02 init-project: refs/nlm_uploads/ already created when notebooklm.enabled=true (sws_init_project.py L313)"
    - "cycle-06 resolver: notebooklm.* keys NOT YET in resolve_overlay.py defaults — cycle-13 adds them"
    - "cycle-06 agent_prelude.sh: exports RESOLVED_DISCLOSURE_REQUIRED etc.; cycle-13 adds RESOLVED_NOTEBOOKLM_ENABLED"
    - "cycle-07: drafter-flagship + drafter-fast + proposal-compliance-helper listed as NLM consumers in roster; drafter agents lack the deferred-stub but proposal-compliance-helper has it"
    - "cycle-09: claim-verifier ships with NLM-deferred stub + notebooklm_enabled: false frontmatter"
    - "cycle-11: literature-searcher + bibliography-curator ship with NLM-deferred stub (D9 of cycle-11)"
    - "cycle-12: cycle-execution-status / spec frontmatter dictionary pattern preserved"
  related_memory:
    - "claude_memory/project_roster_v0.1.md (#22 nlm-librarian Sonnet 4.6 high; the 5 consumers: #5 literature-searcher, #6 drafter, #15 claim-verifier, #19 bibliography-curator, #24 proposal-compliance-helper)"
    - "claude_memory/reference_external_tools.md (MCP-aversion: prefer CLI over MCP when alternative exists; jacob-bd/notebooklm-mcp-cli is the locked binary; PubMed stays as MCP exception)"
    - "claude_memory/feedback_subagent_dispatch.md (consumers dispatch to nlm-librarian instead of calling the CLI directly — single point of contact)"
    - "claude_memory/feedback_integration_smoke.md (smoke_cycle_13.sh = canonical e2e verification including degrade-gracefully assertions)"
    - "claude_memory/feedback_lean_deliverables.md (frontmatter = dictionary, body = orientation)"

scope:
  deliverable: "v0.1 ships. nlm-librarian agent + sws_nlm.sh CLI wrapper land; all 5 consumer agents are wired to dispatch to nlm-librarian when notebooklm.enabled=true and degrade gracefully when false; refs/nlm_uploads/ is documented as the curated-corpus directory; agent_prelude.sh exports RESOLVED_NOTEBOOKLM_ENABLED + RESOLVED_NLM_NOTEBOOK_ID; resolve_overlay.py defaults include the notebooklm.* keys. Banner flips to 'v0.1' and plugin version to '0.1.0'. End-state: a complete docx-first scientific-writing toolkit usable end-to-end via /sws:run-cycle (cycle-12), with NotebookLM RAG as an optional grounded-citation layer for the user who installs the notebooklm-mcp-cli binary."
  not_in_scope:
    - "Bundling notebooklm-mcp-cli with SWS — it's a third-party MIT binary; users opt-in via separate install (npm/pipx/binary). sws_nlm.sh detects absence and degrades."
    - "NotebookLM upload automation (file ingestion into NLM corpora) — manual user action in v0.1. nlm-librarian QUERIES an existing notebook; the user populates refs/nlm_uploads/ and runs the upload themselves. Automating that is v0.2."
    - "MCP-server invocation of NotebookLM — explicitly forbidden by the MCP-aversion principle. The notebooklm-mcp-cli MCP-server mode is NOT used; only its CLI mode is."
    - "Persisting NLM query history — v0.1 nlm-librarian is stateless within a session. v0.2 may add a query log under refs/_nlm-cache/."
    - "Inline NLM answer-citation tagging into the manuscript — v0.1 nlm-librarian returns answers + source-passage references; the calling consumer agent decides whether/how to thread them into draft prose. v0.2 may add a citation-injection helper."
    - "Per-notebook authentication / token management beyond what notebooklm-mcp-cli already supports — SWS does not store NLM credentials; sws_nlm.sh inherits the CLI's auth pattern."
    - "Funding-proposal-compliance NLM grounding against funding-call PDFs (proposal-compliance-helper consumer) — wired this cycle, but the v0.1 user-experience expects the user to upload the funding call PDF to a NotebookLM notebook themselves; nlm-librarian only queries it."

deliverables:
  scripts:
    - scripts/sws_nlm.sh                # bash wrapper around notebooklm-mcp-cli; subcommands: probe (detect binary + auth), query (ask the configured notebook), list-notebooks (enumerate); exits non-zero with explicit message when binary missing or notebooklm.enabled=false
  references:
    - references/nlm-librarian-pattern.md  # the consumer-dispatch contract: when to call, how to pass query, how to consume the return, how to degrade
  agents:
    - agents/nlm-librarian.md           # Sonnet 4.6 high (roster #22). Sole owner of sws_nlm.sh dispatch. All 5 consumers route through it.
  agent_updates:
    - agents/drafter-flagship.md        # wire NLM consumer path (when notebooklm.enabled=true): dispatch to nlm-librarian for grounded-RAG context against the user's research corpus. Was UNDOCUMENTED in v0.1 (D2); becomes documented + active.
    - agents/drafter-fast.md            # same pattern, mirrored
    - agents/literature-searcher.md     # promote the "NLM grounded-RAG: DEFERRED" stub (line 31-32) to an actual dispatch path; renumber cycle-11 reference → cycle-13; update notebooklm_enabled frontmatter to "dynamic" (reads marker)
    - agents/claim-verifier.md          # same: promote NLM degraded mode (line 28) from "Currently never called" to actual dispatch path; renumber cycle-11 → cycle-13
    - agents/bibliography-curator.md    # same: promote NLM step (line 27) from DEFERRED to active when enabled
    - agents/proposal-compliance-helper.md  # same: replace "When nlm-librarian ships in cycle #11" forward-ref (line 18) with documented active dispatch
  resolver_updates:
    - scripts/resolve_overlay.py        # add to schema_defaults: notebooklm.enabled (false), notebooklm.notebook_id (null), notebooklm.cli_path (null=detect-on-PATH)
    - scripts/agent_prelude.sh          # export RESOLVED_NOTEBOOKLM_ENABLED + RESOLVED_NLM_NOTEBOOK_ID + RESOLVED_NLM_CLI_PATH from the resolved overlay (mirrors the existing RESOLVED_* exports pattern)
  reference_updates:
    - references/marker-schema.md       # extend notebooklm.* sub-keys (already has .enabled; add .notebook_id + .cli_path documentation)
    - references/agent-contract.md      # R3 I/O inventory adds refs/nlm_uploads/ (curated corpus dir) + nlm-librarian return-shape (answer + sources[] list)
  banner_updates:
    - README.md                         # 🧪 v0.1 alpha → v0.1; remove the "remaining v0.1 cycles" sentence; add a "v0.1 ships" paragraph
    - .claude-plugin/plugin.json        # version "0.1.0-alpha" → "0.1.0"
  memory_updates:
    - claude_memory/project_v02_backlog.md          # 6 new entries (NLM upload automation, NLM query history cache, inline citation-injection from NLM answers, per-notebook auth/token mgr in SWS, NLM bundled binary, multi-notebook query routing)
    - claude_memory/project_cycle_execution_status.md  # cycle #13 → merged at end of PR; banner state flips
    - claude_memory/reference_external_tools.md     # confirm notebooklm-mcp-cli wired (no longer "planned")
  tests:
    - tests/test_sws_nlm_wrapper.py     # CLI wrapper: probe detects missing binary (exit 4); probe detects notebooklm.enabled=false (exit 0 with "disabled" message); query passes args through to fake-binary-on-PATH; query degrades to exit 5 with hint when binary missing AND enabled=true
    - tests/test_nlm_librarian_dispatch.py  # contract: nlm-librarian agent file references sws_nlm.sh (not MCP); frontmatter notebooklm_enabled is "dynamic" (reads marker); per-consumer dispatch pattern documented
    - tests/test_consumer_nlm_degrade.py    # for each of the 5 consumers, assert: (a) prompt body mentions notebooklm.enabled gate; (b) absent NLM never raises; (c) NLM-disabled fallback path explicit; (d) cycle-13 numbering corrected
    - tests/test_resolve_overlay_notebooklm.py  # resolver defaults include notebooklm.enabled=false; user overlay can flip it; agent_prelude exports the 3 env vars correctly
    - tests/test_banner_v01.py              # README banner reads "v0.1" (no "alpha", no "🧪"); plugin.json version is "0.1.0"
    - tests/smoke_cycle_13.sh               # e2e: probe with no binary -> exit 4; probe with marker disabled -> exit 0 disabled; resolver + prelude pipeline yields RESOLVED_NOTEBOOKLM_ENABLED; banner assertions

locked_decisions:
  D1: |
    One PR. nlm-librarian agent + sws_nlm.sh wrapper + 5 consumer-agent wiring updates + resolver/prelude
    extensions + banner flip — all in one branch cycle/13-nlm-integration.
    Rationale: matches roadmap line 492 bundle exactly. Atomic — the banner flip MUST land with the
    consumer wiring, since flipping to v0.1 with consumers still saying "deferred to cycle #13" would
    be incoherent.

  D2: |
    drafter-flagship + drafter-fast were listed as NLM consumers in the roster (architecture-sketch
    §7 + roster #6) but their cycle-7 implementation never added the deferred-stub language (unlike
    claim-verifier/literature-searcher/etc.). Cycle-13 corrects this: both drafter agents gain the
    same notebooklm.enabled-gated dispatch + degrade-gracefully path as the other consumers.
    Rationale: completeness over consistency. The architecture sketch named 5 consumers; v0.1 cannot
    ship with only 3 of them actually wired.

  D3: |
    sws_nlm.sh subcommands (locked v0.1 surface area):
      probe                 — exit 0 if (notebooklm.enabled=true AND binary on PATH AND auth OK);
                              exit 4 if binary missing;
                              exit 5 if binary present but unconfigured;
                              exit 0 with "disabled" message if notebooklm.enabled=false
      query <question> [--notebook <id>]
                            — pass to notebooklm-mcp-cli CLI mode; returns JSON {answer, sources[]}
                              on stdout; exit 5 if probe would fail
      list-notebooks        — enumerate user's notebooks via notebooklm-mcp-cli; exit 5 if probe fails
    No other subcommands ship in v0.1. The 3 cover the dispatch surface that nlm-librarian needs.
    Rationale: lean surface area; expansion (upload, delete, search-history) belongs to v0.2.

  D4: |
    notebooklm-mcp-cli binary discovery order (in sws_nlm.sh probe):
      1. Marker file notebooklm.cli_path (absolute path) if set
      2. $PATH lookup for `notebooklm-mcp-cli`
      3. $PATH lookup for `notebooklm` (alternate binary name some installs use)
    If none found, exit 4 with message: "notebooklm-mcp-cli binary not found. Install: npm install -g
    notebooklm-mcp-cli OR pipx install notebooklm-mcp-cli (see references/nlm-librarian-pattern.md).
    Then re-run /sws:init-project to refresh marker, or set notebooklm.cli_path manually."
    Rationale: the binary name varies across installers and forks; PATH-first with explicit override
    is the standard pattern.

  D5: |
    nlm-librarian is the SOLE OWNER of sws_nlm.sh dispatch. No other agent calls sws_nlm.sh directly.
    The 5 consumer agents call nlm-librarian (which calls sws_nlm.sh).
    Rationale: single point of contact = single point of error handling = single point of degrade-
    gracefully behavior. Mirrors the cycle-07/cycle-11 single-owner pattern (sws_read_docx.py is
    called by every consumer agent through R3, but all error handling lives in the wrapper itself —
    here, the single-owner is at the agent layer, not the script layer, because the dispatch has
    LLM-mediated query refinement that the script can't do).

  D6: |
    notebooklm.enabled gate semantics:
      enabled = false  → every consumer skips the NLM step and prints a one-line notice. NO error.
                         No "ask user to enable NLM" prompting (users decide their own opt-in).
      enabled = true + binary missing → consumers print "NLM enabled but binary missing — install
                                        notebooklm-mcp-cli; proceeding without NLM" and continue.
      enabled = true + binary present + auth OK → consumers dispatch nlm-librarian and consume answer.
      enabled = true + binary present + auth failed → consumers print "NLM auth failed; check the
                                                      tool's auth setup and re-run" and continue.
    Rationale: NLM is an enhancement, never a hard dependency. NEVER fail a consumer's main job
    because of NLM trouble. This is the explicit "degrade gracefully" contract from the architecture
    sketch §7 line 492.

  D7: |
    refs/nlm_uploads/ stays directory-only in v0.1 — no schema for what goes inside, no SWS-managed
    manifest. Users drop PDFs, prior notes, draft sections, related papers as they see fit;
    nlm-librarian assumes the user has uploaded these (or others) to the configured NotebookLM
    notebook outside SWS.
    Rationale: SWS does not upload to NotebookLM (out-of-scope). The dir is a colocated staging
    area for the user's own ingestion workflow. v0.2 may add upload-automation.

  D8: |
    nlm-librarian return JSON contract:
      {
        "ok": true|false,
        "answer": "natural-language answer from NLM",       # only when ok=true
        "sources": [ { "title": "...", "snippet": "...", "page": <int or null> }, ... ],
        "notebook_id": "...",
        "query": "the question asked",
        "fallback": "none|disabled|missing|auth|error",     # explains why ok=false
        "fallback_message": "..."                          # one-line for the consumer to surface
      }
    The 5 consumers parse this JSON and incorporate `answer` + `sources` into their workflow when
    ok=true. When ok=false, they print fallback_message and proceed without NLM.
    Rationale: structured return is essential — consumers each have specific places where the NLM
    answer slots in (drafter: as additional context; claim-verifier: as a 5th verification source;
    literature-searcher: as a 4th discovery channel; bibliography-curator: as a metadata fallback;
    proposal-compliance-helper: as the primary grounding against the funding call PDF).

  D9: |
    Resolver schema_defaults extension (additive):
      notebooklm:
        enabled: false
        notebook_id: null
        cli_path: null
    The dot-notation (notebooklm.enabled) was the original marker-schema convention but cycle-06
    resolve_overlay.py uses nested-key dict access; cycle-13 adds the nested form to schema_defaults
    and the resolver flattens it via the existing _flatten() helper to RESOLVED_NOTEBOOKLM_ENABLED.
    Rationale: matches the existing nested-key convention from cycle-06. Backward-compatible.

  D10: |
    All 5 consumer agents update their YAML frontmatter:
      notebooklm_enabled: false   →   notebooklm_enabled: dynamic
    Meaning: the agent reads the marker file / RESOLVED_NOTEBOOKLM_ENABLED env var at runtime to
    decide whether the NLM step is active. The literal value "dynamic" replaces the cycle-09/11
    placeholder "false" (which originally meant "deferred, never call").
    Rationale: makes the frontmatter accurate again. Tests assert the literal "dynamic" string.

  D11: |
    Banner-flip + version-bump constraints:
      README.md banner block: "🧪 **v0.1 alpha** ..." → "**v0.1** — the SWS plugin's first stable
      release. All 13 cycles of the v0.1 roadmap have shipped: ..."
      The "remaining v0.1 cycles" sentence is removed.
      A short "What v0.1 means" paragraph is added (mirrors typical 0.1 release-note patterns):
      24 agents shipped; docx-first track usable end-to-end; NotebookLM opt-in; tests > 800.
      plugin.json version: "0.1.0-alpha" → "0.1.0"
      No SemVer change to the API surface; this is the final pre-1.0 release that proves the design
      end-to-end.
    Rationale: the banner is the user-facing signal that v0.1 is real. Half-flipped banners
    (saying alpha but listing all features done) are confusing.

  D12: |
    No new SLASH COMMAND ships in cycle-13. nlm-librarian is not directly user-invocable — it is
    dispatched by other agents through the consumer-dispatch contract.
    Rationale: users don't interact with nlm-librarian directly; they configure notebooklm.enabled
    once via /sws:init-project (already done) and the consumer agents transparently use it.
    Exposing a /sws:nlm-query slash command would invite the user to think NLM is a primary
    interface; v0.1 keeps it an infrastructure layer.

  D13: |
    No profile activation matrix changes in cycle-13. nlm-librarian is infrastructure — every
    consumer that's active in a given profile auto-uses NLM-when-enabled; the profile system
    does not gate NLM separately.
    Rationale: NLM is per-project (marker flag), not per-profile. The 5 consumers' own profile
    activation matrices (cycles #7, #9, #11) already gate WHEN they run; NLM is just an additional
    capability when they do.

  D14: |
    Smoke test policy: NO live NLM calls in smoke_cycle_13.sh (mirrors cycles #9/11/12 — never burn
    network/API budget in CI/smoke). Instead, smoke creates a fake notebooklm-mcp-cli stub on PATH
    that emits a canned JSON response, then asserts sws_nlm.sh probe + query route through it
    correctly. Degrade-gracefully assertions use the WITHOUT-stub state.
    Rationale: established discipline; live-network tests are unreliable and expensive.

  D15: |
    The cycle-13 v02_backlog entries (D-locked here so cycle-13 doesn't accidentally re-scope):
      - NLM upload automation (push refs/nlm_uploads/ contents into the configured NotebookLM notebook)
      - NLM query-history cache under refs/_nlm-cache/ for session reload
      - Inline NLM-citation injection into draft prose (separate helper agent)
      - SWS-managed NLM auth/token storage (currently inherits CLI's own auth)
      - Bundled notebooklm-mcp-cli binary in plugin (vs user-installs); requires upstream licence + version-pin discipline
      - Multi-notebook query routing (right now nlm-librarian uses a single configured notebook_id)
    Rationale: enumerated upfront so cycle-13 stays disciplined and the v0.2 brainstorm has explicit
    starting points.

risks_and_mitigations:
  R1: |
    Risk: notebooklm-mcp-cli is third-party; upstream breaking changes could break sws_nlm.sh.
    Mitigation: sws_nlm.sh probe subcommand is the early-warning system; if the binary version
    changes its output format, probe will detect and exit 5 with an actionable message. Add a
    last-tested-version note to references/nlm-librarian-pattern.md (D15 also flags version-pin
    discipline for the bundling backlog).

  R2: |
    Risk: consumer agents' NLM dispatch paths become noisy ("NLM disabled — proceeding...")
    after the user has explicitly disabled NLM and doesn't want reminders.
    Mitigation: the one-line notice is printed at log/debug level, not at user-facing-stdout level.
    Tests assert the notice exists in logs; user-facing output stays clean.

  R3: |
    Risk: nlm-librarian's `answer + sources[]` JSON structure assumes a stable notebooklm-mcp-cli
    response format. If the upstream binary changes its return shape, every consumer breaks.
    Mitigation: sws_nlm.sh validates the binary's response against the expected schema and
    normalizes it. If validation fails, exit 5 with "NLM binary returned unexpected format; check
    binary version" — better than silent corruption.

  R4: |
    Risk: notebooklm.enabled=true + missing binary makes consumers slower (each one prints a
    one-line warning per call).
    Mitigation: agent_prelude.sh caches the probe result for the session (env var
    SWS_NLM_PROBE_RESULT). Consumers check the cached result instead of re-probing.

  R5: |
    Risk: the banner-flip commit lands but the test suite still has cycle-12 numbering refs (e.g.,
    a test that asserts "🧪 v0.1 alpha" in README); flip would break those tests.
    Mitigation: cycle-13's test_banner_v01.py is the SINGLE test asserting banner state; older
    tests don't reference the banner. Search for any other banner-asserting test as part of
    Task 6.x and update if found (probably none).

  R6: |
    Risk: refs/nlm_uploads/ exists but is empty; nlm-librarian might return useless answers.
    Mitigation: nlm-librarian's prompt includes a check — if the user's NotebookLM notebook
    appears empty (zero sources returned for a benign query), surface a notice to the user:
    "Your NotebookLM notebook appears empty. Upload PDFs/notes from refs/nlm_uploads/ to it
    before querying." This is a UX nudge, not an error.

smoke:
  script: tests/smoke_cycle_13.sh
  step_count: 10
  fixtures: tests/fixtures/sample-cycle-13/ (minimal: marker with notebooklm.enabled toggleable; fake notebooklm-mcp-cli stub script)
  dependencies: none (independent of cycles 9/11/12 fixtures — uses its own minimal one)

unit_test_count_target: ~30-40 new tests (wrapper exit-code matrix + dispatch contract + 5 consumer degrade-gracefully + resolver + banner). Total post-cycle target: ~870 (current ~833 from cycle-12 + ~30-40 new).

handoff_to_planner: |
  Hand off to superpowers:writing-plans for cycle-13. Plan should structure as:
    Phase 1 — Foundations (sws_nlm.sh wrapper + references/nlm-librarian-pattern.md + resolver/prelude
              extension). Stdlib + bash only.
    Phase 2 — nlm-librarian agent.
    Phase 3 — 5 consumer-agent updates (parallel; each is a frontmatter + body edit).
    Phase 4 — Banner flip (README + plugin.json) + memory + status updates.
    Phase 5 — Tests (parallel: wrapper, dispatch, consumer-degrade, resolver, banner).
    Phase 6 — Fixtures + smoke + PR.
  Phase 3 is parallel-9 (per cycle-12 phase-5 pattern: 9 sub-subagents). All other phases sequential.
  This is THE FINAL v0.1 CYCLE. Pre-PR-open: extra grep-pass for identity-leak strings + any leftover
  cycle-12 / cycle-11 / alpha references.
---

# Cycle #13 — NLM Integration

This body is orientation only; **all decisions, scope, deliverables, risks, and the smoke plan live in the frontmatter dictionary above** and are the source of truth.

## What this cycle is

The last v0.1 cycle. It does three jobs:

1. **Ships `nlm-librarian`** — roster agent #22 — and the `sws_nlm.sh` bash wrapper around the third-party `notebooklm-mcp-cli` binary. NLM is invoked as a CLI (not MCP) per the MCP-aversion principle.
2. **Wires the 5 consumer agents** (`drafter-flagship`, `drafter-fast`, `literature-searcher`, `claim-verifier`, `bibliography-curator`, `proposal-compliance-helper`) to dispatch through `nlm-librarian` when `notebooklm.enabled=true` and degrade gracefully when disabled or binary-missing.
3. **Flips the banner** from `🧪 v0.1 alpha` to `v0.1` and bumps the plugin version to `0.1.0`.

## Why "opt-in, last"

The architecture sketch put NLM at the end of v0.1 for a reason: it depends on a third-party binary that not every user will install, and the v0.1 pipeline must work end-to-end without it. Putting NLM last lets the entire prior pipeline (cycles 1-12) demonstrate that degrade-gracefully is a real property — every consumer already handles `notebooklm.enabled=false` gracefully because every previous cycle was built that way. Cycle 13 just activates the other branch.

## Why CLI, not MCP

The MCP-aversion principle (locked in cycle-06 / referenced in `claude_memory/reference_external_tools.md`): MCP token costs add up across every tool call, and a CLI alternative exists. `notebooklm-mcp-cli` ships both MCP and CLI modes; SWS uses CLI only. PubMed stays MCP because no CLI alternative is available.

## Why one wrapper script + one agent

Single point of contact = single point of error handling = single point of degrade-gracefully behavior (D5). Every consumer dispatches to `nlm-librarian` rather than calling `sws_nlm.sh` directly. The wrapper handles binary discovery + invocation; the agent handles query refinement + answer normalization.

## What "v0.1 ships" means

After cycle-13 merges:
- Banner reads `v0.1` (not "alpha")
- Plugin version `0.1.0`
- All 24 agents in the v0.1 roster have shipped
- All 9 writing-context profiles exist with activation matrices
- The docx-first pipeline (init → outline → draft → revise → review → submission) is usable end-to-end via `/sws:run-cycle`
- NLM is opt-in but fully wired
- ~870 tests; smoke for every cycle passes

The user can publish + announce v0.1 after merging this PR.

## Cross-cutting constraints honored

- `nlm-librarian` agent sources `agent_prelude.sh` and calls `agent_should_run.sh nlm-librarian` (agent-contract R1).
- `sws_nlm.sh` is stdlib + bash only (no Python deps).
- `notebooklm.enabled=false` is the GUARANTEE OF DEGRADE-GRACEFULLY — every consumer asserts this with a test.
- No new MCP integrations (MCP-aversion principle).
- Identity-leak grep run on every commit (project STANDING RULE).
- `R5 — no gender-default in user address` baked into the nlm-librarian prompt.
- Banner-flip commit is the FINAL commit on the branch; everything else lands first so the flip is atomic with a passing test suite.
