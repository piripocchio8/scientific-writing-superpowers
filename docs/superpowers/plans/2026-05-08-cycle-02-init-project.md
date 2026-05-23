# SWS Cycle #2 — /sws:init-project Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `/sws:init-project` end-to-end (slash command + skill + 3 deterministic Python utilities + 3 templates + 2 reference docs + tests). After cycle #2 lands, a user can bootstrap a manuscript directory — empty or existing — into the SWS layout with smart-merge, plan-then-apply atomicity, and rollback on failure.

**Architecture:** Skill (`skills/init-project/SKILL.md`) is the model-driven orchestrator (NL parsing, interactive prompts, per-conflict negotiation). Three pure-stdlib Python utilities (`sws_check_env.py`, `sws_render_template.py`, `sws_init_project.py`) handle all deterministic work (env preflight, template rendering, conflict scan, plan build, atomic apply with rollback). The skill calls them via Bash. Lean YAML deliverable rule applies: structured data lives in YAML frontmatter (templates, reference docs, marker, per-paper CLAUDE.md), not duplicated in prose.

**Tech Stack:** Python ≥ 3.9 stdlib (no external deps), `string.Template`, `pathlib`, `json`, `argparse`, `unittest`, `unittest.mock`. Bash for skill orchestration. Markdown + YAML frontmatter for templates and references.

**Working directory:** `$REPO_ROOT/`.

