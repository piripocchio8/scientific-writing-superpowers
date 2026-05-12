# Scientific-Writing-Superpowers v0.1 — Architecture Sketch

**Author:** Marco Chino (@piripocchio8)
**Date:** 2026-05-08
**Status:** Architecture sketch (Pass 1 of 2). Implementation = Pass 2, decomposed into 11 sub-projects (see §7).
**License:** MIT
**Public repo:** `github.com/piripocchio8/scientific-writing-superpowers`
**Local plugin-dev path:** `/Users/piripocchio8/Projects/scientific-writing-superpowers/`

---

## Summary

Scientific-Writing-Superpowers (SWS, alias `sws`) is a Claude Code plugin for scientific manuscript preparation aimed at chemistry, biochemistry, and biology labs. It is docx-first, ships 24 agents across 6 phases plus 1 infra agent, uses cycle-memory hooks for cold-restart resilience, and supports 9 writing-context profiles with journal-style and call-rules overlays. v0.1 ships English + Italian, docx + LaTeX (light), 3 MVP hooks, MIT-licensed, public-from-day-1 with a status banner. v0.2 adds a `format-translator` agent, 2 deferred hooks, WebFetch path for `/sws:resolve-call-rules`, and tuning of NLM-related behavior.

## Differentiators (relative to existing scientific-writing plugins)

1. **DOCX as primary/default format.** Wiley, RSC, ACS, and most chemistry/biology journals submit `.docx`. LaTeX is supported as opt-in.
2. **Cycle-memory hooks.** Each cycle writes `claude_memory/passport.json` so a fresh session loads cold without burning tokens reconstructing context.
3. **Semantic-backup discipline as a `PreToolUse` hook on docx Edit/Write.** Pattern: `<filename>.backup_pre_<event>.docx`.
4. **Zenodo / xlsx-as-data-authority workflow** with co-located fit + plot scripts and resolved formula cells.
5. **Wet-lab-coupled writing.** Claim ↔ experiment ↔ figure traceability is a first-class concern.
6. **Chemistry-aware docx formatting.** Sub/superscripts in formulae, italic species and gene and variable names, bold non-italic figure-caption labels.
7. **Multi-language opt-in.** English default everywhere; Italian opt-in via marker file (`language: it`) for PRIN/MUR/ERC proposals or any other Italian-language work. Other languages = v0.2+.
8. **Filesystem-index utility.** JSON manifest of project state to avoid repeated `ls`/`find` in long sessions.
9. **Writing-context profiles** as a first-class switchable mode (9 profiles).

Prior art surveyed: K-Dense-AI/claude-scientific-writer, andrehuang/academic-writing-agents, Imbad0202/academic-research-skills, matsuikentaro1/humanizer_academic, and ~10 others. SWS draws inspiration from MIT-licensed competitors with attribution; runtime dependencies = none of them.

---

## §1 Positioning, scope, trigger model

### Positioning

SWS is an original plugin (not a wrapper). DOCX-first commitment is non-negotiable. LaTeX support is the parallel-track in v0.1, never the focal track. Inspiration drawn from MIT competitors gets attributed in the README and in per-file `# Adapted from <plugin> (MIT)` headers.

### v0.1 scope

- All 24 agents ship in v0.1 (no phased rollout). Heavy import from `andrehuang/academic-writing-agents` and `Imbad0202/academic-research-skills` reduces marginal effort per agent.
- 9 writing-context profiles ship in v0.1.
- 3 MVP hooks ship in v0.1: pre-edit backup, post-cycle memory write on Stop, SessionStart passport reload.
- 2 hooks deferred to v0.2 backlog: post-edit format check, pre-commit consistency check.
- Format-translator agent deferred to v0.2 (becomes 25th agent then).
- Languages: English (default) and Italian (opt-in via marker file).
- Formats: docx (default) and LaTeX (opt-in via marker file).

### Trigger model

The plugin is loaded in every Claude Code session that has it installed but is **inert** until one of three triggers fires:

1. **Explicit slash command** (dominant entry point). `/sws:init-project`, `/sws:resolve-journal-style`, `/sws:draft-section`, etc. Zero ambiguity.
2. **Auto-triggered skill** based on prompt interpretation. When the user says e.g. "draft a Discussion for this manuscript," a skill whose description matches scientific-writing intent activates. Skills are scoped by user intent, not cwd, but the skill itself checks the SWS marker before destructive actions.
3. **Hooks (conditional).** Fire only when the SWS marker is present in cwd. Always silent in non-SWS sessions.

Agent and skill specs make the entry-point type explicit (e.g., "invoked by `/sws:init-project`" or "auto-triggers on user intent: drafting/revising Discussion sections").

### Pass 1 vs Pass 2 decomposition

- **Pass 1** (this document): one architecture-sketch design covering name, persona roster, model/effort matrix, folder topology, hook inventory, superpowers reuse, profiles, GitHub setup.
- **Pass 2** (later sessions, run from the plugin-dev folder): per-subsystem deep brainstorms → spec → plan → implementation. 11 subsystems, see §7.

### Workflow rules adopted across all agents

