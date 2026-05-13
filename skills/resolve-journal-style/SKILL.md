---
name: resolve-journal-style
description: "This skill should be used when the user invokes /sws:resolve-journal-style, says 'fetch the ChemBioChem guidelines', 'resolve the journal style for <slug>', 'refresh the journal overlay', or asks to populate the per-journal frontmatter overlay for the current paper. Looks up the guide-for-authors URL by slug, fetches it, dispatches a Sonnet subagent to extract frontmatter, asks the user to confirm uncertain fields, archives any prior overlay, writes the new one to Manuscript/_journal-style/<slug>.md, and prints a diff summary."
version: 0.1.0
---

# /sws:resolve-journal-style — Synthesize a per-journal overlay

This skill builds a journal-specific frontmatter overlay that the resolver layers on top of the active profile. It is the journal half of the 3-layer contract (schema < profile < overlay).

## Usage

`/sws:resolve-journal-style <slug>`

Known slugs (initial set, per `references/journal-url-map.yaml`):
- `chembiochem`, `jacs`, `chem-sci`, `ang-chem`, `nat-comm`,
  `j-chem-inf-mod`, `biochem-and-biophys-acta`, `chemistry-european`

For unknown slugs the skill will prompt for the guide-for-authors URL.

## When to invoke

- User explicitly types `/sws:resolve-journal-style <slug>`.
- User says "fetch the journal style", "resolve the <name> overlay", "refresh the ChemBioChem rules", etc., and the cwd contains a valid `.sws-project.local.md` marker **with a profile set**.

Do NOT invoke when:
- The marker has `profile: null`. Tell the user to run `/sws:set-profile <name>` first.
- The cwd has no marker. Print "not an SWS project" and exit.
- `article_type: funding-proposal` is in the marker — funding proposals use `/sws:resolve-call-rules`, not journal-style.

## Steps

1. **Resolve `$PAPER_ROOT`.** cwd must contain `.sws-project.local.md` with a non-null `profile` field. Otherwise abort.

2. **Resolve the URL.** Read `${CLAUDE_PLUGIN_ROOT}/references/journal-url-map.yaml`; look up `<slug>`. If the slug is missing, ask the user to paste the guide-for-authors URL.

3. **WebFetch the page** at the resolved URL. Save the rendered text to a scratch file.

4. **Dispatch the synthesizer subagent.** Invoke a Sonnet subagent (`general-purpose`) with a tightly-scoped prompt:
   - The active profile's frontmatter (read from `${CLAUDE_PLUGIN_ROOT}/profiles/<profile>.md`)
   - The fetched guide-for-authors text
   - The frontmatter schema (see spec `frontmatter_schema_final`)
   - Instruction: "Emit only fields the source actively states or where the user actively confirms. For every field where the source is silent, emit nothing — the resolver will inherit the profile value. For every field where the source is silent but the profile has a non-default value that might not apply, flag it for user confirmation."

5. **User-confirm pass.** For each flagged field, ask the user one at a time: "the source does not mention <field>; profile sets it to <value>. Keep, drop (null), or override?"

6. **Validate.** The synthesizer's emitted YAML must parse and conform to the schema (enum values for `abstract_style` / `refs_style`, list shape for `sections`, etc.). Retry the synthesizer once on parse failure; abort cleanly if it fails twice.

7. **Write the overlay** via the helper script. The helper handles archive + atomic write + diff summary:

   ```bash
   SWS_TEST_FIXTURE_SYNTH_OUTPUT=<path-to-confirmed-yaml> \
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
       "${CLAUDE_PLUGIN_ROOT}/scripts/sws_resolve_journal_style.py" \
       --paper "$PAPER_ROOT" --slug "<slug>" --noninteractive
   ```

   The helper:
   - Validates profile is set (exits 1 otherwise).
   - Validates the URL is on file or `--url` was passed (exits 2 otherwise).
   - Archives any existing `Manuscript/_journal-style/<slug>.md` to `_archive/<slug>-YYYYMMDD-HHMMSS.md`.
   - Writes the new overlay atomically.
   - Prints a JSON object with `overlay_path`, `archived_to`, and a diff summary.

8. **Show the user the diff.** The helper's output is already concise; show it as-is.

## Notes

- No auto-refresh — re-run this skill manually to refresh an overlay (D6).
- Re-running archives the previous overlay; the `_archive/` directory is informational. The resolver never reads from it.
- The synthesizer subagent emits **only** fields the user actively confirmed or the source actively stated. Don't pad with profile values to "be explicit" (D18).
