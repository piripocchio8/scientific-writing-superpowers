# SWS agent contract

All SWS agents (cycle #7 onward) follow this contract. Agent files reference this document instead of duplicating the rules. Future agents (cycles #8 through #11) inherit the same rules; this is the single source of truth.

## Required first action

Every agent's prompt opens with:

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh" <agent-id>
"${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh" <agent-id> || exit 0
```

`agent_prelude.sh` exports `RESOLVED_OK`, `RESOLVED_PROFILE_SET`, `RESOLVED_PROFILE_ID`, plus per-field `RESOLVED_*` variables (e.g. `RESOLVED_WORD_TOTAL`, `RESOLVED_REF_CAP`, `RESOLVED_FIGURES_MAX`, `RESOLVED_ABSTRACT_STYLE`).

`agent_should_run.sh` exits 0 if the agent is allowed to run for the resolved profile, non-zero otherwise. Agents silently exit on the non-zero case (no banner, no chatter — the dispatching skill handles the user-facing message).

## Five cross-cutting rules

### R1 — Python frugality

Reuse `<paper>/.venv/`. Do NOT install new pip packages unless the task genuinely requires them. The default deps in `requirements/sws-deps.txt` cover YAML (PyYAML), DOCX (python-docx), PDF (pypdf), XML (lxml), Excel (openpyxl), and pytest. If a new dependency is unavoidable, raise it in the user-facing reply rather than silently `pip install`ing.

### R2 — Filesystem frugality

Prefer `scripts/sws_fs_index.py` (the project manifest) and the `Explore` tool over `Bash`/`ls`/`find`. Reach for shell only when no alternative exists. Long sessions burn tokens on repeated directory walks; the fs-index utility (cycle #1) was built specifically to avoid that. When you need a single file path you already know, use `Read` directly — do not list its parent first.

### R3 — Format-aware reading

Native `Read` tool works for: PDF (text + low-resolution rendering, ≤10 pages by default — use the `pages` parameter for ranges in larger PDFs), PNG / JPG / TIFF / SVG (multimodal visual input), plain text, markdown, code.

Native `Read` tool does NOT work for: DOCX, XLSX. For those, use the SWS-provided helpers (see "I/O wrapper inventory" below). Do NOT install ad-hoc parsers (`python-docx`, `openpyxl`, `pdfplumber`, etc.) — they are pre-installed in the per-paper venv as part of `requirements/sws-deps.txt`, and the wrappers are the only sanctioned entry point.

Cycle #7 shipped READ wrappers (sws_read_docx, sws_read_xlsx); cycle #8 ships WRITE wrappers (sws_write_docx, sws_restyle_docx, sws_apply_chemistry_format) plus the context-aware AI-tells linter (sws_lint_ai_tells).

### R4 — Token discipline

Concise thinking. Concise user-facing chatter. Avoid restating the request, narrating which file you are about to read, or summarizing what you just did when the file path itself is the deliverable.

**DRAFTED PROSE IS EXEMPT.** The user controls voice and length via `_voice/` profiles and the resolved profile/overlay word targets. Drafted Intro/Discussion/Conclusion/Methods/Results prose, AI-tells reference content, and source-snapshot extracts are written at the length the spec demands — token discipline applies to the agent's *narration around* the work, not to the work itself.

### R5 — No gender-default in user address

Before adopting any pronoun, honorific, or gendered descriptor when addressing or referring to the user, read the user's memory/profile (e.g. `$HOME/.claude/projects/<project>/memory/user_*.md`). If pronouns are unknown, use the user's first name or neutral phrasing ("you", "the user"). Do NOT guess.

This applies recursively: any prose your agent generates that is shown to the user inherits the same rule. Drafted manuscript prose typically has no occasion to address the user; user-facing reply text and budget Q&A prompts do.

## AI-writing-tells avoidance

Before returning drafted prose, every drafting agent greps the output against `references/ai-writing-tells.md` patterns. Block-severity hits abort the response with a fix suggestion; warn-severity hits get flagged in the agent's reply ("warn: pattern X matched, consider rephrasing").

The reference doc is structured by category (lexical, syntactic, structural, hedging, transitions). Each tell ships with a regex pattern, severity, an example_bad sentence, an example_fix, and a one-line `why`. The grep-pass is mechanical — no LLM judgment in the loop. Cycle #8's reviser will gain a smarter linter once we have false-positive data.

## Attribution pattern (for adapted prompts)

Agent files whose prompts are adapted from MIT-licensed prior art carry a one-line header above the YAML frontmatter:

```
# Adapted from <plugin-url> (MIT)
```

Survey targets: `andrehuang/academic-writing-agents`, `Imbad0202/academic-research-skills`. The roster (agent names, scopes, models) is original to SWS; only prompt content adapts. If adaptation is below ~30% of the prompt body, the header is not added — the agent counts as fresh-write with prior-art inspiration only.

## Agent file template

Every cycle-#7 (and onward) agent file follows this shape:

```yaml
---
name: <agent-id>
description: <one-line trigger description>
model: <claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5>
color: <pick from existing palette>
---

# Adapted from <plugin-url> (MIT)   # only if applicable

<Agent-specific 5-10 line prompt focused on the agent's narrow job. Reference RESOLVED_* env vars, file paths, and behaviors specific to this agent's scope. Include a misroute safety net for drafting agents.>

Follow the SWS agent contract: source ${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh <agent-id>, then ${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh <agent-id> || exit 0. See ${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md for the full contract.
```

The agent file stays under ~30 lines. Cross-cutting rules live here, not in the agent file. Future fixes touch this contract document, not seven agent files.

## I/O wrapper inventory

All wrappers are invoked via `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" <wrapper> <args>`. They are pre-installed at init via `requirements/sws-deps.txt`; do not pip install anything yourself.

| Script | Purpose | Cycle |
|---|---|---|
| `scripts/sws_read_docx.py` | Read .docx as plain text or with style annotations; supports --section and --paragraphs scoping | 7 |
| `scripts/sws_read_xlsx.py` | Read .xlsx by sheet/range; --show-formulas preserves formula source | 7 |
| `scripts/sws_write_docx.py` | Write markdown → .docx with SWS style canon | 8 |
| `scripts/sws_restyle_docx.py` | Re-apply SWS styles to an existing .docx | 8 |
| `scripts/sws_apply_chemistry_format.py` | Apply chemistry-formatting patterns to an existing .docx | 8 |
| `scripts/sws_lint_ai_tells.py` | Context-aware AI-tells linter (vs grep-pass) | 8 |
| `scripts/sws_read_pdf.py` (NOT shipped — use native Read) | PDF reading goes through native Read tool with the `pages` parameter for ranges | n/a |
| `scripts/sws_view_image.py` (NOT shipped — use native Read) | Image viewing goes through native Read tool (multimodal input) | n/a |
| `_review/peer-reviewer/report.md` | YAML frontmatter dict (sws_artifact, profile, manuscript_file, decision, overall_score, section_scores, flags, fidelity_status, claim_verification_status) + body with EIC opening, four reviewer sections, DA closing | peer-reviewer |
| `_review/claim-verifier/report.md` | Markdown report — per-claim findings grouped by section, with verification status (verified/unverified/contested) | claim-verifier |
| `_review/claim-verifier/claims.json` | List of `{section, claim, citation_keys[], verification_status, source_match[]}` | claim-verifier |
| `_review/bibliography-fidelity-checker/report.md` | Markdown report with V0.1 LIMITATION header + findings or skip-reason note (D9, D9a, D9b, D9c) | bibliography-fidelity-checker |
| `_review/bibliography-fidelity-checker/flags.json` | List of `{paragraph_id, section, overlap_text, zotero_item_key, zotero_title, zotero_authors, zotero_year, zotero_collection, page_hint}` | bibliography-fidelity-checker |
| `_review/bibliography-fidelity-checker/status.json` | Dict `{zotero_skill_available, zotero_desktop_detected, zotero_sqlite_path, ran, skip_reason, library_item_count?}` | bibliography-fidelity-checker |
| `scripts/sws_xlsx_resolve.py` | Read .xlsx data_only; fail loud on un-cached formula cells (D4) | 11 |
| `scripts/sws_data_manifest.py` | Build/update Zenodo_db/manifest.json atomically; orphan check | 11 |
| `scripts/sws_plot_runner.py` | Inject rcParams font floor, exec user plot script, introspect figure for D6a compliance (font >= 8 pt; width in {7.5 cm or 12–16 cm}); save figure; return JSON result | 11 |
| `scripts/sws_semantic_scholar.py` | Semantic Scholar search + DOI resolve (cached, backoff) | 11 |
| `scripts/sws_crossref.py` | CrossRef DOI resolve + reference formatting | 11 |
| `scripts/sws_openalex.py` | OpenAlex metadata + abstract reconstruction | 11 |
| `Zenodo_db/data/*.xlsx` | Source data files — read via sws_xlsx_resolve.py only | 11 |
| `Zenodo_db/scripts/` | Co-located fit/plot scripts — executed by plot-maker | 11 |
| `Zenodo_db/figures/` | Plot-maker outputs (PNG/PDF/SVG); every file must have a manifest.json entry | 11 |
| `Zenodo_db/manifest.json` | Provenance spine: dataset → script → figure(s); written atomically | 11 |
| `refs/_lit-search/<slug>.md` | literature-searcher output — ranked candidates with metadata + relevance note | 11 |
| `_review/bibliography-audit/report.md` | bibliography-curator audit report — unresolved DOIs, duplicates, format deviations | 11 |
| `_review/bibliography-audit/fixes.json` | bibliography-curator proposed fixes — list of `{key, field, old, new, source}` | 11 |
| `_review/round-<N>/reviewer-comments.md` | USER-PROVIDED reviewer comments in any of three accepted shapes (see `references/submission-artifacts.md` `reviewer_comments_accepted_shapes`). INPUT for `sws_response_matrix.py`. | 12 |
| `_review/round-<N>/response-matrix.json` | R&R Traceability Matrix — list of comment objects (id, reviewer, text, severity_inferred, status, response_text, edits_made, line_refs). INTERMEDIATE between `sws_response_matrix.py` (writes shell) and the `response-to-reviewers` agent (fills the four agent-controlled fields). Schema in `references/submission-artifacts.md` `response_matrix_schema`. | 12 |
| `_review/round-<N>/response-to-reviewers.md` | `response-to-reviewers` agent prose output (per-comment table + per-reviewer summary). | 12 |
| `_review/round-<N>/edits-summary.md` | Optional agent-generated log of concrete edits per comment. | 12 |
| `_submission/cover-letter.md` | `cover-letter-writer` agent OUTPUT. Venue-specific markdown cover letter; structure in `references/submission-artifacts.md` `cover_letter_canonical_structure`. Editor name is never fabricated (D11). | 12 |
| `_submission/ai-disclosure.md` | `sws_disclosure_writer.py` OUTPUT. One of four template bodies (ICMJE / Wiley / RSC / ACS) selected from the journal overlay's `disclosure.template_id`. | 12 |
| `_submission/response-to-reviewers-round-<N>.md` | Mirror of `_review/round-<N>/response-to-reviewers.md` for journal upload. | 12 |
| `_voice/profile.md` | YAML frontmatter (feature targets per `references/voice-profile-schema.md`) + body: `## Global voice` then `## Section deltas` with `### <Section>` blocks. WRITTEN by style-calibrator; READ by drafter-flagship, drafter-fast, reviser-full, reviser-fast, humanizer via the prelude-exported `$VOICE_PROFILE`. SEPARATE axis from `resolve_overlay.py` (D13). | style-calibrator (write) / 5 consumers (read) |
| `_voice/field-profile.md` | One-shot subfield conventions (D5; no per-section breakdown, no loop) | style-calibrator |
| `_voice/style-evolution.md` | Diachronic feature x year/era table + reading (D7) | style-calibrator |
| `_voice/sources.json` | `[{zotero_key, title, year, author_position, has_pdf, role: train|heldout, recency_weight}]` + fitted weights snapshot + gamma + self-band | style-calibrator |
| `_voice/convergence.md` | Per round, per section: distance, RBF sim, Haiku median, what changed, why, seed prompt + candidate text (D11) | style-calibrator |
