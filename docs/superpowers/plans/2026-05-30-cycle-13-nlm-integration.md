# Cycle #13 — NLM Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. **All design decisions live in the spec frontmatter at `docs/superpowers/specs/2026-05-30-cycle-13-nlm-integration-design.md` (D1–D15). Read it first.**

**Goal:** Ship roster agent #22 (`nlm-librarian`, Sonnet 4.6 high), the `sws_nlm.sh` CLI wrapper around `jacob-bd/notebooklm-mcp-cli`, wire all 5 NLM consumer agents (drafter-flagship, drafter-fast, literature-searcher, claim-verifier, bibliography-curator, proposal-compliance-helper) to dispatch through `nlm-librarian` when enabled / degrade gracefully when not, and flip the banner from `🧪 v0.1 alpha` to `v0.1` with plugin version bump `0.1.0-alpha` → `0.1.0`. **THIS IS THE FINAL v0.1 CYCLE.**

**Architecture:** Single-point-of-contact pattern (D5). All 5 consumer agents call `nlm-librarian`; only `nlm-librarian` calls `sws_nlm.sh`; only `sws_nlm.sh` calls the upstream `notebooklm-mcp-cli` binary. Three subcommands (probe / query / list-notebooks) — locked surface area. `notebooklm.enabled=false` is the GUARANTEE that consumers degrade gracefully without warnings to the user.

**Tech Stack:** Bash + stdlib Python. No new dependencies. The upstream `notebooklm-mcp-cli` binary is user-installed separately (npm / pipx); SWS does not bundle it.

**Spec source of truth:** `docs/superpowers/specs/2026-05-30-cycle-13-nlm-integration-design.md`. D1–D15 are canonical.

**Execution mode:** Autonomous. Maximize within-phase parallelism (Phase 3 = 6 parallel consumer-agent edits). PR open in READY state (not draft) for user merge. Banner-flip commit is the FINAL commit so the flip is atomic with a passing test suite.

---

## File Structure

**CREATE:**

Scripts:
- `scripts/sws_nlm.sh`

References:
- `references/nlm-librarian-pattern.md`

Agents:
- `agents/nlm-librarian.md`

Tests:
- `tests/test_sws_nlm_wrapper.py`
- `tests/test_nlm_librarian_dispatch.py`
- `tests/test_consumer_nlm_degrade.py`
- `tests/test_resolve_overlay_notebooklm.py`
- `tests/test_banner_v01.py`
- `tests/fixtures/sample-cycle-13/` (minimal: marker with notebooklm.enabled toggleable + a fake notebooklm-mcp-cli stub script)
- `tests/smoke_cycle_13.sh`

**MODIFY:**
- `scripts/resolve_overlay.py` — add `notebooklm.*` schema_defaults (D9)
- `scripts/agent_prelude.sh` — export `RESOLVED_NOTEBOOKLM_ENABLED`, `RESOLVED_NLM_NOTEBOOK_ID`, `RESOLVED_NLM_CLI_PATH`; cache probe result in `SWS_NLM_PROBE_RESULT` (R4)
- `agents/drafter-flagship.md` — wire NLM consumer path (D2)
- `agents/drafter-fast.md` — wire NLM consumer path (D2)
- `agents/literature-searcher.md` — promote stub → active dispatch; renumber cycle-11 → cycle-13
- `agents/claim-verifier.md` — promote stub → active dispatch; renumber cycle-11 → cycle-13
- `agents/bibliography-curator.md` — promote stub → active dispatch
- `agents/proposal-compliance-helper.md` — replace forward-ref → active dispatch
- All 6 of the above: frontmatter `notebooklm_enabled: false` → `notebooklm_enabled: dynamic` (D10)
- `references/marker-schema.md` — extend `notebooklm.*` sub-keys (.notebook_id, .cli_path)
- `references/agent-contract.md` — R3 I/O inventory: `refs/nlm_uploads/` + nlm-librarian JSON return shape
- `README.md` — banner flip (D11)
- `.claude-plugin/plugin.json` — version bump `0.1.0-alpha` → `0.1.0`
- `claude_memory/project_v02_backlog.md` — append D15's 6 deferred items
- `claude_memory/project_cycle_execution_status.md` — mark cycle #13 PR-open, banner flipped
- `claude_memory/reference_external_tools.md` — notebooklm-mcp-cli wired (not planned)

