# Scientific-Writing-Superpowers (SWS)

Public Claude Code plugin for scientific manuscript preparation. Author: Marco Chino (@piripocchio8). Status: **architecture-sketch in progress** — no code written yet.

## What this is

A docx-first scientific-writing toolkit for chemistry / biochemistry / biology labs. Differentiated from the existing LaTeX-centric prior art (K-Dense-AI/claude-scientific-writer, andrehuang/academic-writing-agents, Imbad0202/academic-research-skills, etc.) by:

1. **DOCX as primary/default format** (Wiley/RSC/ACS journals submit .docx). LaTeX supported as opt-in in v0.1 via marker file (`format: latex`); a bidirectional `format-translator` agent ships in v0.2.
2. **Cycle-memory hooks** that write `claude_memory/passport.json` after each work cycle so a fresh session loads cold without burning tokens
3. **Semantic-backup discipline as a `PreToolUse` hook** on docx Edit/Write (the `*.backup_pre_<event>.docx` pattern)
4. **Zenodo / xlsx-as-data-authority** workflow with co-located fit + plot scripts and formula-cell handling
5. **Wet-lab-coupled writing** — claim ↔ experiment ↔ figure traceability
6. **Chemistry-aware docx formatting** — sub/superscripts in formulae, italic species/genes/variables, bold non-italic figure caption labels
7. **Multi-language opt-in** — English default everywhere; Italian opt-in via marker file (`language: it`) for PRIN/MUR/ERC proposals or any other Italian-language work. Other languages = v0.2+.
8. **Filesystem-index utility** — JSON manifest of project state to avoid repeated `ls`/`find` in long sessions
9. **Writing-context profiles** as first-class switchable mode (9 profiles: full-article, communication, perspective, review-paper, mini-review, editorial, methodological-paper, commentary-reply, funding-proposal)

## Critical rules for any session in this folder

1. **Read `claude_memory/MEMORY.md` first**, then `claude_memory/project_brainstorm_progress.md` — the index points to the brainstorm-progress file which tells you exactly where to resume in the `superpowers:brainstorming` 9-step checklist.
2. **Cycle #6 (Profile + overlay layer) implemented; PR open.** Next cycle is #7 — drafting + funding-proposal helpers (6 agents). Pick up from `claude_memory/project_cycle_execution_status.md` for current PR state; if PR has merged, run a fresh brainstorm for cycle #7 against the architecture sketch §5. Full procedural state lives in `claude_memory/project_brainstorm_progress.md` — read it after MEMORY.md.
3. **Never invent agent names or models.** The 24-agent roster is fixed in `claude_memory/project_roster_v0.1.md`. Do not add or remove without explicit user approval.
4. **Don't use AI-writing tells** in any prose generated for SWS docs (em-dash overuse, hyphenation chains, "delve/leverage", triplets, "Not just X but Y"). See `claude_memory/feedback_ai_writing_tells.md`.
5. **Python env:** `/Users/piripocchio8/opt/miniconda3/envs/pymol25/bin/python` (the `pymol25` mamba env). Don't use system `python3`.
6. **Brainstorming protocol applies** — if asked to design something new, follow `superpowers:brainstorming` (one question at a time, propose 2-3 approaches, present design in sections, get approval, write spec doc, hand off to `writing-plans`).
7. **Public repo destination:** `github.com/piripocchio8/scientific-writing-superpowers`. License: **MIT** (locked 2026-05-06 — see `claude_memory/project_decisions_so_far.md`).

## Inherited environment notes (carried from the hDF/ChemBioChem session where SWS was conceived)

- The hDF/ChemBioChem manuscript is at `/Users/piripocchio8/Library/CloudStorage/OneDrive-SharedLibraries-UniversitàdiNapoliFedericoII/hDF paper - General/ChemBioChem_Submission/`. **Do not read it from here unless explicitly asked** — context bleed is a known issue and the user moved SWS work into this dedicated folder for compartmentalization.
- The user is at Università di Napoli Federico II. Proposals may be in Italian (PRIN, MUR).
- The user has loaded plugins: `superpowers`, `plugin-dev`, `code-review`, `commit-commands`, `claude-md-management`, `huggingface-skills`, `telegram`, `skill-creator`, plus their own `peer-review`, `zotero`, `zotero-notes-import` skills. SWS will recycle a few (brainstorming, writing-plans, code-reviewer) and call others as tools (zotero, peer-review).

## Where things go (planned — not yet built)

```
scientific-writing-superpowers/
├── .claude-plugin/
│   └── plugin.json
├── agents/                     # 24 agent files
├── skills/                     # user-invoked skills (slash commands)
│   ├── init-project/
│   ├── resolve-journal-style/
│   ├── resolve-call-rules/
│   ├── calibrate-style/
│   ├── draft-section/
│   ├── run-cycle/
│   └── ... (one folder per skill)
├── hooks/
│   ├── hooks.json
│   └── scripts/                # all marker-scoped (no-op outside SWS projects)
├── profiles/                   # 9 writing-context profiles (.md + YAML frontmatter)
├── templates/                  # bootstrap templates with .template suffix
│   ├── manuscript-claude-md.template       # init-project writes to user paper's CLAUDE.md
│   ├── manuscript-memory-md.template       # init-project writes to user paper's claude_memory/MEMORY.md
│   └── sws-project-marker.template         # init-project writes to user paper's .sws-project.local.md
├── references/                 # codified principles, AI-tells dictionary, journal-style schema
├── examples/                   # demo manuscript repo skeleton, demo Zenodo db
├── .mcp.json                   # NotebookLM MCP, opt-in
├── docs/superpowers/specs/     # design docs
├── claude_memory/              # GITIGNORED — plugin-dev brainstorm scratch, not pushed
├── .gitignore                  # excludes claude_memory/, project_*.md, .venv/, dev backups
├── .github/ISSUE_TEMPLATE/     # bug, feature, journal-style overlay
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md          # Contributor Covenant 2.1
├── LICENSE                     # MIT
├── README.md                   # with "🚧 v0.1 in design" status banner
└── CLAUDE.md                   # plugin-DEV cold-start guide (NOT the user-project template)
```

**Plugin-vs-user file naming rule (cross-cutting):** any file with the same name in plugin repo vs user manuscript project gets explicitly disambiguated. Plugin's `/CLAUDE.md` ≠ user manuscript's `/CLAUDE.md` (the latter is generated from `templates/manuscript-claude-md.template`). Plugin's `/claude_memory/` ≠ user manuscript's `/claude_memory/`. SKILL.md files exist *only* in `skills/<name>/SKILL.md`; never in user space.
