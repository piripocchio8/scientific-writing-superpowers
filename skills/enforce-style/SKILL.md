---
name: enforce-style
description: "This skill should be used when the user invokes /sws:enforce-style, says 'apply SWS style', 'generate the final docx', 'restyle the docx', 'apply chemistry formatting' — and the cwd is an SWS project. Dispatches style-enforcer to produce Manuscript/<paper-name>.docx with the SWS style canon and chemistry formatting applied."
version: 0.1.0
---

# /sws:enforce-style — Produce the final .docx

Dispatches `style-enforcer`. Produces `Manuscript/<paper-name>.docx` with the SWS style canon and chemistry formatting applied. Can also restyle an existing .docx via `--restyle`.

## Arguments

- `[--from <markdown-file>]` — stitch from a single pre-assembled markdown file instead of reading `_drafts/` section-by-section.
- `[--restyle <existing-docx>]` — re-apply SWS styles to an existing .docx (handles Word Heading 1/2 → SWS-H1/H2 conversion; direct character formatting is preserved).

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check. If absent, print "not an SWS project (no .sws-project.local.md found)" and exit. Resolve the overlay:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
       "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
       --paper "$PAPER_ROOT"
   ```
2. **If `--restyle <file>`:** the agent calls `scripts/sws_restyle_docx.py` on the supplied file. Skips the markdown-to-docx step.
3. **Else:** read `_drafts/<section>-humanized.md` for each section in profile order (falls back to `-revised.md` if no humanized version exists, then to the bare draft). Call `scripts/sws_write_docx.py` to generate `Manuscript/<paper-name>.docx`.
4. **Call `scripts/sws_apply_chemistry_format.py`** on the result. Skipped automatically when `format: latex` is set in the marker (D7).
5. **Print summary:** sections written, word count, chemistry patterns applied, docx path.

## Style canon

Applied by `scripts/sws_write_docx.py` per `references/docx-style.md` (SWS-Body, SWS-H1, SWS-H2, SWS-Caption, SWS-References). Chemistry formatting catalog: `references/chemistry-formatting.md`.

## Backup

The cycle-#5 PreToolUse hook fires on the docx Write and produces `<paper>.backup_pre_style_enforcer_<timestamp>.docx` automatically.

## When to invoke

- Explicit `/sws:enforce-style`, `/sws:enforce-style --from <file>`, `/sws:enforce-style --restyle <file>`.
- User says "generate the final docx", "apply chemistry formatting", "restyle this docx".
- Also called as the final step of `/sws:revise-paper`.

Do NOT invoke when the marker is missing or no drafts exist (and `--from`/`--restyle` not supplied).
