---
name: init-project
description: "This skill should be used when the user invokes /sws:init-project, says 'init this paper as SWS', 'bootstrap an SWS project here', 'set up SWS for this manuscript folder', or otherwise asks to create the SWS layout in the current directory. Bootstraps the directory (new or existing) into the SWS folder topology via smart-merge with per-conflict prompts, plan-then-apply atomicity, and rollback on failure. Reads inputs in priority order: named args, then natural-language $ARGUMENTS, then interactive prompts. Writes the marker file, the per-paper CLAUDE.md, the per-paper claude_memory/MEMORY.md, plus an empty claude_memory/passport.json (cycle 0) and an initial claude_memory/fs_index.json snapshot."
version: 0.1.0
---

# /sws:init-project — Bootstrap a manuscript directory into SWS layout

This skill orchestrates `/sws:init-project`. The deterministic work (file scan, plan build, atomic apply, rollback, template render, env preflight) lives in three Python utilities under `scripts/`. The skill is the model-driven layer: argument resolution, interactive prompts, per-conflict negotiation, plan presentation, summary output.

Read the cycle #2 spec frontmatter before doing anything: `docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md` is the structured-data source of truth (locked decisions, orchestration steps a–g, edge cases, deliverables list).

## When to invoke

- User explicitly types `/sws:init-project` (with or without arguments).
- User asks "set up SWS in this folder", "init this paper", "bootstrap an SWS project", or similar in natural language **and** the cwd does not already contain a valid `.sws-project.local.md` marker (or contains one and the user explicitly asks to re-init).

Do NOT invoke when:
- The user is in an unrelated directory and only mentions SWS in passing.
- The cwd is `$HOME`, `/`, a read-only filesystem, or a directory the user lacks write permission for. Refuse early with a clear message.

## Step a — Argument resolution (3-tier waterfall)

1. **Named args:** parse the slash-command invocation for any of:
   `--article-type, --language, --format, --target-journal, --target-call, --first-author, --year, --co-authors, --notebooklm, --c1, --c2, --c3, --c4, --c5, --c6`
2. **Natural-language `$ARGUMENTS`:** if free text accompanies the slash command (e.g., `/sws:init-project Communication for ChemBioChem on hDF kinetics, first author Smith with co-authors`), parse it for any unset fields. Use the model's natural-language understanding; do not require structured syntax.
3. **Interactive prompts:** for any required field still missing, prompt one at a time. Defaults come from `references/marker-schema.md` (`language: en`, `format: docx`, `notebooklm.enabled: false`). For `year`, default to the current system year.

**Conflict override flags:** `--c1`..`--c6` each take a string value matching that conflict class's `options` list (e.g., `--c4=replace`, `--c4=append`, `--c4=skip`). These override the safe-default resolution computed in Step c. NL-parse counterparts:
- "overwrite my CLAUDE.md" / "replace existing CLAUDE.md" → c4=replace
- "skip the docx move" / "leave paper.docx where it is" → c1=skip
- "replace my memory" / "overwrite claude_memory" → c5=replace
- "skip the claude_material rename" → c3=skip
- similar patterns apply for c2 and c6

**Override validation:** If the user supplies a value not in the conflict's `options` list (e.g., `--c4=foobar`), abort before calling plan with: `Error: --c4=foobar is not a valid override. Valid options for C4: [replace, append, skip].`

**Override for absent conflict:** If the user supplies `--c4=replace` but no CLAUDE.md exists (C4 not detected), silently ignore the override (no harm, no warning). Accepted v0.1 behavior.

After arg resolution, slugify `first_author` and compute `short_handle = <slug> + ("_et_al_" if co_authors_present else "_") + <year>`.

## Step b — Preflight + detection scan

All Python utilities live inside the plugin at `${CLAUDE_PLUGIN_ROOT}/scripts/`. The skill is invoked from the user's manuscript directory (the cwd), NOT from the plugin root, so every Bash call must use the `${CLAUDE_PLUGIN_ROOT}` env var for absolute paths. Relative `scripts/...` paths will fail.

Before any disk work, run the env preflight:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sws_check_env.py"
```

If exit non-zero, print the error verbatim and abort. Do not attempt to invoke any other Python utility.

Then scan the cwd for the 6 conflict classes:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sws_init_project.py" scan --root .
```

The output is a JSON array of conflicts (each with `cls`, `path`, `suggested_action`, `options`). If empty, jump straight to step d (fresh-init). Otherwise proceed to step c.

## Step c — Per-conflict prompts

For each conflict in scan output, prompt the user with the suggested-default UX:

```
Found `paper.docx` at root. Move to `Manuscript/paper.docx`? [Y/n/skip/manual]
```

- `Y` (or empty input) = accept suggested action (resolution: `accept`).
- `n` = reject suggested action (resolution: `reject`).
- `skip` = leave the file alone, continue init (resolution: `skip`).
- `manual` = abort the whole init for user-handled cleanup (exit cleanly, no disk writes).

For **C4 (existing CLAUDE.md)** the options are `[r]eplace / [a]ppend / [s]kip`:
  - `replace` = overwrite user's CLAUDE.md with the SWS per-paper template. The user's existing content is lost (no automatic backup in v0.1).
  - `append` = preserve the user's CLAUDE.md verbatim and append a marker-delimited `## SWS-managed` section at the end (cross-refs to plugin canonical references; pointer to `.sws-project.local.md` for project metadata). Idempotent on re-run: the HTML-comment markers let SWS replace the existing section instead of duplicating it. Recommended for hand-curated CLAUDE.md files.
  - `skip` = leave the user's CLAUDE.md entirely untouched. SWS still writes the marker (`.sws-project.local.md`); agents reading via session auto-load get the user's existing CLAUDE.md as primary context.

