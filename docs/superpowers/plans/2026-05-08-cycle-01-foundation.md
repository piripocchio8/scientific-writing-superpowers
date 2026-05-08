# SWS Cycle #1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the foundation that every subsequent SWS cycle depends on — plugin manifest, canonical directory tree, two reference docs (folder-topology and marker-schema), the recycled superpowers trio (`brainstormer`, `planner`, `code-reviewer`), the filesystem-index utility, and the four community-surface files (CONTRIBUTING, CODE_OF_CONDUCT, three issue templates). Banner stays `🚧 v0.1 in design`.

**Architecture:** SWS is a Claude Code plugin published from `/Users/piripocchio8/Projects/scientific-writing-superpowers/` with the manifest at `.claude-plugin/plugin.json`, components auto-discovered from `agents/`, `skills/`, `commands/`, `hooks/`, and `.mcp.json`. Cycle #1 ships only the manifest, the recycled trio, the filesystem-index utility, the reference docs, and the community surface — no SWS-original agents, skills, hooks, slash commands, or templates yet. Those land in cycles #2 onward per the locked 11-cycle roadmap.

**Tech Stack:** Markdown + YAML frontmatter for skills/agents; JSON for plugin manifest and filesystem-index output; Python 3.9 (pymol25 mamba env at `/Users/piripocchio8/opt/miniconda3/envs/pymol25/bin/python`) for the filesystem-index utility (stdlib only); Bash for git operations; `gh` CLI for the optional PR step.

**Working directory throughout:** `/Users/piripocchio8/Projects/scientific-writing-superpowers/`.