---

## Phase Map

**Phase 1 — Foundations (3 tasks, sequential within phase):**
- Task 1.1: `references/nlm-librarian-pattern.md`
- Task 1.2: `scripts/sws_nlm.sh`
- Task 1.3: `scripts/resolve_overlay.py` + `scripts/agent_prelude.sh` extensions

**Phase 2 — nlm-librarian agent (1 task):**
- Task 2.1: `agents/nlm-librarian.md`

**Phase 3 — 6 consumer-agent updates (6 parallel tasks):**
- Task 3.1: `agents/drafter-flagship.md`
- Task 3.2: `agents/drafter-fast.md`
- Task 3.3: `agents/literature-searcher.md`
- Task 3.4: `agents/claim-verifier.md`
- Task 3.5: `agents/bibliography-curator.md`
- Task 3.6: `agents/proposal-compliance-helper.md`

**Phase 4 — Reference + memory updates (3 sequential tasks):**
- Task 4.1: `references/marker-schema.md` + `references/agent-contract.md`
- Task 4.2: `claude_memory/` updates (3 files)
- Task 4.3: hold — banner flip happens in Phase 6

**Phase 5 — Tests (5 parallel tasks + fixtures):**
- Task 5.1: `tests/test_sws_nlm_wrapper.py`
- Task 5.2: `tests/test_nlm_librarian_dispatch.py`
- Task 5.3: `tests/test_consumer_nlm_degrade.py`
- Task 5.4: `tests/test_resolve_overlay_notebooklm.py`
- Task 5.5: `tests/test_banner_v01.py` (deliberately created BEFORE the banner-flip — will FAIL initially; Phase 6 makes it pass)
- Task 5.6: fixtures + `tests/smoke_cycle_13.sh`

**Phase 6 — Banner flip + PR (sequential, depends on all prior):**
- Task 6.1: `README.md` banner flip
- Task 6.2: `.claude-plugin/plugin.json` version bump
- Task 6.3: Full test suite + smoke; confirm `test_banner_v01.py` now passes
- Task 6.4: Commit + push + open PR (READY, not draft)

---

## PHASE 1 — Foundations

### Task 1.1: `references/nlm-librarian-pattern.md`

**Files:** Create `references/nlm-librarian-pattern.md`.

Content (full doc with frontmatter as dictionary):

````markdown
---
sws_artifact: nlm-librarian-pattern
artifact_version: 0.1
locked: 2026-05-30
used_by:
  - agents/nlm-librarian.md
  - agents/drafter-flagship.md
  - agents/drafter-fast.md
  - agents/literature-searcher.md
  - agents/claim-verifier.md
  - agents/bibliography-curator.md
  - agents/proposal-compliance-helper.md
  - scripts/sws_nlm.sh

binary:
  name: notebooklm-mcp-cli
  upstream: "https://github.com/jacob-bd/notebooklm-mcp-cli"
  licence: MIT
  install_options:
    - "npm install -g notebooklm-mcp-cli"
    - "pipx install notebooklm-mcp-cli"
  last_tested_version: "TBD (record at first successful probe)"
  alternate_binary_names: [notebooklm]

invocation_mode: CLI ONLY (the MCP-server mode of this binary is NOT used; MCP-aversion principle).

wrapper_contract:
  script: scripts/sws_nlm.sh
  subcommands:
    probe:
      exit_codes:
        0: "all green (binary on PATH AND auth OK AND notebooklm.enabled=true), OR notebooklm.enabled=false with 'disabled' message"
        4: "binary missing"
        5: "binary present but unconfigured / auth failed"
    query:
      args: "<question> [--notebook <id>]"
      stdout: JSON {ok, answer, sources[], notebook_id, query, fallback, fallback_message}
      exit_codes:
        0: success (ok=true) OR graceful-degrade (ok=false but with explanation)
        5: hard failure
    list-notebooks:
      stdout: JSON list of {id, title}
      exit_codes:
        0: success
        5: probe would fail

