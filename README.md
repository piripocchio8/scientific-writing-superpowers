# Scientific-Writing-Superpowers (SWS)

> 🚧 **v0.1 in design.** Implementation begins with cycle #1 (foundation). The full architecture is specified in [`docs/superpowers/specs/2026-05-08-architecture-sketch-design.md`](docs/superpowers/specs/2026-05-08-architecture-sketch-design.md).

A Claude Code plugin for scientific manuscript preparation, aimed at chemistry, biochemistry, and biology labs. SWS is **docx-first** (matching the actual submission format for most chemistry and biology journals), ships 24 specialized agents across 6 phases of the writing cycle, and uses cycle-memory hooks to make cold-restart sessions cheap and fast.

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

## Status

- **Now:** v0.1 architecture-sketch design doc committed.
- **Next:** Cycle #1 — plugin scaffold, folder topology, recycled trio re-export, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue templates. See §7 of the design doc for the 11-cycle roadmap.
- **Banner lifecycle:** `🚧 v0.1 in design` → `🧪 v0.1 alpha` (after cycle #7) → `v0.1` (after a paper has been written end-to-end through SWS).

## Author

Marco Chino ([@piripocchio8](https://github.com/piripocchio8)) — Università di Napoli Federico II.

## License

MIT — see [`LICENSE`](LICENSE). Aligns with the rest of the Claude Code plugin ecosystem.