**Branch:** `cycle/02-init-project` (matches cycle #1's in-place feature-branch pattern; no worktree).

**Source-of-truth references** (do not duplicate their content in plan steps; cross-ref):
- Spec: `docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md` (frontmatter is the design dictionary)
- Architecture sketch: `docs/superpowers/specs/2026-05-08-architecture-sketch-design.md`
- Marker schema: `references/marker-schema.md`
- Folder topology: `references/folder-topology.md`
- Typography canon rationale: `claude_memory/feedback_docx_typography.md`
- Lean-deliverable rule: `claude_memory/feedback_lean_deliverables.md`
- Python env reference: `claude_memory/feedback_python_env.md`

**Reference Python interpreter for local testing:** `$DEV_PY` (per CLAUDE.md). Skills invoke generic `python3` at runtime; tests run with the dev-env path locally.

---

## Pre-flight: Branch creation

- [ ] **Step 1: Verify clean working tree.**

```bash
git -C $REPO_ROOT status -s
```
Expected: empty (no uncommitted changes). Two commits already on local main ahead of origin (`8e4378e` rename + `336d400` cycle-#2 spec) are fine to carry into the branch.

- [ ] **Step 2: Create and switch to feature branch.**

```bash
git checkout -b cycle/02-init-project
```
Expected: `Switched to a new branch 'cycle/02-init-project'`.

- [ ] **Step 3: Confirm branch.**

```bash
git branch --show-current
```
Expected: `cycle/02-init-project`.

---

## Task 1 — Python env preflight (TDD)

**Files:**
- Create: `scripts/sws_check_env.py`
- Test: `tests/test_python_env.py`

Single function `check_env() -> (ok: bool, msg: str)` plus a `main()` CLI returning rc 0/1. Skills invoke this before any Python utility to fail fast with a clear message.

- [ ] **Step 1: Write failing test at `tests/test_python_env.py`.**

```python
"""Tests for sws_check_env.py — pure stdlib + unittest."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sws_check_env  # noqa: E402


class TestCheckEnv(unittest.TestCase):
    def test_passes_on_current_python(self):
        ok, msg = sws_check_env.check_env()
        self.assertTrue(ok)
        self.assertEqual(msg, "ok")

    def test_fails_on_old_python(self):
        fake_version = (3, 8, 0, "final", 0)
        with mock.patch.object(sys, "version_info", fake_version):
            ok, msg = sws_check_env.check_env()
        self.assertFalse(ok)
        self.assertIn("3.9", msg)
        self.assertIn("3.8", msg)

    def test_main_returns_0_on_pass(self):
        rc = sws_check_env.main()
        self.assertEqual(rc, 0)

    def test_main_returns_1_on_fail(self):
        fake_version = (3, 8, 0, "final", 0)
        with mock.patch.object(sys, "version_info", fake_version):
            rc = sws_check_env.main()
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to confirm import-failure.**

```bash
$DEV_PY -m unittest tests.test_python_env -v
```
Expected: `ModuleNotFoundError: No module named 'sws_check_env'`.

- [ ] **Step 3: Write `scripts/sws_check_env.py`.**

```python
#!/usr/bin/env python3
"""SWS environment preflight.

Run before any SWS Python utility. Returns clear error message + non-zero
exit if Python is missing or too old. Skills invoke this first to fail
fast with a useful diagnostic instead of letting the model thrash on
phantom errors.
"""
from __future__ import annotations
import sys

MIN_PYTHON = (3, 9)


def check_env() -> tuple[bool, str]:
    """Returns (ok, message). ok=True means env is fine."""
    if sys.version_info < MIN_PYTHON:
        return (
            False,
            f"SWS requires Python >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}. "
            f"Detected {sys.version_info.major}.{sys.version_info.minor}. "
            f"Activate or install a compatible env."
        )
    return (True, "ok")


def main() -> int:
    ok, msg = check_env()
    if not ok:
        print(msg, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to confirm pass.**

```bash
$DEV_PY -m unittest tests.test_python_env -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Smoke-test the CLI.**

```bash
$DEV_PY scripts/sws_check_env.py && echo OK
```
Expected: `OK`.

- [ ] **Step 6: Commit.**

```bash
git add scripts/sws_check_env.py tests/test_python_env.py
git commit -m "feat: add Python env preflight (sws_check_env.py)

Single check_env() function returns (ok, msg) tuple plus a CLI main()
returning rc 0/1. Used by every SWS skill before invoking Python
utilities to fail fast with a clear message instead of letting the
model thrash on phantom errors. Pure stdlib. Cycle #2 task 1.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 2 — `references/python-env.md`

**Files:**
- Create: `references/python-env.md`

Lean YAML-as-dictionary form per the lean-deliverable rule. Cross-refs `feedback_python_env.md` for rationale.

- [ ] **Step 1: Write `references/python-env.md`.**

````markdown
---
sws_artifact: python-env
artifact_version: 0.1
locked: 2026-05-08
sources:
  - claude_memory/feedback_python_env.md (user's preferred local env: dev mamba env)
  - docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md (python_env_policy)

policy:
  min_python: "3.9"
  reference_local_env_for_dev: dev mamba env at $DEV_PY
  shipped_runtime_invocation: python3 (whatever's on PATH that meets min_python)
  deps_state_v0_1_through_cycle_4: stdlib-only
  first_real_dep_cycle: 5  # likely python-docx for OOXML manipulation
  setup_infrastructure_cycle: 5  # requirements.txt at repo root + scripts/sws_setup_env.sh

preflight:
  utility: scripts/sws_check_env.py
  invoked_by: every SWS skill before calling a Python utility
  failure_action: print clear error to stderr, exit 1, do not invoke the broken tool
  fallback_inline_pattern: |
    python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' \
      || { echo "SWS requires Python >= 3.9. Activate or install a compatible env, then re-run."; exit 1; }

stdlib_modules_used_through_cycle_4:
  cycle_1: [pathlib, json, datetime, fnmatch, sys, argparse]   # sws_fs_index.py
  cycle_2: [pathlib, json, sys, argparse, string.Template, unicodedata, shutil, tempfile]   # sws_render_template.py + sws_init_project.py + sws_check_env.py

testing:
  framework: unittest (Python stdlib)
  test_runner: "python -m unittest <module> -v"
  reference_env_for_local_test_runs: the dev env (per claude_memory/feedback_python_env.md)
  mocking: unittest.mock
---

# Python env policy

Frontmatter is the source of truth. Body is orientation.

SWS commits to stdlib-only through cycle #4 to keep first-time-user friction at zero — no `pip install`, no virtualenv, no compatibility surface to debug. When cycle #5 introduces the first OOXML manipulation (drafter), it ships `requirements.txt` and `scripts/sws_setup_env.sh` together; the upgrade is documented in that cycle's plan.

Skills invoke Python utilities through `scripts/sws_check_env.py` first. The check is a one-line preflight: if Python is missing or too old, print a clear error and exit non-zero. Skills then know to abort without burning model tokens debugging a phantom error.
````

- [ ] **Step 2: Verify the YAML parses.**

```bash
$DEV_PY -c "
import re, yaml
fm = yaml.safe_load(re.search(r'^---\n(.*?)\n---', open('references/python-env.md').read(), re.S|re.M).group(1))
assert fm['sws_artifact'] == 'python-env'
assert fm['policy']['min_python'] == '3.9'
print('OK', fm['sws_artifact'], 'min_python=' + fm['policy']['min_python'])
"
```
Expected: `OK python-env min_python=3.9`.

- [ ] **Step 3: Commit.**

```bash
git add references/python-env.md
git commit -m "docs: add Python env reference (lean YAML-as-dictionary form)

Codifies the SWS Python env policy: min 3.9, stdlib-only through
cycle #4, first real dep + setup infrastructure in cycle #5. Skill
preflight pattern documented with the inline fallback bash snippet.

Cycle #2 task 2.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 3 — Template render utility (TDD)

**Files:**
- Create: `scripts/sws_render_template.py`
- Test: `tests/test_render_template.py`

Single `render(template_path, vars_dict, out_path)` function. Strict mode: missing variable raises `KeyError`. CLI for skill invocation.

- [ ] **Step 1: Write failing test at `tests/test_render_template.py`.**

```python
"""Tests for sws_render_template.py — pure stdlib + unittest."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sws_render_template  # noqa: E402


class TestRenderTemplate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_template(self, name, content):
        p = self.root / name
        p.write_text(content)
        return p

    def test_happy_path(self):
        tpl = self._write_template("t.template", "hello ${name}")
        out = self.root / "out.md"
        sws_render_template.render(tpl, {"name": "world"}, out)
        self.assertEqual(out.read_text(), "hello world")

    def test_missing_variable_raises_keyerror(self):
        tpl = self._write_template("t.template", "hello ${name}")
        out = self.root / "out.md"
        with self.assertRaises(KeyError):
            sws_render_template.render(tpl, {}, out)

    def test_unicode_in_variable(self):
        tpl = self._write_template("t.template", "author: ${first_author}")
        out = self.root / "out.md"
        sws_render_template.render(tpl, {"first_author": "Müller"}, out)
        self.assertEqual(out.read_text(), "author: Müller")

    def test_creates_parent_dirs(self):
        tpl = self._write_template("t.template", "${x}")
        out = self.root / "deep" / "nested" / "out.md"
        sws_render_template.render(tpl, {"x": "y"}, out)
        self.assertTrue(out.exists())
        self.assertEqual(out.read_text(), "y")

    def test_cli_main_happy_path(self):
        tpl = self._write_template("t.template", "${greeting}")
        vars_path = self.root / "vars.json"
        vars_path.write_text(json.dumps({"greeting": "hi"}))
        out = self.root / "out.md"
        rc = sws_render_template.main([
            "--template", str(tpl),
            "--vars-file", str(vars_path),
            "--out", str(out),
        ])
        self.assertEqual(rc, 0)
        self.assertEqual(out.read_text(), "hi")

    def test_cli_returns_2_on_missing_variable(self):
        tpl = self._write_template("t.template", "${missing}")
        vars_path = self.root / "vars.json"
        vars_path.write_text(json.dumps({"other": "value"}))
        out = self.root / "out.md"
        rc = sws_render_template.main([
            "--template", str(tpl),
            "--vars-file", str(vars_path),
            "--out", str(out),
        ])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to confirm import-failure.**

```bash
$DEV_PY -m unittest tests.test_render_template -v
```
Expected: `ModuleNotFoundError: No module named 'sws_render_template'`.

- [ ] **Step 3: Write `scripts/sws_render_template.py`.**

```python
#!/usr/bin/env python3
"""SWS template renderer — string.Template-based, stdlib-only.

Renders a .template file with ${var} substitutions into an output path.
Strict mode: missing variables raise KeyError. CLI returns rc 2 on
missing-variable, 0 on success.

Usage:
    python sws_render_template.py --template <path> --vars-file <vars.json> --out <path>
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from string import Template


def render(template_path, vars_dict, out_path) -> None:
    """Render template_path with vars_dict to out_path. Strict on missing vars."""
    template_text = Path(template_path).read_text()
    template = Template(template_text)
    rendered = template.substitute(vars_dict)  # raises KeyError on missing var
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True)
    parser.add_argument("--vars-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    vars_dict = json.loads(Path(args.vars_file).read_text())
    try:
        render(args.template, vars_dict, args.out)
    except KeyError as e:
        print(f"Missing template variable: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to confirm pass.**

```bash
$DEV_PY -m unittest tests.test_render_template -v
```
Expected: 6 tests pass.

- [ ] **Step 5: Commit.**

```bash
git add scripts/sws_render_template.py tests/test_render_template.py
git commit -m "feat: add template renderer (sws_render_template.py)

Pure-stdlib string.Template-based renderer with strict-mode substitution.
Missing variables raise KeyError; CLI returns rc 2 on that case so
skill orchestration can detect malformed inputs cleanly. 6 unit tests:
happy path, missing-var, Unicode, parent-dir creation, CLI happy,
CLI missing-var. Cycle #2 task 3.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 4 — 3 template files

**Files:**
- Create: `templates/sws-project-marker.template`
- Create: `templates/manuscript-claude-md.template`
- Create: `templates/manuscript-memory-md.template`
- Delete: `templates/.gitkeep`

Templates use `${var}` syntax matching `sws_render_template.py`. Variables that may be null (`target_journal`, `target_call`) are passed as the literal string `"null"` or the slug; the orchestrator pre-processes nullable values before substitution. Booleans are passed as the literal strings `"true"` / `"false"`.

- [ ] **Step 1: Write `templates/sws-project-marker.template`.**

```markdown
---
sws_version: 0.1
article_type: ${article_type}
language: ${language}
format: ${format}
target_journal: ${target_journal}
target_call: ${target_call}
notebooklm:
  enabled: ${notebooklm_enabled}
created: ${created_iso}
---

# ${short_handle} — SWS marker

Free-form notes preserved across regenerations.
```

- [ ] **Step 2: Write `templates/manuscript-claude-md.template`.**

```markdown
---
sws_project:
  article_type: ${article_type}
  language: ${language}
  format: ${format}
  target_journal: ${target_journal}
  target_call: ${target_call}
  first_author: ${first_author}
  year: ${year}
  co_authors_present: ${co_authors_present}
  short_handle: ${short_handle}
  notebooklm_enabled: ${notebooklm_enabled}
  created: ${created_iso}
---

# ${short_handle}

SWS-bootstrapped manuscript project.

## Where to find context

- `.sws-project.local.md` — active SWS settings (article_type, language, format, target journal/call, NLM opt-in).
- `claude_memory/MEMORY.md` — session-state index; update as you work.
- `Manuscript/_journal-style/<slug>.md` — journal-specific overlay (run `/sws:resolve-journal-style` if missing).
- SWS plugin canonical references: `references/folder-topology.md`, `references/marker-schema.md`, `references/docx-style.md`, `references/python-env.md`.

## Per-paper notes

(add anything specific to this paper — collaborators, lab-specific conventions, in-flight reviewer comments, etc.)
```

- [ ] **Step 3: Write `templates/manuscript-memory-md.template`.**

```markdown
- [Project marker](../.sws-project.local.md) — active SWS settings.
- [Per-paper CLAUDE.md](../CLAUDE.md) — paper context.

(append entries as you accrue working state — passport summaries, decisions, in-flight section drafts, etc.)
```

- [ ] **Step 4: Smoke-render each template** (catches `${var}` typos before runtime):

```bash
mkdir -p /tmp/sws_tpl_smoke
cat > /tmp/sws_tpl_smoke/vars.json <<'EOF'
{
  "article_type": "communication",
  "language": "en",
  "format": "docx",
  "target_journal": "chembiochem",
  "target_call": "null",
  "first_author": "smith",
  "year": "2026",
  "co_authors_present": "true",
  "short_handle": "smith_et_al_2026",
  "notebooklm_enabled": "false",
  "created_iso": "2026-05-08T00:00:00Z"
}
EOF

for tpl in templates/sws-project-marker.template templates/manuscript-claude-md.template templates/manuscript-memory-md.template; do
  out="/tmp/sws_tpl_smoke/$(basename $tpl .template).rendered.md"
  $DEV_PY scripts/sws_render_template.py \
    --template "$tpl" --vars-file /tmp/sws_tpl_smoke/vars.json --out "$out" \
    && echo "rendered $tpl"
done
ls -la /tmp/sws_tpl_smoke/
```
Expected: 3 `.rendered.md` files; no rc 2 (missing-var) errors.

- [ ] **Step 5: Inspect one rendered file for sanity.**

```bash
cat /tmp/sws_tpl_smoke/sws-project-marker.rendered.md
```
Expected: a valid YAML frontmatter block with `article_type: communication`, `target_journal: chembiochem`, `target_call: null`, `notebooklm.enabled: false`, etc.

- [ ] **Step 6: Clean up smoke artifacts.**

```bash
rm -rf /tmp/sws_tpl_smoke
```

- [ ] **Step 7: Commit.**

```bash
rm templates/.gitkeep
git add templates/ -A
git commit -m "feat: add 3 init-project template files

- sws-project-marker.template: marker schema fields only (8 keys)
- manuscript-claude-md.template: 12-key project metadata frontmatter
  + ~15-line orientation body cross-referencing plugin canonical refs
- manuscript-memory-md.template: empty index with 2 bootstrap pointers

Variables use \${var} syntax matching sws_render_template.py.
Nullable fields (target_journal, target_call) and booleans
(co_authors_present, notebooklm_enabled) passed as literal strings;
orchestrator pre-processes before substitution.

Cycle #2 task 4.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 5 — `references/docx-style.md`

**Files:**
- Create: `references/docx-style.md`

Typography canon — consumed by docx-touching agents from cycle #5 onward; cycle #2 ships it as the canonical lookup.

- [ ] **Step 1: Write `references/docx-style.md`.**

````markdown
---
sws_artifact: docx-style
artifact_version: 0.1
locked: 2026-05-08
sources:
  - claude_memory/feedback_docx_typography.md (canonical rationale + slot semantics)
  - docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md (custom_typography section)

styles:
  SWS-Body:        { font: Arial, size: 12, bold: false, italic: false }
  SWS-H1:          { font: Arial, size: 12, bold: true,  italic: false }   # top-level sections
  SWS-H2:          { font: Arial, size: 12, bold: true,  italic: true  }   # sub-sections within Results
  SWS-Caption:     { font: Arial, size: 10, bold: false, italic: false }   # figure + table captions
  SWS-References:  { font: Arial, size: 10, bold: false, italic: false }   # reference list

forbidden_word_styles: [Heading 1, Heading 2, Heading 3, Title, Subtitle]

slot_assignments_locked:
  top_level_sections: SWS-H1   # Intro, Results, Discussion, Experimental, Acknowledgments, References
  results_subsections: SWS-H2  # e.g. Synthesis, Spectroscopic characterization, Catalytic activity
  body_text: SWS-Body
  figure_captions: SWS-Caption
  table_captions: SWS-Caption
  reference_list_entries: SWS-References

slot_assignments_TBD:
  - Title
  - Author block
  - Abstract
  - Keyword block
  - Footnote
  - Equation numbering
  - Bullet/Numbered list items
  - Table-cell text

scope:
  applies_to: docx (format=docx in marker)
  exempt: latex (journal .cls owns typography; SWS does not override)

consumers:
  cycle_1: none
  cycle_2: this file ships; init-project does NOT apply styles to existing manuscripts (style normalization is style-enforcer's job in cycle #6)
  cycle_5_onward: drafter, style-enforcer, format-checker, table-formatter, equation-handler, figure-caption-writer
---

# SWS docx typography canon

Frontmatter is the source of truth. Rationale: `claude_memory/feedback_docx_typography.md`.

Custom named styles only. Word's built-in `Heading 1` / `Heading 2` / `Title` / `Subtitle` styles are visually ugly and trigger TOC-field generation the user doesn't want.

`slot_assignments_TBD` resolved as the drafter (cycle #5) needs each slot. Add new slots by extending `styles` and `slot_assignments_locked`; never embed style fields in agent prompts directly.
````

- [ ] **Step 2: Verify YAML parses.**

```bash
$DEV_PY -c "
import re, yaml
fm = yaml.safe_load(re.search(r'^---\n(.*?)\n---', open('references/docx-style.md').read(), re.S|re.M).group(1))
assert fm['sws_artifact'] == 'docx-style'
assert 'SWS-Body' in fm['styles']
assert 'SWS-H1' in fm['styles']
assert 'SWS-H2' in fm['styles']
assert 'SWS-Caption' in fm['styles']
assert 'SWS-References' in fm['styles']
assert 'Heading 1' in fm['forbidden_word_styles']
print('OK styles:', list(fm['styles'].keys()))
"
```
Expected: `OK styles: ['SWS-Body', 'SWS-H1', 'SWS-H2', 'SWS-Caption', 'SWS-References']`.

- [ ] **Step 3: Commit.**

```bash
git add references/docx-style.md
git commit -m "docs: add docx typography canon reference

5 SWS-named custom styles (SWS-Body, SWS-H1, SWS-H2, SWS-Caption,
SWS-References) with locked slot assignments (top-level sections,
results subsections, body, captions, references). Word's built-in
heading/title styles forbidden. 8 TBD slots flagged for cycle #5
drafter. LaTeX projects exempt (journal .cls owns typography).

Rationale in claude_memory/feedback_docx_typography.md.
Cycle #2 task 5.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 6 — Init utility: `slugify` (TDD)

**Files:**
- Create: `scripts/sws_init_project.py` (skeleton + first function)
- Create: `tests/test_init_project.py` (skeleton + first tests)

Slugifies `first_author` family name: NFD-decompose → drop non-ASCII → lowercase → strip apostrophes/hyphens.

- [ ] **Step 1: Write failing test at `tests/test_init_project.py`.**

```python
"""Tests for sws_init_project.py — pure stdlib + unittest.

Tests grow incrementally per cycle-#2 task: slugify (Task 6),
validate_inputs (Task 7), scan_conflicts (Task 8), build_plan
(Task 9), apply_plan + rollback (Task 10).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sws_init_project  # noqa: E402


class TestSlugify(unittest.TestCase):
    def test_simple_lowercase(self):
        self.assertEqual(sws_init_project.slugify("Smith"), "smith")

    def test_unicode_umlaut(self):
        self.assertEqual(sws_init_project.slugify("Müller"), "muller")

    def test_apostrophe(self):
        self.assertEqual(sws_init_project.slugify("O'Brien"), "obrien")

    def test_hyphen(self):
        self.assertEqual(sws_init_project.slugify("Smith-Jones"), "smithjones")

    def test_diacritics_combined(self):
        self.assertEqual(sws_init_project.slugify("Søren"), "soren")
        self.assertEqual(sws_init_project.slugify("Şefik"), "sefik")
        self.assertEqual(sws_init_project.slugify("García"), "garcia")

    def test_whitespace_stripped(self):
        self.assertEqual(sws_init_project.slugify("  Smith  "), "smith")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            sws_init_project.slugify("")
        with self.assertRaises(ValueError):
            sws_init_project.slugify("   ")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to confirm import-failure.**

```bash
$DEV_PY -m unittest tests.test_init_project -v
```
Expected: `ModuleNotFoundError: No module named 'sws_init_project'`.

- [ ] **Step 3: Write skeleton + slugify in `scripts/sws_init_project.py`.**

```python
#!/usr/bin/env python3
"""SWS init-project orchestration utility.

Functions exposed (built incrementally across cycle-#2 tasks 6-10):
    slugify(name)                  — normalize first_author family name
    validate_inputs(inputs)        — Q5b conditional rules (target_journal/call)
    scan_conflicts(root)           — 6-class smart-merge detection scan
    build_plan(inputs, resolutions)— assemble ordered op list
    apply_plan(plan)               — atomic apply with rollback

CLI subcommands wrap these for skill invocation:
    python sws_init_project.py scan --root <dir>
    python sws_init_project.py plan --inputs <vars.json> --resolutions <res.json>
    python sws_init_project.py apply --plan <plan.json>
"""
from __future__ import annotations
import unicodedata


def slugify(name: str) -> str:
    """Normalize first_author family name: NFD-decompose → drop non-ASCII →
    lowercase → strip apostrophes/hyphens.

    Examples:
        Smith → smith
        Müller → muller
        O'Brien → obrien
        Smith-Jones → smithjones

    Raises ValueError on empty/whitespace input.
    """
    s = name.strip()
    if not s:
        raise ValueError("first_author cannot be empty")
    decomposed = unicodedata.normalize("NFD", s)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    ascii_only = ascii_only.encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(c for c in ascii_only if c.isalnum())
    return cleaned.lower()
```

- [ ] **Step 4: Run tests to confirm pass.**

```bash
$DEV_PY -m unittest tests.test_init_project -v
```
Expected: 7 tests pass.

- [ ] **Step 5: Commit.**

```bash
git add scripts/sws_init_project.py tests/test_init_project.py
git commit -m "feat: add init-project utility skeleton + slugify

Pure-stdlib slugify(): NFD-decompose, drop non-ASCII, lowercase,
strip apostrophes/hyphens. Used to derive first_author component
of short_handle. 7 tests cover Smith, Müller, O'Brien, Smith-Jones,
Søren/Şefik/García, whitespace, empty-raises.

Cycle #2 task 6 (1/5 init utility tasks).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 7 — Init utility: `validate_inputs` (TDD)

**Files:**
- Modify: `scripts/sws_init_project.py` (add `validate_inputs`)
- Modify: `tests/test_init_project.py` (add `TestValidateInputs`)

Enforces Q5b conditional rules:
- `article_type == funding-proposal` ⇒ `target_call` required, `target_journal` must be null.
- `article_type != funding-proposal` ⇒ `target_journal` required, `target_call` must be null.
- `article_type` must be in the 9-profile set.
- `language` in `{en, it}`. `format` in `{docx, latex}`. `co_authors_present` boolean.

- [ ] **Step 1: Append `TestValidateInputs` class to `tests/test_init_project.py`.**

Append after `TestSlugify`:

```python
class TestValidateInputs(unittest.TestCase):
    def _base_inputs(self, **overrides):
        defaults = {
            "article_type": "communication",
            "language": "en",
            "format": "docx",
            "target_journal": "chembiochem",
            "target_call": None,
            "first_author": "smith",
            "year": 2026,
            "co_authors_present": True,
            "notebooklm_enabled": False,
        }
        defaults.update(overrides)
        return defaults

    def test_communication_with_journal_passes(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs())
        self.assertTrue(ok, msg)

    def test_funding_proposal_requires_call(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal=None,
            target_call="prin-2025",
        ))
        self.assertTrue(ok, msg)

    def test_communication_with_call_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            target_call="prin-2025",
        ))
        self.assertFalse(ok)
        self.assertIn("target_call", msg)

    def test_funding_proposal_with_journal_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal="chembiochem",
            target_call="prin-2025",
        ))
        self.assertFalse(ok)
        self.assertIn("target_journal", msg)

    def test_funding_proposal_missing_call_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal=None,
            target_call=None,
        ))
        self.assertFalse(ok)
        self.assertIn("target_call", msg)

    def test_non_funding_missing_journal_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            target_journal=None,
        ))
        self.assertFalse(ok)
        self.assertIn("target_journal", msg)

    def test_invalid_article_type_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="not-a-real-type",
        ))
        self.assertFalse(ok)
        self.assertIn("article_type", msg)

    def test_invalid_language_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            language="fr",
        ))
        self.assertFalse(ok)
        self.assertIn("language", msg)

    def test_invalid_format_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            format="rtf",
        ))
        self.assertFalse(ok)
        self.assertIn("format", msg)

    def test_co_authors_present_must_be_bool(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            co_authors_present="yes",
        ))
        self.assertFalse(ok)
        self.assertIn("co_authors_present", msg)
```

- [ ] **Step 2: Run tests to confirm 10 new failures (AttributeError on `validate_inputs`).**

```bash
$DEV_PY -m unittest tests.test_init_project -v 2>&1 | tail -20
```
Expected: 10 errors with `AttributeError: module 'sws_init_project' has no attribute 'validate_inputs'`.

- [ ] **Step 3: Add `validate_inputs` to `scripts/sws_init_project.py`.**

Append after `slugify`:

```python
ARTICLE_TYPES = (
    "full-article", "communication", "perspective", "review-paper",
    "mini-review", "editorial", "methodological-paper",
    "commentary-reply", "funding-proposal",
)
LANGUAGES = ("en", "it")
FORMATS = ("docx", "latex")


def validate_inputs(inputs: dict) -> tuple[bool, str]:
    """Enforce Q5b conditional rules + enum validation.

    Returns (True, "ok") if inputs pass; (False, error_msg) otherwise.
    """
    article_type = inputs.get("article_type")
    if article_type not in ARTICLE_TYPES:
        return False, (
            f"article_type must be one of {ARTICLE_TYPES}; got {article_type!r}"
        )

    language = inputs.get("language")
    if language not in LANGUAGES:
        return False, f"language must be one of {LANGUAGES}; got {language!r}"

    fmt = inputs.get("format")
    if fmt not in FORMATS:
        return False, f"format must be one of {FORMATS}; got {fmt!r}"

    co_authors = inputs.get("co_authors_present")
    if not isinstance(co_authors, bool):
        return False, (
            f"co_authors_present must be bool; got {type(co_authors).__name__}"
        )

    target_journal = inputs.get("target_journal")
    target_call = inputs.get("target_call")

    if article_type == "funding-proposal":
        if not target_call:
            return False, (
                "article_type=funding-proposal requires target_call"
            )
        if target_journal:
            return False, (
                "article_type=funding-proposal must have target_journal=null; "
                f"got {target_journal!r}"
            )
    else:
        if not target_journal:
            return False, (
                f"article_type={article_type} requires target_journal"
            )
        if target_call:
            return False, (
                f"article_type={article_type} must have target_call=null; "
                f"got {target_call!r}"
            )

    return True, "ok"
```

- [ ] **Step 4: Run all tests to confirm pass.**

```bash
$DEV_PY -m unittest tests.test_init_project -v
```
Expected: 17 tests pass (7 slugify + 10 validate_inputs).

- [ ] **Step 5: Commit.**

```bash
git add scripts/sws_init_project.py tests/test_init_project.py
git commit -m "feat: add validate_inputs to init-project utility

Enforces Q5b conditional rules: target_journal/target_call exclusivity
based on article_type, plus enum validation for article_type (9 valid),
language (en/it), format (docx/latex), and bool typecheck for
co_authors_present. 10 unit tests cover both happy paths (communication
+ funding-proposal) and 8 failure modes.

Cycle #2 task 7 (2/5 init utility tasks).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 8 — Init utility: `scan_conflicts` (TDD)

**Files:**
- Modify: `scripts/sws_init_project.py` (add `scan_conflicts` + `Conflict` dataclass)
- Modify: `tests/test_init_project.py` (add `TestScanConflicts`)

Walks a project root and returns the 6-class conflict list (per spec `Q1_existing_files_behavior.detection_set`).

- [ ] **Step 1: Append `TestScanConflicts` to `tests/test_init_project.py`.**

```python
import tempfile  # add to top of file if not already imported


class TestScanConflicts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _classes(self, conflicts):
        return sorted(c.cls for c in conflicts)

    def test_empty_dir_no_conflicts(self):
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(conflicts, [])

    def test_root_docx_detected_as_C1(self):
        (self.root / "paper.docx").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].cls, "C1")
        self.assertEqual(conflicts[0].path, "paper.docx")

    def test_loose_figures_detected_as_C2(self):
        (self.root / "Figures").mkdir()
        (self.root / "Figures" / "fig1.png").write_bytes(b"x")
        (self.root / "Figures" / "fig2.pdf").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C2", self._classes(conflicts))

    def test_existing_main_subdir_suppresses_C2(self):
        (self.root / "Figures" / "main").mkdir(parents=True)
        (self.root / "Figures" / "main" / "fig1.png").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertNotIn("C2", self._classes(conflicts))

    def test_claude_material_detected_as_C3(self):
        (self.root / "claude_material").mkdir()
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C3", self._classes(conflicts))

    def test_root_claude_md_detected_as_C4(self):
        (self.root / "CLAUDE.md").write_text("# my notes")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C4", self._classes(conflicts))

    def test_existing_claude_memory_detected_as_C5(self):
        (self.root / "claude_memory").mkdir()
        (self.root / "claude_memory" / "MEMORY.md").write_text("- one")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C5", self._classes(conflicts))

    def test_existing_marker_detected_as_C6(self):
        (self.root / ".sws-project.local.md").write_text("---\nsws_version: 0.1\n---")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C6", self._classes(conflicts))

    def test_multiple_classes_detected_together(self):
        (self.root / "paper.docx").write_bytes(b"x")
        (self.root / "claude_material").mkdir()
        (self.root / "CLAUDE.md").write_text("notes")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(self._classes(conflicts), ["C1", "C3", "C4"])

    def test_conflict_has_suggested_action(self):
        (self.root / "paper.docx").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("Manuscript/", conflicts[0].suggested_action)
```

- [ ] **Step 2: Run tests to confirm new failures.**

```bash
$DEV_PY -m unittest tests.test_init_project -v 2>&1 | tail -10
```
Expected: 10 errors with `AttributeError: module 'sws_init_project' has no attribute 'scan_conflicts'`.

- [ ] **Step 3: Add `scan_conflicts` + `Conflict` dataclass to `scripts/sws_init_project.py`.**

Add to imports near top:
```python
from dataclasses import dataclass, field
from pathlib import Path
```

Append after `validate_inputs`:

```python
@dataclass
class Conflict:
    cls: str           # "C1".."C6"
    path: str          # relative to project root
    suggested_action: str
    options: list = field(default_factory=list)


def scan_conflicts(root) -> list[Conflict]:
    """Walk root for the 6 detection classes; return ordered Conflict list.

    Class definitions per
    docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md
    locked_decisions.Q1_existing_files_behavior.detection_set.
    """
    root = Path(root)
    conflicts: list[Conflict] = []

    # C1: root *.docx
    for docx in sorted(root.glob("*.docx")):
        conflicts.append(Conflict(
            cls="C1",
            path=docx.name,
            suggested_action=f"Move to Manuscript/{docx.name}",
            options=["Y", "n", "skip", "manual"],
        ))

    # C2: loose Figures/* with no main/ or SI/ subfolder
    figures_dir = root / "Figures"
    if figures_dir.is_dir():
        has_main = (figures_dir / "main").is_dir()
        has_si = (figures_dir / "SI").is_dir()
        if not (has_main or has_si):
            loose = []
            for ext in ("png", "jpg", "jpeg", "svg", "pdf"):
                loose.extend(figures_dir.glob(f"*.{ext}"))
            if loose:
                conflicts.append(Conflict(
                    cls="C2",
                    path="Figures/",
                    suggested_action="Move loose figures into Figures/main/",
                    options=["Y", "n", "skip", "manual"],
                ))

    # C3: claude_material/
    if (root / "claude_material").is_dir():
        conflicts.append(Conflict(
            cls="C3",
            path="claude_material/",
            suggested_action="Rename to scratch/",
            options=["Y", "n", "skip", "manual"],
        ))

    # C4: existing root CLAUDE.md
    if (root / "CLAUDE.md").is_file():
        conflicts.append(Conflict(
            cls="C4",
            path="CLAUDE.md",
            suggested_action="[r]eplace / [a]ppend (under '## SWS-managed' section) / [s]kip",
            options=["replace", "append", "skip"],
        ))

    # C5: existing claude_memory/
    if (root / "claude_memory").is_dir():
        conflicts.append(Conflict(
            cls="C5",
            path="claude_memory/",
            suggested_action="[k]eep / [m]ove to _archive/ / [r]eplace",
            options=["keep", "move", "replace"],
        ))

    # C6: existing .sws-project.local.md
    if (root / ".sws-project.local.md").is_file():
        conflicts.append(Conflict(
            cls="C6",
            path=".sws-project.local.md",
            suggested_action=(
                "Re-init flow: load existing values, prompt edits per field, write merged"
            ),
            options=["proceed", "abort"],
        ))

    return conflicts
```

- [ ] **Step 4: Run tests.**

```bash
$DEV_PY -m unittest tests.test_init_project -v
```
Expected: 27 tests pass (7 + 10 + 10).

- [ ] **Step 5: Commit.**

```bash
git add scripts/sws_init_project.py tests/test_init_project.py
git commit -m "feat: add scan_conflicts to init-project utility

Detects the 6 smart-merge classes (C1..C6) per spec
Q1_existing_files_behavior.detection_set: root *.docx (C1), loose
Figures/ contents (C2), claude_material/ (C3), existing CLAUDE.md
(C4), existing claude_memory/ (C5), existing .sws-project.local.md
(C6). Each Conflict carries cls, path, suggested_action, options.

10 tests: empty-dir, each class detected individually, multiple
classes together, suppression of C2 when main/SI subdirs already exist,
suggested_action sanity check.

Cycle #2 task 8 (3/5 init utility tasks).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 9 — Init utility: `build_plan` (TDD)

**Files:**
- Modify: `scripts/sws_init_project.py` (add `build_plan` + `Op` dataclass)
- Modify: `tests/test_init_project.py` (add `TestBuildPlan`)

`build_plan(inputs, resolutions)` takes the validated inputs dict + the per-conflict resolution dict (e.g., `{"C1": "accept", "C3": "skip"}`) and returns an ordered op list.

- [ ] **Step 1: Append `TestBuildPlan` to `tests/test_init_project.py`.**

```python
class TestBuildPlan(unittest.TestCase):
    def _base_inputs(self, **overrides):
        defaults = {
            "article_type": "communication",
            "language": "en",
            "format": "docx",
            "target_journal": "chembiochem",
            "target_call": None,
            "first_author": "smith",
            "year": 2026,
            "co_authors_present": True,
            "notebooklm_enabled": False,
            "short_handle": "smith_et_al_2026",
            "created_iso": "2026-05-08T12:00:00Z",
        }
        defaults.update(overrides)
        return defaults

    def test_fresh_init_no_conflicts_produces_mkdirs_and_renders(self):
        plan = sws_init_project.build_plan(self._base_inputs(), conflicts=[], resolutions={})
        kinds = [op.kind for op in plan]
        self.assertIn("mkdir", kinds)
        self.assertIn("render_template", kinds)
        self.assertIn("write_json", kinds)
        # mkdirs must come before any render that writes inside them
        first_render = next(i for i, op in enumerate(plan) if op.kind == "render_template")
        first_mkdir = next(i for i, op in enumerate(plan) if op.kind == "mkdir")
        self.assertLess(first_mkdir, first_render)

    def test_funding_proposal_creates_call_dir(self):
        inputs = self._base_inputs(
            article_type="funding-proposal",
            target_journal=None,
            target_call="prin-2025",
        )
        plan = sws_init_project.build_plan(inputs, conflicts=[], resolutions={})
        mkdir_dests = [op.dest for op in plan if op.kind == "mkdir"]
        self.assertIn("call", mkdir_dests)

    def test_non_funding_does_not_create_call_dir(self):
        plan = sws_init_project.build_plan(self._base_inputs(), conflicts=[], resolutions={})
        mkdir_dests = [op.dest for op in plan if op.kind == "mkdir"]
        self.assertNotIn("call", mkdir_dests)

    def test_notebooklm_enabled_creates_nlm_uploads(self):
        inputs = self._base_inputs(notebooklm_enabled=True)
        plan = sws_init_project.build_plan(inputs, conflicts=[], resolutions={})
        mkdir_dests = [op.dest for op in plan if op.kind == "mkdir"]
        self.assertIn("refs/nlm_uploads", mkdir_dests)

    def test_C1_accept_produces_mv_op(self):
        from sws_init_project import Conflict
        c = Conflict(cls="C1", path="paper.docx",
                     suggested_action="Move to Manuscript/paper.docx",
                     options=["Y", "n", "skip", "manual"])
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[c],
            resolutions={"C1": "accept"},
        )
        mv_ops = [op for op in plan if op.kind == "mv"]
        self.assertTrue(any(op.source == "paper.docx" and op.dest == "Manuscript/paper.docx"
                            for op in mv_ops))

    def test_C1_skip_produces_no_mv(self):
        from sws_init_project import Conflict
        c = Conflict(cls="C1", path="paper.docx",
                     suggested_action="Move to Manuscript/paper.docx",
                     options=["Y", "n", "skip", "manual"])
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[c],
            resolutions={"C1": "skip"},
        )
        mv_ops = [op for op in plan if op.kind == "mv"]
        self.assertFalse(any(op.source == "paper.docx" for op in mv_ops))

    def test_C3_accept_renames_claude_material_to_scratch(self):
        from sws_init_project import Conflict
        c = Conflict(cls="C3", path="claude_material/",
                     suggested_action="Rename to scratch/",
                     options=["Y", "n", "skip", "manual"])
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[c],
            resolutions={"C3": "accept"},
        )
        mv_ops = [op for op in plan if op.kind == "mv"]
        self.assertTrue(any(op.source == "claude_material" and op.dest == "scratch"
                            for op in mv_ops))

    def test_template_render_ops_use_correct_template_paths(self):
        plan = sws_init_project.build_plan(self._base_inputs(), conflicts=[], resolutions={})
        renders = [op for op in plan if op.kind == "render_template"]
        templates_used = {op.source for op in renders}
        self.assertEqual(templates_used, {
            "templates/sws-project-marker.template",
            "templates/manuscript-claude-md.template",
            "templates/manuscript-memory-md.template",
        })
```

- [ ] **Step 2: Run tests to confirm 8 new failures.**

```bash
$DEV_PY -m unittest tests.test_init_project -v 2>&1 | tail -10
```
Expected: errors on `build_plan` and `Op` not defined.

- [ ] **Step 3: Add `build_plan` + `Op` to `scripts/sws_init_project.py`.**

Append after `scan_conflicts`:

```python
@dataclass
class Op:
    kind: str       # mkdir | mv | render_template | copy | write_json
    source: str = ""
    dest: str = ""
    reason: str = ""
    extra: dict = field(default_factory=dict)


# Base directories created unconditionally (per references/folder-topology.md)
BASE_DIRS = (
    "Manuscript",
    "Manuscript/_journal-style",
    "Manuscript/_archive",
    "Figures",
    "Figures/main",
    "Figures/SI",
    "Figures/_archive",
    "Tables",
    "Tables/_archive",
    "SI",
    "SI/SI_Figures",
    "Zenodo_db",
    "Zenodo_db/data",
    "Zenodo_db/scripts",
    "Zenodo_db/_archive",
    "scratch",
    "refs",
    "claude_memory",
)


def build_plan(inputs: dict, conflicts: list = None, resolutions: dict = None) -> list[Op]:
    """Assemble ordered op list for atomic apply.

    Order:
      1. mkdir base topology + conditional dirs (call/, refs/nlm_uploads/)
      2. mv ops from conflict resolutions (in C1..C6 order)
      3. render_template ops for marker, per-paper CLAUDE.md, MEMORY.md
      4. write_json ops for passport.json (cycle 0)
    """
    conflicts = conflicts or []
    resolutions = resolutions or {}
    ops: list[Op] = []

    # 1. Base directories
    for d in BASE_DIRS:
        ops.append(Op(kind="mkdir", dest=d, reason="base topology"))

    # 1b. Conditional dirs
    if inputs.get("article_type") == "funding-proposal":
        ops.append(Op(kind="mkdir", dest="call", reason="article_type=funding-proposal"))
    if inputs.get("notebooklm_enabled"):
        ops.append(Op(kind="mkdir", dest="refs/nlm_uploads",
                      reason="notebooklm.enabled=true"))

    # 2. Conflict-resolution mv ops
    for c in conflicts:
        resolution = resolutions.get(c.cls, "skip")
        if resolution in ("accept", "Y"):
            if c.cls == "C1":
                # paper.docx → Manuscript/paper.docx
                src = c.path
                dest = f"Manuscript/{c.path}"
                ops.append(Op(kind="mv", source=src, dest=dest, reason=f"smart-merge C1 ({c.path})"))
            elif c.cls == "C2":
                # loose Figures/*.{png,...} → Figures/main/
                ops.append(Op(kind="mv_glob", source="Figures/*.{png,jpg,jpeg,svg,pdf}",
                              dest="Figures/main/", reason="smart-merge C2"))
            elif c.cls == "C3":
                ops.append(Op(kind="mv", source="claude_material", dest="scratch",
                              reason="smart-merge C3 (legacy hDF rename)"))
            # C4/C5/C6 use option-specific resolutions (replace/append/etc.) handled
            # in the apply layer; for now, build_plan emits a placeholder marker.

    # 3. render_template ops
    ops.append(Op(
        kind="render_template",
        source="templates/sws-project-marker.template",
        dest=".sws-project.local.md",
        reason="marker file",
        extra={"vars": _marker_vars(inputs)},
    ))
    ops.append(Op(
        kind="render_template",
        source="templates/manuscript-claude-md.template",
        dest="CLAUDE.md",
        reason="per-paper CLAUDE.md",
        extra={"vars": _claude_md_vars(inputs)},
    ))
    ops.append(Op(
        kind="render_template",
        source="templates/manuscript-memory-md.template",
        dest="claude_memory/MEMORY.md",
        reason="per-paper MEMORY.md",
        extra={"vars": {}},  # template uses no substitutions
    ))

    # 4. passport.json stub
    ops.append(Op(
        kind="write_json",
        dest="claude_memory/passport.json",
        reason="cycle 0 stub",
        extra={"content": {"sws_version": "0.1", "cycle": 0, "history": []}},
    ))

    return ops


def _marker_vars(inputs: dict) -> dict:
    """Render-time vars dict for the marker template."""
    return {
        "article_type": inputs["article_type"],
        "language": inputs["language"],
        "format": inputs["format"],
        "target_journal": inputs.get("target_journal") or "null",
        "target_call": inputs.get("target_call") or "null",
        "notebooklm_enabled": "true" if inputs["notebooklm_enabled"] else "false",
        "created_iso": inputs["created_iso"],
        "short_handle": inputs["short_handle"],
    }


def _claude_md_vars(inputs: dict) -> dict:
    """Render-time vars dict for the per-paper CLAUDE.md template."""
    return {
        **_marker_vars(inputs),
        "first_author": inputs["first_author"],
        "year": str(inputs["year"]),
        "co_authors_present": "true" if inputs["co_authors_present"] else "false",
    }
```

- [ ] **Step 4: Run tests.**

```bash
$DEV_PY -m unittest tests.test_init_project -v
```
Expected: 35 tests pass (7 + 10 + 10 + 8).

- [ ] **Step 5: Commit.**

```bash
git add scripts/sws_init_project.py tests/test_init_project.py
git commit -m "feat: add build_plan to init-project utility

Assembles ordered op list (mkdir base topology, conditional dirs
for funding-proposal/notebooklm, smart-merge mv ops based on
resolutions, 3 render_template ops, 1 write_json passport stub).
Ops carry kind, source, dest, reason, extra. _marker_vars and
_claude_md_vars helpers normalize nullable + boolean fields for
string.Template substitution.

8 unit tests: fresh-init op order, funding-proposal call/ creation,
NLM-enabled refs/nlm_uploads/, C1 accept/skip, C3 rename, template
paths.

Cycle #2 task 9 (4/5 init utility tasks).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 10 — Init utility: `apply_plan` + rollback (TDD)

**Files:**
- Modify: `scripts/sws_init_project.py` (add `apply_plan` + helpers + CLI subcommands)
- Modify: `tests/test_init_project.py` (add `TestApplyPlan`)

Atomic apply with in-memory undo log; reverse log on per-op failure or interrupt. Op kinds handled: `mkdir`, `mv`, `mv_glob`, `render_template`, `write_json`. The `render_template` op delegates to `sws_render_template.render`.

- [ ] **Step 1: Append `TestApplyPlan` to `tests/test_init_project.py`.**

```python
import json  # add to top of file if not already imported


class TestApplyPlan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # plugin templates need to be reachable; tests use real templates from repo
        self.plugin_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, plan):
        return sws_init_project.apply_plan(
            plan, project_root=self.root, plugin_root=self.plugin_root,
        )

    def test_mkdir_creates_dirs(self):
        from sws_init_project import Op
        plan = [Op(kind="mkdir", dest="Manuscript"),
                Op(kind="mkdir", dest="Figures/main")]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        self.assertTrue((self.root / "Manuscript").is_dir())
        self.assertTrue((self.root / "Figures" / "main").is_dir())

    def test_mv_moves_file(self):
        from sws_init_project import Op
        (self.root / "paper.docx").write_bytes(b"abc")
        plan = [Op(kind="mkdir", dest="Manuscript"),
                Op(kind="mv", source="paper.docx", dest="Manuscript/paper.docx")]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        self.assertFalse((self.root / "paper.docx").exists())
        self.assertTrue((self.root / "Manuscript" / "paper.docx").exists())

    def test_render_template_uses_renderer(self):
        from sws_init_project import Op
        plan = [
            Op(kind="mkdir", dest="claude_memory"),
            Op(kind="render_template",
               source="templates/manuscript-memory-md.template",
               dest="claude_memory/MEMORY.md",
               extra={"vars": {}}),
        ]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        self.assertTrue((self.root / "claude_memory" / "MEMORY.md").exists())
        content = (self.root / "claude_memory" / "MEMORY.md").read_text()
        self.assertIn("Project marker", content)

    def test_write_json_creates_file(self):
        from sws_init_project import Op
        plan = [
            Op(kind="mkdir", dest="claude_memory"),
            Op(kind="write_json",
               dest="claude_memory/passport.json",
               extra={"content": {"cycle": 0}}),
        ]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        data = json.loads((self.root / "claude_memory" / "passport.json").read_text())
        self.assertEqual(data, {"cycle": 0})

    def test_rollback_on_failed_op(self):
        from sws_init_project import Op
        (self.root / "paper.docx").write_bytes(b"original")
        plan = [
            Op(kind="mkdir", dest="Manuscript"),
            Op(kind="mv", source="paper.docx", dest="Manuscript/paper.docx"),
            # 3rd op intentionally invalid: source missing
            Op(kind="mv", source="nonexistent_source", dest="anywhere"),
        ]
        ok, log = self._run(plan)
        self.assertFalse(ok)
        # rollback should restore paper.docx to root
        self.assertTrue((self.root / "paper.docx").exists())
        self.assertEqual((self.root / "paper.docx").read_bytes(), b"original")
        # Manuscript/paper.docx should be gone
        self.assertFalse((self.root / "Manuscript" / "paper.docx").exists())
        # Manuscript/ dir is created by op 1; rollback removes it
        self.assertFalse((self.root / "Manuscript").exists())

    def test_rollback_does_not_remove_user_files(self):
        from sws_init_project import Op
        (self.root / "user_file.txt").write_text("hands off")
        plan = [
            Op(kind="mkdir", dest="Manuscript"),
            Op(kind="mv", source="nonexistent", dest="anywhere"),
        ]
        ok, log = self._run(plan)
        self.assertFalse(ok)
        # User-pre-existing file untouched
        self.assertEqual((self.root / "user_file.txt").read_text(), "hands off")
```

- [ ] **Step 2: Run tests to confirm new failures.**

```bash
$DEV_PY -m unittest tests.test_init_project -v 2>&1 | tail -10
```
Expected: 6 errors with `AttributeError: module 'sws_init_project' has no attribute 'apply_plan'`.

- [ ] **Step 3: Add `apply_plan` + helpers + CLI to `scripts/sws_init_project.py`.**

Add to imports near top:
```python
import argparse
import json
import shutil
import sys
```

Append at end of file:

```python
def apply_plan(plan: list, project_root, plugin_root) -> tuple[bool, list[str]]:
    """Execute plan ops in order; rollback on per-op failure or exception.

    Returns (ok, log). On success, log contains executed-op messages.
    On failure, log contains executed-op messages + rollback messages.
    User-pre-existing files are touched only via the resolutions the user
    accepted at scan-prompt time.
    """
    project_root = Path(project_root).resolve()
    plugin_root = Path(plugin_root).resolve()
    log: list[str] = []
    undo: list[Op] = []

    try:
        for op in plan:
            _execute_op(op, project_root, plugin_root, undo)
            log.append(f"OK  {op.kind:16s} {op.dest or op.source}")
    except Exception as e:
        log.append(f"FAIL {op.kind:16s} {op.dest or op.source}: {e!r}")
        log.append("--- rolling back ---")
        for undo_op in reversed(undo):
            try:
                _rollback_op(undo_op, project_root)
                log.append(f"UNDO {undo_op.kind:15s} {undo_op.dest or undo_op.source}")
            except Exception as ue:
                log.append(f"UNDO-FAIL {undo_op.kind}: {ue!r}")
        return False, log

    return True, log


def _execute_op(op, project_root, plugin_root, undo: list) -> None:
    """Execute a single op; record undo info on success."""
    if op.kind == "mkdir":
        target = project_root / op.dest
        if target.exists():
            return  # idempotent — pre-existing dir, do not record undo
        target.mkdir(parents=True, exist_ok=False)
        undo.append(op)

    elif op.kind == "mv":
        src = project_root / op.source
        dest = project_root / op.dest
        if not src.exists():
            raise FileNotFoundError(f"source missing: {op.source}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        undo.append(op)

    elif op.kind == "mv_glob":
        # source like "Figures/*.{png,jpg,...}", dest is a directory
        # For v0.1 simplicity we expand a fixed set of extensions.
        import re
        m = re.match(r"^(.+?)/\*\.\{([^}]+)\}$", op.source)
        if not m:
            raise ValueError(f"unsupported mv_glob source: {op.source}")
        src_dir = project_root / m.group(1)
        exts = m.group(2).split(",")
        moved = []
        for ext in exts:
            for f in sorted(src_dir.glob(f"*.{ext}")):
                target = project_root / op.dest / f.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(target))
                moved.append((str(f), str(target)))
        undo.append(Op(kind="mv_glob", extra={"moved": moved}))

    elif op.kind == "render_template":
        # late import to avoid cycle on import-time
        sys.path.insert(0, str(plugin_root / "scripts"))
        import sws_render_template
        tpl = plugin_root / op.source
        out = project_root / op.dest
        sws_render_template.render(tpl, op.extra.get("vars", {}), out)
        undo.append(op)

    elif op.kind == "write_json":
        out = project_root / op.dest
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(op.extra["content"], indent=2, sort_keys=True))
        undo.append(op)

    else:
        raise ValueError(f"unknown op kind: {op.kind}")


def _rollback_op(op, project_root) -> None:
    """Reverse a previously-executed op."""
    if op.kind == "mkdir":
        target = project_root / op.dest
        if target.is_dir():
            # rmdir only if empty; if non-empty (subsequent ops added contents),
            # the contents were created by other ops which we'll roll back first.
            try:
                target.rmdir()
            except OSError:
                shutil.rmtree(target)

    elif op.kind == "mv":
        # reverse the move
        src = project_root / op.dest
        dest = project_root / op.source
        if src.exists():
            shutil.move(str(src), str(dest))

    elif op.kind == "mv_glob":
        for original, moved_to in reversed(op.extra.get("moved", [])):
            if Path(moved_to).exists():
                shutil.move(moved_to, original)

    elif op.kind == "render_template":
        target = project_root / op.dest
        if target.exists():
            target.unlink()

    elif op.kind == "write_json":
        target = project_root / op.dest
        if target.exists():
            target.unlink()


def _cli_scan(args):
    conflicts = scan_conflicts(args.root)
    print(json.dumps([
        {"cls": c.cls, "path": c.path, "suggested_action": c.suggested_action,
         "options": c.options}
        for c in conflicts
    ], indent=2))
    return 0


def _cli_plan(args):
    inputs = json.loads(Path(args.inputs).read_text())
    resolutions = json.loads(Path(args.resolutions).read_text()) if args.resolutions else {}
    conflicts_data = json.loads(Path(args.conflicts).read_text()) if args.conflicts else []
    conflicts = [Conflict(**c) for c in conflicts_data]
    ok, msg = validate_inputs(inputs)
    if not ok:
        print(msg, file=sys.stderr)
        return 2
    plan = build_plan(inputs, conflicts=conflicts, resolutions=resolutions)
    print(json.dumps([
        {"kind": op.kind, "source": op.source, "dest": op.dest,
         "reason": op.reason, "extra": op.extra}
        for op in plan
    ], indent=2))
    return 0


def _cli_apply(args):
    plan_data = json.loads(Path(args.plan).read_text())
    plan = [Op(**op) for op in plan_data]
    ok, log = apply_plan(plan, project_root=args.root, plugin_root=args.plugin_root)
    for line in log:
        print(line)
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--root", default=".")
    p_scan.set_defaults(func=_cli_scan)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--inputs", required=True)
    p_plan.add_argument("--conflicts")
    p_plan.add_argument("--resolutions")
    p_plan.set_defaults(func=_cli_plan)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--plan", required=True)
    p_apply.add_argument("--root", default=".")
    p_apply.add_argument("--plugin-root", required=True)
    p_apply.set_defaults(func=_cli_apply)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests.**

```bash
$DEV_PY -m unittest tests.test_init_project -v
```
Expected: 41 tests pass (7 + 10 + 10 + 8 + 6).

- [ ] **Step 5: Smoke-test the CLI subcommands.**

```bash
mkdir -p /tmp/sws_smoke && cd /tmp/sws_smoke && touch paper.docx
$DEV_PY $REPO_ROOT/scripts/sws_init_project.py scan --root /tmp/sws_smoke
cd $REPO_ROOT
rm -rf /tmp/sws_smoke
```
Expected: JSON list with one C1 conflict for `paper.docx`.

- [ ] **Step 6: Commit.**

```bash
git add scripts/sws_init_project.py tests/test_init_project.py
git commit -m "feat: add apply_plan with rollback to init-project utility

Atomic apply: executes plan ops in order (mkdir/mv/mv_glob/render_template/
write_json); on per-op failure or exception, reverses the in-memory undo
log. User-pre-existing files only touched via user-approved resolutions
(rollback safety guarantee). render_template ops delegate to
sws_render_template.render via late-import.

Plus CLI subcommands (scan/plan/apply) for skill orchestration via
Bash.

6 unit tests: mkdir, mv, render_template (uses real
manuscript-memory-md.template from plugin), write_json, rollback on
failed mv, rollback safety for user files.

Cycle #2 task 10 (5/5 init utility tasks).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 11 — `skills/init-project/SKILL.md` orchestration prompt

**Files:**
- Create: `skills/init-project/SKILL.md`

The model-driven orchestration layer. Frontmatter per `plugin-dev:skill-development` schema research (cycle #1); body in imperative form, ~1500-2000 words target, cross-refs the spec + reference docs.

- [ ] **Step 1: Write `skills/init-project/SKILL.md`.**

````markdown
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
   `--article-type, --language, --format, --target-journal, --target-call, --first-author, --year, --co-authors, --notebooklm`
2. **Natural-language `$ARGUMENTS`:** if free text accompanies the slash command (e.g., `/sws:init-project Communication for ChemBioChem on hDF kinetics, first author Smith with co-authors`), parse it for any unset fields. Use the model's natural-language understanding; do not require structured syntax.
3. **Interactive prompts:** for any required field still missing, prompt one at a time. Defaults come from `references/marker-schema.md` (`language: en`, `format: docx`, `notebooklm.enabled: false`). For `year`, default to the current system year.

After arg resolution, slugify `first_author` and compute `short_handle = <slug> + ("_et_al_" if co_authors_present else "_") + <year>`.

## Step b — Preflight + detection scan

Before any disk work, run the env preflight:

```bash
python3 scripts/sws_check_env.py
```

If exit non-zero, print the error verbatim and abort. Do not attempt to invoke any other Python utility.

Then scan the cwd for the 6 conflict classes:

```bash
python3 scripts/sws_init_project.py scan --root .
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

For C4 (existing CLAUDE.md) the options are `[r]eplace / [a]ppend / [s]kip`.
For C5 (existing claude_memory/) the options are `[k]eep / [m]ove / [r]eplace`.
For C6 (existing marker) load the existing marker's values, present them as defaults during the arg-resolution prompts, write a merged marker.

Build a `resolutions` dict mapping `cls` → user choice.

## Step d — Plan assembly

Write the inputs and resolutions to temp JSON files and call:

```bash
python3 scripts/sws_init_project.py plan \
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
python3 scripts/sws_init_project.py apply \
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
````

- [ ] **Step 2: Verify the SKILL.md frontmatter parses.**

```bash
$DEV_PY -c "
import re, yaml
fm = yaml.safe_load(re.search(r'^---\n(.*?)\n---', open('skills/init-project/SKILL.md').read(), re.S|re.M).group(1))
assert fm['name'] == 'init-project'
assert 'description' in fm
print('OK', fm['name'], 'desc len:', len(fm['description']))
"
```
Expected: `OK init-project desc len: <number around 700>`.

- [ ] **Step 3: Commit.**

```bash
git add skills/init-project/SKILL.md
git commit -m "feat: add init-project orchestration skill

Model-driven orchestrator for /sws:init-project: handles 3-tier
argument resolution (named args → \$ARGUMENTS NL parse → interactive
prompts), per-conflict negotiation, plan presentation, summary output.
Deterministic work delegated to scripts/sws_check_env.py,
sws_init_project.py (scan/plan/apply), sws_render_template.py,
sws_fs_index.py via Bash.

Body covers steps a–g with explicit Bash commands and expected
behavior. Cross-refs the spec for edge cases (E1-E10) and the
canonical references for schema details. Frontmatter description
follows plugin-dev:skill-development guidance for triggering.

Cycle #2 task 11.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 12 — Manual smoke test + cycle wrap

The orchestration is model-driven, so end-to-end behavior is tested by exercising the skill against a fixture. This task validates that the integrated cycle-#2 deliverables work together.

- [ ] **Step 1: Run all unit tests one final time.**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -8
```
Expected: 4 (cycle #1 fs_index) + 41 (cycle #2 init-project + render + env) = **45 tests pass**.

- [ ] **Step 2: Smoke-test scan + plan CLI against a fixture project.**

```bash
mkdir -p /tmp/sws_e2e && cd /tmp/sws_e2e
touch paper.docx
mkdir -p claude_material
echo "# notes" > CLAUDE.md

# scan
$DEV_PY \
  $REPO_ROOT/scripts/sws_init_project.py \
  scan --root /tmp/sws_e2e > /tmp/sws_e2e_conflicts.json
cat /tmp/sws_e2e_conflicts.json

# plan (with hand-crafted inputs + accept-all resolutions)
cat > /tmp/sws_e2e_inputs.json <<'EOF'
{
  "article_type": "communication",
  "language": "en",
  "format": "docx",
  "target_journal": "chembiochem",
  "target_call": null,
  "first_author": "smith",
  "year": 2026,
  "co_authors_present": true,
  "notebooklm_enabled": false,
  "short_handle": "smith_et_al_2026",
  "created_iso": "2026-05-08T12:00:00Z"
}
EOF

cat > /tmp/sws_e2e_resolutions.json <<'EOF'
{"C1": "accept", "C3": "accept", "C4": "skip"}
EOF

$DEV_PY \
  $REPO_ROOT/scripts/sws_init_project.py \
  plan --inputs /tmp/sws_e2e_inputs.json \
       --conflicts /tmp/sws_e2e_conflicts.json \
       --resolutions /tmp/sws_e2e_resolutions.json > /tmp/sws_e2e_plan.json
cat /tmp/sws_e2e_plan.json | head -40

# apply
$DEV_PY \
  $REPO_ROOT/scripts/sws_init_project.py \
  apply --plan /tmp/sws_e2e_plan.json \
        --root /tmp/sws_e2e \
        --plugin-root $REPO_ROOT

# verify
ls -la /tmp/sws_e2e
cat /tmp/sws_e2e/.sws-project.local.md
cat /tmp/sws_e2e/CLAUDE.md | head -20

# clean up
cd $REPO_ROOT
rm -rf /tmp/sws_e2e /tmp/sws_e2e_*.json
```

Expected:
- scan output: 3 conflicts (C1 paper.docx, C3 claude_material/, C4 CLAUDE.md).
- plan output: ordered ops including `mkdir` for the topology + `mv` for paper.docx → Manuscript/ + `mv` for claude_material → scratch/ + 3 `render_template` + 1 `write_json`.
- apply output: log lines `OK mkdir / mv / render_template / write_json` for each op.
- `/tmp/sws_e2e/.sws-project.local.md` exists with rendered marker fields (article_type=communication, target_journal=chembiochem, etc.).
- `/tmp/sws_e2e/CLAUDE.md` rendered (existing CLAUDE.md preserved because resolution=skip).
- `/tmp/sws_e2e/Manuscript/paper.docx` exists.
- `/tmp/sws_e2e/scratch/` exists (renamed from claude_material/).

- [ ] **Step 3: Confirm `claude_memory/` is still gitignored.**

```bash
git status -s | grep -E "(claude_memory|project_)" || echo "clean"
```
Expected: `clean`.

- [ ] **Step 4: Confirm cycle-#2 commit log on the feature branch.**

```bash
git log --oneline cycle/02-init-project ^main
```
Expected: 11 commits in this order:
1. `feat: add Python env preflight (sws_check_env.py)`
2. `docs: add Python env reference (lean YAML-as-dictionary form)`
3. `feat: add template renderer (sws_render_template.py)`
4. `feat: add 3 init-project template files`
5. `docs: add docx typography canon reference`
6. `feat: add init-project utility skeleton + slugify`
7. `feat: add validate_inputs to init-project utility`
8. `feat: add scan_conflicts to init-project utility`
9. `feat: add build_plan to init-project utility`
10. `feat: add apply_plan with rollback to init-project utility`
11. `feat: add init-project orchestration skill`

- [ ] **Step 5: Open PR (option 2 from cycle #1 — same convention).**

```bash
git push -u origin cycle/02-init-project
gh pr create --base main --head cycle/02-init-project \
  --title "Cycle #2: /sws:init-project + 3 templates" \
  --body-file /tmp/sws_cycle2_pr_body.md
```

Where `/tmp/sws_cycle2_pr_body.md` is the PR body template (write it before invoking `gh`):

```markdown
## Summary

Cycle #2 ships `/sws:init-project` end-to-end: the slash command, the model-driven skill, three pure-stdlib Python utilities (env preflight, template renderer, init orchestration with rollback), three `.template` files, two reference docs (Python env policy, docx typography canon), and a 41-test suite. Banner stays `🚧 v0.1 in design`.

Spec: `docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md`.
Plan: `docs/superpowers/plans/2026-05-08-cycle-02-init-project.md`.

## Key features

- Smart-merge with 6 conflict classes (root *.docx, loose Figures/, claude_material/, existing CLAUDE.md / claude_memory/ / marker).
- Plan-then-apply atomicity with in-memory undo log; rollback on per-op failure or interrupt.
- 3-tier argument resolution (named args → $ARGUMENTS NL parse → interactive prompts).
- Pure stdlib through cycle #4; first real Python dep arrives in cycle #5.
- Lean YAML-as-dictionary deliverables; structured data in frontmatter, prose body cross-refs source-of-truth.

## Test plan

- [x] 45/45 unit tests pass under the dev env (`python -m unittest discover tests -v`).
- [x] Manual end-to-end smoke test against `/tmp/sws_e2e` fixture (3 conflicts → resolved → applied → verified).
- [ ] Plugin loads in Claude Code without error post-merge.
- [ ] `/sws:init-project` invokable from a fresh Claude Code session post-merge against a real test directory.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Expected output: PR URL printed; PR is open on GitHub.

- [ ] **Step 6: Stop here for user merge decision.**

Per cycle #1 convention, do NOT auto-merge. The user reviews the PR and chooses option 1 (direct merge) or option 2 (PR self-review then merge). The branch is ready.

---

## Self-Review Checklist

**1. Spec coverage:** Each spec section maps to a task:

| Spec section / decision | Task |
|---|---|
| Q1 smart-merge UX (6 classes) | Task 8 (scan) + Task 9 (plan) + Task 10 (apply) |
| Q2 3-tier arg waterfall | Task 11 (skill) |
| Q3 minimal + initial state files | Task 9 (build_plan) + Task 10 (apply_plan) |
| Q4 detection + suggested default | Task 8 (scan_conflicts.suggested_action) |
| Q5 input set + computed short_handle | Task 6 (slugify) + Task 7 (validate_inputs) + Task 11 (skill arg resolution) |
| Q5b article_type rename | Already landed pre-cycle-#2 (commit `8e4378e` on main) — referenced throughout |
| Q6 plan-then-apply atomicity | Task 10 (apply_plan + rollback) |
| custom_typography canon | Task 5 (`references/docx-style.md`) |
| python_env_policy | Task 1 (`sws_check_env.py`) + Task 2 (`references/python-env.md`) |
| 3 templates | Task 4 |
| `scripts/sws_render_template.py` | Task 3 |
| `skills/init-project/SKILL.md` | Task 11 |
| 3 test files | Tasks 1, 3, 6–10 |
| All 10 edge cases (E1-E10) | Spec-referenced; skill body defers to spec frontmatter |
| Cycle #5 follow-ups (skeleton, requirements.txt) | Excluded from cycle #2 by spec — not implemented here |

All 14 spec line items mapped. ✓

**2. Placeholder scan:** No `TBD`, `TODO`, `implement later`, or "fill in details" in this plan. ✓

**3. Type / signature consistency:**
- `slugify(name)` is defined in Task 6 and referenced consistently. ✓
- `validate_inputs(inputs) -> (bool, str)` matches in Task 7 def + use. ✓
- `scan_conflicts(root) -> list[Conflict]` matches in Task 8 def + Task 9 use + Task 10 use. ✓
- `build_plan(inputs, conflicts, resolutions) -> list[Op]` matches in Task 9 def + Task 10 test. ✓
- `apply_plan(plan, project_root, plugin_root) -> (bool, list[str])` matches in Task 10 def + manual smoke test. ✓
- `Conflict` and `Op` dataclass fields consistent across producer (scan/build) and consumer (apply) tasks. ✓
- `render(template_path, vars_dict, out_path)` matches in Task 3 def + Task 10 use (via late-import). ✓

**Plan ready.**

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-08-cycle-02-init-project.md`. Two execution options:

**1. Subagent-Driven (recommended).** Dispatch a fresh subagent per task, review between tasks. Best for cycle #2 because Tasks 1–5 are nearly independent (env preflight, env-ref doc, template renderer, templates, docx-style ref) and can land via sequential subagents with review between commits. Tasks 6–10 build incrementally on `sws_init_project.py` and benefit from one subagent per TDD cycle (one function per commit). Required sub-skill: `superpowers:subagent-driven-development`. Sonnet at medium effort sufficient per task; Opus inherit only for Task 10 (apply + rollback design judgment).

**2. Inline Execution.** Execute in this session using `superpowers:executing-plans`, batch with checkpoints. Best if you want one-shot continuity and don't mind a longer single conversation.

Which approach?