binary_discovery_order:  # D4
  - "marker file notebooklm.cli_path if set"
  - "$PATH lookup for `notebooklm-mcp-cli`"
  - "$PATH lookup for `notebooklm`"

consumer_dispatch_contract:
  pre_check: |
    Consumer checks RESOLVED_NOTEBOOKLM_ENABLED env var (exported by agent_prelude.sh).
    - false → skip NLM step entirely, no warning printed to user (D6).
    - true  → continue to dispatch.
  dispatch: |
    Consumer dispatches the nlm-librarian agent with the query, optionally specifying a notebook_id.
    nlm-librarian calls sws_nlm.sh probe; if probe fails, returns degrade JSON without ever calling query.
    If probe passes, calls sws_nlm.sh query and returns the normalized JSON.
  consume: |
    Consumer parses returned JSON:
      ok=true → incorporate `answer` + `sources[]` into its workflow (placement is consumer-specific)
      ok=false → print `fallback_message` at debug-log level, proceed without NLM
  guarantee: NLM trouble NEVER fails the consumer's main job (D6).

return_json_schema:
  ok: bool
  answer: string                                            # only when ok=true
  sources: list of {title, snippet, page (int or null)}
  notebook_id: string
  query: string
  fallback: enum [none, disabled, missing, auth, error]
  fallback_message: string

degrade_gracefully_states:
  disabled:
    when: notebooklm.enabled=false in marker
    fallback_message: "NLM disabled in this project; proceeding without NLM."
    user_facing: false (debug-log only — see R2)
  missing:
    when: notebooklm.enabled=true AND binary not found on PATH
    fallback_message: "NLM enabled but notebooklm-mcp-cli binary missing; install it (see references/nlm-librarian-pattern.md) or set notebooklm.cli_path. Proceeding without NLM."
    user_facing: true (one-time per session via SWS_NLM_PROBE_RESULT cache, R4)
  auth:
    when: binary present but probe shows auth not configured
    fallback_message: "NLM auth not configured; check the tool's auth setup and re-run. Proceeding without NLM."
    user_facing: true (one-time per session)
  error:
    when: query call returns malformed output / unexpected schema
    fallback_message: "NLM binary returned an unexpected format; check binary version. Proceeding without NLM."
    user_facing: true (one-time per session)

per_consumer_use:
  drafter-flagship:
    placement: "Optional additional context for Introduction / Discussion / Conclusion / Abstract drafting."
    consumes: "answer (as inspiration) + sources[] (as candidate citations to verify against Zotero)"
  drafter-fast:
    placement: "Optional additional context for non-flagship sections (Results, Methods, etc.)."
    consumes: same as drafter-flagship
  literature-searcher:
    placement: "5th discovery channel (after Zotero, PubMed, Semantic Scholar, OpenAlex)."
    consumes: "sources[] merged into discovery ranking; answer used for query-refinement"
  claim-verifier:
    placement: "5th verification source (after Zotero, Semantic Scholar, PubMed, [the user's read corpus])."
    consumes: "sources[] checked for claim support; answer for natural-language verification"
  bibliography-curator:
    placement: "Metadata fallback (after Zotero, CrossRef, OpenAlex)."
    consumes: "sources[] for DOI/metadata recovery on unresolved citations"
  proposal-compliance-helper:
    placement: "PRIMARY grounding against the funding call PDF (the call PDF should be uploaded by the user to a dedicated NotebookLM notebook)."
    consumes: "answer + sources[] for compliance-check answers (rather than scanning the call PDF locally)"

refs_nlm_uploads_dir:  # D7
  path: refs/nlm_uploads/
  v01_schema: "directory-only; users drop PDFs/notes as they see fit"
  user_workflow: "the user uploads these (or others) to a NotebookLM notebook themselves; SWS does not push"
  sws_does_not_manage: [contents, manifest, upload]
  v02_potential: upload-automation may add a manifest + sync script
---

# nlm-librarian Pattern (v0.1)

