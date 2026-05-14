---
name: revise-section
description: "This skill should be used when the user invokes /sws:revise-section <section-id>, says 'revise the intro', 'polish the results section', 'clean up <section>' — and the cwd is an SWS project with at least one drafted section in _drafts/. Always dispatches reviser-fast (D18 — no --full flag in v0.1). Optionally skips the humanizer pass via --no-humanize."
version: 0.1.0
---

# /sws:revise-section — Revise a single section

Dispatches `reviser-fast` on one section draft. The humanizer runs by default after the reviser; pass `--no-humanize` to skip it. To run `reviser-full` on a single long section, use `/sws:revise-paper` instead (D18).

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check. If absent, print "not an SWS project (no .sws-project.local.md found)" and exit.
2. **Read `_drafts/<section-id>.md`.** If missing, print "no draft found for '<section-id>' — run /sws:draft-section <section-id> first" and exit.
3. **Dispatch `reviser-fast`** via the Task tool. Pass `PAPER_ROOT`, `CLAUDE_PLUGIN_ROOT`, and the section id in env. The agent writes:
   - `_drafts/<section-id>-revised.md` — revised prose
   - `_review/revision-notes-<section-id>.md` — side-by-side change notes (what changed and why)
4. **Unless `--no-humanize`:** dispatch `humanizer` on `_drafts/<section-id>-revised.md`. Humanizer writes `_drafts/<section-id>-humanized.md`. If `_drafts/<section-id>-humanized.md` already exists, humanizer skips (preserves hand edits).
5. **Print summary:** revised word count, humanizer changes (if run), paths written.

## Routing note

`reviser-fast` always handles single-section revisions (Sonnet 4.6 high). This agent is optimized for sentence- and paragraph-level passes. Cross-section reasoning (redundancy across Intro/Discussion, citation deduplication) belongs to `reviser-full`, which `/sws:revise-paper` dispatches when word_total ≥ 1500.

## When to invoke

- Explicit `/sws:revise-section <section-id>`.
- Explicit `/sws:revise-section <section-id> --no-humanize`.
- User says "revise the <section>", "polish <section>", "tighten up the <section>".

Do NOT invoke when the marker is missing or `_drafts/<section-id>.md` does not exist.
