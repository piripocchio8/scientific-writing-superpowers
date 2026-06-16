# Scientific-Writing-Superpowers (SWS)

> **v0.1** — the SWS plugin's first stable release. All 13 cycles of the v0.1 roadmap have shipped: 24 agents, 9 writing-context profiles, marker-scoped hooks, the data/figures/literature/voice tooling, the submission orchestrator (`/sws:run-cycle`), and the opt-in NotebookLM RAG layer. Docx-first, end-to-end usable.

**SWS is a Claude Code plugin for writing scientific manuscripts — built docx-first, for chemistry, biochemistry, and biology labs.** It turns Claude Code into a structured writing environment: a project scaffold, a roster of specialized agents for each phase of the writing cycle, profile/journal-aware constraints, wet-lab-to-figure traceability, and cycle-memory hooks that make a fresh session pick up where the last one left off without re-reading everything.

## Why SWS exists

Most "AI scientific writing" tooling is LaTeX-centric and CS-flavored. But the journals chemists and biologists actually submit to (Wiley, RSC, ACS, Nature family) take **`.docx`**, and the day-to-day reality of a wet-lab paper is messier than a preprint: data lives in spreadsheets, claims must trace back to experiments and figures, formulae need sub/superscripts, species and gene names need italics, and the same manuscript gets reshaped for different article types and journals. SWS is built around that reality:

- **Docx is the default, not an afterthought.** LaTeX is opt-in; a bidirectional translator is on the roadmap.
- **Your data is the authority.** Spreadsheets are read as the source of truth (never silently re-computed), figures are generated from co-located scripts, and every figure traces back to its data.
- **Long projects stay cheap.** A "passport" written after each work cycle, plus a filesystem index, let a cold session reload context in a few tokens instead of re-reading the whole tree.
- **The writing is disciplined.** Profiles and journal/call overlays carry the real constraints (word caps, section structure, reference style); an AI-writing-tells linter and a voice profile keep the prose human and yours.

## What's different about SWS

1. **DOCX as the primary format**, not LaTeX. LaTeX is supported as opt-in.
2. **Cycle-memory hooks** that write a passport file after each work cycle, so a fresh session loads cold without burning tokens.
3. **Semantic-backup discipline** as a `PreToolUse` hook on docx Edit/Write.
4. **Zenodo / xlsx-as-data-authority** workflow with co-located fit + plot scripts.
5. **Wet-lab-coupled writing** with claim ↔ experiment ↔ figure traceability.
6. **Chemistry-aware docx formatting** (sub/superscripts in formulae, italic species/genes/variables, bold non-italic figure-caption labels).
7. **Multi-language opt-in** (English default; Italian opt-in via marker file for PRIN/MUR/ERC proposals).
8. **Filesystem-index utility** to avoid repeated `ls`/`find` in long sessions.
9. **Writing-context profiles** as a first-class switchable mode (9 profiles, including funding-proposal).

## How a paper flows through SWS

A typical lifecycle, with the slash command at each step (run them as you need — nothing is forced):

| Stage | Commands | What happens |
|---|---|---|
| **Set up** | `/sws:init-project` · `/sws:install-deps` | Scaffold the folder topology, marker file, and per-paper memory; bootstrap a project-local Python venv. |
| **Frame** | `/sws:set-profile` · `/sws:resolve-journal-style` · `/sws:resolve-call-rules` | Pick one of 9 writing-context profiles; layer the target journal's guide-for-authors (or a funding call's rules) as a constraints overlay. |
| **Find your voice** | `/sws:calibrate-style` | Learn your personal voice from your own papers → a reusable `_voice/` profile the drafter and reviser consume. See the [voice-calibration methodology](docs/voice-calibration-methodology.md). |
| **Gather literature** | `/sws:search-literature` · `/sws:prepare-lit-context` | Discover relevant sources (Zotero-first, then PubMed / Semantic Scholar). |
| **Outline & draft** | `/sws:outline-paper` · `/sws:draft-section` · `/sws:draft-paper` | Build the section architecture, then draft in your voice within the resolved constraints. |
| **Data & figures** | `/sws:curate-data` · `/sws:make-figure` | Ingest spreadsheet data (fail-loud on un-cached formulae), generate publication figures sized to the journal with a readability check (≥8 pt fonts, column-fit widths). |
| **Revise** | `/sws:revise-paper` · `/sws:revise-section` · `/sws:humanize` · `/sws:enforce-style` · `/sws:check-consistency` · `/sws:lint-ai-tells` | Improve soundness/flow, humanize toward your voice, enforce the docx style, and catch inconsistencies and AI-writing tells. |
| **Review** | `/sws:review-paper` · `/sws:peer-review` · `/sws:verify-claims` · `/sws:check-fidelity` | Run a diagnostic peer review, verify claims against the literature, and check verbatim fidelity against your Zotero corpus. |
| **Submission** | `/sws:audit-bibliography` | Validate, dedup, and format the bibliography. (Cover letter + response-to-reviewers land in the next cycle.) |
| **Proposals** | `/sws:proposal-budget` · `/sws:proposal-compliance` | Funding-proposal helpers, activated by the `funding-proposal` profile. |