This body is orientation only; **the frontmatter dictionary above is the source of truth** for the binary discovery order, the wrapper contract, the consumer dispatch contract, the return JSON schema, and the per-consumer use placement.

## What this pattern anchors

The single-point-of-contact discipline for NotebookLM RAG in SWS:

- One agent (`nlm-librarian`) owns NLM dispatch.
- One wrapper script (`sws_nlm.sh`) owns the binary invocation.
- Five consumer agents call `nlm-librarian` (never the script directly).
- `notebooklm.enabled=false` is the explicit degrade-gracefully gate.

## Why CLI not MCP

`notebooklm-mcp-cli` ships both modes. SWS uses CLI only. See `claude_memory/reference_external_tools.md` for the MCP-aversion rationale (token cost; CLI is the cheaper alternative when available).

## Why a return JSON shape

Each consumer slots the NLM answer in differently (`per_consumer_use` above). A structured return — `{ok, answer, sources[], fallback}` — lets every consumer make the same call and apply consumer-specific consumption logic.

## Last-tested-version policy (R1)

When you successfully run `sws_nlm.sh probe` against the upstream binary for the first time, record the binary's `--version` output in this doc's `last_tested_version` field. Upstream breaking changes get caught by the next probe.
````

- [ ] Implement.
- [ ] Commit: `references(nlm): single-point-of-contact pattern + binary contract + degrade states`

### Task 1.2: `scripts/sws_nlm.sh`

**Files:** Create `scripts/sws_nlm.sh`. Make executable (`chmod +x`).

Subcommands per D3:
- `probe`
- `query <question> [--notebook <id>]`
- `list-notebooks`

Exit codes per D3.

Binary discovery order per D4.

**Pseudocode shape:**

```bash
#!/usr/bin/env bash
# sws_nlm.sh - CLI wrapper around notebooklm-mcp-cli.
# Single point of contact between SWS and the upstream NLM binary.

set -euo pipefail

# 1. Source agent_prelude.sh to get RESOLVED_NOTEBOOKLM_ENABLED, _NOTEBOOK_ID, _CLI_PATH.
# 2. Helper: detect_binary() prints the binary path (D4 order) or empty.
# 3. Helper: probe_binary() returns: ok | missing | unconfigured | auth.
# 4. Dispatch on first arg:
#    probe              → run probe_binary, exit accordingly
#    query <q> [--notebook <id>]
#                       → if probe!=ok exit 5 with reason; else exec binary "query" with args, validate JSON, print
#    list-notebooks     → if probe!=ok exit 5; else exec binary "list-notebooks", print JSON
#    *                  → print usage and exit 2
# 5. SWS_NLM_PROBE_RESULT cache (R4): if env set, reuse; else compute and export.

# JSON validation: use python3 -c 'json.loads(sys.stdin.read())' to validate before print
# Stdlib + bash only. No new dependencies.
```

Key requirements:
- All output is JSON on stdout (for query and list-notebooks); messages go to stderr.
- Exit 0 with stderr-only "NLM disabled in this project; proceeding without NLM." when `RESOLVED_NOTEBOOKLM_ENABLED=false`.
- Exit 4 when binary not found.
- Exit 5 when binary found but probe fails (unconfigured / auth / version-mismatch).
- D8 return schema: `{ok, answer, sources[], notebook_id, query, fallback, fallback_message}`. Even on graceful-degrade (ok=false), still print this JSON to stdout.

- [ ] Implement; chmod +x.
- [ ] Commit: `scripts(nlm): CLI wrapper for notebooklm-mcp-cli; probe|query|list-notebooks (D3, D4, D6, D8)`

### Task 1.3: Resolver + prelude extensions

**Files:** Modify `scripts/resolve_overlay.py` and `scripts/agent_prelude.sh`.

**resolve_overlay.py** — extend `schema_defaults` (D9):

```python
"notebooklm": {
    "enabled": False,
    "notebook_id": None,
    "cli_path": None,
},
```

The existing `_flatten()` helper handles the nested key → flat `RESOLVED_NOTEBOOKLM_*` form. If `_flatten()` doesn't already handle a 2-deep nested dict, extend it; otherwise the new defaults just flow through.