**Branch strategy:** feature branch `cycle/01-foundation` (decided in `claude_memory/project_brainstorm_progress.md` — solo work + small cycle-#1 scope makes a worktree overkill). Cycle ends with merge or PR-then-merge to `main` and a banner-unchanged push.

**Source-of-truth references for content:**
- Locked decisions: `claude_memory/project_decisions_so_far.md`
- Architecture-sketch design: `docs/superpowers/specs/2026-05-08-architecture-sketch-design.md`
- Roster + profiles + v0.2 backlog: `claude_memory/project_roster_v0.1.md`, `project_profiles.md`, `project_v02_backlog.md`
- Upstream recycled-trio sources (read-only — these are what we copy from):
  - `/Users/piripocchio8/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/SKILL.md`
  - `/Users/piripocchio8/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/writing-plans/SKILL.md`
  - `/Users/piripocchio8/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/agents/code-reviewer.md`

**Recycled-trio mechanism (locked from research):** mechanism (b) — copy upstream file, append `# Adapted from superpowers (MIT)` attribution comment above the YAML frontmatter, rename via the `name:` frontmatter field. Reasoning: neither `plugin-dev:skill-development` nor `plugin-dev:agent-development` documents a manifest-level re-export or alias system; auto-discovery is purely filesystem-based; copy-with-attribution is the only mechanism consistent with the documented loader. MIT-on-MIT compatibility verified.

**Plan validation note:** all four `.md` reference cards from the parallel research subagents (plugin-structure, skill-development, agent-development) match. Required agent frontmatter is `name`, `description`, `model`, `color` — color is required, not optional. `model: inherit` is documented only as "Use same model as parent (recommended)" with no further nuance.

---

## Revision note (post-plan, 2026-05-08)

After this plan was written, the user issued a constitutional rule about lean deliverables (see `claude_memory/feedback_lean_deliverables.md`): generated `.md` files put structured data in YAML frontmatter and keep the body short with cross-refs to source-of-truth (CLAUDE.md, design doc, decisions log) rather than duplicating their content. This applies retroactively to **Tasks 2, 3, and 6**: the file contents shipped will deviate from the verbose drafts in those tasks and use a leaner YAML-as-dictionary form. Tasks 1, 4, 5, 7, 8, 9 are unaffected (JSON, code, copy-edit, fetch-with-substitution, and templates respectively). Each affected commit message documents the deviation.

## Pre-flight: Branch creation

Before Task 1.

- [ ] **Verify clean working tree.**

```bash
git -C /Users/piripocchio8/Projects/scientific-writing-superpowers status -s
```

Expected: empty output (no uncommitted changes).

- [ ] **Create and switch to the feature branch.**

```bash
git -C /Users/piripocchio8/Projects/scientific-writing-superpowers checkout -b cycle/01-foundation
```

Expected: `Switched to a new branch 'cycle/01-foundation'`.

- [ ] **Confirm branch.**

```bash
git -C /Users/piripocchio8/Projects/scientific-writing-superpowers branch --show-current
```

Expected: `cycle/01-foundation`.

---

## Task 1 — Plugin manifest + directory scaffold

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `agents/.gitkeep`
- Create: `skills/.gitkeep`
- Create: `hooks/.gitkeep`
- Create: `profiles/.gitkeep`
- Create: `templates/.gitkeep`
- Create: `examples/.gitkeep`
- Create: `references/.gitkeep`

(`commands/`, `scripts/`, `tests/`, `.github/` are created later by tasks that populate them. YAGNI — don't pre-create empty dirs we won't fill in cycle #1.)

- [ ] **Step 1: Create `.claude-plugin/` directory.**

```bash
mkdir -p .claude-plugin
```

- [ ] **Step 2: Write `.claude-plugin/plugin.json` with the canonical manifest.**

Content (use `Write` tool; exact JSON):

```json
{
  "name": "scientific-writing-superpowers",
  "version": "0.0.1",
  "description": "DOCX-first scientific manuscript preparation toolkit for chemistry and biology labs. Recycles the superpowers brainstorming + planning + code-review trio and adds 24 SWS-original agents, 9 writing-context profiles, marker-scoped hooks, and a filesystem-index utility.",
  "author": {
    "name": "Marco Chino",
    "email": "65242025+piripocchio8@users.noreply.github.com",
    "url": "https://github.com/piripocchio8"
  },
  "homepage": "https://github.com/piripocchio8/scientific-writing-superpowers",
  "repository": "https://github.com/piripocchio8/scientific-writing-superpowers",
  "license": "MIT",
  "keywords": [
    "scientific-writing",
    "manuscript",
    "docx",
    "chemistry",
    "biology",
    "academic-writing",
    "peer-review",
    "claude-code",
    "claude-plugin"
  ]
}
```

Why these field choices:
- `name` is `kebab-case` and matches the public repo name (canonical loader requirement).
- `version` is `0.0.1` because cycle #1 is pre-alpha scaffold; bumps to `0.1.0-alpha.0` after cycle #7 (when banner becomes `🧪 v0.1 alpha`); `0.1.0` after the first real paper (banner `v0.1`).
- `author` uses the same name + noreply email as the repo's local git config (already set; `Marco Chino <65242025+piripocchio8@users.noreply.github.com>`). No global git config touched.
- `repository` is a bare URL string (per canonical schema — the docs example uses string form, not the npm-style `{type, url}` object).
- No `commands`, `agents`, `hooks`, or `mcpServers` custom-path overrides — auto-discovery from default directories is sufficient and overrides supplement (don't replace) defaults.

- [ ] **Step 3: Create empty placeholder dirs with `.gitkeep` files.**

```bash
mkdir -p agents skills hooks profiles templates examples references
touch agents/.gitkeep skills/.gitkeep hooks/.gitkeep profiles/.gitkeep templates/.gitkeep examples/.gitkeep references/.gitkeep
```

Note: `references/.gitkeep` will be deleted in Task 3 once the first real reference doc lands. The other six stay until the cycle that populates them.

- [ ] **Step 4: Verify the manifest is valid JSON.**

```bash
python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); print('OK')"
```

Expected: `OK`.

- [ ] **Step 5: Verify the tree.**

```bash
ls -la .claude-plugin agents skills hooks profiles templates examples references
```

Expected: each subdir contains `.gitkeep` (except `.claude-plugin/`, which contains `plugin.json`).

- [ ] **Step 6: Commit.**

```bash
git add .claude-plugin agents skills hooks profiles templates examples references
git commit -m "$(cat <<'EOF'
feat: plugin manifest and directory scaffold

Adds .claude-plugin/plugin.json (canonical manifest with name, version,
description, author, repository, license, keywords) and empty
auto-discoverable component dirs with .gitkeep. Cycle #1 task 1.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2 — `references/folder-topology.md`

The folder-topology reference doc that user-manuscript projects bootstrapped by `/sws:init-project` (cycle #2) will instantiate. Source: locked decisions in `claude_memory/project_decisions_so_far.md` (2026-05-06 entry "Folder topology for SWS-bootstrapped projects").

**Files:**
- Create: `references/folder-topology.md`
- Delete: `references/.gitkeep`

- [ ] **Step 1: Write `references/folder-topology.md`.**

Content (exact — use `Write` tool):

````markdown
# SWS Folder Topology — Bootstrapped Manuscript Projects

> Reference for `/sws:init-project` (cycle #2) and any SWS agent that walks the user's manuscript-project directory tree. Locked 2026-05-06.

## Base layout (every SWS project gets this)

```
<paper-root>/
├── CLAUDE.md                  # bootstrap-generated; per-paper context
├── claude_memory/             # session state — passport.json, MEMORY.md, cycle logs, fs_index.json
├── .sws-project.local.md      # SWS marker (hooks no-op outside its presence)
├── Manuscript/
│   ├── <paper>.docx           # primary deliverable (or main.tex when format: latex)
│   ├── _journal-style/<journal-slug>.md   # cached profile overlay
│   └── _archive/              # pre-edit backups, prior versions
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
│   ├── data/                  # xlsx-as-data-authority
│   ├── scripts/               # fit + plot, co-located with the data they describe
│   └── _archive/
├── scratch/                   # ephemeral working files (replaces hDF's claude_material/)
└── refs/                      # Zotero exports, BibTeX, .ris
```

## Conditional additions

Triggered by profile or opt-in flags in `.sws-project.local.md`:

- **`call/`** at `<paper-root>/` — created **only when `active_profile: funding-proposal`**. Holds call-specific artifacts (call rules, eligibility/expense rules, deadlines, evaluation criteria, official call PDFs, lab-of-origin requirements). Persists across cycles within a proposal; **not deleted** when the user switches profiles afterwards.
- **`refs/nlm_uploads/`** — created **only when `notebooklm.enabled: true`**. Curated NotebookLM corpus (PDFs, prior notes, draft sections, related papers) ingested by the `nlm-librarian` agent. Subfoldered to keep stable curated content separate from bibliography exports.

## Naming and conventions (locked)

- `Manuscript/` (not `Paper/`, not root) holds the primary docx + journal overlay.
- `scratch/` (not hDF's `claude_material/`) holds ephemeral work.
- `_archive/` is **per-folder** — no global `_archive/` at root. Each folder owns its own.
- `Tables/` is a separate top-level folder mirroring `Figures/`.
- `SI/` is top-level; SI figures live at `SI/SI_Figures/` (not at `Figures/SI/`).
- `refs/` is top-level for bibliography artifacts.
- Underscore-prefixed folders (`_archive/`, `_journal-style/`, `_voice/`, `_call-style/`) signal SWS-managed metadata.

## Why this layout

Matches how scientific-writing projects naturally split into deliverables (manuscript, SI, figures, tables, data) and avoids the flat-folder antipattern from prior projects. Per-folder `_archive/` makes pruning local. Conditional folders avoid clutter when the feature is inactive.

## Apply

`/sws:init-project` creates the base layout unconditionally and the conditional folders only when their trigger fires. If the user switches `active_profile` away from `funding-proposal`, `call/` is preserved (the user may still need it for revisions or grant reports).
````

- [ ] **Step 2: Remove the `.gitkeep` placeholder now that `references/` has real content.**

```bash
rm references/.gitkeep
```

- [ ] **Step 3: Verify the file is well-formed Markdown.**

```bash
head -5 references/folder-topology.md && wc -l references/folder-topology.md
```

Expected: heading + first lines visible; line count > 50.

- [ ] **Step 4: Commit.**

```bash
git add references/folder-topology.md references/.gitkeep
git commit -m "$(cat <<'EOF'
docs: add folder-topology reference for SWS manuscript projects

Codifies the bootstrapped-project directory tree (Manuscript/, Figures/,
Tables/, SI/, Zenodo_db/, scratch/, refs/) and the two conditional adds
(call/ for funding-proposal profile; refs/nlm_uploads/ when NLM opt-in).
Source: project_decisions_so_far.md 2026-05-06 entry. Cycle #1 task 2.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3 — `references/marker-schema.md`

The schema for `<paper-root>/.sws-project.local.md`, the marker file every SWS hook checks before doing anything substantive. Source: locked decisions in `claude_memory/project_decisions_so_far.md` (2026-05-06 entry "Hook scoping rule" + 2026-05-06 Section 2 revisions).

**Files:**
- Create: `references/marker-schema.md`

- [ ] **Step 1: Write `references/marker-schema.md`.**

Content (exact):

````markdown
# `.sws-project.local.md` — Marker Schema

> The marker file written by `/sws:init-project` and checked by every SWS hook. Absent marker = silent hook no-op. Locked 2026-05-06.

## Location

`<paper-root>/.sws-project.local.md`. Each user-manuscript project has exactly one. The hooks check the current working directory; nested invocations resolve from the directory the user is operating in.

## Schema (v0.1)

YAML frontmatter, free-form Markdown body.

```yaml
---
sws_version: 0.1
active_profile: communication        # one of the 9 v0.1 profiles
language: en                         # v0.1: en | it
format: docx                         # v0.1: docx | latex
target_journal: chembiochem          # optional; null until /sws:resolve-journal-style runs
target_call: null                    # optional; null until /sws:resolve-call-rules runs
notebooklm:
  enabled: false                     # opt-in for nlm-librarian agent + refs/nlm_uploads/
created: 2026-05-08T00:00:00Z        # ISO 8601 with timezone
---

# free-form notes about this paper-project
# (anything below the closing --- is preserved across regenerations)
```

## Field semantics

| Field | Required | Type | Valid values (v0.1) | Default |
|---|---|---|---|---|
| `sws_version` | yes | string | `0.1` | `0.1` |
| `active_profile` | yes | string | `full-article`, `communication`, `perspective`, `review-paper`, `mini-review`, `editorial`, `methodological-paper`, `commentary-reply`, `funding-proposal` | (none — `/sws:init-project` asks) |
| `language` | yes | string | `en`, `it` | `en` |
| `format` | yes | string | `docx`, `latex` | `docx` |
| `target_journal` | no | string \| null | journal slug (lowercase, no spaces) | `null` |
| `target_call` | no | string \| null | call slug (lowercase, no spaces) | `null` |
| `notebooklm.enabled` | yes | bool | `true`, `false` | `false` |
| `created` | yes | string | ISO 8601 with timezone | (set by `/sws:init-project`) |

## Conditional triggers

- `active_profile: funding-proposal` → triggers creation of `call/` directory (see `folder-topology.md`).
- `notebooklm.enabled: true` → triggers creation of `refs/nlm_uploads/` and activates `nlm-librarian` agent (`nlm-librarian` becomes inert when `false`).
- `format: latex` → format-aware agents (drafter, reviser, style-enforcer, format-checker, table-formatter, equation-handler, figure-caption-writer) read `main.tex` instead of `<paper>.docx`; pre-edit backup hook covers `*.{tex,bib,cls}` in addition to `*.docx`.

## Why this design

- **Marker file = scope gate.** Every SWS hook's first ~3 lines check for marker presence; absent = silent no-op (microseconds, zero output). Makes SWS inert outside SWS projects.
- **Profile and language are orthogonal.** A US researcher writing an NSF proposal stays at `language: en`; an Italian researcher writing a PRIN proposal sets `language: it` explicitly. Profile YAML stays language-agnostic.
- **Format and profile are orthogonal.** LaTeX is opt-in via `format: latex`; one active format per project.
- **`target_journal` / `target_call` are nullable** so the marker can be written before the user has resolved the venue. Resolver slash commands (`/sws:resolve-journal-style`, `/sws:resolve-call-rules`) populate them.
- **`.local.md` suffix** keeps the file out of common dotfile-collision patterns and signals a per-project config.

## Validation rules

- An SWS hook seeing a malformed marker (missing required field, wrong type) prints a single warning and falls back to no-op behavior; never crashes the user's session.
- `/sws:init-project` writes a fresh marker; rewriting an existing marker requires `--force` to prevent accidental clobber of user-edited notes below the body separator.

## Apply

When implementing hooks (cycle #3), the marker check is the first ~3 lines of every hook script. New hooks added later (e.g., v0.2 promotions) inherit the same scoping rule. New marker fields land via additive minor-version bumps (`sws_version: 0.2` etc.) with backward-compatible defaults.
````

- [ ] **Step 2: Verify formatting.**

```bash
head -5 references/marker-schema.md && wc -l references/marker-schema.md
```

Expected: heading + lines visible; line count > 60.

- [ ] **Step 3: Commit.**

```bash
git add references/marker-schema.md
git commit -m "$(cat <<'EOF'
docs: add marker-schema reference for .sws-project.local.md

Codifies the YAML-frontmatter schema every SWS hook checks before
acting (sws_version, active_profile, language, format, target_journal,
target_call, notebooklm.enabled, created). Source:
project_decisions_so_far.md 2026-05-06 entries. Cycle #1 task 3.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4 — Recycled trio (`brainstormer`, `planner`, `code-reviewer`)

Mechanism: copy upstream file, prepend `# Adapted from superpowers (MIT)` attribution comment above the YAML frontmatter, change the `name:` field. The skill body is preserved verbatim so behavior matches upstream exactly.

**Files:**
- Create: `skills/brainstormer/SKILL.md`
- Create: `skills/planner/SKILL.md`
- Create: `agents/code-reviewer.md`
- Delete: `skills/.gitkeep`
- Delete: `agents/.gitkeep`

**Sub-task 4a — `skills/brainstormer/SKILL.md`**

- [ ] **Step 1: Create the directory and copy the upstream skill.**

```bash
mkdir -p skills/brainstormer
cp /Users/piripocchio8/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/SKILL.md skills/brainstormer/SKILL.md
```

- [ ] **Step 2: Verify the copy is intact.**

```bash
head -5 skills/brainstormer/SKILL.md
wc -l skills/brainstormer/SKILL.md
```

Expected: file starts with `---` frontmatter; line count matches upstream (use `wc -l` on upstream as the comparison: should be identical).

- [ ] **Step 3: Prepend attribution comment + rename via frontmatter.**

Use the `Edit` tool. Read the current first ~10 lines of `skills/brainstormer/SKILL.md` to find the exact upstream `name:` line. Then:

a. Prepend `<!-- Adapted from superpowers:brainstorming (MIT). Original at https://github.com/obra/superpowers — see LICENSE for full attribution. -->` as a single-line HTML comment **before** the opening `---` of the frontmatter (HTML comments outside frontmatter are valid Markdown and inert to the loader).

b. Change the `name:` field in the frontmatter from `brainstorming` (or whatever the upstream value is) to `brainstormer`.

c. Update the `description:` field to add an SWS-aware preamble: replace the leading sentence with `Use when starting any creative SWS work — drafting a section, designing a new agent or skill, defining a workflow — before implementation.` Keep the rest of the upstream description verbatim so SWS triggers preserve upstream triggers.

- [ ] **Step 4: Verify the frontmatter parses.**

```bash
python3 -c "
import re, yaml, sys
content = open('skills/brainstormer/SKILL.md').read()
m = re.search(r'^---\n(.*?)\n---', content, re.S | re.M)
fm = yaml.safe_load(m.group(1))
assert fm['name'] == 'brainstormer', f\"name is {fm['name']!r}\"
assert 'description' in fm and len(fm['description']) > 20
print('OK', fm['name'])
"
```

Expected: `OK brainstormer`. (If `pyyaml` is missing in the active env, install it: `pip install pyyaml`. The pymol25 env should already have it; fall back to manual `head -10` inspection if not.)

**Sub-task 4b — `skills/planner/SKILL.md`**

- [ ] **Step 1: Copy.**

```bash
mkdir -p skills/planner
cp /Users/piripocchio8/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/writing-plans/SKILL.md skills/planner/SKILL.md
```

- [ ] **Step 2: Prepend attribution + rename.**

a. Prepend `<!-- Adapted from superpowers:writing-plans (MIT). Original at https://github.com/obra/superpowers — see LICENSE for full attribution. -->` before the opening `---`.

b. Change `name:` from `writing-plans` to `planner`.

c. Replace the leading sentence of `description:` with `Use when you have an SWS spec or design doc and need a multi-task implementation plan, before touching code.` Keep the rest of the upstream description verbatim.

- [ ] **Step 3: Verify.**

```bash
python3 -c "
import re, yaml
fm = yaml.safe_load(re.search(r'^---\n(.*?)\n---', open('skills/planner/SKILL.md').read(), re.S|re.M).group(1))
assert fm['name'] == 'planner', f\"name is {fm['name']!r}\"
print('OK', fm['name'])
"
```

Expected: `OK planner`.

**Sub-task 4c — `agents/code-reviewer.md`**

- [ ] **Step 1: Copy.**

```bash
cp /Users/piripocchio8/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/agents/code-reviewer.md agents/code-reviewer.md
```

- [ ] **Step 2: Read upstream frontmatter to capture exact field values.**

```bash
sed -n '1,30p' agents/code-reviewer.md
```

Confirm the upstream agent has `model: inherit` and a `color:` field. Required-field check: `name`, `description`, `model`, `color` must all be present. If any are missing, add minimal canonical values (`color: cyan` is a reasonable default for review work) before continuing.

- [ ] **Step 3: Prepend attribution + verify required fields.**

a. Prepend `<!-- Adapted from superpowers (MIT). Original at https://github.com/obra/superpowers — see LICENSE for full attribution. -->` before the opening `---`.

b. Confirm `name: code-reviewer` (no rename needed; the SWS-namespaced invocation will be `sws:code-reviewer` automatically because the plugin manifest sets the namespace).

c. Confirm `model: inherit` is preserved verbatim. **Do not change this.** It is load-bearing — the recycled reviewer must run as the parent session's model.

d. Confirm `color:` is present and one of `blue`, `cyan`, `green`, `yellow`, `magenta`, `red`. Default to `cyan` if absent (least intrusive, common reviewer color).

e. Confirm `description:` is present and 200–1000 chars. Keep verbatim if so.

- [ ] **Step 4: Verify all required fields parse.**

```bash
python3 -c "
import re, yaml
fm = yaml.safe_load(re.search(r'^---\n(.*?)\n---', open('agents/code-reviewer.md').read(), re.S|re.M).group(1))
for f in ('name', 'description', 'model', 'color'):
    assert f in fm, f'missing {f}'
assert fm['model'] == 'inherit', f\"model is {fm['model']!r}, expected 'inherit'\"
assert fm['color'] in ('blue', 'cyan', 'green', 'yellow', 'magenta', 'red'), f\"color is {fm['color']!r}\"
print('OK', fm['name'], fm['model'], fm['color'])
"
```

Expected: `OK code-reviewer inherit <color>`.

- [ ] **Step 5: Remove `.gitkeep` placeholders.**

```bash
rm skills/.gitkeep agents/.gitkeep
```

- [ ] **Step 6: Commit the recycled trio.**

```bash
git add skills/brainstormer/ skills/planner/ agents/code-reviewer.md skills/.gitkeep agents/.gitkeep
git commit -m "$(cat <<'EOF'
feat: recycled superpowers trio (brainstormer, planner, code-reviewer)

Imports superpowers:brainstorming → sws:brainstormer,
superpowers:writing-plans → sws:planner, and superpowers:code-reviewer
(model: inherit) via copy-with-MIT-attribution. Behavior matches upstream
verbatim except for SWS-aware preamble in skill descriptions. Mechanism
chosen because plugin-dev:skill-development and plugin-dev:agent-development
do not document a manifest-level re-export. Cycle #1 task 4.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5 — Filesystem-index utility (TDD)

Pure-stdlib Python utility that walks a project tree and writes a JSON manifest of file metadata (path, size, mtime, ext) so later tool calls read the manifest instead of repeatedly running `ls`/`find`. Designed for the pymol25 env (Python 3.9+).

**Files:**
- Create: `tests/__init__.py` (empty file so pytest discovers `tests/`)
- Create: `tests/test_fs_index.py`
- Create: `scripts/sws_fs_index.py`

- [ ] **Step 1: Create directories.**

```bash
mkdir -p tests scripts
touch tests/__init__.py
```

- [ ] **Step 2: Write the failing test.**

`tests/test_fs_index.py`:

```python
"""Tests for sws_fs_index.py — pure stdlib + unittest, runs under pymol25."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import sws_fs_index  # noqa: E402


class TestFilesystemIndex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Fixture tree:
        #   root/Manuscript/paper.docx
        #   root/Manuscript/_archive/old.docx          <- excluded (_archive)
        #   root/Figures/main/fig1.png
        #   root/.git/HEAD                             <- excluded (.git)
        #   root/paper.backup_pre_edit.docx            <- excluded (backup pattern)
        #   root/scratch/note.md
        (self.root / "Manuscript").mkdir()
        (self.root / "Manuscript" / "paper.docx").write_bytes(b"abc")
        (self.root / "Manuscript" / "_archive").mkdir()
        (self.root / "Manuscript" / "_archive" / "old.docx").write_bytes(b"x")
        (self.root / "Figures" / "main").mkdir(parents=True)
        (self.root / "Figures" / "main" / "fig1.png").write_bytes(b"png")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "HEAD").write_text("ref: ...")
        (self.root / "paper.backup_pre_edit.docx").write_bytes(b"bk")
        (self.root / "scratch").mkdir()
        (self.root / "scratch" / "note.md").write_text("# note")

    def tearDown(self):
        self.tmp.cleanup()

    def test_index_includes_manuscript_and_figures(self):
        manifest = sws_fs_index.build_index(self.root)
        paths = {entry["path"] for entry in manifest["files"]}
        self.assertIn("Manuscript/paper.docx", paths)
        self.assertIn("Figures/main/fig1.png", paths)
        self.assertIn("scratch/note.md", paths)

    def test_index_excludes_archives_git_and_backups(self):
        manifest = sws_fs_index.build_index(self.root)
        paths = {entry["path"] for entry in manifest["files"]}
        self.assertNotIn("Manuscript/_archive/old.docx", paths)
        self.assertNotIn(".git/HEAD", paths)
        self.assertNotIn("paper.backup_pre_edit.docx", paths)

    def test_manifest_metadata_fields(self):
        manifest = sws_fs_index.build_index(self.root)
        self.assertIn("version", manifest)
        self.assertIn("generated", manifest)
        self.assertIn("root", manifest)
        self.assertIsInstance(manifest["files"], list)
        for entry in manifest["files"]:
            self.assertIn("path", entry)
            self.assertIn("size_bytes", entry)
            self.assertIn("mtime", entry)
            self.assertIn("ext", entry)

    def test_cli_writes_json(self):
        out_path = self.root / "claude_memory" / "fs_index.json"
        out_path.parent.mkdir()
        rc = sws_fs_index.main(["--root", str(self.root), "--out", str(out_path)])
        self.assertEqual(rc, 0)
        self.assertTrue(out_path.exists())
        data = json.loads(out_path.read_text())
        self.assertEqual(Path(data["root"]).resolve(), self.root.resolve())
        self.assertGreaterEqual(len(data["files"]), 3)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to confirm it fails (no implementation yet).**

```bash
/Users/piripocchio8/opt/miniconda3/envs/pymol25/bin/python -m unittest tests.test_fs_index -v
```

Expected: `ModuleNotFoundError: No module named 'sws_fs_index'` or equivalent import failure. **Do not proceed until you see this.**

- [ ] **Step 4: Write the minimal implementation.**

`scripts/sws_fs_index.py`:

```python
#!/usr/bin/env python3
"""SWS filesystem-index utility.

Walk a project directory, write a JSON manifest of file metadata so later
tool calls read the manifest instead of repeatedly running ls/find.
Designed for the pymol25 mamba env (Python 3.9+, stdlib only).

Usage:
    python sws_fs_index.py [--root <dir>] [--out <path>]
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import sys
from pathlib import Path

VERSION = "0.1.0"

DEFAULT_EXCLUDES = (
    ".git",
    ".venv",
    "__pycache__",
    "_archive",
    "node_modules",
    ".DS_Store",
    "*.backup_pre_*.docx",
    "*.backup_pre_*.tex",
    "*.backup_pre_*.bib",
    "*.backup_pre_*.cls",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
)


def _is_excluded(path: Path, root: Path, patterns) -> bool:
    rel = path.relative_to(root)
    for part in rel.parts:
        for pattern in patterns:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False


def build_index(root, excludes=DEFAULT_EXCLUDES) -> dict:
    root = Path(root).resolve()
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _is_excluded(path, root, excludes):
            continue
        stat = path.stat()
        files.append({
            "path": str(path.relative_to(root)),
            "size_bytes": stat.st_size,
            "mtime": dt.datetime.fromtimestamp(
                stat.st_mtime, tz=dt.timezone.utc
            ).isoformat(),
            "ext": path.suffix.lower(),
        })
    return {
        "version": VERSION,
        "generated": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "root": str(root),
        "files": files,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root (default: cwd)")
    parser.add_argument(
        "--out",
        default="./claude_memory/fs_index.json",
        help="output JSON path (default: ./claude_memory/fs_index.json)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_index(root)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"Wrote {len(manifest['files'])} entries to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the test to confirm it passes.**

```bash
/Users/piripocchio8/opt/miniconda3/envs/pymol25/bin/python -m unittest tests.test_fs_index -v
```

Expected:
```
test_cli_writes_json (tests.test_fs_index.TestFilesystemIndex) ... ok
test_index_excludes_archives_git_and_backups (tests.test_fs_index.TestFilesystemIndex) ... ok
test_index_includes_manuscript_and_figures (tests.test_fs_index.TestFilesystemIndex) ... ok
test_manifest_metadata_fields (tests.test_fs_index.TestFilesystemIndex) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.0Ns

OK
```

- [ ] **Step 6: Smoke-test the CLI against the SWS repo itself.**

```bash
cd /Users/piripocchio8/Projects/scientific-writing-superpowers
mkdir -p claude_memory
/Users/piripocchio8/opt/miniconda3/envs/pymol25/bin/python scripts/sws_fs_index.py --root . --out /tmp/sws_self_index.json
head -30 /tmp/sws_self_index.json
```

Expected: JSON with `version`, `generated`, `root` fields and a `files[]` list containing entries like `Manuscript/...` (none, but should include `CLAUDE.md`, `LICENSE`, `README.md`, `.claude-plugin/plugin.json`, `agents/code-reviewer.md`, etc.). `_archive/`, `.git/`, and `*.backup_pre_*` files excluded.

- [ ] **Step 7: Confirm `claude_memory/` is gitignored** (don't accidentally commit `fs_index.json`).

```bash
git check-ignore -v claude_memory/fs_index.json
```

Expected output: a line ending with `claude_memory/` matched by `.gitignore` rule. If not ignored, stop and inspect `.gitignore` — `claude_memory/` should already be on the ignore list per the existing `.gitignore` committed in the architecture-sketch landing.

- [ ] **Step 8: Commit.**

```bash
git add scripts/sws_fs_index.py tests/__init__.py tests/test_fs_index.py
git commit -m "$(cat <<'EOF'
feat: filesystem-index utility for project state snapshots

Adds scripts/sws_fs_index.py (pure stdlib, pymol25-compatible) that
walks a project tree and writes a JSON manifest of file metadata so
later tool calls read the manifest instead of running ls/find.
Excludes .git, _archive, .venv, __pycache__, *.backup_pre_*.{docx,tex,bib,cls},
.pytest_cache, .mypy_cache. Includes 4 unittest-based tests covering
inclusion, exclusion, metadata fields, and CLI behavior. Cycle #1 task 5.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6 — `CONTRIBUTING.md`

One-page contributing guide. Source: locked decisions in `claude_memory/project_decisions_so_far.md` (2026-05-06 Q12 entry, reaffirmed in Section 6).

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Write `CONTRIBUTING.md`.**

Content (exact):

```markdown
# Contributing to Scientific-Writing-Superpowers

Thanks for considering a contribution! SWS is a Claude Code plugin for chemistry and biology lab manuscript preparation, with DOCX as the primary format and LaTeX as a parallel-track. This page describes what we welcome, what's out of scope, and how to test changes locally.

## In scope

- **Agent improvements** — sharpening prompts, tightening output formats, fixing edge cases in any of the 24 agents listed in `agents/` (or the `code-reviewer` recycled from superpowers).
- **New journal-style overlays** — adding `.md` overlay files for journals SWS doesn't yet support. The journal-style overlay issue template guides this.
- **New writing-context profiles** — only with discussion first; the v0.1 set of 9 profiles is locked. v0.2+ may add more.
- **Bug reports** with minimal reproductions. Use the bug template.
- **Feature requests.** Use the feature-request template.
- **Peer-review and proofreading** of agent prose — especially flagging AI-writing tells (em-dashes, "delve/leverage", triplets, "Not just X but Y") in agent outputs.
- **Documentation fixes** in `references/`, `CLAUDE.md`, `README.md`, and the design doc.
- **Examples** in `examples/` — sanitized, synthetic, never real unpublished research.

## Out of scope

- Rewriting the locked 24-agent roster without prior discussion (open an issue first).
- Switching SWS to LaTeX-as-primary. DOCX-first is a load-bearing positioning decision.
- Removing the docx-first commitment.
- Adding telemetry, analytics, or call-home behavior of any kind.
- Moving from MIT to GPL/CC0 or any other license.

## Local-test setup

SWS is a Claude Code plugin; most testing happens by installing it locally and exercising agents/skills/hooks in a separate manuscript project.

1. **Install Claude Code** (https://claude.com/claude-code) if not already installed.
2. **Clone this repo** to your plugin directory of choice.
3. **Add the plugin to your Claude Code config.** Either via `claude plugins install <path>` or by editing `~/.claude/settings.json` to add the path. (See Claude Code docs for the current canonical method.)
4. **Run the filesystem-index test suite** to confirm the Python utility works in your environment:

   ```bash
   /path/to/pymol25-or-equivalent/python -m unittest tests.test_fs_index -v
   ```

   The repo's reference Python env is `pymol25` (mamba). Any Python 3.9+ with stdlib-only is fine — `sws_fs_index.py` uses no external dependencies.

5. **Test an agent change** by installing the plugin, opening Claude Code in a synthetic SWS manuscript project, and invoking the affected agent.
6. **Test a journal-style overlay** by placing it at `Manuscript/_journal-style/<slug>.md` in a test project and confirming the relevant agent reads it.

## Pull requests

- Branch from `main`.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`).
- Atomic commits — one logical concept per commit.
- No PR template in v0.1; describe what you changed, why, and how you tested it in the PR description.
- The `code-reviewer` agent (recycled from superpowers, `model: inherit`) is available; the maintainer typically runs it before merge.

## Attribution and licensing

- SWS is MIT-licensed.
- Recycled agents/skills (the `brainstormer`, `planner`, `code-reviewer` trio) carry `<!-- Adapted from superpowers (MIT) -->` headers. Apply the same convention to anything you import from another MIT plugin.
- New work you submit is contributed under the project's MIT license; you retain copyright.

## Code of conduct

This project follows the Contributor Covenant 2.1 — see `CODE_OF_CONDUCT.md`.

## Questions

Open an issue. There are no GitHub Discussions in v0.1 — issues are sufficient at this scale and may be revisited if traffic justifies.
```

- [ ] **Step 2: Verify.**

```bash
head -5 CONTRIBUTING.md && wc -l CONTRIBUTING.md
```

Expected: heading + lines visible; line count > 50.

- [ ] **Step 3: Commit.**

```bash
git add CONTRIBUTING.md
git commit -m "$(cat <<'EOF'
docs: add CONTRIBUTING.md with scope, test setup, and PR conventions

Codifies the in-scope/out-of-scope contribution surface (locked
2026-05-06), the local-test setup (pymol25 stdlib-only Python),
PR conventions (Conventional Commits, atomic), and the recycled-
trio attribution rule. Cycle #1 task 6.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7 — `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1)

Off-the-shelf Contributor Covenant 2.1, downloaded from the canonical source.

**Files:**
- Create: `CODE_OF_CONDUCT.md`

- [ ] **Step 1: Download the canonical Contributor Covenant 2.1 Markdown.**

```bash
curl -fsSL -o CODE_OF_CONDUCT.md https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md
```

Expected: file written. If `curl` fails (network, hash mismatch, 404), fall back to fetching from the GitHub mirror:

```bash
curl -fsSL -o CODE_OF_CONDUCT.md \
  https://raw.githubusercontent.com/EthicalSource/contributor_covenant/release/content/version/2/1/code_of_conduct/code_of_conduct.md
```

- [ ] **Step 2: Verify the downloaded text is the actual covenant.**

```bash
head -3 CODE_OF_CONDUCT.md
grep -c "Contributor Covenant" CODE_OF_CONDUCT.md
wc -l CODE_OF_CONDUCT.md
```

Expected: title line beginning with `# Contributor Covenant Code of Conduct`; `grep -c` count >= 3; line count between 100 and 200.

- [ ] **Step 3: Fill the contact placeholder.**

Contributor Covenant 2.1 contains the line `Community leaders are responsible for ... [INSERT CONTACT METHOD]` (the exact placeholder string varies; recent versions use `[INSERT CONTACT METHOD]` or similar). Replace with the SWS contact:

```bash
sed -i.bak 's/\[INSERT CONTACT METHOD\]/the maintainer via a GitHub issue at https:\/\/github.com\/piripocchio8\/scientific-writing-superpowers\/issues/g' CODE_OF_CONDUCT.md
rm CODE_OF_CONDUCT.md.bak
```

If the placeholder text differs (Covenant occasionally renames it), open `CODE_OF_CONDUCT.md` and replace the contact-method placeholder manually with the same text.

- [ ] **Step 4: Verify the placeholder is resolved.**

```bash
grep -i "INSERT" CODE_OF_CONDUCT.md
```

Expected: empty output (no placeholder left).

- [ ] **Step 5: Commit.**

```bash
git add CODE_OF_CONDUCT.md
git commit -m "$(cat <<'EOF'
docs: add CODE_OF_CONDUCT.md (Contributor Covenant 2.1)

Off-the-shelf Contributor Covenant 2.1 with the contact-method
placeholder resolved to the GitHub issues URL. Cycle #1 task 7.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8 — GitHub issue templates (3 files)

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/ISSUE_TEMPLATE/journal_style_overlay.md`

- [ ] **Step 1: Create the directory.**

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

- [ ] **Step 2: Write `bug_report.md`.**

```markdown
---
name: Bug report
about: Report unexpected behavior in SWS
title: "[bug] "
labels: bug
---

**SWS version**

(check `.claude-plugin/plugin.json` `version` field, or your installed plugin manifest)

**Affected component**

- [ ] agent — name:
- [ ] skill — name:
- [ ] hook — name:
- [ ] slash command — name:
- [ ] utility — name:
- [ ] other (describe)

**What you tried to do**

**What happened**

**What you expected**

**Reproduction steps**

1.
2.
3.

**Environment**

- OS:
- Claude Code version:
- Python env (pymol25 / other; only relevant for the filesystem-index utility or future Python utilities):
- Active SWS profile (from `.sws-project.local.md`):
- Active SWS format (`docx` or `latex`):

**docx attachment policy**

Do **not** attach a `.docx` that contains unpublished research, redacted patient data, or anything you wouldn't post publicly. If the bug requires a docx to reproduce, create a minimal synthetic one (a stub paragraph + a fake figure caption is usually enough).

**Logs / output**

```
(paste any relevant Claude Code output, agent transcripts with sensitive content redacted, or hook stderr)
```
```

- [ ] **Step 3: Write `feature_request.md`.**

```markdown
---
name: Feature request
about: Suggest a new SWS capability
title: "[feature] "
labels: enhancement
---

**Problem**

What's the writing- or research-workflow problem you're trying to solve? Describe the situation, not the solution.

**Proposed solution**

What you'd like SWS to do.

**Profile / agent / skill / hook affected**

Which v0.1 component does this touch, or is it a new component?

**Alternatives considered**

What else could solve this? Why is your proposed solution better?

**Why this fits SWS scope**

SWS is a docx-first plugin for chemistry and biology labs (see `CONTRIBUTING.md`'s "In scope"). Confirm the proposal is consistent with that positioning.

**Willing to PR?**

- [ ] Yes
- [ ] No (request only)
- [ ] Maybe — depending on direction
```

- [ ] **Step 4: Write `journal_style_overlay.md`.**

````markdown
---
name: Journal-style overlay
about: Submit an overlay for a journal SWS doesn't yet support
title: "[overlay] <Journal Name>"
labels: journal-style-overlay
---

**Journal**

**Publisher**

**Author guidelines URL**

**Date guidelines were checked**

(YYYY-MM-DD)

**Overlay frontmatter**

Fill in the values from the journal's current author guidelines:

```yaml
---
journal_slug:                       # lowercase, no spaces, e.g. chembiochem
inherits:                           # one of: full-article, communication, perspective, review-paper, mini-review, editorial, methodological-paper, commentary-reply, funding-proposal
word_total:                         # integer or null
ref_cap:                            # integer or null
abstract_style:                     # structured | unstructured | graphical | null
figures_max:                        # integer or null
tables_max:                         # integer or null
sections:                           # list of expected section names, in order
disclosure_required:                # true | false
latex_class: null                   # path to journal .cls if applicable, else null
---
```

**Overlay body**

Tone, citation style, special conventions (e.g., compound-numbering rules, preferred figure aspect ratios, supporting-information policy):

**Verification**

- [ ] Values above were pulled directly from the journal's current author guidelines (URL provided).
- [ ] The journal does not require any additional fields not represented in the schema. (If it does, list them below — they're useful signal for v0.2+ schema extensions.)

**Additional fields the schema might be missing**

(optional)
````

- [ ] **Step 5: Verify the templates.**

```bash
ls -la .github/ISSUE_TEMPLATE/
head -7 .github/ISSUE_TEMPLATE/bug_report.md
head -7 .github/ISSUE_TEMPLATE/feature_request.md
head -7 .github/ISSUE_TEMPLATE/journal_style_overlay.md
```

Expected: 3 files; each starts with `---` frontmatter containing `name:`, `about:`, `title:`, `labels:`.

- [ ] **Step 6: Commit.**

```bash
git add .github/ISSUE_TEMPLATE/
git commit -m "$(cat <<'EOF'
docs: add GitHub issue templates (bug, feature, journal-style overlay)

Three templates per the locked 2026-05-06 community-surface decision:
bug_report (with docx attachment policy), feature_request (with
scope-fit check), journal_style_overlay (the high-leverage template
that lets users at unsupported journals contribute overlays directly).
No PR template — out of scope for v0.1. Cycle #1 task 8.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9 — Merge to `main` and push

Cycle #1 wraps with the feature branch merging into `main` and pushing. Banner stays `🚧 v0.1 in design` — no README change in cycle #1.

- [ ] **Step 1: Confirm the cycle-#1 commit log on the feature branch.**

```bash
git log --oneline cycle/01-foundation ^main
```

Expected: 8 commits, in this order from oldest to newest:
1. `feat: plugin manifest and directory scaffold`
2. `docs: add folder-topology reference for SWS manuscript projects`
3. `docs: add marker-schema reference for .sws-project.local.md`
4. `feat: recycled superpowers trio (brainstormer, planner, code-reviewer)`
5. `feat: filesystem-index utility for project state snapshots`
6. `docs: add CONTRIBUTING.md with scope, test setup, and PR conventions`
7. `docs: add CODE_OF_CONDUCT.md (Contributor Covenant 2.1)`
8. `docs: add GitHub issue templates (bug, feature, journal-style overlay)`

If counts or ordering differ, stop and inspect — re-running steps from earlier tasks is safer than fast-forwarding past confused state.

- [ ] **Step 2: Run the test suite one more time** to confirm nothing regressed.

```bash
/Users/piripocchio8/opt/miniconda3/envs/pymol25/bin/python -m unittest tests.test_fs_index -v
```

Expected: 4 tests pass.

- [ ] **Step 3: Confirm `claude_memory/` is still gitignored** (sanity check before push).

```bash
git status -s | grep -E "(claude_memory|project_)" || echo "clean"
```

Expected: `clean`. If anything from `claude_memory/` is staged, **stop** — the gitignore rule is the only thing preventing brainstorm scratch from going public.

- [ ] **Step 4: Decide merge mechanism.**

Two acceptable paths:

**Path A — Direct merge to main (solo work).**

```bash
git checkout main
git merge --no-ff cycle/01-foundation -m "$(cat <<'EOF'
Merge cycle #1: foundation

Plugin manifest, directory scaffold, recycled superpowers trio,
filesystem-index utility, folder-topology + marker-schema references,
CONTRIBUTING, CODE_OF_CONDUCT (Contributor Covenant 2.1), 3 issue
templates. Banner stays 🚧 v0.1 in design.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

**Path B — PR via gh.**

```bash
git push -u origin cycle/01-foundation
gh pr create --title "Cycle #1: foundation (manifest, recycled trio, fs-index, community surface)" --body "$(cat <<'EOF'
## Summary

- `.claude-plugin/plugin.json` and the canonical directory scaffold.
- `references/folder-topology.md` and `references/marker-schema.md`.
- Recycled superpowers trio: `brainstormer`, `planner`, `code-reviewer` (`model: inherit`) — copy-with-MIT-attribution mechanism.
- `scripts/sws_fs_index.py` filesystem-index utility (pure stdlib, pymol25-compatible) with 4 unit tests.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), 3 issue templates.

## Test plan

- [ ] `python -m unittest tests.test_fs_index -v` passes (4 tests).
- [ ] `python -c "import json; json.load(open('.claude-plugin/plugin.json'))"` succeeds.
- [ ] `git check-ignore claude_memory/fs_index.json` confirms ignore.
- [ ] Plugin loads in Claude Code without error (manual smoke test).
- [ ] Recycled `sws:brainstormer` and `sws:planner` invokable from a test session.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Pick A for solo work, B if you want a reviewable record. Both are acceptable.

- [ ] **Step 5: Push `main`.**

```bash
git push origin main
```

Expected: push succeeds. If credentials prompt, the user runs `gh auth login` in their own terminal first (model cannot authenticate).

- [ ] **Step 6: Verify the public repo reflects the cycle-#1 state.**

```bash
gh repo view piripocchio8/scientific-writing-superpowers --web 2>/dev/null || echo "open https://github.com/piripocchio8/scientific-writing-superpowers in a browser"
```

Visually confirm:
- README banner still reads `🚧 v0.1 in design`.
- New top-level files visible: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `.claude-plugin/`, `agents/`, `skills/`, `references/`, `scripts/`, `tests/`, `.github/`.
- `agents/code-reviewer.md`, `skills/brainstormer/SKILL.md`, `skills/planner/SKILL.md` all present.
- `claude_memory/` and `project_*.md` files **not** present.

- [ ] **Step 7: Optional cleanup.**

If Path A was chosen and the feature branch is no longer needed:

```bash
git branch -d cycle/01-foundation
```

Skip this if you'd rather keep the branch as a record. (User confirmation recommended before deleting branches per general session rules.)

---

## Self-Review Checklist

Run this checklist before declaring cycle #1 complete.

**Spec coverage** (each item in `claude_memory/project_brainstorm_progress.md` cycle-#1 scope list maps to a task here):

| Spec item | Task |
|---|---|
| Plugin scaffold (`plugin.json` + directories) | Task 1 |
| Folder-topology reference doc | Task 2 |
| Marker schema reference doc | Task 3 |
| Recycled-trio re-export | Task 4 |
| Filesystem-index utility (Python pymol25) | Task 5 |
| `CONTRIBUTING.md` | Task 6 |
| `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1) | Task 7 |
| 3 issue templates | Task 8 |
| Final cycle-#1 commit + push | Task 9 |
| Banner stays `🚧 v0.1 in design` | Confirmed in Task 9 step 6 |

All 10 line items have a matching task. ✓

**Placeholder scan:** No `TBD`, `TODO`, `implement later`, or "fill in details" remains in this plan. ✓

**Type / signature consistency:**
- `build_index(root, excludes=DEFAULT_EXCLUDES)` is referenced exactly the same way in test (`sws_fs_index.build_index(self.root)`) and impl. ✓
- `main(argv=None) -> int` matches the test's `sws_fs_index.main(["--root", ..., "--out", ...])` invocation. ✓
- `manifest["files"][i]` field set (`path`, `size_bytes`, `mtime`, `ext`) is consistent between test assertions and implementation dict. ✓

**Decisions honored** (cross-checked against `claude_memory/project_decisions_so_far.md`):
- DOCX-first kept as primary; LaTeX deferred to format-aware-agent cycles. ✓
- 24 v0.1 agents not opened; only the recycled `code-reviewer` lands. ✓
- MIT license; attribution comments on recycled files. ✓
- No telemetry. ✓
- No PR template, no Discussions, no `FUNDING.yml` in v0.1. ✓
- `claude_memory/` stays gitignored throughout. ✓
- Marker-scoped hooks land in cycle #3, not cycle #1. ✓

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-08-cycle-01-foundation.md`. Two execution options:

**1. Subagent-Driven (recommended).** Dispatch a fresh subagent per task, review between tasks, fast iteration. Required sub-skill: `superpowers:subagent-driven-development`. Best for cycle #1 because the 9 tasks are largely independent (Task 1 unblocks all subsequent tasks; Tasks 2–8 are mutually independent; Task 9 depends on all). Sonnet medium-effort is sufficient per task; the recycled-trio task (Task 4) benefits from sonnet-high for the YAML frontmatter edits.

**2. Inline Execution.** Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review. Best if you want to keep the conversation in one place and review each commit as it lands.

Which approach?
