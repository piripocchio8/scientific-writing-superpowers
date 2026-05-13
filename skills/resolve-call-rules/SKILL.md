---
name: resolve-call-rules
description: "This skill should be used when the user invokes /sws:resolve-call-rules, says 'resolve the funding call rules', 'parse the PRIN call', 'set up the MUR/ERC overlay', or otherwise asks to populate the funding-call frontmatter overlay for the current paper. Requires profile=funding-proposal. Scans Manuscript/call/ for source documents (PDF/DOCX/MD/TXT/HTML); if a source is found, runs a hybrid heuristic+LLM extractor with user-confirm on uncertain fields; otherwise runs a 5-field Q&A wizard. Archives any prior overlay, writes the new one to Manuscript/_call/<slug>.md, and prints a diff."
version: 0.1.0
---

# /sws:resolve-call-rules — Synthesize a per-call overlay

This skill builds a funding-call-specific frontmatter overlay. It is the call half of the 3-layer contract (schema < profile < overlay) and replaces journal-style overlays for funding proposals.

## Usage

`/sws:resolve-call-rules [<slug>]`

Slug is optional — if absent, derived from the source filename or "qa-wizard" when no source is present.

## When to invoke

- User explicitly types `/sws:resolve-call-rules`.
- User says "resolve the call", "parse the PRIN/MUR/ERC", "set up the funding overlay", etc., **and**:
  - cwd has a `.sws-project.local.md` marker, **and**
  - marker `profile` is `funding-proposal`.

Do NOT invoke when:
- profile is anything other than `funding-proposal`. Tell the user to run `/sws:set-profile funding-proposal` first.
- cwd has no marker. Print "not an SWS project" and exit.

## Pre-step — scan Manuscript/call/

1. Ensure `<paper>/Manuscript/call/` exists. Create it if absent.
2. Scan for non-underscore source files matching: `*.pdf`, `*.docx`, `*.md`, `*.txt`, `*.html`. Underscore-prefixed files and the `_archive/` subdir are skipped.
3. If sources found → "uploaded source" path. If none → "Q&A wizard" path.

## Uploaded-source path (hybrid B+C parser, D13)

1. Show the file list; the user confirms which source is authoritative.
2. Extract plain text (use `Read` for PDF/DOCX/MD/TXT/HTML — all supported natively). Save to a tempfile.
3. Run the regex/heuristic extractor (in `sws_resolve_call_rules.py:heuristic_extract`) for deadline, page limit, budget.
4. Dispatch a Sonnet subagent (general-purpose) with: the text, the heuristic hits, and the spec's frontmatter schema. Instruction: "Fill the remaining schema fields. Emit only fields the source actively states; flag each uncertain field for user confirmation."
5. User-confirm pass on every uncertain field — one prompt at a time.
6. Pass the confirmed YAML to the helper via `SWS_TEST_FIXTURE_SYNTH_OUTPUT` env var.

## Q&A wizard path (D10)

When no source is found, the SKILL.md prose collects exactly 5 fields one at a time:

1. **Program name** (e.g., "PRIN 2024", "MUR Consortium", "ERC Starting Grant")
2. **Deadline** (date)
3. **Page limit** (integer; e.g., 12)
4. **Required sections** (multi-select from a small canonical set, defaulting to the funding-proposal profile's section ids)
5. **Language** (en | it)

Free-form notes can be added to the overlay body after writing.

## Common tail

After either path:

1. Pass the confirmed frontmatter (as YAML) via the synthesizer-fixture env var:

   ```bash
   SWS_TEST_FIXTURE_SYNTH_OUTPUT=<tmpfile.yaml> \
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
       "${CLAUDE_PLUGIN_ROOT}/scripts/sws_resolve_call_rules.py" \
       --paper "$PAPER_ROOT" [--slug "<slug>"] --noninteractive
   ```

2. The helper:
   - Validates profile is `funding-proposal` (exits 1 otherwise).
   - Reads the optional source-text fixture (`SWS_TEST_FIXTURE_SOURCE_TEXT`) for the regex pass.
   - Archives any existing `Manuscript/_call/<slug>.md` → `_archive/<slug>-YYYYMMDD-HHMMSS.md`.
   - Writes the new overlay atomically; prints a JSON object with `overlay_path`, `archived_to`, `source`, `heuristics`, and `diff`.

3. Show the user the diff. Direct them to edit the body of the overlay file for free-form notes.

## Notes

- No auto-refresh. Re-run this skill to refresh after a call amendment.
- Re-running archives the previous overlay.
- Wizards are intentionally minimal in v0.1 — comprehensive wizards bloat fast (D10).
