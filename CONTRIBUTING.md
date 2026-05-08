# Contributing to Scientific-Writing-Superpowers

Thanks for contributing. SWS is a Claude Code plugin for chemistry and biology lab manuscript preparation.

Read these first — they hold the project's design context and scope rules:

- `README.md` — what SWS is and where it's going.
- `CLAUDE.md` — the project's differentiators (DOCX-first, marker-scoped hooks, recycled superpowers trio, etc.) and the locked-decisions list.
- `docs/superpowers/specs/2026-05-08-architecture-sketch-design.md` — the full architecture sketch.

This file describes only how to interact with the repo as a contributor.

## In scope

- Agent prompt improvements, output-format tightening, edge-case fixes for any agent in `agents/`.
- New journal-style overlays via the `journal_style_overlay` issue template.
- New writing-context profiles (`profiles/`) — discuss in an issue first; the v0.1 set is locked.
- Bug reports with minimal reproductions.
- Feature requests aligned with `CLAUDE.md`'s differentiator list.
- Documentation fixes in `references/`, `CLAUDE.md`, `README.md`, and the design doc.
- Sanitized synthetic examples in `examples/`. Never real unpublished research.

## Out of scope (without a prior open issue)

Anything that contradicts a locked decision in `CLAUDE.md` (e.g., switching to LaTeX-as-primary, removing the docx-first commitment, opening the 24-agent roster, adding telemetry, relicensing).

## Local-test setup

```bash
git clone https://github.com/piripocchio8/scientific-writing-superpowers.git
cd scientific-writing-superpowers
# Install into Claude Code (current canonical method per Claude Code docs).
# Then run the filesystem-index test suite:
python -m unittest tests.test_fs_index -v
```

The reference Python env is `pymol25` (mamba). Any Python ≥ 3.9 with stdlib only is fine — the utility takes no external dependencies.

For agent or skill changes, install the plugin and exercise the affected component in a synthetic SWS project.

## Pull-request conventions

- Branch from `main`.
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`.
- One logical concept per commit.
- Describe what, why, and how-tested in the PR body. No PR template in v0.1.

## Attribution

SWS is MIT. Agents or skills imported from another MIT plugin keep an attribution comment in their YAML frontmatter (`# Adapted from <plugin> (MIT) — <url>`) — see the recycled trio (`agents/code-reviewer.md`, `skills/brainstormer/SKILL.md`, `skills/planner/SKILL.md`) for the canonical form.

## Code of conduct

`CODE_OF_CONDUCT.md` (Contributor Covenant 2.1).