**agent_prelude.sh** — extend the `RESOLVED_*` exports list:

```bash
# Cycle-13 additions
RESOLVED_NOTEBOOKLM_ENABLED="${RESOLVED_NOTEBOOKLM_ENABLED:-false}"
RESOLVED_NLM_NOTEBOOK_ID="${RESOLVED_NLM_NOTEBOOK_ID:-}"
RESOLVED_NLM_CLI_PATH="${RESOLVED_NLM_CLI_PATH:-}"
export RESOLVED_NOTEBOOKLM_ENABLED RESOLVED_NLM_NOTEBOOK_ID RESOLVED_NLM_CLI_PATH

# Cached probe result (R4): caller may set SWS_NLM_PROBE_RESULT to skip re-probing.
# Values: ok|disabled|missing|auth|unset
```

- [ ] Implement.
- [ ] Commit: `resolver+prelude: notebooklm.* defaults + RESOLVED_NLM_* env exports (D9, R4)`

---

## PHASE 2 — nlm-librarian agent

### Task 2.1: `agents/nlm-librarian.md`

**Files:** Create `agents/nlm-librarian.md`.

Frontmatter:
```yaml
name: nlm-librarian
description: |
  Use this agent when any of the 5 NLM consumers (drafter-flagship, drafter-fast, literature-searcher,
  claim-verifier, bibliography-curator, proposal-compliance-helper) needs grounded RAG against the user's
  NotebookLM notebook. Sole owner of scripts/sws_nlm.sh dispatch. Reads RESOLVED_NOTEBOOKLM_ENABLED;
  exits with the degrade JSON if disabled or binary missing. Never fails the consumer's main job.
tools: Bash, Read, Glob, Grep
model: sonnet
notebooklm_enabled: dynamic
```

Body sections (mirror cycle-9/11 agent structure):