For **C5 (existing claude_memory/)** the options are `[k]eep / [r]eplace`:
  - `keep` = leave user's claude_memory/ contents alone. SWS does NOT write MEMORY.md or passport.json. Use this if the user is migrating an existing claude_memory layout and wants to integrate manually.
  - `replace` = overwrite `claude_memory/MEMORY.md` and `claude_memory/passport.json` only. Other files inside `claude_memory/` are preserved.

For **C6 (existing marker)** the options are `[proceed]` / `[abort]`. On `proceed`, load the existing marker's values, present them as defaults during the arg-resolution prompts, then write a merged marker.

**Note (v0.2 backlog):** Smarter merges deferred to v0.2 — `[m]ove` for C5 (rotate `claude_memory/` to `claude_memory/_archive/` then write fresh), frontmatter merge for existing YAML in user's CLAUDE.md, content-aware section placement. The v0.1 options ship the data-loss-safe defaults plus the `[a]ppend` smart-merge for the typical case (existing CLAUDE.md with hand-curated content).

Build a `resolutions` dict mapping `cls` → user choice.

## Step d — Plan assembly

Write the inputs and resolutions to temp JSON files and call:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sws_init_project.py" plan \
  --inputs /tmp/sws_inputs.json \
  --conflicts /tmp/sws_conflicts.json \
  --resolutions /tmp/sws_resolutions.json
```

The output is the ordered op list as JSON.

## Step e — Plan presentation

Display the plan to the user as a numbered list before any disk write. Example format:

```
Plan (12 ops):
  1. mkdir Manuscript/, Figures/main/, Figures/SI/, Tables/, ...
  2. mv ./paper.docx → Manuscript/paper.docx
  3. mv claude_material/ → scratch/
  4. render templates/sws-project-marker.template → .sws-project.local.md
  5. render templates/manuscript-claude-md.template → CLAUDE.md
  6. render templates/manuscript-memory-md.template → claude_memory/MEMORY.md
  7. write claude_memory/passport.json (cycle 0)

Apply? [apply/cancel]
```

Group consecutive `mkdir` ops on one line for readability. Show `mv`, `render`, `write_json` distinctly.

If user types `cancel`, exit cleanly with no disk writes. If `apply`, proceed to step f.

## Step f — Apply with rollback

Save the plan JSON to a temp file and execute:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sws_init_project.py" apply \
  --plan /tmp/sws_plan.json \
  --root . \
  --plugin-root "${CLAUDE_PLUGIN_ROOT}"
```

The utility executes ops in order with an in-memory undo log; on failure or `ctrl-C` it reverses the log. User-pre-existing files are touched only via ops the user explicitly approved at step c.

If exit non-zero, print the rollback log and stop. If exit zero, proceed to step g.

## Step g — Post-apply

Run the filesystem indexer to write the initial `claude_memory/fs_index.json`:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sws_fs_index.py" --root . --out claude_memory/fs_index.json
```

Print summary:

```
Bootstrapped <short_handle> at <cwd>.
  N files created
  M files relocated
  article_type=<...>, language=<...>, format=<...>
  target_journal=<...> | target_call=<...>
  marker → .sws-project.local.md
  per-paper context → CLAUDE.md, claude_memory/MEMORY.md
  passport.json: cycle 0
  fs_index.json: <count> files indexed

Next steps (suggested):
  - Run /sws:resolve-journal-style <slug> to cache the venue style overlay (cycle #4).
  - Drop your manuscript at Manuscript/<short_handle>.docx (or .tex).
  - Start drafting (cycle #5 ships the drafter agent).
```

## Edge cases (defer to spec)

The 10 edge cases are enumerated in the spec's `edge_cases` frontmatter (E1 unsafe cwd, E2 arg mismatch journal, E3 funding-proposal no call, E4 Unicode first-author slugify, E5 empty first-author, E6 implausible year, E7 partial NL parse, E8 malformed existing marker, E9 cancel at plan, E10 failure mid apply). Behave per spec.

## What NOT to do

- Do not apply SWS docx styles to existing manuscript files. That's the `style-enforcer` agent's job in cycle #6.
- Do not auto-fetch journal-style overlays. That's `/sws:resolve-journal-style` (cycle #4).
- Do not create a stub manuscript file (`Manuscript/<short_handle>.docx`). The drafter generates this in cycle #5.
- Do not create a per-paper `.gitignore`. Adoption is uneven; user can add one if they `git init`.
- Do not push, merge, or modify any SWS plugin file from inside init-project. Only the user's manuscript directory is touched.

## Additional Resources

- `docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md` — spec frontmatter (locked decisions dictionary)
- `references/folder-topology.md` — base + conditional directory tree
- `references/marker-schema.md` — marker field schema
- `references/python-env.md` — Python preflight pattern + version policy
- `references/docx-style.md` — typography canon (cycle #5+ consumers only)
- `scripts/sws_check_env.py` — env preflight (called at step b)
- `scripts/sws_init_project.py` — scan / plan / apply utility (called at b, d, f)
- `scripts/sws_render_template.py` — template renderer (called transitively by apply for `render_template` ops)
- `scripts/sws_fs_index.py` — filesystem indexer (called at step g)
- `templates/sws-project-marker.template`, `templates/manuscript-claude-md.template`, `templates/manuscript-memory-md.template` — substituted by step f
- `claude_memory/feedback_lean_deliverables.md` — guidance for any rendered docs (lean YAML form)
- `claude_memory/feedback_docx_typography.md` — rationale for the typography canon
