# Cycle #8 — Revising — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) to dispatch the parallel tasks below. Each task is independent within its phase. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 5 revising agents (reviser-full / reviser-fast / humanizer / style-enforcer / consistency-checker), 5 skills (`/sws:revise-paper`, `/sws:revise-section`, `/sws:enforce-style`, `/sws:check-consistency`, `/sws:lint-ai-tells`), 1 reference doc (chemistry-formatting), 5 wrapper scripts (3 docx WRITE wrappers + AI-tells linter + consistency-check static-analysis core), 1 router extension (action axis), 1 agent-contract update, 9 profile updates, and an e2e smoke. End-of-cycle: a user with cycle-#7 drafts in `_drafts/` can run `/sws:revise-paper` and end up with a final `Manuscript/<paper>.docx`.

**Spec source of truth:** `docs/superpowers/specs/2026-05-14-cycle-08-revising-design.md`. Frontmatter (D1–D20) is canonical; this plan implements it.

**Tech Stack:** Bash (skills), Python 3.9+ via per-paper `.venv/` (python-docx, openpyxl, PyYAML — all already in cycle-#7 `requirements/sws-deps.txt`), markdown + YAML frontmatter, pytest, shell smoke.

**Autonomous-run caveat:** This plan was written overnight on 2026-05-14 alongside the spec. The PR opens in draft state for user revision tomorrow morning.

---

## File Structure

**CREATE (new files):**

References:
- `references/chemistry-formatting.md`

Scripts:
- `scripts/sws_write_docx.py`
- `scripts/sws_restyle_docx.py`
- `scripts/sws_apply_chemistry_format.py`
- `scripts/sws_lint_ai_tells.py`
- `scripts/sws_consistency_check.py`

Agents (5 files):
- `agents/reviser-full.md`
- `agents/reviser-fast.md`
- `agents/humanizer.md`
- `agents/style-enforcer.md`
- `agents/consistency-checker.md`

Skills (5 dirs, each with one SKILL.md):
- `skills/revise-paper/SKILL.md`
- `skills/revise-section/SKILL.md`
- `skills/enforce-style/SKILL.md`
- `skills/check-consistency/SKILL.md`
- `skills/lint-ai-tells/SKILL.md`

Tests:
- `tests/test_write_docx.py`
- `tests/test_restyle_docx.py`
- `tests/test_apply_chemistry_format.py`
- `tests/test_lint_ai_tells.py`
- `tests/test_consistency_check.py`
- `tests/test_chemistry_formatting_catalog.py`
- `tests/test_revising_section_router.py`
- `tests/test_revising_agent_activation.py`
- `tests/fixtures/cycle_08_paper/` (mirrors `cycle_07_paper` but seeded with `_drafts/<section>.md`)
- `tests/fixtures/manuscripts/styled_ok.docx` (generation script + committed binary)
- `tests/fixtures/manuscripts/word_default.docx` (generation script + committed binary)
- `tests/smoke_cycle_08.sh`

**MODIFY (existing files):**

- `scripts/sws_section_router.py` — add `action` axis (D12 of spec)
- `references/agent-contract.md` — add WRITE wrappers + linter to I/O wrapper inventory (cross-cutting block of spec)
- `profiles/*.md` (all 9) — add cycle-#8 agents to `agents_active` per D13
- `tests/smoke_cycle_07.sh` — adjust any assertions that touch the router action axis (verify no breakage)

---

## Pre-flight (Task 0)

### Task 0: Create feature branch

**Files:**
- (none — branch only)

- [ ] **Step 1: Confirm we're on `main` and clean**

```bash
git status
git log --oneline -3
```

- [ ] **Step 2: Create branch**

```bash
git checkout -b cycle/08-revising
```

---

## Phase 1 — Foundation (parallel)

Six independent deliverables. Dispatch six subagents in parallel. Task A blocks Task D (D depends on the chemistry catalog). All others are independent.

### Task 1A: `references/chemistry-formatting.md`

**Files:**
- Create: `references/chemistry-formatting.md`
- Create: `tests/test_chemistry_formatting_catalog.py`

- [ ] **Step 1: Author the YAML catalog**

Implement per spec D6. Frontmatter dictionary with categories: `latin_abbreviations`, `chemical_formulae`, `species_names`, `species_abbreviated`, `gene_names`, `figure_label_prefix`. Each pattern: regex, apply (italic|subscript|superscript|bold), severity (auto|suggest), example_before, example_after, why. Body is orientation only.

Source patterns from spec D6 schema. Add a `lang: en` field — Italian deferred to v0.2.

- [ ] **Step 2: Author the catalog validator test**

`tests/test_chemistry_formatting_catalog.py`:
- All categories have ≥1 pattern.
- Every pattern has fields: regex (compilable), apply, severity, example_before, example_after, why.
- severity is one of `auto|suggest`.
- apply is one of `italic|subscript|superscript|bold`.
- regex compiles via `re.compile` without error.
- example_before matches the regex; example_after does NOT match (after the transform applies).

- [ ] **Step 3: Run test, commit**

```bash
"$PAPER_ROOT/.venv/bin/python" -m pytest tests/test_chemistry_formatting_catalog.py -v
git add references/chemistry-formatting.md tests/test_chemistry_formatting_catalog.py
git commit -m "feat(cycle-08): chemistry-formatting reference catalog (D11 deferral from cycle-07)"
```

### Task 1B: `scripts/sws_write_docx.py`

**Files:**
- Create: `scripts/sws_write_docx.py`
- Create: `tests/test_write_docx.py`
- Create: `tests/fixtures/manuscripts/_gen_styled_ok.py` (generator script for the fixture)
- Create: `tests/fixtures/manuscripts/styled_ok.docx` (committed binary)

- [ ] **Step 1: Implement `sws_write_docx.py`**

CLI:
```
sws_write_docx.py <output.docx> --from-markdown <md-file>
sws_write_docx.py <output.docx> --from-stitched <stitched.md>
sws_write_docx.py <output.docx> --from-drafts-dir <drafts-dir> --profile <profile-id>
```

Behavior:
- Read source markdown.
- Parse heading structure: `# H1` → SWS-H1; `## H2` → SWS-H2; body → SWS-Body.
- Lines that look like figure captions (start with `**Figure N.**` or `**Table N.**`) → SWS-Caption.
- Lines under a `## References` heading → SWS-References.
- Build .docx via `python-docx`, defining the five SWS styles in `word/styles.xml` (per references/docx-style.md frontmatter).
- Write to output path.

Exit codes: 0 ok, 2 input file not found, 3 python-docx error.

Reuse the style definitions from `references/docx-style.md` — read it at script start, build the style XML from the YAML. Don't hardcode style values in the Python file.

- [ ] **Step 2: Implement tests**

`tests/test_write_docx.py`:
- Empty markdown → empty docx with the five styles defined.
- One H1 + body → one SWS-H1 paragraph + N SWS-Body paragraphs.
- H1 / H2 / body / figure caption / references → correct style applied to each.
- Missing input file → exit 2.
- Style values read from references/docx-style.md (mock it, change the YAML, verify the generated docx picks up the change).

- [ ] **Step 3: Generate fixture**

`tests/fixtures/manuscripts/_gen_styled_ok.py` — a tiny python script that runs sws_write_docx.py on a hardcoded markdown sample to produce `styled_ok.docx`. Commit the resulting docx binary alongside the generator.

- [ ] **Step 4: Run tests, commit**

```bash
"$PAPER_ROOT/.venv/bin/python" -m pytest tests/test_write_docx.py -v
git add scripts/sws_write_docx.py tests/test_write_docx.py tests/fixtures/manuscripts/
git commit -m "feat(cycle-08): sws_write_docx.py WRITE wrapper (D22 deferral from cycle-07)"
```

### Task 1C: `scripts/sws_restyle_docx.py`

**Files:**
- Create: `scripts/sws_restyle_docx.py`
- Create: `tests/test_restyle_docx.py`
- Create: `tests/fixtures/manuscripts/_gen_word_default.py` (fixture generator)
- Create: `tests/fixtures/manuscripts/word_default.docx` (committed binary)

- [ ] **Step 1: Implement `sws_restyle_docx.py`**

CLI:
```
sws_restyle_docx.py <input.docx>            # restyles in place (after backup hook)
sws_restyle_docx.py <input.docx> --out <output.docx>
```

Behavior:
- Open existing .docx.
- For each paragraph, detect old style:
  - `Heading 1` / `Title` → SWS-H1
  - `Heading 2` / `Heading 3` / `Heading 4` / `Subtitle` → SWS-H2
  - `Normal` / `Body Text` / no style → SWS-Body
  - paragraphs matching `^Figure \d+|^Table \d+|^Fig\. \d+` start → SWS-Caption
  - paragraphs under a `References` heading → SWS-References
- Replace style assignment.
- PRESERVE direct character formatting (bold, italic, underline) — DO NOT clear runs.
- PRESERVE highlight color, comment markers.
- Inject SWS styles into `word/styles.xml` if not present (idempotent).
- Write output (in place or to --out).

Mitigation for R2: a test asserts that an explicit italic run survives restyle.

- [ ] **Step 2: Implement tests**

`tests/test_restyle_docx.py`:
- Word-default docx (Heading 1/2 styles) → restyled docx has SWS-H1/H2.
- Direct italic run survives restyle (R2 mitigation).
- Idempotence: restyle(restyle(x)) == restyle(x) byte-for-byte (or at minimum, no style drift).
- Already-SWS-styled docx → no changes (no-op).
- Highlight color preserved.

- [ ] **Step 3: Generate fixture**

`_gen_word_default.py` — uses python-docx to produce a docx with `Heading 1`, `Heading 2`, `Normal` styles + one italic run.

- [ ] **Step 4: Run tests, commit**

```bash
git add scripts/sws_restyle_docx.py tests/test_restyle_docx.py tests/fixtures/manuscripts/_gen_word_default.py tests/fixtures/manuscripts/word_default.docx
git commit -m "feat(cycle-08): sws_restyle_docx.py WRITE wrapper (D22)"
```

### Task 1D: `scripts/sws_apply_chemistry_format.py` (DEPENDS ON 1A)

**Files:**
- Create: `scripts/sws_apply_chemistry_format.py`
- Create: `tests/test_apply_chemistry_format.py`

- [ ] **Step 1: Implement the script**

CLI:
```
sws_apply_chemistry_format.py <input.docx>
sws_apply_chemistry_format.py <input.docx> --out <output.docx>
sws_apply_chemistry_format.py <input.docx> --dry-run    # report what would change, no write
sws_apply_chemistry_format.py <input.docx> --severity auto    # apply only auto-severity (default)
sws_apply_chemistry_format.py <input.docx> --severity all     # apply auto and suggest (suggest = flagged in stdout)
```

Behavior:
- Read references/chemistry-formatting.md, extract categories.
- For each paragraph in the docx, scan runs for each pattern.
- When a pattern matches:
  - apply=italic → set the matched run (or split run) to italic
  - apply=subscript → set vertAlign to subscript via run XML
  - apply=superscript → set vertAlign to superscript
  - apply=bold → set bold true on the matched span
- Track applied counts per category; print summary at end.
- severity=suggest patterns: report only by default; with `--severity all`, apply them too.
- format=latex marker → exit 0 with "skipped (format=latex)" message (D7).

The trickiest case is splitting a run at a regex match position. python-docx does not natively support run-splitting; implement a helper that walks paragraph XML directly via lxml.

- [ ] **Step 2: Implement tests**

`tests/test_apply_chemistry_format.py`:
- "H2O is a solvent" → "H₂O is a solvent" with subscript on the 2.
- "et al." → italic "et al.".
- "E. coli grows" → italic "E. coli grows" (species_abbreviated, auto).
- "Genus species pattern" → suggest only, NOT applied with default severity.
- "Figure 1. Caption text" → bold "Figure 1." prefix, regular body.
- format=latex (mock marker) → no-op exit 0.
- Dry-run does not write the file.
- Idempotence: applying twice yields the same docx (or byte-identical).

- [ ] **Step 3: Run tests, commit**

```bash
git add scripts/sws_apply_chemistry_format.py tests/test_apply_chemistry_format.py
git commit -m "feat(cycle-08): sws_apply_chemistry_format.py — applies chemistry-formatting catalog to .docx"
```

### Task 1E: `scripts/sws_lint_ai_tells.py`

**Files:**
- Create: `scripts/sws_lint_ai_tells.py`
- Create: `tests/test_lint_ai_tells.py`
- Modify: `references/ai-writing-tells.md` — add `linter_rule:` field to ~3 tells (em-dash overuse, sentence-initial connector adverbs, stacked compound adjectives) per D8 / D20

- [ ] **Step 1: Implement the linter**

CLI:
```
sws_lint_ai_tells.py <file.md>
sws_lint_ai_tells.py <file.md> --severity block      # show only block
sws_lint_ai_tells.py <file.md> --severity warn       # show only warn
sws_lint_ai_tells.py <file.md> --severity all        # show all (default)
sws_lint_ai_tells.py <file.md> --json                # JSON output for agent consumption
```

Behavior:
- Read references/ai-writing-tells.md, extract all tells with regex + severity + optional linter_rule.
- Read the input markdown.
- Skip text inside ` ``` ` fenced blocks (any language).
- Skip text inside inline `code` spans.
- Skip text inside `[CITATION_NEEDED: ...]` placeholders.
- For each tell, find matches in the remaining prose.
- If linter_rule.min_count_per_paragraph: only emit a finding if the pattern fires ≥N times in the same paragraph (paragraph = blank-line-delimited block).
- Else: emit one finding per match.
- Each finding: line, column, snippet (~80 chars context), pattern_name, severity, why.
- Stdout: human-readable findings, grouped by severity.
- Exit code 0 if no block-severity findings, 1 otherwise.

- [ ] **Step 2: Add `linter_rule:` to ~3 tells**

In `references/ai-writing-tells.md`:
- The em-dash-overuse pattern (` — [a-zA-Z]+ — `) gets `linter_rule: { min_count_per_paragraph: 3 }`.
- The sentence-initial connector pattern (`(?im)^\s*(Furthermore|Moreover|...),`) gets `linter_rule: { min_count_per_paragraph: 2 }` (sentence-initial connectors are fine once per paragraph; flag when stacked).
- The stacked compound adjectives pattern gets `linter_rule: { min_count_per_paragraph: 2 }` (a single compound-adjective triplet is acceptable; flag when piled).

- [ ] **Step 3: Implement tests**

`tests/test_lint_ai_tells.py`:
- "We delve into the kinetics" → 1 block finding (delve is block-severity).
- "Furthermore, X. Y. Z." (one Furthermore) → no finding (linter_rule min_count 2).
- "Furthermore, X. Moreover, Y." (two connectors) → 1 warn finding.
- Code fence content with "delve" → no finding (skip rule).
- "[CITATION_NEEDED: leverage]" → no finding (placeholder skip).
- --json returns valid JSON with the right schema.
- Exit code 0 when no block; 1 when block.

- [ ] **Step 4: Run tests, commit**

```bash
git add scripts/sws_lint_ai_tells.py references/ai-writing-tells.md tests/test_lint_ai_tells.py
git commit -m "feat(cycle-08): sws_lint_ai_tells.py — context-aware AI-tells linter (D5 follow-up)"
```

### Task 1F: `scripts/sws_consistency_check.py`

**Files:**
- Create: `scripts/sws_consistency_check.py`
- Create: `tests/test_consistency_check.py`

- [ ] **Step 1: Implement the static-analysis core**

CLI:
```
sws_consistency_check.py <drafts-dir>
sws_consistency_check.py <drafts-dir> --outline _outline/outline.md
sws_consistency_check.py <drafts-dir> --json
```

Checks (per D9):
1. Figure-reference cross-check: scan prose for `Fig\.?\s\d+`, `Figure \d+`, `Figures \d+( and \d+)*`; ensure each cited figure exists in `_outline/outline.md`'s `figures:` dict.
2. Table-reference cross-check: same pattern for tables.
3. Section-list cross-check: section IDs in drafts-dir filenames match profile's required sections.
4. Citation-key uniqueness: parse `[Author Year; doi:X]` keys via existing `scripts/sws_citation_key.py`; flag duplicates with different DOIs.
5. Abbreviation introduction: detect `(?P<full>[A-Z][a-z][^()]{2,40})\s\((?P<abbr>[A-Z]{2,})\)` as introductions; subsequent abbreviation occurrences must match an introduced abbreviation. Read sections in profile order (whole document, not per-section in isolation — R3 mitigation).
6. Terminology uniformity: case-sensitive token frequency table; flag terms that appear in ≥2 case variants with combined freq ≥ 3 (e.g., "thrombin" 4× + "Thrombin" 2×).

Output:
- Human-readable to stdout.
- `--json` for agent consumption.
- Writes `_review/consistency-report.md` per spec auxiliary_file_shapes.

Exit code 0 if no block findings, 1 otherwise. Severity: missing figure ref = block; duplicate citation key = block; case-variant terminology = warn; never-defined abbreviation = warn (could be standard like NMR/DOI).

- [ ] **Step 2: Implement tests**

`tests/test_consistency_check.py`:
- All checks individually: pass/fail cases for each.
- Abbreviation cross-section: introduced in Methods, used in Results → no false negative.
- Funding-proposal profile → exits 0 with "unsupported profile" message (D19).
- JSON output schema validates.
- Report file shape matches spec.

- [ ] **Step 3: Run tests, commit**

```bash
git add scripts/sws_consistency_check.py tests/test_consistency_check.py
git commit -m "feat(cycle-08): sws_consistency_check.py — static analysis core for consistency-checker agent"
```

### Phase-1 gate

- [ ] All Phase-1 tests pass.
- [ ] Run full test suite for sanity: `pytest tests/ -v` — no regressions.

---

## Phase 2 — Agents + skills + router (parallel)

Eleven independent deliverables. Dispatch parallel subagents. Tasks 2G–2K (agents) and 2L–2P (skills) are independent of each other. Task 2Q (router) is independent.

### Task 2G: `agents/reviser-full.md`

**Files:**
- Create: `agents/reviser-full.md`

- [ ] Author the agent file (~30 lines): frontmatter with `name: reviser-full`, `model: claude-opus-4-7`, `color: red`. Description: "Use when /sws:revise-paper invokes a full-paper revision pass on profiles with word_total ≥ 1500. Reads _drafts/*.md, surfaces cross-section redundancy / logical consecutio / claim grounding / sentence-level fluency issues; writes _drafts/<section>-revised.md per section + _review/revision-notes-full.md."

- [ ] Prompt body: misroute safety net (if asked to revise a single section, dispatch to reviser-fast). Inputs: outline.md, _review/consistency-report.md (if present), zotero-manifest.md (if present), _voice/profile.md (if present). Output: revised markdown per section + revision-notes-full.md.

- [ ] AI-tells discipline: grep against ai-writing-tells.md; INVOKE sws_lint_ai_tells.py via sws_python.sh on the revised output BEFORE returning (this is the canonical post-revision linter pass). Block-severity hits in the revised output abort and ask for a second pass.

- [ ] User address: R5 (no gender-default). Include the standard contract footer.

- [ ] **Commit:** `git add agents/reviser-full.md && git commit -m "feat(cycle-08): reviser-full agent (Opus 4.7, full-paper passes, D1)"`

### Task 2H: `agents/reviser-fast.md`

**Files:**
- Create: `agents/reviser-fast.md`

- [ ] Author the agent file: `name: reviser-fast`, `model: claude-sonnet-4-6`, `color: pink`. Description: "Use when /sws:revise-section is invoked or /sws:revise-paper dispatches a single-section pass on short-form profiles (word_total < 1500). Reads one _drafts/<section>.md, revises in place, writes _drafts/<section>-revised.md + _review/revision-notes-<section>.md."

- [ ] Prompt body: scope = one section. Misroute safety net (if asked for whole-paper, dispatch to reviser-full). Inputs: outline.md, the single section file, optional voice/zotero. Same AI-tells discipline as reviser-full. Same R5. Same contract footer.

- [ ] **Commit:** `git add agents/reviser-fast.md && git commit -m "feat(cycle-08): reviser-fast agent (Sonnet 4.6, single-section passes, D1)"`

### Task 2I: `agents/humanizer.md`

**Files:**
- Create: `agents/humanizer.md`

- [ ] Author the agent file: `name: humanizer`, `model: claude-haiku-4-5`, `color: cyan-bright`. Description: "Use when /sws:revise-paper or /sws:revise-section needs to clean AI-writing tells from a draft. Reads _drafts/<section>-revised.md (or -<section>.md), runs sws_lint_ai_tells.py, rewrites flagged constructions, writes _drafts/<section>-humanized.md. Prose-only — no docx editing."

- [ ] Prompt body: sole job = remove AI-tells while preserving meaning. Must run sws_lint_ai_tells.py BEFORE returning; the output must exit 0 (no block-severity findings). Detect-and-replace per-tell: each block-severity match gets a rewrite suggestion that the humanizer applies. warn-severity matches: humanizer decides whether to rewrite or keep (context-dependent). NEVER edit chemistry-formula numbers or species names or citation placeholders — only prose constructions. R5 applies. Contract footer.

- [ ] **Commit:** `git add agents/humanizer.md && git commit -m "feat(cycle-08): humanizer agent (Haiku 4.5, AI-tells cleanup, prose-only)"`

### Task 2J: `agents/style-enforcer.md`

**Files:**
- Create: `agents/style-enforcer.md`

- [ ] Author the agent file: `name: style-enforcer`, `model: claude-sonnet-4-6`, `color: brown`. Description: "Use when /sws:enforce-style is invoked OR /sws:revise-paper reaches the final pass. Reads _drafts/<section>-humanized.md (fallback -revised.md, fallback <section>.md) per profile section order, calls sws_write_docx.py to produce Manuscript/<paper>.docx, then calls sws_apply_chemistry_format.py to apply chemistry typography. Only cycle-#8 agent that writes .docx."

- [ ] Prompt body: pipeline of 4 wrappers (sws_python.sh → sws_write_docx → sws_apply_chemistry_format). Skip chemistry pass if marker has format: latex. Use --restyle on user-supplied legacy docx (--from <file>). Print summary: section count, words, chemistry patterns applied (auto vs suggest), AI-tells block hits if any leaked through. Backup hook auto-fires (cycle #5). R5. Contract footer.

- [ ] **Commit:** `git add agents/style-enforcer.md && git commit -m "feat(cycle-08): style-enforcer agent (Sonnet 4.6, produces final .docx, D10)"`

### Task 2K: `agents/consistency-checker.md`

**Files:**
- Create: `agents/consistency-checker.md`

- [ ] Author the agent file: `name: consistency-checker`, `model: claude-sonnet-4-6`, `color: gray`. Description: "Use when /sws:check-consistency is invoked OR /sws:revise-paper starts a pass. Reads _drafts/*.md + _outline/outline.md, calls sws_consistency_check.py, interprets ambiguous findings (possible abbreviation collisions, case-variant terminology), writes _review/consistency-report.md. Publication profiles only — funding-proposal exits 0 with v0.1-unsupported message (D19)."

- [ ] Prompt body: dispatch logic — for deterministic findings (missing figure ref, duplicate citation key) the script's output is final. For ambiguous findings (case-variant terminology = real synonym or typo?) the agent adds a one-line judgment to the report. Output report shape per spec auxiliary_file_shapes. R5. Contract footer.

- [ ] **Commit:** `git add agents/consistency-checker.md && git commit -m "feat(cycle-08): consistency-checker agent (Sonnet 4.6, text-internal checks only, D9)"`

### Task 2L: `skills/revise-paper/SKILL.md`

**Files:**
- Create: `skills/revise-paper/SKILL.md`

- [ ] Author per spec orchestration_model./sws:revise-paper. Sequential 7-step pipeline (D4). Size-aware reviser dispatch (D4 short_profile_carve_out). Reads marker → resolves profile → reads word_total. < 1500 → reviser-fast; ≥ 1500 → reviser-full. Flags: --skip-humanize, --skip-lint, --skip-style (advanced users only).

- [ ] Skill body explains the pipeline, what files are written, exit conditions.

- [ ] **Commit:** `git add skills/revise-paper/SKILL.md && git commit -m "feat(cycle-08): /sws:revise-paper skill (sequential orchestrator)"`

### Task 2M: `skills/revise-section/SKILL.md`

**Files:**
- Create: `skills/revise-section/SKILL.md`

- [ ] Author per spec. Args: `<section-id> [--no-humanize]`. Always dispatches reviser-fast (D18). 5-step pipeline (resolve, read draft, dispatch reviser-fast, optionally humanizer, summarize).

- [ ] **Commit:** `git add skills/revise-section/SKILL.md && git commit -m "feat(cycle-08): /sws:revise-section skill (reviser-fast on one section)"`

### Task 2N: `skills/enforce-style/SKILL.md`

**Files:**
- Create: `skills/enforce-style/SKILL.md`

- [ ] Author per spec. Args: `[--from <markdown-file>] [--restyle <existing-docx>]`. Dispatches style-enforcer agent.

- [ ] **Commit:** `git add skills/enforce-style/SKILL.md && git commit -m "feat(cycle-08): /sws:enforce-style skill"`

### Task 2O: `skills/check-consistency/SKILL.md`

**Files:**
- Create: `skills/check-consistency/SKILL.md`

- [ ] Author per spec. No args (operates on _drafts/). Dispatches consistency-checker agent; for funding-proposal exits early with the v0.1-unsupported message (D19).

- [ ] **Commit:** `git add skills/check-consistency/SKILL.md && git commit -m "feat(cycle-08): /sws:check-consistency skill"`

### Task 2P: `skills/lint-ai-tells/SKILL.md`

**Files:**
- Create: `skills/lint-ai-tells/SKILL.md`

- [ ] Author per spec. Args: `<file.md> [--severity ...] [--json]`. Dispatches NO agent — calls sws_python.sh sws_lint_ai_tells.py directly.

- [ ] **Commit:** `git add skills/lint-ai-tells/SKILL.md && git commit -m "feat(cycle-08): /sws:lint-ai-tells skill (script-only)"`

### Task 2Q: Section router action axis

**Files:**
- Modify: `scripts/sws_section_router.py`
- Create: `tests/test_revising_section_router.py`

- [ ] **Step 1: Extend the router**

Add CLI flag `--action draft|revise|consistency|style|lint`. Default `draft` (backwards-compat per R5 mitigation).

For action=draft: existing cycle-#7 routes (per `routes_publication` / `routes_funding_proposal` dicts) untouched.

For action=revise: new dict per spec section_router_action_axis.routes_revise.

For action=consistency: `"*" → consistency-checker`.

For action=style: `"*" → style-enforcer`.

For action=lint: `"*" → script:sws_lint_ai_tells.py` (special-case: the router prints a sentinel that callers parse as "this is a script not an agent").

- [ ] **Step 2: Tests**

`tests/test_revising_section_router.py`:
- action=draft (default) returns cycle-#7 routes.
- action=revise + intro → reviser-fast.
- action=revise + full → reviser-full.
- action=consistency + anything → consistency-checker.
- action=style + anything → style-enforcer.
- action=lint + anything → script sentinel.
- Backwards-compat: existing cycle-#7 callers without --action still work.

- [ ] **Step 3: Run all router tests, commit**

```bash
"$PAPER_ROOT/.venv/bin/python" -m pytest tests/test_section_to_agent_map.py tests/test_revising_section_router.py -v
git add scripts/sws_section_router.py tests/test_revising_section_router.py
git commit -m "feat(cycle-08): section router action axis (draft|revise|consistency|style|lint)"
```

### Task 2R: Update `references/agent-contract.md`

**Files:**
- Modify: `references/agent-contract.md`

- [ ] Per spec cross_cutting.agent_contract_changes. Add 4 new rows to the I/O wrapper inventory table:

```
| scripts/sws_write_docx.py             | Write markdown → .docx with SWS style canon              | 8 |
| scripts/sws_restyle_docx.py           | Re-apply SWS styles to an existing .docx                 | 8 |
| scripts/sws_apply_chemistry_format.py | Apply chemistry-formatting patterns to an existing .docx | 8 |
| scripts/sws_lint_ai_tells.py          | Context-aware AI-tells linter (vs grep-pass)             | 8 |
```

Update R3 closing sentence to reflect cycle-#8 WRITE wrappers now ship.

- [ ] **Commit:** `git add references/agent-contract.md && git commit -m "docs(cycle-08): agent-contract R3 I/O wrapper inventory — add WRITE wrappers + linter"`

### Phase-2 gate

- [ ] All 5 agent files exist and follow the cycle-#7 template (~30 lines, contract footer, R5).
- [ ] All 5 skill files exist and reference the agents they dispatch.
- [ ] Router test passes both old and new action axes.
- [ ] Agent-contract is updated.

---

## Phase 3 — Profiles + smoke + regression (parallel within phase, then sequential gate)

### Task 3R: Update all 9 profile files

**Files:**
- Modify: `profiles/full-article.md`, `profiles/communication.md`, `profiles/perspective.md`, `profiles/review-paper.md`, `profiles/mini-review.md`, `profiles/editorial.md`, `profiles/methodological-paper.md`, `profiles/commentary-reply.md`, `profiles/funding-proposal.md`

- [ ] Per D13: ADD the 5 cycle-#8 agents (`reviser-full`, `reviser-fast`, `humanizer`, `style-enforcer`, `consistency-checker`) to `agents_active` for ALL profiles. Do NOT add any to `agents_inactive` — size-aware dispatch lives in the orchestrator skill, not in the matrix.

- [ ] Verify each profile's frontmatter still validates against the cycle-#6 schema.

- [ ] **Commit:** `git add profiles/ && git commit -m "feat(cycle-08): profiles activate 5 revising agents across all 9 profiles (D13)"`

### Task 3S: `tests/test_revising_agent_activation.py`

**Files:**
- Create: `tests/test_revising_agent_activation.py`

- [ ] Test that every profile has all 5 cycle-#8 agents in agents_active (or implicitly via empty agents_inactive). For each profile + each cycle-#8 agent, assert agent_should_run.sh exits 0.

- [ ] **Commit:** `git add tests/test_revising_agent_activation.py && git commit -m "test(cycle-08): per-profile activation matrix for 5 revising agents"`

### Task 3T: `tests/fixtures/cycle_08_paper/` skeleton

**Files:**
- Create: `tests/fixtures/cycle_08_paper/Manuscript/` (empty)
- Create: `tests/fixtures/cycle_08_paper/_outline/outline.md` (with frontmatter sections + figures dicts)
- Create: `tests/fixtures/cycle_08_paper/_drafts/intro.md`
- Create: `tests/fixtures/cycle_08_paper/_drafts/results.md`
- Create: `tests/fixtures/cycle_08_paper/_drafts/discussion.md`
- Create: `tests/fixtures/cycle_08_paper/_drafts/conclusion.md`
- Create: `tests/fixtures/cycle_08_paper/figures/Fig1.png` (copy from cycle_07_paper)

- [ ] The drafts contain chemistry-formatting triggers (H2O, et al., E. coli, Figure 1.) and a couple of intentional AI-tells (one delve, one "Furthermore + Moreover" stack) for the smoke to catch. Drafts also have one citation key `[Smith2023; doi:10.x]` and one `[CITATION_NEEDED: ...]` placeholder.

- [ ] outline.md frontmatter `sections:` matches the 4 draft files; `figures:` has f1 mapped to figures/Fig1.png.

- [ ] **Commit:** `git add tests/fixtures/cycle_08_paper/ && git commit -m "test(cycle-08): smoke fixture with seeded _drafts/ files for revising pipeline"`

### Task 3U: `tests/smoke_cycle_08.sh`

**Files:**
- Create: `tests/smoke_cycle_08.sh` (chmod +x)

- [ ] Mirrors the structure of `smoke_cycle_07.sh`. Steps:
  1. Copy fixture cycle_08_paper to tmpdir; bootstrap .venv symlink; write marker.
  2. agent_prelude resolves correctly (perspective profile, default).
  3. agent_should_run for all 5 cycle-#8 agents → exit 0.
  4. sws_consistency_check.py on _drafts/ → exits 0 or 1 (report shape valid).
  5. sws_lint_ai_tells.py on _drafts/intro.md → exits 1 (the seeded delve is block-severity).
  6. sws_apply_chemistry_format.py dry-run on a fixture docx → reports H2O subscript candidate.
  7. sws_write_docx.py on _drafts/intro.md → produces a valid docx with SWS-H1/Body styles.
  8. Router action=revise + section=intro → reviser-fast.
  9. Router action=consistency + anything → consistency-checker.
 10. Router action=style + anything → style-enforcer.
 11. AI-tells linter --json output validates as JSON.
 12. Final: chemistry-formatting catalog has all 6 categories from D6.

- [ ] **Commit:** `git add tests/smoke_cycle_08.sh && git commit -m "test(cycle-08): smoke_cycle_08.sh end-to-end revising pipeline"`

### Task 3V: cycle-#7 regression check

**Files:**
- Verify: `tests/smoke_cycle_07.sh` still passes 14/14
- Possibly modify: `tests/smoke_cycle_07.sh` if router action axis touched any assertion

- [ ] Run `bash tests/smoke_cycle_07.sh` after Phase 2 lands. If it fails, debug the router changes (most likely culprit) before continuing.

- [ ] If a step needs adjustment (e.g., section-router invocation), update the smoke and commit:

```bash
git add tests/smoke_cycle_07.sh
git commit -m "test(cycle-08): adapt smoke_cycle_07 to new router action axis (backwards-compat verified)"
```

### Phase-3 gate

- [ ] `pytest tests/` — all tests pass.
- [ ] `bash tests/smoke_cycle_08.sh` — all steps pass.
- [ ] `bash tests/smoke_cycle_07.sh` — still 14/14.
- [ ] `git log --oneline cycle/08-revising` shows ~25 commits with clear messages.

---

## Phase 4 — PR

### Task 4W: Push branch

- [ ] **Step 1:** `git push -u origin cycle/08-revising`

### Task 4X: Open PR (DRAFT)

- [ ] **Step 1:** Open a DRAFT PR (the user requested overnight autonomy with revision tomorrow — draft state makes revision low-friction).

```bash
gh pr create --draft --title "Cycle #8: Revising (5 agents, 5 skills, 3 wrapper scripts, AI-tells linter)" --body "$(cat <<'EOF'
## Summary

- 5 revising agents (`reviser-full`, `reviser-fast`, `humanizer`, `style-enforcer`, `consistency-checker`)
- 5 skills (`/sws:revise-paper`, `/sws:revise-section`, `/sws:enforce-style`, `/sws:check-consistency`, `/sws:lint-ai-tells`)
- 3 DOCX WRITE wrappers (`sws_write_docx`, `sws_restyle_docx`, `sws_apply_chemistry_format`) — closes cycle-#7 D22 deferral
- 1 reference doc (`chemistry-formatting.md`) — closes cycle-#7 D11 deferral
- 1 AI-tells linter (`sws_lint_ai_tells.py`) — closes cycle-#7 D5 deferral
- 1 consistency-check static-analysis core (`sws_consistency_check.py`)
- Section router gains an `action` axis (`draft|revise|consistency|style|lint`, backwards-compatible)
- All 9 profiles activate the 5 new agents

## Autonomous-run caveat

This PR was authored overnight on 2026-05-14 under the user's explicit grant ("run everything in cycle 8 that does not need my intervention. Go with recommended options and then I'll revise this tomorrow"). Spec at `docs/superpowers/specs/2026-05-14-cycle-08-revising-design.md` carries one-line rationale on every locked decision (D1–D20). Most likely candidates for tomorrow's revision are listed at the end of that spec.

## Test plan

- [ ] `pytest tests/` passes
- [ ] `bash tests/smoke_cycle_08.sh` walks revise-paper end-to-end
- [ ] `bash tests/smoke_cycle_07.sh` still passes 14/14 (regression check)
- [ ] User reviews D1–D20 in the spec and approves before un-drafting the PR

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 2:** Print the PR URL to the user.

---

## Definition of done

- Branch `cycle/08-revising` exists with ~25 commits.
- All deliverables in the spec's `deliverables:` block exist.
- All tests pass.
- Smoke for cycle #8 passes 12/12.
- Smoke for cycle #7 still passes 14/14.
- Draft PR opened with summary + test plan + autonomous-run caveat.
- TaskList shows all tasks complete.

---

## Notes for the overnight executor

- **Parallel dispatch:** Phases 1, 2, and 3R/3S are independent enough to run as parallel subagents. Phase-2 agent + skill tasks (G–P) are 9-way parallel.
- **Light context per subagent:** each subagent gets only its task description + relevant file paths + a one-line reference to the spec.
- **Model match:** wrapper scripts (Phase 1) → Sonnet. Agent prompts (Phase 2) → Sonnet. Tests → Sonnet. Skill files (markdown only) → Haiku.
- **Commit per task:** every task ends with a focused commit. Each commit message starts with `feat(cycle-08):`, `test(cycle-08):`, or `docs(cycle-08):` per existing convention.
- **No new pip installs:** all wrapper scripts use python-docx + openpyxl + PyYAML which are already in `requirements/sws-deps.txt` from cycle #6.
- **Verification before claiming done:** run pytest + both smokes BEFORE pushing the branch.