## Agent roster

SWS ships **21 of a planned 24 specialized agents** (plus 3 recycled from `superpowers`), organized by writing phase. Each agent reads the resolved profile/journal constraints and the voice profile when present, and only the agents relevant to the active profile run.

- **Plan:** `outline-architect`, `style-calibrator`, `literature-searcher` (+ recycled `brainstormer`, `planner`)
- **Draft:** `drafter-flagship`, `drafter-fast`, `methods-writer`, `caption-writer`
- **Revise:** `reviser-full`, `reviser-fast`, `humanizer`, `style-enforcer`, `consistency-checker`
- **Review:** `peer-reviewer`, `claim-verifier`, `bibliography-fidelity-checker` (+ recycled `code-reviewer`)
- **Data:** `plot-maker`, `data-curator`
- **Submit:** `bibliography-curator` *(cover-letter-writer, response-to-reviewers — upcoming)*
- **Proposal:** `proposal-budget-helper`, `proposal-compliance-helper`
- **Infra:** *nlm-librarian — upcoming (opt-in NotebookLM)*

The roster is fixed by design; external tools are reached the cheap way (CLI/HTTP scripts over MCP where possible — PubMed via MCP, Zotero via the user's skill, Semantic Scholar/CrossRef/OpenAlex via scripts).

## Featured capabilities

- **Author voice calibration** — an iterative, held-out loop that scores generated prose with a **two-channel metric** (a clipped stylometric kernel plus a real-Haiku voice judge, combined at the similarity level) and refines a voice profile until the prose lands in the author's own self-similarity band. The full method, the dogfooding that exposed and corrected an anti-correlation, the fitted weights, and the convergence statistics are in the [**voice-calibration methodology**](docs/voice-calibration-methodology.md).
- **Figure readability** — `make-figure` enforces a font floor (≥8 pt) and journal column widths (single ≈7.5 cm, double 12–16 cm), with an opt-in vision pass on the rendered figure.
- **Profiles + overlays** — 9 writing-context profiles, each refined by a journal-style or funding-call overlay resolved into the project.
- **Cycle memory** — a `passport.json` written after each cycle and reloaded at session start; a filesystem index to avoid repeated scans.
- **Data integrity** — xlsx read as the authority, failing loudly (never guessing) on un-cached formula cells.
- **Human prose** — a 55-entry AI-writing-tells linter and the voice profile keep output from reading like generic AI.

## Quickstart

```text
# 1. Install the plugin (from the marketplace or a local clone)
/plugin marketplace add piripocchio8/scientific-writing-superpowers
/plugin install sws

# 2. In your manuscript folder, scaffold the project
/sws:init-project

# 3. Set a writing context and (optionally) resolve the journal style
/sws:set-profile full-article
/sws:resolve-journal-style chembiochem

# 4. Write
/sws:outline-paper
/sws:draft-section introduction
```

## Requirements

- **Claude Code** (plugin host).
- **Python ≥ 3.9** — plugin scripts run in a per-paper `.venv` that `/sws:install-deps` bootstraps; hooks and the filesystem index are stdlib-only.
- **Optional integrations:** the `zotero` skill (corpus + citation checks), the PubMed MCP (literature), and the NotebookLM CLI (opt-in, grounded retrieval — upcoming).

## Roadmap

- **Cycle 12 — Submission orchestration:** cover-letter writer, response-to-reviewers with a traceability matrix.
- **Cycle 13 — NotebookLM integration (opt-in, last):** grounded retrieval for literature/claim agents; flips the banner to `v0.1`.
- **v0.2 candidates:** a **self-improving figure-layout vision loop** (Sonnet inspects rendered multipanel figures for overlapping panels, illegible labels, legend-over-data, and clipping, then re-renders until clean); a bidirectional **docx ↔ LaTeX format translator**; author personal-skill lookup; a real-Haiku calibration study for the voice metric.

## Documentation

- [Author-voice calibration: method, validation, and correction](docs/voice-calibration-methodology.md) — the two-channel metric (clipped stylometric kernel + real-Haiku judge), the dogfooding that exposed and fixed an anti-correlation, the fitted weights, the convergence statistics, limitations, and a verified bibliography. Written end-to-end with SWS's own agents. Useful whether you want to *use* voice calibration or *contribute* to it.
- [Architecture sketch](docs/superpowers/specs/2026-05-08-architecture-sketch-design.md) — the full v0.1 design and the cycle roadmap.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). The voice metric, figure checks, and external-source adapters are all explicit and tunable — the style-calibration guide's "for contributors" section points at the most promising directions.

## Author

Marco Chino ([@piripocchio8](https://github.com/piripocchio8)) — Università di Napoli Federico II.

## License

MIT — see [`LICENSE`](LICENSE). Aligns with the rest of the Claude Code plugin ecosystem.
