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
    - false  -> skip NLM step entirely, no warning printed to user (D6).
    - true   -> continue to dispatch.
  dispatch: |
    Consumer dispatches the nlm-librarian agent with the query, optionally specifying a notebook_id.
    nlm-librarian calls sws_nlm.sh probe; if probe fails, returns degrade JSON without ever calling query.
    If probe passes, calls sws_nlm.sh query and returns the normalized JSON.
  consume: |
    Consumer parses returned JSON:
      ok=true  -> incorporate `answer` + `sources[]` into its workflow (placement is consumer-specific)
      ok=false -> print `fallback_message` at debug-log level, proceed without NLM
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
