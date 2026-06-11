# Cycle #12 — Submission Orchestration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **All design decisions live in the spec frontmatter at `docs/superpowers/specs/2026-05-30-cycle-12-submission-orchestration-design.md` (D1–D20). Read it first; this plan only implements those decisions.**

**Goal:** Ship 2 rostered agents (cover-letter-writer #20 Sonnet 4.6 high; response-to-reviewers #21 Opus 4.7 xhigh), 4 skills (`/sws:write-cover-letter`, `/sws:respond-to-reviewers`, `/sws:disclose-ai-usage`, `/sws:run-cycle`), 4 helper scripts (response_matrix, disclosure_writer, review_round, run_cycle), 1 reference doc (submission-artifacts), `_review/round-<N>/` + `_submission/` folder schemas, passport submission-phase fields, profile-activation updates across all 9 profiles, full unit + smoke test suite. End-of-cycle: full v0.1-alpha pipeline reachable from a single `/sws:run-cycle` command.

**Architecture:** Same thin-agent pattern as cycles #7–#11. Each agent sources `agent_prelude.sh`, calls `agent_should_run.sh`, then performs its narrow job. `cover-letter-writer` and `response-to-reviewers` are PROSE generators (write to `_submission/`, never to the manuscript `.docx`). `sws_response_matrix.py` is deterministic Python — no LLM. `/sws:run-cycle` is a thin Python orchestrator that dispatches existing skills in phase order with idempotency.

**Tech Stack:** Python 3.9+ via per-paper `.venv/`, stdlib-only (no new deps). Bash for skills. Markdown + YAML frontmatter for agents, profiles, references. `unittest` (stdlib) for unit tests. Shell smoke for e2e.

**Spec source of truth:** `docs/superpowers/specs/2026-05-30-cycle-12-submission-orchestration-design.md`. Frontmatter dictionary is canonical; this plan implements D1–D20.

**Execution mode:** Autonomous. Maximize within-phase parallelism. Open PR in READY state (not draft) for user merge.

---

## File Structure

**CREATE (new files):**

Scripts:
- `scripts/sws_response_matrix.py`
- `scripts/sws_disclosure_writer.py`
- `scripts/sws_review_round.py`
- `scripts/sws_run_cycle.py`

References:
- `references/submission-artifacts.md`

Agents (2 files):
- `agents/cover-letter-writer.md`
- `agents/response-to-reviewers.md`

Skills (4 dirs, each with one SKILL.md):
- `skills/write-cover-letter/SKILL.md`
- `skills/respond-to-reviewers/SKILL.md`
- `skills/disclose-ai-usage/SKILL.md`
- `skills/run-cycle/SKILL.md`

Tests:
- `tests/test_response_matrix.py`
- `tests/test_disclosure_writer.py`
- `tests/test_review_round.py`
- `tests/test_run_cycle.py`
- `tests/test_section_router_submit_action.py`
- `tests/test_profile_activation_submission.py`
- `tests/test_passport_submission_fields.py`
- `tests/fixtures/sample-cycle-12/` (fixture dir with .sws-project.local.md + outline.md + _drafts/ + _review/<agent>/ + _review/round-1/reviewer-comments.md)
- `tests/smoke_cycle_12.sh`

**MODIFY (existing files):**
- `references/agent-contract.md` — extend R3 I/O inventory with `_review/round-<N>/` and `_submission/` shapes
- `scripts/sws_section_router.py` — add 7th action axis: `submit` (routes cover-letter|response|disclosure)
- `scripts/sws_hook_stop_passport.py` — passport schema extension (optional `phase`, `venue`, `round` fields)
- `profiles/full-article.md` — agents_active: + [cover-letter-writer, response-to-reviewers]
- `profiles/communication.md` — same
- `profiles/perspective.md` — same
- `profiles/review-paper.md` — same
- `profiles/mini-review.md` — same
- `profiles/methodological-paper.md` — same
- `profiles/commentary-reply.md` — same
- `profiles/editorial.md` — agents_active: + [cover-letter-writer]; agents_inactive: + [response-to-reviewers]
- `profiles/funding-proposal.md` — agents_inactive: + [cover-letter-writer, response-to-reviewers]
- `claude_memory/project_v02_backlog.md` — append cycle-12 deferred items
- `claude_memory/project_cycle_execution_status.md` — mark cycle #12 PR-open at end

---

## Phase Map (for parallel dispatch)

**Phase 1 — Foundation scripts + reference doc (5 tasks, parallelizable):** `sws_response_matrix.py`, `sws_disclosure_writer.py`, `sws_review_round.py`, `sws_run_cycle.py` (planner skeleton only), `references/submission-artifacts.md`.

**Phase 2 — Router + passport extension (3 tasks, parallel, depends on Phase 1 file conventions):** section-router 7th axis, passport stop-hook fields, agent-contract R3 update.

**Phase 3 — Agents (2 tasks, parallel, depends on Phase 1):** `cover-letter-writer.md`, `response-to-reviewers.md`.

**Phase 4 — Skills (4 tasks, parallel, depends on Phase 3 agents):** `/sws:write-cover-letter`, `/sws:respond-to-reviewers`, `/sws:disclose-ai-usage`, `/sws:run-cycle`.

**Phase 5 — Profile updates (9 tasks, parallel, depends on Phase 3):** all 9 profile files.

**Phase 6 — Unit tests (7 tasks, parallel, depends on Phase 1–5):** response_matrix, disclosure_writer, review_round, run_cycle, section_router_submit, profile_activation_submission, passport_submission_fields.

**Phase 7 — Fixtures + smoke + PR (sequential, depends on all prior):** `tests/fixtures/sample-cycle-12/`, `tests/smoke_cycle_12.sh`, commit, push, open PR (ready, not draft).

---

## PHASE 1 — Foundation scripts + reference doc

These tasks are independent and parallelize fully.

### Task 1.1: Reference doc — `references/submission-artifacts.md`

**Files:** Create `references/submission-artifacts.md`.

Content (full doc; YAML frontmatter as project-memory dictionary, body is orientation):

````markdown
---
sws_artifact: submission-artifacts
artifact_version: 0.1
locked: 2026-05-30
used_by:
  - agents/cover-letter-writer.md
  - agents/response-to-reviewers.md
  - scripts/sws_disclosure_writer.py
  - scripts/sws_response_matrix.py
  - skills/write-cover-letter/SKILL.md
  - skills/respond-to-reviewers/SKILL.md
  - skills/disclose-ai-usage/SKILL.md

folder_schemas:
  _review/round-<N>/:
    reviewer-comments.md: USER-PROVIDED (or pasted from journal email/portal); markdown
    response-matrix.json: sws_response_matrix.py output; deterministic parse
    response-to-reviewers.md: response-to-reviewers agent output
    edits-summary.md: optional agent-generated edit log
  _submission/:
    cover-letter.md: cover-letter-writer agent output
    ai-disclosure.md: sws_disclosure_writer.py output
    response-to-reviewers-round-<N>.md: copy of _review/round-<N>/response-to-reviewers.md for journal upload

reviewer_comments_accepted_shapes:
  shape_a:
    description: "Per-reviewer headings with numbered/bulleted comments"
    example: |
      ## Reviewer 1
      1. The novelty claim in the abstract overreaches.
      2. Figure 3 lacks error bars.
      ## Reviewer 2
      - Methodology is sound but Section 4.2 needs clarification.
  shape_b:
    description: "Flat numbered list (single implicit reviewer)"
    example: |
      1. The introduction misses ref. X.
      2. Equation 3 needs derivation.
  shape_c:
    description: "Prefixed ID per Imbad0202 convention"
    example: |
      R1.1: The novelty claim overreaches.
      R1.2: Figure 3 lacks error bars.
      R2.1: Section 4.2 needs clarification.

response_matrix_schema:
  type: list of comment objects
  comment_fields:
    id: "R<reviewer>.<comment>"; e.g. R1.2
    reviewer: int
    text: string (verbatim reviewer comment)
    severity_inferred: enum [major, minor, suggestion]; inferred from keywords (must|should|consider|optional)
    status: enum [pending, accepted, partial, rejected]; default pending
    response_text: string; agent fills
    edits_made: list of strings (each: section + edit description); agent fills
    line_refs: list of "file:line" pointers into _drafts/ or final .docx; agent fills

disclosure_templates:
  icmje:
    body_template: |
      The author(s) used generative AI tools (Anthropic Claude via the Scientific Writing Superpowers
      plugin) to assist with manuscript preparation. All scientific claims, data interpretations, and
      conclusions are the author's own, and the author takes full responsibility for the manuscript's
      content. AI-assisted writing was used for {USE_CATEGORIES}; all AI output was reviewed and revised
      by the author.
    use_categories_options: [drafting prose, copyediting, formatting references, generating figure captions, summarising prior work]
    policy_url: "https://www.icmje.org/recommendations/"
    last_verified: "2026-05-30"
  wiley:
    body_template: |
      Generative AI tools (Anthropic Claude via the Scientific Writing Superpowers plugin) were used to
      assist with {USE_CATEGORIES}. The author(s) reviewed and edited all AI-generated content and take
      full responsibility for the integrity of the manuscript. AI was not used to generate or interpret
      scientific data, nor is it listed as a co-author. This statement is provided in accordance with
      Wiley's Best Practice Guidelines on Research Integrity and Publishing Ethics.
    use_categories_options: [language polishing, structural drafting, reference formatting, caption generation]
    policy_url: "https://authorservices.wiley.com/author-resources/Journal-Authors/open-access/best-practice-guidelines-on-research-integrity-and-publishing-ethics.html"
    last_verified: "2026-05-30"
  rsc:
    body_template: |
      The author(s) declare the use of generative AI (Anthropic Claude via the Scientific Writing
      Superpowers plugin) in the preparation of this manuscript, limited to {USE_CATEGORIES}. The AI was
      not used for scientific reasoning, data analysis, or to make decisions about study design. All
      AI-assisted text was carefully reviewed, fact-checked, and revised by the author(s), who take full
      responsibility for the manuscript's content. This disclosure is provided per RSC's policy on
      generative AI in scholarly publishing.
    use_categories_options: [draft prose generation, language editing, reference formatting, figure caption drafting]
    policy_url: "https://www.rsc.org/journals-books-databases/journal-authors-reviewers/policies/"
    last_verified: "2026-05-30"
  acs:
    body_template: |
      The author(s) used generative AI (Anthropic Claude through the Scientific Writing Superpowers
      plugin) to assist with {USE_CATEGORIES} in this manuscript. All AI-assisted content was reviewed
      and edited by the author(s). The AI was not used to generate, analyse, or interpret experimental
      data, and is not listed as an author. The author(s) accept full responsibility for the manuscript
      in accordance with ACS Publishing Ethics.
    use_categories_options: [drafting prose, polishing language, formatting references, generating captions]
    policy_url: "https://pubs.acs.org/page/policy/authoring/index.html"
    last_verified: "2026-05-30"

cover_letter_canonical_structure:
  - opening_address: "Dear {EDITOR_NAME or 'Editor'}," (per D11 — never fabricate editor name)
  - opening_paragraph: one-sentence submission statement + manuscript title + manuscript type
  - significance_paragraph: 3-5 sentences on the scientific significance and novelty (no superlatives, no AI-tells)
  - fit_paragraph: 2-3 sentences explaining fit with the journal's scope
  - conflict_disclosure: brief statement on no conflicts (or list)
  - suggested_editors: optional — only if the journal overlay lists suggested_handling_editors
  - signoff: "Sincerely, {AUTHOR_NAME or '[Author Name]'}"

cover_letter_constraints:
  - max_word_count: 400
  - never_fabricate: [editor_name, journal_editor_history, prior_paper_references]
  - tone: measured, evidence-led; no superlatives ("groundbreaking", "novel" etc.)
  - must_grep_pass: scripts/sws_lint_ai_tells.py
---

# Submission Artifacts (v0.1)

This body is orientation only; **the frontmatter dictionary above is the source of truth** for folder schemas, accepted reviewer-comment shapes, the response matrix schema, the 4 disclosure templates, and the cover-letter structure.

## What this doc anchors

Three submission outputs, produced by cycle-12 agents and scripts:

1. **Cover letter** (`_submission/cover-letter.md`) — venue-specific, generated by `cover-letter-writer` from the resolved journal-style overlay + the paper's abstract + the profile.
2. **AI-usage disclosure** (`_submission/ai-disclosure.md`) — venue-specific, generated by `sws_disclosure_writer.py` from a 4-template catalog (ICMJE / Wiley / RSC / ACS).
3. **Response-to-reviewers** (`_submission/response-to-reviewers-round-<N>.md`) — generated by `response-to-reviewers` agent from the user-provided `_review/round-<N>/reviewer-comments.md` + the R&R Traceability Matrix JSON (`_review/round-<N>/response-matrix.json`) that `sws_response_matrix.py` builds deterministically.

## Folder layout

`_review/round-<N>/` lives alongside the cycle-09 `_review/<agent>/` outputs and never collides (agent folders use known agent names, never starting with "round-").

`_submission/` is new in cycle-12 and is reserved for journal-upload-ready artifacts.

## Disclosure-template selection

The journal-style overlay's `disclosure.template_id` field selects the template. v0.1 ships 4 templates; missing template_id falls back to "icmje" with a TODO. v0.2 expands the catalog.
````

- [ ] Commit: `references(submission): folder schemas, reviewer-comment shapes, R&R matrix, 4 AI-disclosure templates`

### Task 1.2: `scripts/sws_response_matrix.py`

**Files:** Create `scripts/sws_response_matrix.py`.

Deterministic markdown parser. Reads `_review/round-<N>/reviewer-comments.md`, detects shape (a/b/c per submission-artifacts.md), produces `_review/round-<N>/response-matrix.json` with the schema in submission-artifacts.md `response_matrix_schema`.

**Key behaviours:**
- Auto-detects shape. If detection fails (no `## Reviewer N` heading, no `R<n>.<m>:` prefix, no top-level numbered list), exits 3 with an error printing the 3 accepted shapes inline.
- Severity inference: keyword-based. Lowercase comment text contains `must|critical|fatal|wrong|incorrect` → major. Contains `should|important|missing` → major. Contains `consider|suggest|might|could` → suggestion. Else → minor.
- Idempotency (per D5/R3): on re-parse, preserves existing `status`/`response_text`/`edits_made`/`line_refs` fields when a comment's `id` is unchanged. New comments appended; deleted comments dropped. Field-preservation is unit-tested.
- Exit codes: 0 success, 1 file-not-found, 2 invalid markdown, 3 shape-detection failed.
- CLI: `python3 sws_response_matrix.py <reviewer-comments.md> [--out <matrix.json>]`. Default `--out`: same dir as input, filename `response-matrix.json`.
- Stdlib only (no PyYAML — we keep it portable).

- [ ] Implement, write inline docstring with usage + schema link.
- [ ] Commit: `scripts(response-matrix): deterministic md → JSON parser with shape auto-detect (D5/D6, R3 idempotent)`

### Task 1.3: `scripts/sws_disclosure_writer.py`

**Files:** Create `scripts/sws_disclosure_writer.py`.

Renders `_submission/ai-disclosure.md` from a template_id + use-categories list.

**Key behaviours:**
- Sources `agent_prelude.sh` semantics: reads marker file + resolved overlay to get `RESOLVED_DISCLOSURE_REQUIRED` (must be true to write; else exits 0 with "not required for this profile").
- Reads journal overlay's `disclosure.template_id` (one of icmje / wiley / rsc / acs). Missing → fallback to "icmje" with stderr warning.
- Use-categories: defaults to template's `use_categories_options[:3]` (top 3). CLI `--use-categories=a,b,c` overrides.
- CLI: `python3 sws_disclosure_writer.py [--paper-root <path>] [--venue <slug>] [--use-categories <csv>]`. Defaults to cwd + marker `target_journal`.
- Prints last_verified date of the chosen template to stderr (R6).
- Renders to `_submission/ai-disclosure.md`. Atomic write (tmp + rename).
- Exit codes: 0 success or not-required, 2 missing overlay, 3 unknown template_id.
- Stdlib only.

- [ ] Implement.
- [ ] Commit: `scripts(disclosure): venue-specific AI-usage statement renderer (D7, R6 last_verified)`

### Task 1.4: `scripts/sws_review_round.py`

**Files:** Create `scripts/sws_review_round.py`.

Idempotent helper for managing `_review/round-<N>/` folders.

**Key behaviours:**
- Subcommands: `init [N]` (create `_review/round-<N>/` and a template `reviewer-comments.md`; default N = highest existing + 1), `find` (print highest existing N or `none`), `inventory <N>` (print which artifacts exist in round-<N>: comments, matrix, response, edits).
- CLI: `python3 sws_review_round.py {init [N] | find | inventory <N>}`.
- Stdlib only.

- [ ] Implement.
- [ ] Commit: `scripts(review-round): init/find/inventory helper for _review/round-<N>/ folders (D3)`

### Task 1.5: `scripts/sws_run_cycle.py` (planner skeleton)

**Files:** Create `scripts/sws_run_cycle.py`.

The orchestrator driver. **Phase-1 task creates the SKELETON ONLY** — the step-plan computer + dry-run + --only filtering. The actual dispatch loop (Phase 4 / Task 4.4) wires it to the skills.

**Phase-1 skeleton scope:**
- `plan_steps(paper_root)` function: returns ordered list of step dicts `{step: int, name: str, skill: str, should_run: bool, reason: str}` following D9. Inspects:
  - marker file: `RESOLVED_COVER_LETTER_REQUIRED`, `RESOLVED_DISCLOSURE_REQUIRED`, active profile
  - filesystem: `outline.md`, `_drafts/*.md`, `_review/<agent>/`, `_submission/cover-letter.md`, `_submission/ai-disclosure.md`, `_review/round-<N>/reviewer-comments.md`
- CLI: `python3 sws_run_cycle.py {--dry-run | --only=<csv> | (no flag = full run)}`. Phase-1 implements `--dry-run` and `--only` parsing + the planner; actual dispatch is a `TODO(phase-4)` stub that prints the planned steps and exits 0.
- Stale-detection helper `is_stale(artifact, source)` with 5-second mtime tolerance window (R4).
- Stdlib only.

- [ ] Implement skeleton.
- [ ] Commit: `scripts(run-cycle): step planner skeleton + dry-run + --only (D9, D10, D14, R4)`

---

## PHASE 2 — Router + passport extension + agent-contract

Depends on Phase 1 (file conventions established). Parallel within Phase 2.

### Task 2.1: Section-router 7th action axis — `scripts/sws_section_router.py`

**Files:** Modify `scripts/sws_section_router.py`.

Add `submit` action axis. Routes:
- `cover-letter` → `/sws:write-cover-letter`
- `response` → `/sws:respond-to-reviewers`
- `disclosure` → `/sws:disclose-ai-usage`

Preserve existing 6 axes (`draft|revise|consistency|style|lint|review`) untouched.

- [ ] Read existing router, add the axis.
- [ ] Commit: `scripts(router): 7th action axis 'submit' for cover-letter|response|disclosure (D17)`

### Task 2.2: Passport extension — `scripts/sws_hook_stop_passport.py`

**Files:** Modify `scripts/sws_hook_stop_passport.py`.

Per D4 (additive-only):
- Add optional fields to passport entry: `phase` (enum: plan|draft|revise|review|submit), `venue` (string), `round` (int).
- Older entries without these fields remain valid.
- The Stop-hook continues to write its existing 5-field entry; cycle-12 only adds the SCHEMA support (downstream skills like `/sws:run-cycle` can write entries with the new fields).
- Update the schema docstring at the top of the file.

- [ ] Read existing stop-hook, add optional fields to entry-building branch. Do NOT change the default-field-emission for non-orchestrated runs.
- [ ] Commit: `passport: additive optional submission-phase fields (phase|venue|round) per D4`

### Task 2.3: Agent-contract R3 update — `references/agent-contract.md`

**Files:** Modify `references/agent-contract.md`.

Extend R3 I/O inventory with:
- `_review/round-<N>/` shape (reviewer-comments.md INPUT, response-matrix.json INTERMEDIATE, response-to-reviewers.md + edits-summary.md OUTPUT)
- `_submission/` shape (cover-letter.md, ai-disclosure.md, response-to-reviewers-round-<N>.md — all OUTPUT)

Reference `references/submission-artifacts.md` for the schemas (no duplication).

- [ ] Edit.
- [ ] Commit: `agent-contract(R3): add _review/round-<N>/ + _submission/ I/O shapes`

---

## PHASE 3 — Agents

Depends on Phase 1. Parallel within Phase 3.

### Task 3.1: `agents/cover-letter-writer.md`

**Files:** Create `agents/cover-letter-writer.md`.

Agent frontmatter:
```yaml
name: cover-letter-writer
description: Drafts a venue-specific cover letter for a journal submission. Reads the resolved journal-style overlay + paper abstract + profile. Output to _submission/cover-letter.md.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
```

Body prompt rules:
- Source `agent_prelude.sh`; run `agent_should_run.sh cover-letter-writer`.
- If not active in current profile → exit cleanly with notice.
- R5 (cycle-07): no gender-default in user address (use the user's name or "you", never male pronoun/honorific).
- R3 (cycle-07 agent-contract): use SWS read wrappers (`sws_read_docx.py`) for any .docx input.
- Cover-letter structure: follow `references/submission-artifacts.md` `cover_letter_canonical_structure`.
- Constraints: max 400 words, no superlatives, no fabricated editor name (use `{EDITOR_NAME}` placeholder + TODO comment), no fabricated prior-paper references (D11/R2).
- Must grep-pass `sws_lint_ai_tells.py` before write (D16).
- Write to `_submission/cover-letter.md`. If file exists → ask user to confirm overwrite (or accept `--force`).
- Final action: print one-line summary + path.

- [ ] Write the agent file (full content with the prompt sections).
- [ ] Commit: `agent(cover-letter-writer): Sonnet 4.6 high, venue-specific cover letter (roster #20)`

### Task 3.2: `agents/response-to-reviewers.md`

**Files:** Create `agents/response-to-reviewers.md`.

Agent frontmatter:
```yaml
name: response-to-reviewers
description: Drafts a Response-to-Reviewers document and fills the R&R Traceability Matrix. Reads _review/round-<N>/reviewer-comments.md + response-matrix.json + the paper drafts. Output to _review/round-<N>/response-to-reviewers.md (mirrored to _submission/).
tools: Read, Write, Edit, Bash, Glob, Grep
model: opus
```

Body prompt rules:
- Source `agent_prelude.sh`; run `agent_should_run.sh response-to-reviewers`.
- Reads `_review/round-<N>/response-matrix.json` (built by `sws_response_matrix.py` first; if missing, dispatch the script).
- Optionally cross-reads `_review/peer-reviewer/report.md` (cycle-09 output) for the SWS internal review's view.
- For each comment in the matrix:
  - Score 1–5 for soundness (encoded in agent prompt per D12).
  - Concede only when score ≥ 4 AND requested change does not contradict thesis/evidence.
  - Otherwise: push back with evidence, or partial-accept with explicit scope.
- Fills `status` (accepted|partial|rejected), `response_text`, `edits_made` (concrete edits per comment), `line_refs` (file:line into _drafts/) for each comment.
- Re-writes the matrix JSON (preserving comments that already had user-modified fields — coordinate with `sws_response_matrix.py` idempotency).
- Renders `_review/round-<N>/response-to-reviewers.md` (markdown table per comment + per-reviewer summary paragraph).
- Mirrors to `_submission/response-to-reviewers-round-<N>.md`.
- R5 no gender-default; R3 wrappers for .docx.
- Must grep-pass `sws_lint_ai_tells.py` before write (D16).
- R1 cost warning: prompt explicitly says "Run only after a finalized revision and after receiving actual reviewer comments."

- [ ] Write the agent file.
- [ ] Commit: `agent(response-to-reviewers): Opus 4.7 xhigh, R&R matrix + rebuttal prose (roster #21, D12)`

---

## PHASE 4 — Skills

Depends on Phase 3. Parallel within Phase 4.

### Task 4.1: `/sws:write-cover-letter` — `skills/write-cover-letter/SKILL.md`

**Files:** Create `skills/write-cover-letter/SKILL.md`.

Skill structure:
- Step a: marker check (cwd marker present? else exit with "Run /sws:init-project first").
- Step b: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh`.
- Step c: if `--venue=<slug>` flag given, override `RESOLVED_VENUE`; else use `target_journal` from marker (D18).
- Step d: dispatch the `cover-letter-writer` agent with the resolved context.
- Step e: post-step: print `_submission/cover-letter.md` path + word count + grep-pass status.

`--force` flag for overwrite (mentioned in agent).

- [ ] Write the SKILL.md (full content + frontmatter).
- [ ] Commit: `skill(/sws:write-cover-letter): wrapper for cover-letter-writer agent + --venue + --force`

### Task 4.2: `/sws:respond-to-reviewers` — `skills/respond-to-reviewers/SKILL.md`

**Files:** Create `skills/respond-to-reviewers/SKILL.md`.

Skill structure:
- Step a: marker check.
- Step b: source agent_prelude.sh.
- Step c: parse `--round <N>` (default: highest existing N from `sws_review_round.py find`).
- Step d: verify `_review/round-<N>/reviewer-comments.md` exists; else exit with init-comments instructions.
- Step e: invoke `sws_response_matrix.py` to build/update matrix.json (deterministic, no LLM).
- Step f: dispatch `response-to-reviewers` agent on the matrix.
- Step g: print summary (rebuttal word count, concession count, status counts, grep-pass status).

- [ ] Write.
- [ ] Commit: `skill(/sws:respond-to-reviewers): wraps response-to-reviewers agent + --round + matrix preflight`

### Task 4.3: `/sws:disclose-ai-usage` — `skills/disclose-ai-usage/SKILL.md`

**Files:** Create `skills/disclose-ai-usage/SKILL.md`.

Skill structure:
- Step a: marker check.
- Step b: source agent_prelude.sh.
- Step c: if `RESOLVED_DISCLOSURE_REQUIRED` is false → exit clean with "Disclosure not required for this profile" notice.
- Step d: parse `--venue` (override) and `--use-categories=a,b,c` flags (D18).
- Step e: invoke `sws_disclosure_writer.py` (deterministic, no agent dispatch).
- Step f: print path + last_verified date warning.

- [ ] Write.
- [ ] Commit: `skill(/sws:disclose-ai-usage): wraps sws_disclosure_writer.py + --venue + --use-categories`

### Task 4.4: `/sws:run-cycle` — `skills/run-cycle/SKILL.md`

**Files:** Create `skills/run-cycle/SKILL.md`. Wire `scripts/sws_run_cycle.py` dispatch (Phase-1 stub upgrade).

Skill structure:
- Step a: marker check.
- Step b: parse `--dry-run`, `--only=<csv>` flags.
- Step c: invoke `sws_run_cycle.py` to compute step plan.
- Step d: if `--dry-run` → print plan and exit.
- Step e: else dispatch each planned step (each step calls the corresponding skill via the agent SDK's skill-invocation mechanism). Skip steps marked `should_run: false`.
- Step f: at end, write ONE passport entry with `phase: submit`, `change_summary` listing steps run, `next_step` listing TODOs or "ready for upload" if all artifacts exist.

Also upgrade `sws_run_cycle.py` from skeleton: replace the Phase-1 `TODO(phase-4)` stub with the actual dispatch logic. Dispatch can be implemented via subprocess calls to the skill bash entry-points, or — simpler — by printing a directive list that the SKILL.md bash body reads + executes.

Choose: SKILL.md bash body reads the planner's JSON output and dispatches via `claude -p` invocations OR via dispatching the corresponding script. **Pick the script-dispatch path** (idempotent, testable): the planner emits a list of skill names; the SKILL.md `case` statement maps each skill name to its bash entry-point and runs them in order. Steps that need agent dispatch (cover-letter-writer, response-to-reviewers) emit a "MANUAL: dispatch the cover-letter-writer agent" line that the user (or the calling agent context) acts on.

- [ ] Write SKILL.md + finalise sws_run_cycle.py dispatch.
- [ ] Commit: `skill(/sws:run-cycle): master orchestrator dispatching outline → draft → revise → review → submission (D9, D10, D14)`

---

## PHASE 5 — Profile updates

9 files, all parallel. Each adds `cover-letter-writer` and/or `response-to-reviewers` per D8.

For each profile file in `profiles/`:
- [ ] Read existing `agents_active` and `agents_inactive` lists.
- [ ] Apply D8 activation matrix:
  - full-article, communication, perspective, review-paper, mini-review, methodological-paper, commentary-reply: + both agents in `agents_active`.
  - editorial: + cover-letter-writer in `agents_active`; + response-to-reviewers in `agents_inactive`.
  - funding-proposal: + both agents in `agents_inactive`.
- [ ] Commit (one commit covering all 9): `profiles: D8 activation matrix for cover-letter-writer + response-to-reviewers`

---

## PHASE 6 — Unit tests

7 test files, all parallel. Depends on Phases 1–5.

### Task 6.1: `tests/test_response_matrix.py`

- Detects shape a/b/c correctly.
- Parses 3-reviewer × 5-comment fixture correctly.
- Severity inference covers each keyword cluster.
- Idempotent re-parse preserves `status`/`response_text`/`edits_made` for unchanged IDs.
- New comments appended; deleted comments dropped on re-parse.
- Shape-detection failure exits 3 with the expected error message.
- [ ] Implement.

### Task 6.2: `tests/test_disclosure_writer.py`

- Renders each of the 4 templates correctly.
- `RESOLVED_DISCLOSURE_REQUIRED=false` → exits 0 with "not required" message.
- Missing `template_id` → falls back to "icmje" with stderr warning.
- Unknown `template_id` → exits 3.
- Prints `last_verified` to stderr.
- [ ] Implement.

### Task 6.3: `tests/test_review_round.py`

- `init` creates `_review/round-1/` with reviewer-comments.md template when none exists.
- `init` with explicit N creates `round-<N>/`.
- `find` returns the highest existing N, or `none`.
- `inventory <N>` correctly reports which artifacts exist.
- [ ] Implement.

### Task 6.4: `tests/test_run_cycle.py`

- Planner produces correct step list for each of the 9 profiles.
- Idempotent skip: when artifacts exist, those steps are marked `should_run: false`.
- `--dry-run` prints plan + exits 0 without dispatch.
- `--only=cover-letter,disclosure` filters to those two steps.
- Stale-detection: when source `_drafts/*.md` mtime > `_submission/cover-letter.md` mtime + 5s → step planner prints "stale: cover-letter.md predates current draft" notice (but does not auto-trigger; D10).
- [ ] Implement.

### Task 6.5: `tests/test_section_router_submit_action.py`

- The `submit` action axis exists.
- `cover-letter` / `response` / `disclosure` route correctly.
- Existing 6 axes routes unchanged (regression check).
- [ ] Implement.

### Task 6.6: `tests/test_profile_activation_submission.py`

- Read all 9 profile YAML frontmatters directly.
- Assert the D8 matrix for cover-letter-writer + response-to-reviewers.
- Regression check: other agents' activations unchanged.
- [ ] Implement.

### Task 6.7: `tests/test_passport_submission_fields.py`

- Entry with `phase`, `venue`, `round` fields validates.
- Entry WITHOUT them (older 5-field entry) validates too.
- JSON schema unchanged otherwise.
- [ ] Implement.

After Phase 6:
- [ ] Run full unittest suite. Target: ~750 passing total (current ~680 + ~60-70 new).
- [ ] Commit (one per test): `tests(<area>): ...`

---

## PHASE 7 — Fixtures + smoke + PR

Sequential. Depends on all prior phases.

### Task 7.1: Smoke fixtures — `tests/fixtures/sample-cycle-12/`

Create directory `tests/fixtures/sample-cycle-12/` with:
- `.sws-project.local.md` (marker: sws_version=0.1, article_type=full-article, language=en, format=docx, target_journal=chembiochem, notebooklm.enabled=false, created=...)
- `outline.md` (4 lines: abstract / intro / results / conclusions)
- `_drafts/abstract.md`, `_drafts/introduction.md`, `_drafts/results.md`, `_drafts/conclusions.md` (each: 2-3 trivial paragraphs)
- `_review/peer-reviewer/report.md`, `_review/claim-verifier/report.md`, `_review/bibliography-fidelity-checker/report.md` (each: 5-line placeholder)
- `_review/round-1/reviewer-comments.md` with 2 reviewers × 3 comments each, in shape (a)

- [ ] Create fixtures.

### Task 7.2: `tests/smoke_cycle_12.sh`

Steps (12 total):
1. Set up `tmp/sws-smoke-12/` from fixture.
2. Run `sws_response_matrix.py` on `_review/round-1/reviewer-comments.md`. Assert matrix.json created with correct structure (`jq` check or grep for shape).
3. Re-run `sws_response_matrix.py` after manually adding a `response_text` to one comment. Assert that text is preserved.
4. Run `sws_disclosure_writer.py` with marker `disclosure_required: true` and `target_journal: chembiochem`. Assert `_submission/ai-disclosure.md` created and contains the appropriate template body.
5. Run `sws_review_round.py find`. Assert output `1`.
6. Run `sws_review_round.py inventory 1`. Assert all 4 expected artifacts listed (comments + matrix + responses-still-missing).
7. Run `sws_section_router.py submit cover-letter`. Assert routes to `/sws:write-cover-letter`.
8. Run `sws_run_cycle.py --dry-run`. Assert step plan printed and all 4 review-phase steps marked `should_run: false` (artifacts exist), and `should_run: true` for cover-letter + disclosure + response.
9. Run `sws_run_cycle.py --only=disclosure`. Assert it dispatches the disclosure step only.
10. Verify passport entry written with `phase: submit` after step 9.
11. Run full unittest suite from cycle-12 tests; assert 0 failures.
12. Print "SMOKE PASS: 12/12".

- [ ] Implement smoke.

### Task 7.3: Memory + status updates

- `claude_memory/project_v02_backlog.md` — append 5 new deferred items per spec scope.not_in_scope (per-portal submission automation, OCR-ingest reviewer PDF, multi-round automation, inline docx-comment threading, disclosure-catalog expansion).
- `claude_memory/project_cycle_execution_status.md` — update cycle-12 row: PR open + branch name.

- [ ] Edit both files.

### Task 7.4: Branch + commit + push + PR

- [ ] Create branch `cycle/12-submission-orchestration` from main.
- [ ] Stage and commit each phase's work in sensible commits (already done per-task; final cycle-spec + plan commits if not already).
- [ ] Push branch.
- [ ] Open PR (ready, NOT draft) titled `Cycle 12 — Submission orchestration (2 agents, 4 skills, R&R matrix, AI-disclosure, run-cycle orchestrator)` with the spec frontmatter scope.deliverable as the body summary + a checklist of D1–D20.
- [ ] Print PR URL.

---

## Exit criteria

- [ ] All 7 phases complete; all tests pass; smoke 12/12.
- [ ] PR opened (ready) at `github.com/piripocchio8/scientific-writing-superpowers`.
- [ ] Branch `cycle/12-submission-orchestration` pushed.
- [ ] `claude_memory/project_cycle_execution_status.md` updated.
- [ ] No identity / local-paths / collaborator info in any committed file (project STANDING RULE; grep diffs before each commit).
- [ ] Banner remains `🧪 v0.1 alpha` (no flip this cycle).