- **Review-Then-Act** (← andrehuang). Review agents diagnose only. Only revise/draft/style-enforcer agents write to files. No reviewer edits docx directly.
- **Material Passport** (← Imbad0202). Each cycle writes `claude_memory/passport.json` capturing provenance: agent, file, change, next step. Resumable across sessions.
- **`.review/` persistence** (← andrehuang). Review findings persist; subsequent runs are incremental.
- **Sprint contracts** (← Imbad0202). `peer-reviewer` commits scoring rubric BEFORE reading the paper (paper-blind Phase 1).
- **Concession threshold** (← Imbad0202). Adversarial agents score rebuttals 1–5; concessions only ≥4; no consecutive concessions.
- **R&R Traceability Matrix** (← Imbad0202). `response-to-reviewers` tracks Author's Claim + Verified? columns.
- **Disclosure mode** (← Imbad0202). Venue-specific AI-usage statement generator as slash command.
- **VLM figure verification** (← Imbad0202). Optional vision check on rendered figures, available to `plot-maker`.

When designing any agent, default behavior is one of these patterns. Deviation needs explicit reason.

### Skipped from competitors (revisit in v0.2+)

`socratic_mentor`, `ethical_auditor`, `risk_of_bias_agent`, `meta_analysis_agent`, `systematic_review_agent`, `monitoring_agent`, `collaboration_depth_agent`, cross-model verification (GPT/Gemini sanity checks), 30-codified-principles framework as agent-enforced rubric (kept as reference doc only). Reasons: scope discipline; some are systematic-review-specific or sycophancy-research-specific.

### Telemetry

**None, ever.** SWS ships no usage analytics, no anonymous telemetry, no opt-in metrics in v0.1. Locked default. Reject any future suggestion without explicit maintainer-pain justification.

---

## §2 Two layouts: plugin repo + bootstrapped manuscript project

### Plugin repo layout (this folder, `/Users/piripocchio8/Projects/scientific-writing-superpowers/`)

```
scientific-writing-superpowers/
├── .claude-plugin/
│   └── plugin.json
├── agents/                     # 24 agent files (see §3)
├── skills/                     # user-invoked skills (slash commands)
│   ├── init-project/
│   ├── resolve-journal-style/
│   ├── resolve-call-rules/
│   ├── calibrate-style/
│   ├── draft-section/
│   ├── run-cycle/
│   └── ...
├── hooks/
│   ├── hooks.json
│   └── scripts/                # all marker-scoped (no-op outside SWS projects)
├── profiles/                   # 9 writing-context profiles (.md + YAML frontmatter)
├── templates/                  # bootstrap templates with .template suffix
│   ├── manuscript-claude-md.template       # → user paper's CLAUDE.md
│   ├── manuscript-memory-md.template       # → user paper's claude_memory/MEMORY.md
│   └── sws-project-marker.template         # → user paper's .sws-project.local.md
├── references/                 # codified principles, AI-tells dictionary, journal-style schema, profile schema
├── examples/                   # demo manuscript repo skeleton, demo Zenodo db
├── .mcp.json                   # near-empty in v0.1: only PubMed if not in user env
├── docs/superpowers/specs/     # design docs (this file lives here)
├── claude_memory/              # GITIGNORED — plugin-dev brainstorm scratch, not pushed
├── .gitignore
├── .github/ISSUE_TEMPLATE/     # bug, feature, journal-style overlay
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md          # Contributor Covenant 2.1
├── LICENSE                     # MIT
├── README.md                   # with status banner (see §6)
└── CLAUDE.md                   # plugin-dev cold-start guide (NOT user-project template)
```

### Plugin `.gitignore`

```
# Plugin-development working files
claude_memory/
project_*.md
.sws-project.local.md
*.backup_pre_*.docx
scratch/
tmp/
# Python / general
.venv/
__pycache__/
*.pyc
.DS_Store
.vscode/
.idea/
```

### Bootstrapped manuscript-project layout (output of `/sws:init-project`)

Base layout, every SWS-bootstrapped project gets this:

```
<paper-root>/
├── CLAUDE.md                       # generated from manuscript-claude-md.template
├── .sws-project.local.md           # marker file, generated from sws-project-marker.template
├── claude_memory/
│   ├── MEMORY.md                   # generated from manuscript-memory-md.template
│   └── passport.json               # appended by Stop hook
├── Manuscript/
│   ├── <paper>.docx                # OR main.tex + refs.bib + optional <journal>.cls
│   ├── _journal-style/<slug>.md    # cached journal-style overlay
│   └── _archive/
├── Figures/
│   ├── main/
│   ├── SI/
│   └── _archive/
├── Tables/
│   └── _archive/
├── SI/
│   ├── SI_text.docx
│   └── SI_Figures/
├── Zenodo_db/
│   ├── data/
│   ├── scripts/                    # fit + plot scripts, co-located
│   └── _archive/
├── scratch/                        # ephemeral working files
├── refs/                           # Zotero exports, BibTeX, .ris
└── _voice/                         # populated by /sws:calibrate-style
    ├── profile.md
    ├── sources.json
    ├── field-profile.md
    └── _archive/
```

Conditional additions, triggered by profile or opt-in flags:

- **`call/`** at root, created **only when `article_type == funding-proposal`**. Holds call rules, eligibility/expense rules, deadlines, evaluation criteria, official call PDFs, lab-of-origin requirements. Persists after profile change (user may still need it for revisions or grant reports).
- **`refs/nlm_uploads/`**, created **only when `notebooklm.enabled: true` in `.sws-project.local.md`**. Curated corpus of files (PDFs, prior notes, draft sections, related papers) for `nlm-librarian` ingestion.

### Naming and conventions (locked)

- `Manuscript/` (not `Paper/`, not root) for the docx + journal overlay.
- One active format per project: `Manuscript/` holds either `<paper>.docx` OR `main.tex` + `refs.bib` (+ optional `<journal>.cls`), not both.
- `scratch/` (renamed from prior projects' `claude_material/`) for ephemeral work.
- `_archive/` is **per-folder**, co-located with what it archives. No global `_archive/` at root.
- `Tables/` is a separate top-level folder, mirroring `Figures/`.
- `SI/` is top-level and contains both `SI_text.docx` and `SI_Figures/`. SI figures live under `SI/SI_Figures/`, not under `Figures/SI/`.
- `refs/` at root for bibliography artifacts; `refs/nlm_uploads/` is the only subfolder created automatically (when opt-in).
- Per-folder `_<purpose>/` underscore-prefix convention signals "auto-generated SWS metadata" (e.g., `_journal-style/`, `_call-style/`, `_archive/`, `_voice/`).

### Plugin-vs-user file naming-convention rule (cross-cutting)

Any file with the same name in plugin repo vs user manuscript project gets explicitly disambiguated. Plugin's `/CLAUDE.md` (development cold-start) ≠ user manuscript's `/CLAUDE.md` (generated from `manuscript-claude-md.template`). Plugin's `/claude_memory/` (gitignored dev scratch) ≠ user manuscript's `/claude_memory/` (per-paper session state). `SKILL.md` files exist *only* in `skills/<name>/SKILL.md`; never in user space.

### Marker file schema (`<paper-root>/.sws-project.local.md`)

```yaml
---
sws_version: 0.1
article_type: communication        # one of the 9 profiles
language: en                         # default; opt-in via `language: it` (v0.1: en|it)
format: docx                         # default; opt-in via `format: latex` (v0.1: docx|latex)
target_journal: chembiochem          # null until /sws:resolve-journal-style runs
target_call: null                    # analog of target_journal for funding-proposal profile
notebooklm:
  enabled: false
created: <ISO date>
---

# free-form notes about this paper-project
```

The marker is the trigger and configuration file for everything SWS does in a project. Hooks check it before doing anything substantive (see §5).

---

## §3 Agent roster (24 agents)

24 agents across 6 phases, plus 1 infra agent (`nlm-librarian`) and 1 inherit-model agent (`code-reviewer`). Recycled: 3. Inspired-by-existing: 9. Pure new: 12. Locked unless user explicitly approves changes.

| # | Agent | Phase | Source | Model | Effort | External tools |
|---|---|---|---|---|---|---|
| 1 | `brainstormer` | Plan | Recycled `superpowers:brainstorming` | Sonnet 4.6 | high | — |
| 2 | `planner` | Plan | Recycled `superpowers:writing-plans` | Sonnet 4.6 | high | — |
| 3 | `outline-architect` | Plan | New | Sonnet 4.6 | high | — |
| 4 | `style-calibrator` | Plan | New (← Imbad0202 style_calibrator) | Sonnet 4.6 | high | Zotero |
| 5 | `literature-searcher` | Plan | New (← Imbad0202 bibliography_agent + andrehuang paper-crawler) | Sonnet 4.6 | high | Zotero + PubMed MCP + Semantic Scholar + nlm-librarian |
| 6 | `drafter` | Draft | New | Opus 4.7 (Intro/Discussion/Conclusion/Abstract) / Sonnet 4.6 (other) | xhigh / high | nlm-librarian |
| 7 | `methods-writer` | Draft | New | Sonnet 4.6 | high | — |
| 8 | `caption-writer` | Draft | New | Haiku 4.5 | medium | — |
| 9 | `reviser` | Revise | New (scientific soundness + logical consecutio + fluency + redundancy) | Opus 4.7 (full-paper) / Sonnet 4.6 (paragraph) | xhigh / high | — |
| 10 | `humanizer` | Revise | New (← matsuikentaro1/humanizer_academic + Imbad0202 writing_quality_check) | Haiku 4.5 | medium | — |
| 11 | `style-enforcer` | Revise | New (bumped from Haiku because docx XML risk) | Sonnet 4.6 | high | — |
| 12 | `consistency-checker` | Revise | New (← andrehuang consistency-checker) | Sonnet 4.6 | high | — |
| 13 | `peer-reviewer` | Review | New (wraps user's `peer-review` skill; + Imbad0202 EIC+3+DA + sprint-contracts + concession-threshold) | Opus 4.7 | max | — |
| 14 | `code-reviewer` | Review | Recycled `superpowers:code-reviewer` | inherit | parent-session | — |
| 15 | `claim-verifier` | Review | New (← Imbad0202 fact_checker + integrity-gates) | Sonnet 4.6 | high | Semantic Scholar + PubMed + Zotero + nlm-librarian |
| 16 | `plagiarism-screener` | Review | New (← Imbad0202) | Sonnet 4.6 | high | Semantic Scholar |
| 17 | `plot-maker` | Data | New (+ optional VLM verification ← Imbad0202) | Sonnet 4.6 | high | — |
| 18 | `data-curator` | Data | New (Zenodo/xlsx, formula resolution per `feedback_openpyxl_formulas.md`) | Sonnet 4.6 | high | — |
| 19 | `bibliography-curator` | Submit | New (← andrehuang bibliography-auditor + Imbad0202 citation_compliance, Zotero-first) | Sonnet 4.6 | high | Zotero + Semantic Scholar + nlm-librarian |
| 20 | `cover-letter-writer` | Submit | New | Sonnet 4.6 | high | — |
| 21 | `response-to-reviewers` | Submit | New (← Imbad0202 revision_coach + R&R Traceability Matrix) | Opus 4.7 | xhigh | — |
| 22 | `nlm-librarian` | Infra | New (wraps `jacob-bd/notebooklm-mcp-cli` **CLI binary, not the MCP**) | Sonnet 4.6 | high | Bash → notebooklm-mcp-cli (opt-in) |
| 23 | `proposal-budget-helper` | Proposal | New | Sonnet 4.6 | high | — |
| 24 | `proposal-compliance-helper` | Proposal | New (NLM-grounded against funding-call PDFs) | Sonnet 4.6 | high | nlm-librarian |

### Model/effort defaults (locked)

- **Sonnet 4.6** → always `high` effort. Never `medium` for code/docx/data tasks.
- **Opus 4.7** → `xhigh` for: `drafter` on Intro/Discussion/Conclusion/Abstract; full-paper `reviser` passes; `response-to-reviewers`.
- **Opus 4.7** → `max` for: `peer-reviewer` (highest-stakes adversarial work).
- **Haiku 4.5** → `medium` only for prose-only agents (`caption-writer`, `humanizer`). Never for agents that touch docx XML/styles.
- **`model: inherit`** → only for `code-reviewer` (recycled from superpowers; runs as parent-session model).

Reason for the Haiku exclusion: prior debugging captured in `claude_memory/feedback_docx_editing.md` documents Haiku failures with TOC fields and `w:t` XML manipulation. If a future agent design proposes Haiku for anything that opens a `.docx` file, push back.

### Format-aware agents (read `format` from marker, adapt)

Definitive v0.1 list (7 agents): `drafter`, `methods-writer`, `reviser`, `style-enforcer`, `consistency-checker`, `outline-architect`, `bibliography-curator`. These agents either open the manuscript file directly, write to it, or produce structure that depends on docx-vs-LaTeX conventions. Prose-only agents (`humanizer`, `caption-writer`) are deliberately format-agnostic: they consume and emit text strings, leaving file-write decisions to the caller. `plot-maker` works on figure files (not the manuscript) and is also format-agnostic. The pre-edit backup hook generalizes from `*.docx` to `*.{docx,tex,bib,cls}` so LaTeX users get the same safety net.

### NLM consumer agents (5 total)

`drafter`, `literature-searcher`, `claim-verifier`, `bibliography-curator`, `proposal-compliance-helper`. All dispatch to `nlm-librarian` rather than calling NotebookLM tooling directly. If `notebooklm.enabled: false`, `nlm-librarian` becomes inert and consumers degrade gracefully (use Zotero/PubMed/Semantic Scholar only; never fail).

---

## §4 Profile system, journal-style, call-rules

### The 9 v0.1 profiles (locked)

`full-article`, `communication`, `perspective`, `review-paper`, `mini-review`, `editorial`, `methodological-paper`, `commentary-reply`, `funding-proposal`.

The conditional `call/` folder triggers on `article_type == funding-proposal`. Agent names containing "proposal" (`proposal-budget-helper`, `proposal-compliance-helper`) keep their names; "proposal" describes a job, not a profile-binding.

### Profile delivery format

Each profile lives at `profiles/<name>.md` and ships as `.md` with YAML frontmatter:

- **Frontmatter** = machine-readable constraints: `sections[]` (id, label, word_limit, required), `ref_cap`, `word_total`, `figures_max`, `tables_max`, `abstract_style`, `disclosure_required`, `agents_active`, `agents_inactive`, optional `inherits:`.
- **Body prose** = guidance for the drafter: tone, audience, voice conventions, AI-tells to avoid, section-specific advice.
- **Profile YAML stays language-agnostic and format-agnostic.** `language` and `format` live only in the per-paper marker file. Profile files are reused across languages and formats.
- Canonical schema: `references/profile-schema.md`.

Frontmatter example (full-article):

```yaml
---
profile: full-article
inherits: null
sections:
  - { id: abstract, label: Abstract, word_limit: 250, required: true }
  - { id: introduction, label: Introduction, word_limit: null, required: true }
  - { id: results, label: Results and Discussion, word_limit: null, required: true }
  - { id: experimental, label: Experimental Section, word_limit: null, required: true }
  - { id: conclusion, label: Conclusions, word_limit: 300, required: true }
  - { id: references, label: References, word_limit: null, required: true }
ref_cap: 80
word_total: null
figures_max: null
tables_max: null
abstract_style: structured
disclosure_required: true
agents_active: [drafter, methods-writer, reviser, peer-reviewer, ...]
agents_inactive: [proposal-budget-helper, proposal-compliance-helper]
---
```

### Journal-style overlay (`/sws:resolve-journal-style`)

Explicit user-invoked slash command. Path:

1. User runs `/sws:resolve-journal-style <slug-or-url>`.
2. WebFetch on the journal's guide-for-authors.
3. Generate `<paper-root>/Manuscript/_journal-style/<slug>.md` — inherits from active profile, overrides journal-specific fields (word/ref limits, abstract style, figure count, supplementary policy, optional `latex_class:` path).
4. Cache. Re-fetch only on user re-invocation. No automatic TTL refresh in v0.1.
5. SessionStart hook (one of the three MVP hooks) prints one read-only line if no overlay is cached and `article_type != funding-proposal`. No fetching inside hooks or agents.

Agents read the resolved overlay path; if missing, they prompt the user with the exact slash-command line rather than fetching themselves.

### Call-rules overlay (`/sws:resolve-call-rules`) — funding-proposal profile

Parallel mechanism for the `funding-proposal` profile. Slash command: `/sws:resolve-call-rules <call-id-or-url>`. Output: `call/_call-style/<call-slug>.md`. Inherits from `funding-proposal` profile, overrides call-specific fields (page/word limits, required sections, eligibility, expense rules, evaluation criteria, deadlines, lab-of-origin requirements). Optional `latex_class:` field.

**Resolution flow (v0.1):**

1. **First check — uploaded source.** Look in `call/` for any non-underscore-prefixed file matching call-document patterns (PDF, DOCX, TXT, MD, HTML). If found, ask the user: "Use `<filename>` as the call-rules source?" If confirmed, the model parses it directly (Read tool handles PDF and docx natively) and writes the overlay. **Skip both Q&A and WebFetch.**
2. **Fallback — interactive Q&A.** If no source file is present, or the user declines the detected one, the resolver steps through the call-overlay schema fields one at a time, asks the user for each missing value, and writes the answers into the overlay file.
3. **WebFetch path = v0.2.** Per-portal parsers for PRIN, MUR, ERC, Horizon Europe with cache-first behavior and a fallback to the v0.1 Q&A path on failure.

Why uploaded-source-first: the official call PDF or DOCX is the highest-fidelity source available and the user typically has it locally when preparing a real proposal. Parsing it directly is strictly better than re-typing fields via Q&A or fetching a possibly-stale public version. Q&A is the always-works fallback.

User-supplied call source files live at `call/<filename>` (no underscore prefix) so they remain visible alongside the overlay output. The Q&A path reuses the same overlay schema; downstream agents see a consistent file regardless of source.

### Inheritance / consumption

Three-layer resolution: **journal-or-call overlay > profile > schema defaults**. Each layer overrides the prior. Agents read the resolved overlay file and never the bare profile, so behavior is deterministic regardless of whether an overlay exists.

When a `drafter` or `reviser` opens, it reads `Manuscript/_journal-style/<slug>.md` (or `call/_call-style/<call-slug>.md` for proposals); falls back to `profiles/<article_type>.md`; falls back to schema defaults at `references/profile-schema.md`. No agent hardcodes word counts, section names, or citation styles.

---

## §5 Hooks and external integrations

### Hook scoping rule (cross-cutting)

Every SWS hook checks for an SWS marker file at the current working directory before doing anything substantive. If absent, the hook is a silent no-op (microseconds, zero output). This makes SWS inert in unrelated Claude Code sessions. New hooks added later (v0.2 promotions or otherwise) inherit this rule.

### Three MVP hooks (v0.1)

**(a) Pre-edit backup — `PreToolUse` on Edit/Write.**
Fires on `*.docx` always; extends to `*.{tex,bib,cls}` when the marker has `format: latex`. Creates `<filename>.backup_pre_<event>.docx` (or `.tex` etc.) before the model writes. Backups land beside the file. Pruning is the user's responsibility (gitignored anyway).

**(b) Post-cycle memory write — `Stop` hook.**
On every Stop, writes `claude_memory/passport.json` capturing the cycle's provenance: agent, file touched, change summary, next-step pointer. Material Passport pattern adapted from Imbad0202. Cold restarts read the passport instead of replaying the session.

**(d) SessionStart passport reload + journal-style nudge.**
On SessionStart, reads `claude_memory/passport.json` and prints a one-line "where you left off" summary. If `article_type != funding-proposal` and no journal-style overlay is cached, also prints one read-only line: `💡 No journal style cached. Run /sws:resolve-journal-style <slug> when ready.` No fetch, no blocking.

### Deferred hooks (v0.2 backlog)

- **(c) Post-edit docx format check** — naive every-edit form is too noisy. Needs opt-in flag, sampled triggering, async non-blocking, cheap pre-screen before invoking `style-enforcer`.
- **(e) Pre-commit consistency check** — pre-commit hooks block users; false positives breed `--no-verify` habits. Needs soft mode by default, hard mode opt-in, scoped diff, time budget.

Both live in `claude_memory/project_v02_backlog.md` with the tuning required before promotion. v0.1 does not stub them.

### External integrations

**User-owned skills (already installed in user's env):**
- `peer-review` — wrapped by SWS `peer-reviewer` agent.
- `zotero`, `zotero-notes-import` — used by `literature-searcher`, `claim-verifier`, `bibliography-curator`, `style-calibrator`.

**CLI (preferred per MCP-aversion principle):**
- `notebooklm-mcp-cli` (jacob-bd) — invoked **as a CLI binary via Bash**, not as MCP. Gated by `notebooklm.enabled: true` in marker file. Only `nlm-librarian` agent talks to it. Other agents call `nlm-librarian`. If disabled, `nlm-librarian` becomes inert and consumers degrade gracefully.

**MCP (kept where no CLI alternative exists):**
- `claude_ai_PubMed` — used by `literature-searcher`, `claim-verifier`. Stays as MCP because writing our own E-utilities REST wrapper would be net-negative for v0.1.

**WebFetch + small utility scripts (no MCP):**
- **Semantic Scholar** — primary for citation graph traversal, title fuzzy match (Levenshtein ≥0.70), DOI verification, claim→source verification.
- **CrossRef** — fallback DOI resolver (`bibliography-curator`).
- **OpenAlex** — alternative to Semantic Scholar, useful for non-CS chemistry/biology papers.

### MCP-aversion principle (locked, applies to all future integrations)

When a tool ships both an MCP server and a CLI binary (or a usable REST API + a thin shell wrapper), prefer the CLI/Bash path. MCP tool calls inflate token cost because the catalog and parameter schemas live in model context; CLI invocations via Bash cost nothing beyond the command line. PubMed is the only v0.1 exception. The plugin's `.mcp.json` is near-empty in v0.1.

### Consumption order for citation/verification work

When an agent needs to query literature, citations, or claims:

1. **Zotero first** — the user's curated corpus is the highest-quality source.
2. **Semantic Scholar / PubMed** — fill gaps the user's library doesn't cover.
3. **`nlm-librarian`** — only if grounded RAG over a curated corpus is needed AND `notebooklm.enabled: true`.
4. **Arbitrary WebFetch** — never, unless going through one of the above.

`peer-reviewer` is the only agent that wraps a user-owned skill end-to-end (`peer-review`). All other consumer agents use the user-owned skills as building blocks alongside their own logic.

---

## §6 Superpowers reuse, GitHub workflow, community

### Recycled superpowers components

Three direct re-exports, no forks (so upstream improvements flow in):

- `superpowers:brainstorming` → `sws:brainstormer`
- `superpowers:writing-plans` → `sws:planner`
- `superpowers:code-reviewer` → `sws:code-reviewer` (`model: inherit`)

Each recycled file carries an `# Adapted from superpowers (MIT)` header. Same attribution rule applies to any agent that reuses prompts or rubrics from MIT competitors (andrehuang, Imbad0202, K-Dense-AI, matsuikentaro1).

### License

**MIT.** Matches the rest of the Claude Code plugin ecosystem (superpowers, andrehuang, Imbad0202, K-Dense-AI all MIT). Lets commercial and closed academic labs adopt SWS without copyleft contagion. Preserves the attribution norm SWS commits to in the README. Reject any future relicense suggestion (GPL, CC0, or other) without explicitly re-opening this decision.

### GitHub setup — public-from-day-1 with status banner

The repo goes public the moment this design doc is committed. The design doc is itself a substantive academic-tooling deliverable worth citing publicly with a timestamp. Early-public-then-iterate beats big-bang reveal for credibility and discoverability. The status banner removes any "ghost repo" ambiguity.

**Initial public commit contents** (`claude_memory/` is excluded; the design doc is the public artifact):

- `README.md` with banner: `🚧 v0.1 in design — code starts <date>`
- `LICENSE` (MIT)
- `CLAUDE.md` (plugin-dev cold-start guide)
- `docs/superpowers/specs/2026-05-08-architecture-sketch-design.md` (this file)
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1)
- `.github/ISSUE_TEMPLATE/bug_report.md`, `feature_request.md`, `journal_style_overlay.md`
- `.gitignore`

No agents, skills, hooks, or templates yet. Those land in v0.1-implementation phase commits.

**Authentication:** the model cannot run `gh auth login`. When push time arrives, the model prompts the user with the exact command line and waits.

### Banner lifecycle

Three stages, each banner update a first-class commit:

1. `🚧 v0.1 in design` — design doc committed, no code.
2. `🧪 v0.1 alpha` — agents/skills/hooks scaffolded but not yet validated end-to-end.
3. `v0.1` — first stable release after a paper has actually been written through SWS once.

### Community surface

Day-1 contribution surface, intentionally minimal:

- **`CONTRIBUTING.md`** (one page) — welcome contributions; what's in scope (agent improvements, new profiles, journal-style overlays for additional venues, bug reports, peer-review polish); what's out of scope (rewriting the locked roster, switching to LaTeX-primary, removing the docx-first commitment); local-test setup.
- **`CODE_OF_CONDUCT.md`** — Contributor Covenant 2.1, off-the-shelf.
- **3 GitHub issue templates** in `.github/ISSUE_TEMPLATE/`:
  - `bug_report.md` (versions, reproduction, expected vs actual, docx attachment policy)
  - `feature_request.md` (problem, proposal, alternatives, profile/agent affected)
  - `journal_style_overlay.md` (the high-leverage one — lets users at unsupported venues submit overlays for inclusion)

Deferred:

- **No PR template in v0.1.** Overengineering for expected volume. Revisit if traffic justifies.
- **No GitHub Discussions in v0.1.** Issues sufficient at this scale.
- **No `good first issue` / `help wanted` labels seeded** until real curated easy issues exist.
- **No `FUNDING.yml`.** Not relevant for v0.1.

### Disclosure mode

Venue-specific AI-usage statement generator ships as a slash command, lands in cycle #10 (cycle + submission orchestration). Inherits venue rules from the resolved journal-style overlay. Pattern adapted from Imbad0202 Disclosure mode.

---

## §7 Sub-projects roadmap (11 cycles)

Each cycle has its own brainstorm → spec → plan → implementation flow run from the plugin-dev folder. Order is fixed by dependency, with proposal-track capability prioritized to cycle #5 because the user has near-term proposal and perspective deadlines.

### Ordering

| # | Cycle | Scope summary |
|---|---|---|
| 1 | **Foundation + public launch** | Plugin scaffold (`plugin.json`), folder topology specs, marker schema, filesystem-index utility, `.gitignore`, recycled trio re-export, public-launch commit (this design doc + README banner + LICENSE + CONTRIBUTING + CoC + 3 issue templates). Banner becomes `🚧 v0.1 in design`. |
| 2 | **`/sws:init-project` + templates** | The bootstrapper that takes an empty folder and produces a complete SWS-managed manuscript project. Implements the 3 templates (`manuscript-claude-md.template`, `manuscript-memory-md.template`, `sws-project-marker.template`), creates the base folder layout, writes the marker file, validates the result. |
| 3 | **Three MVP hooks + `passport.json`** | Hooks (a)/(b)/(d), all marker-scoped via the wrapper pattern. Defines and locks the `passport.json` schema (cycle, agent, file, change-summary, next-step pointer). Format-aware backup pattern for `*.{tex,bib,cls}` when `format: latex`. |
| 4 | **Profile + overlay layer** (broader scope) | 9 profile bodies (`profiles/`), frontmatter schema (`references/profile-schema.md`), `/sws:resolve-journal-style` slash command + overlay format, `/sws:resolve-call-rules` slash command (uploaded-source-first detection + Q&A fallback) + overlay format, agent-side overlay-consumption protocol. |
| 5 | **Drafting + funding-proposal helpers** (6 agents) | `outline-architect`, `drafter`, `methods-writer`, `caption-writer`, `proposal-budget-helper`, `proposal-compliance-helper`. Format-aware behavior, AI-tells avoidance prompts. **End-of-#5: first usable proposal/perspective writing capability.** |
| 6 | **Revising** (4 agents) | `reviser`, `humanizer`, `style-enforcer`, `consistency-checker`. |
| 7 | **Review** (3 agents) | `peer-reviewer` (wraps user's `peer-review` skill, sprint contracts + concession threshold), `claim-verifier`, `plagiarism-screener`. `code-reviewer` already shipped via re-export in #1. **End-of-#7: full writing+review track usable. Banner becomes `🧪 v0.1 alpha`.** |
| 8 | **Style calibration** | `/sws:calibrate-style` skill + `style-calibrator` agent + `_voice/` folder. Wires Zotero ingestion via the user's existing `zotero` skill. |
| 9 | **Data + literature wave** (4 agents) | `plot-maker` (with optional VLM verification), `data-curator` (Zenodo/xlsx, formula resolution per `feedback_openpyxl_formulas.md`), `literature-searcher`, `bibliography-curator`. Wires Semantic Scholar / PubMed / Zotero / CrossRef / OpenAlex. Locks the `Zenodo_db/` layout. |
| 10 | **Cycle + submission orchestration** | `/sws:run-cycle` skill, `cover-letter-writer`, `response-to-reviewers` (with R&R Traceability Matrix), Disclosure-mode slash command (venue-specific AI-usage statement). Final maturation of `passport.json` with submission-phase fields. `.review/` persistence pattern. |
| 11 | **NLM integration** (opt-in, last) | `nlm-librarian` agent, CLI invocation pattern (`Bash` tool, not MCP), `notebooklm.enabled` marker-flag wiring, verification that all 5 consumer agents (`drafter`, `literature-searcher`, `claim-verifier`, `bibliography-curator`, `proposal-compliance-helper`) degrade gracefully when disabled. **End-of-#11 (or #10 if user judges first paper complete earlier): banner becomes `v0.1`.** |

### Why this order

- **Dependencies flow downward.** #1 unblocks everything. #2 sets up the marker file that #3 hooks depend on. #4 defines the overlay that drafters in #5 consume. #6/#7 need something to revise/review. #10 (orchestration) needs the agents from #5/#6/#7 to be present. #11 (NLM) is opt-in and consumers must degrade gracefully without it; testing that against the most-complete codebase yields the strongest signal.
- **Proposal track prioritized.** End-of-#5 marks first usable proposal/perspective writing capability. This was originally cycle #10 but moves up because the user has near-term proposal and perspective deadlines (see `claude_memory/project_urgent_deadlines.md`). Style calibration (#8) and data/literature (#9) slip later because they don't block first drafts.
- **Banner transitions are natural milestones.** Each transition is a first-class commit at the cycle boundary it ends.

### Caveat

SWS will not be ready before the user's near-term writing deadlines (perspective transformation 2026-05-09; new funding proposal during May 2026). The roadmap is need-aligned planning, not a delivery promise. The user will write both with regular Claude Code + existing skills in the meantime.

### Transformation-task agent decision (resolved)

**Question:** does proposal → perspective transformation need a dedicated agent?
**Answer:** No (in v0.1).
**Reason:** transformation = swap profile (`funding-proposal` → `perspective`) + re-outline + redraft + revise. The existing `outline-architect` + `drafter` + `reviser` + `style-enforcer` chain handles it. Adding a `proposal-to-perspective` agent is too narrow; a generic `genre-shifter` is overengineered for v0.1.
**Action:** document the transformation as a recipe in CONTRIBUTING.md examples. Revisit a generic workflow in v0.2 if recurring need emerges.

---

## §8 v0.2 backlog (deferred from v0.1 with explicit reasoning)

- **`format-translator` agent.** Bidirectional docx ↔ latex. Roster grows to 25. Tuning required: pandoc + post-processing layer; round-trip-fidelity test corpus; Zotero CSL key preservation; figure cross-reference preservation; equation handling (MathML ↔ LaTeX); `.cls` awareness; educational mode.
- **Hook (c) post-edit docx format check.** Tuning required: opt-in via profile flag; sampled triggering; async non-blocking; cheap pre-screen before agent invocation.
- **Hook (e) pre-commit consistency check.** Tuning required: soft mode default; hard mode opt-in; scoped diff; time budget; false-positive threshold from real use.
- **WebFetch path for `/sws:resolve-call-rules`.** Per-portal parsers (PRIN, MUR, ERC, Horizon Europe); cache-first; fallback chain to v0.1 Q&A path; field-coverage check; test corpus of 3–5 real calls per portal.
- **Languages beyond en/it.** Decision deferred until real demand.
- **Voice profiling enhancements.** Per-coauthor profiles; analysis of unpublished drafts.
- **`good first issue` / `help wanted` labels** seeded with real curated easy issues.
- **PR template; GitHub Discussions; FUNDING.yml.** Promote when real contribution volume justifies.
- **Generic `genre-shifter` workflow** (or skill, not agent) if recurring need beyond proposal→perspective emerges.
- **Skipped competitor features revisit:** `socratic_mentor`, `ethical_auditor`, `risk_of_bias_agent`, `meta_analysis_agent`, `systematic_review_agent`, `monitoring_agent`, `collaboration_depth_agent`, cross-model verification, 30-codified-principles framework as enforced rubric.

---

## §9 Open questions

None at design-doc time. New questions arising during sub-project planning will be tracked in `claude_memory/project_open_questions.md`.

---

## §10 Cross-cutting principles (locked)

- **Brainstorming protocol applies to every sub-project.** Each Pass-2 sub-project follows `superpowers:brainstorming` (one question at a time, propose 2–3 approaches, present design in sections, get approval, write spec doc, hand off to `superpowers:writing-plans`).
- **Don't invent agent names.** The 24-agent roster is locked. Don't add or remove without explicit user approval.
- **AI-writing-tells avoidance.** Don't use em-dash overuse, hyphenation chains, "delve/leverage", triplets, "Not just X but Y" in any prose generated for SWS docs or in agent output. See `claude_memory/feedback_ai_writing_tells.md`.
- **Python env.** `/Users/piripocchio8/opt/miniconda3/envs/pymol25/bin/python` (the `pymol25` mamba env). Don't use system `python3`.
- **MCP-aversion principle.** Prefer CLI/Bash when alternative exists. PubMed is the only v0.1 MCP exception.
- **Marker-scoping for hooks.** Every hook checks `<cwd>/.sws-project.local.md` first; absent marker = silent no-op.

---

## §11 Glossary (selected)

- **Marker file.** `<paper-root>/.sws-project.local.md`. The trigger and configuration file for SWS in a project.
- **Passport.** `<paper-root>/claude_memory/passport.json`. Cycle-memory artifact written by Stop hook.
- **Overlay.** A profile-inheriting `.md + YAML frontmatter` file that overrides journal-or-call-specific fields. Lives at `Manuscript/_journal-style/<slug>.md` or `call/_call-style/<slug>.md`.
- **Cycle.** One unit of writing work, tracked by a passport entry. Typically section-sized.
- **Sub-project (cycle #N).** One of the 11 v0.1 implementation packages from §7.

---

**End of architecture-sketch design doc.**