1. **Pre-check**: source `agent_prelude.sh`; run `agent_should_run.sh nlm-librarian`.
2. **Probe (cached)**: if `SWS_NLM_PROBE_RESULT` env var unset, exec `sws_nlm.sh probe` and cache. If `disabled`, emit degrade JSON `{ok:false, fallback:"disabled", fallback_message:"..."}` and exit 0.
3. **Query refinement** (this is the LLM-mediated step that motivates having an agent layer above the script):
   - Read the consumer's query.
   - Optionally rephrase for NLM (e.g., add context from the resolved overlay's target_journal).
   - Choose notebook_id (default from `RESOLVED_NLM_NOTEBOOK_ID`; consumer may override).
4. **Dispatch**: exec `sws_nlm.sh query "<refined>" --notebook <id>`. Capture JSON.
5. **Empty-notebook check (R6)**: if `sources[]` is empty, append a UX nudge to `fallback_message` suggesting the user populate `refs/nlm_uploads/` and upload to NLM.
6. **Return**: emit the validated JSON. ok=true on success; ok=false with `fallback` reason on degrade.
7. **R5 / agent-contract**: no gender-default; use SWS read wrappers if any docx/xlsx is referenced (unlikely in this agent).

- [ ] Write.
- [ ] Commit: `agent(nlm-librarian): Sonnet 4.6 high; single-owner of sws_nlm.sh dispatch (roster #22, D5)`

---

## PHASE 3 — Consumer-agent updates (6 parallel)

Each task is a small frontmatter + body edit to one agent file. Dispatch as 6 parallel sub-subagents (one per file). Each sub-subagent:
1. Reads the file.
2. Edits frontmatter `notebooklm_enabled: false` → `notebooklm_enabled: dynamic` (D10).
3. Edits the body's NLM section per the per_consumer_use spec in `references/nlm-librarian-pattern.md`.
4. Renumbers any "cycle #11" or "DEFERRED to cycle #11" references → "cycle #13" or removes the "DEFERRED" framing entirely (the path is now active).
5. The body changes follow this template (adapt phrasing per consumer):

```
**NLM grounded-RAG** (gated by notebooklm.enabled):

If RESOLVED_NOTEBOOKLM_ENABLED=true, dispatch the nlm-librarian agent with your query.
- On success (ok=true), consume `answer` and `sources[]` per `references/nlm-librarian-pattern.md`
  per_consumer_use.<this-agent>.
- On degrade (ok=false), proceed without NLM. The agent will have surfaced any needed
  user-facing message (D6).
- If RESOLVED_NOTEBOOKLM_ENABLED=false, skip this step entirely — no notice to the user (R2).
```

### Task 3.1: `agents/drafter-flagship.md`

- [ ] Add a new "NLM context (optional)" section in the body. Per D2, this is a NEW section, not a stub-promote.
- [ ] Frontmatter `notebooklm_enabled: dynamic`.
- [ ] Commit: `agent(drafter-flagship): wire NLM consumer path (D2, D10)`

### Task 3.2: `agents/drafter-fast.md`

- [ ] Same as 3.1.
- [ ] Commit: `agent(drafter-fast): wire NLM consumer path (D2, D10)`

### Task 3.3: `agents/literature-searcher.md`

- [ ] Promote the existing "5. NLM grounded-RAG: DEFERRED (D9)" stub to active dispatch.
- [ ] Renumber cycle-11 reference → cycle-13.
- [ ] Frontmatter `notebooklm_enabled: dynamic`.
- [ ] Commit: `agent(literature-searcher): activate NLM 5th discovery channel (D10, renumber 11→13)`

### Task 3.4: `agents/claim-verifier.md`

- [ ] Promote the "NLM degraded mode — DEFERRED to cycle #11" line to active.
- [ ] Renumber cycle-11 → cycle-13.
- [ ] Frontmatter `notebooklm_enabled: dynamic`.
- [ ] Commit: `agent(claim-verifier): activate NLM 5th verification source (D10, renumber 11→13)`

### Task 3.5: `agents/bibliography-curator.md`

- [ ] Promote the "4. NLM: DEFERRED (D9)" step to active (metadata fallback role per per_consumer_use).
- [ ] Frontmatter `notebooklm_enabled: dynamic`.
- [ ] Commit: `agent(bibliography-curator): activate NLM metadata-fallback channel (D10)`

### Task 3.6: `agents/proposal-compliance-helper.md`

- [ ] Replace "When nlm-librarian ships in cycle #11, this agent will be upgraded..." forward-ref with documented active dispatch (PRIMARY grounding role per per_consumer_use).
- [ ] Frontmatter `notebooklm_enabled: dynamic`.
- [ ] Commit: `agent(proposal-compliance-helper): activate NLM as primary funding-call grounding (D10)`

---

## PHASE 4 — Reference + memory updates

### Task 4.1: `references/marker-schema.md` + `references/agent-contract.md`

**marker-schema.md** — under `notebooklm`, extend with `notebook_id` and `cli_path` sub-key documentation:

```yaml
notebooklm:
  enabled:
    required: true
    type: bool
    default: false
  notebook_id:
    required: false
    type: "string | null"
    default: null
    note: configured NotebookLM notebook to query; null = first available from list-notebooks
  cli_path:
    required: false
    type: "string | null"
    default: null
    note: absolute path to notebooklm-mcp-cli binary; null = PATH discovery (D4)
```

**agent-contract.md** — R3 I/O inventory append:

```
- `refs/nlm_uploads/` — curated corpus directory for user's NLM notebook ingestion (USER-MANAGED, SWS does not touch contents in v0.1)
- nlm-librarian return JSON: {ok, answer, sources[], notebook_id, query, fallback, fallback_message} per references/nlm-librarian-pattern.md
```

- [ ] Edit both.
- [ ] Commit: `references: marker .notebooklm.* sub-keys + R3 NLM I/O inventory`

### Task 4.2: `claude_memory/` updates

`project_v02_backlog.md` — append 6 D15 entries.

`project_cycle_execution_status.md` — update the cycle-13 row + add a "Cycles all merged — v0.1 SHIPPED" summary block at the top once PR opens (the actual update will land in the post-PR-open commit OR as a working-tree only doc, depending on whether the executor decides to commit memory updates here; per cycle-12 the standard is they stay working-tree-only since claude_memory/ is gitignored).

`reference_external_tools.md` — flip `notebooklm-mcp-cli` from "planned (cycle #13)" → "wired (cycle #13 — see references/nlm-librarian-pattern.md)".

- [ ] Edit all 3 (working-tree only; not committed since gitignored).

---

## PHASE 5 — Tests

5 parallel tasks + fixtures task. All depend on Phases 1–4.

### Task 5.1: `tests/test_sws_nlm_wrapper.py`

Test matrix:
- probe with `RESOLVED_NOTEBOOKLM_ENABLED=false` → exit 0; stderr says "disabled".
- probe with `RESOLVED_NOTEBOOKLM_ENABLED=true` AND no binary on PATH AND no marker cli_path → exit 4 with "binary missing" stderr.
- probe with stub binary returning version → exit 0.
- query with stub binary returning fixture JSON → stdout is valid JSON matching return schema; exit 0.
- query with `RESOLVED_NOTEBOOKLM_ENABLED=true` but stub binary returning auth-failed → exit 5.
- query JSON-validation: malformed binary output → exit 5 with "unexpected format" stderr (R3).
- list-notebooks with stub binary → JSON list on stdout, exit 0.
- SWS_NLM_PROBE_RESULT cache: when set to `ok`, probe skips re-execution.

Use a temp dir + a tiny bash stub script as the "binary" (`cat > "$TMPDIR/notebooklm-mcp-cli" <<EOF ... EOF; chmod +x ...; PATH="$TMPDIR:$PATH"`). Stdlib only.

- [ ] Implement.

### Task 5.2: `tests/test_nlm_librarian_dispatch.py`

Contract tests against the agent file:
- `agents/nlm-librarian.md` frontmatter has `notebooklm_enabled: dynamic` and `model: sonnet`.
- Body references `sws_nlm.sh` (single-owner contract — D5).
- Body has the 7-step structure (pre-check, probe-cached, query refinement, dispatch, empty-notebook check, return, R5).
- Body never directly invokes `notebooklm-mcp-cli` (only via `sws_nlm.sh`).

- [ ] Implement (markdown + YAML parsing; no live agent dispatch).

### Task 5.3: `tests/test_consumer_nlm_degrade.py`

For each of the 6 consumer agent files, assert:
- Frontmatter has `notebooklm_enabled: dynamic` (not `false`, not absent).
- Body has the NLM section with the gate language (mentions `RESOLVED_NOTEBOOKLM_ENABLED` or `notebooklm.enabled`).
- Body explicitly mentions degrade-gracefully behavior.
- Body does NOT contain "DEFERRED" / "cycle #11" leftover (regression check — the renumber must have happened).
- Body references the `nlm-librarian` agent (not `sws_nlm.sh` directly — D5).

Parameterize the test over the 6 files.

- [ ] Implement.

### Task 5.4: `tests/test_resolve_overlay_notebooklm.py`

- Default resolver returns `notebooklm.enabled=false` (after _flatten, `RESOLVED_NOTEBOOKLM_ENABLED=false`).
- User marker with `notebooklm.enabled: true` flips it.
- User marker with `notebooklm.notebook_id: "abc"` flows through.
- Sourcing `agent_prelude.sh` against a marker with `notebooklm.enabled=true` exports all 3 env vars.

- [ ] Implement.

### Task 5.5: `tests/test_banner_v01.py`

- `README.md` contains the literal string `**v0.1**` in its banner block.
- `README.md` does NOT contain `🧪` or `v0.1 alpha` in the banner block (regex on lines 1-10).
- `.claude-plugin/plugin.json` has `"version": "0.1.0"` (no `-alpha` suffix).

This test will FAIL until Phase 6's banner-flip commit. That's by design — it asserts the flip occurred, and is the gate before opening the PR.

- [ ] Implement.

### Task 5.6: Fixtures + smoke

`tests/fixtures/sample-cycle-13/`:
- `.sws-project.local.md` template (smoke writes it inline with toggleable `notebooklm.enabled`)
- `fake_notebooklm_mcp_cli.sh` (the stub binary used by smoke + wrapper tests)

`tests/smoke_cycle_13.sh` — 10 steps per spec:
1. Set up tmp dir from fixture.
2. Probe with marker `notebooklm.enabled=false` → assert exit 0, stderr says "disabled".
3. Probe with marker `notebooklm.enabled=true` and NO stub on PATH → assert exit 4.
4. Place stub on PATH (`PATH="$TMP:$PATH"`); probe again → assert exit 0.
5. Query through wrapper → assert valid JSON on stdout, ok=true, sources[] non-empty.
6. Resolver+prelude pipeline: marker `enabled=true, notebook_id=xyz` → RESOLVED_NOTEBOOKLM_ENABLED=true and RESOLVED_NLM_NOTEBOOK_ID=xyz exported.
7. Run unit tests `python3 -m unittest tests.test_sws_nlm_wrapper tests.test_nlm_librarian_dispatch tests.test_consumer_nlm_degrade tests.test_resolve_overlay_notebooklm`.
8. (banner assertions deliberately deferred — see step 9)
9. Run `tests.test_banner_v01` AFTER Phase 6 commit applies — this is the smoke's correctness gate for v0.1 deploy.
10. Print "SMOKE PASS: 10/10".

- [ ] Implement.

After Phase 5:
- [ ] Run full unittest suite. Expect `test_banner_v01.py` to FAIL until Phase 6.
- [ ] Commit each test individually with descriptive messages: `tests(<area>): ...`

---

## PHASE 6 — Banner flip + PR

Sequential. Depends on all prior phases.

### Task 6.1: `README.md` banner flip

Per D11. Replace lines 2-3:

```
> 🧪 **v0.1 alpha** — the drafting → revising → review track is usable end-to-end, and the data/figures, literature, and author-voice tooling has landed. Submission orchestration and opt-in NotebookLM integration are the remaining v0.1 cycles.
```

with:

```
> **v0.1** — the SWS plugin's first stable release. All 13 cycles of the v0.1 roadmap have shipped: 24 agents, 9 writing-context profiles, marker-scoped hooks, the data/figures/literature/voice tooling, the submission orchestrator (`/sws:run-cycle`), and the opt-in NotebookLM RAG layer. Docx-first, end-to-end usable.
```

- [ ] Edit.

### Task 6.2: `.claude-plugin/plugin.json` version bump

Change `"version": "0.1.0-alpha"` to `"version": "0.1.0"`.

- [ ] Edit.

### Task 6.3: Verification

- [ ] Run `python3 -m unittest discover tests/`. Assert 0 failures.
- [ ] Run `tests/smoke_cycle_13.sh`. Assert 10/10 pass.
- [ ] Identity-leak audit: `git diff origin/main..HEAD | grep -iE "/Users/|piripocchio|chino|federico II|UniNA"` should return empty (the author email noreply is intentional and pre-existing, not introduced by this cycle).

### Task 6.4: Commit + push + open PR

Final commits in this order:
1. `cycle-13: banner flip — v0.1 alpha → v0.1, plugin 0.1.0-alpha → 0.1.0` (D11)

Push branch `cycle/13-nlm-integration` to origin.

Open PR:
- Title: `Cycle 13 — NLM integration + v0.1 banner flip (nlm-librarian agent, sws_nlm.sh wrapper, 6 consumers wired)`
- NOT draft (READY).
- Body: spec frontmatter scope.deliverable + checklist of D1–D15 + a "WHAT v0.1 MEANS" summary block.
- Print PR URL.

Do NOT merge.

---

## Exit criteria

- [ ] All 6 phases complete.
- [ ] Smoke 10/10 passes.
- [ ] Full unittest suite passes (~870 total).
- [ ] `test_banner_v01.py` passes (the banner-flip gate).
- [ ] PR `#19` (or next-available) opened (READY) on `cycle/13-nlm-integration`.
- [ ] Identity-leak grep clean.
- [ ] Banner now reads `v0.1` in README and plugin version is `0.1.0`.
- [ ] v0.1 is ready to merge → publish → announce.
