# SWS Cycle #3 — init-project C4 append Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the C4 `[a]ppend` option from v0.2 backlog to v0.1 so `/sws:init-project` is non-destructive by default when an existing CLAUDE.md is present. After this cycle, users can choose `append` to preserve their hand-curated notes while still getting SWS cross-refs at the bottom of their CLAUDE.md.

**Architecture:** All work is in the utility layer (`scripts/sws_init_project.py`). The skill (`skills/init-project/SKILL.md`) is updated to document the new option in Step c. No new files, no new imports, no new dependencies.

**Tech stack:** Same as cycle #2. Pure stdlib, `pathlib`, `json`, `unittest`. HTML-comment markers for idempotent section replacement.

**Working directory:** `$REPO_ROOT/`.

**Branch:** `cycle/03-claude-md-append`.

**Source-of-truth references:**
- Spec: `docs/superpowers/specs/2026-05-12-cycle-03-claude-md-append-design.md`
- Cycle-#2 spec: `docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md`
- Script under edit: `scripts/sws_init_project.py`
- Tests under edit: `tests/test_init_project.py`
- Skill under edit: `skills/init-project/SKILL.md`

**Reference Python interpreter:** `$DEV_PY`

---

## Task 1 — `scan_conflicts` C4 options re-add `append`

**Files:** `scripts/sws_init_project.py`, `tests/test_init_project.py`

Change C4 Conflict construction so the options list is `["replace", "append", "skip"]` and the suggested_action reflects all three.

- [ ] **Step 1: Write failing test `test_C4_options_include_append` in `TestScanConflicts`.**

```python
def test_C4_options_include_append(self):
    (self.root / "CLAUDE.md").write_text("# my notes")
    conflicts = sws_init_project.scan_conflicts(self.root)
    c4 = next(c for c in conflicts if c.cls == "C4")
    self.assertIn("append", c4.options)
```

- [ ] **Step 2: Run test — expect failure (options list does not yet contain "append").**

```bash
$DEV_PY -m unittest tests.test_init_project.TestScanConflicts.test_C4_options_include_append -v
```

- [ ] **Step 3: Update C4 block in `scan_conflicts`.**

```python
# C4: existing root CLAUDE.md
if (root / "CLAUDE.md").is_file():
    conflicts.append(Conflict(
        cls="C4",
        path="CLAUDE.md",
        suggested_action="[r]eplace with SWS template / [a]ppend SWS-managed section / [s]kip (leave file untouched)",
        options=["replace", "append", "skip"],
    ))
```

- [ ] **Step 4: Run test — expect pass.**

- [ ] **Step 5: Commit.**

```
feat: re-add append option to C4 in scan_conflicts
```

---

## Task 2 — `build_plan` emits `append_sws_section` op + helper `_build_sws_section`

**Files:** `scripts/sws_init_project.py`, `tests/test_init_project.py`

Add module-level constants and helper function. Wire `build_plan` to emit the new op when `c4_resolution == "append"`.

- [ ] **Step 1: Write failing test `test_C4_append_emits_append_op_and_omits_render` in `TestBuildPlanResolutions`. Also update `_c4()` to use the new 3-option list.**

```python
def _c4(self):
    from sws_init_project import Conflict
    return Conflict(cls="C4", path="CLAUDE.md",
                    suggested_action="[r]eplace with SWS template / [a]ppend SWS-managed section / [s]kip (leave file untouched)",
                    options=["replace", "append", "skip"])

def test_C4_append_emits_append_op_and_omits_render(self):
    plan = sws_init_project.build_plan(
        self._base_inputs(),
        conflicts=[self._c4()],
        resolutions={"C4": "append"},
    )
    render_dests = self._dests_of_kind(plan, "render_template")
    append_dests = self._dests_of_kind(plan, "append_sws_section")
    self.assertNotIn("CLAUDE.md", render_dests)
    self.assertIn("CLAUDE.md", append_dests)
    # Marker + MEMORY/passport still emitted
    self.assertIn(".sws-project.local.md", render_dests)
    self.assertIn("claude_memory/MEMORY.md", render_dests)
```

- [ ] **Step 2: Run test — expect failure (no `append_sws_section` op kind exists yet).**

- [ ] **Step 3: Add constants and helper to `sws_init_project.py` (place near `_marker_vars`).**

```python
SWS_MARKER_OPEN = "<!-- SWS-managed start: do not hand-edit between the markers below -->"
SWS_MARKER_CLOSE = "<!-- SWS-managed end -->"


def _build_sws_section(short_handle: str) -> str:
    """Return the marker-delimited SWS-managed block for C4=append.

    Idempotent: re-running with the same or different short_handle replaces
    only the content between the open/close markers, leaving the user's
    surrounding content untouched.
    """
    return (
        f"{SWS_MARKER_OPEN}\n\n"
        "## SWS-managed\n\n"
        f"This manuscript directory is SWS-bootstrapped (`{short_handle}`). "
        "Canonical project metadata lives in `.sws-project.local.md`; agents "
        "reading this CLAUDE.md should look there for `article_type`, "
        "`language`, `format`, `target_journal`/`target_call`, etc.\n\n"
        "Where to find context:\n\n"
        "- `.sws-project.local.md` — active SWS settings.\n"
        "- `claude_memory/MEMORY.md` — session-state index; update as you work.\n"
        "- `Manuscript/_journal-style/<slug>.md` — journal-specific overlay "
        "(run `/sws:resolve-journal-style` if missing).\n"
        "- SWS plugin canonical references: `references/folder-topology.md`, "
        "`references/marker-schema.md`, `references/docx-style.md`, "
        "`references/python-env.md`.\n\n"
        f"{SWS_MARKER_CLOSE}"
    )
```

- [ ] **Step 4: In `build_plan`, add `append_sws_section` op after the C4 gate.**

After the existing block:
```python
c4_resolution = resolutions.get("C4")  # None if no C4 conflict, else "replace"|"skip"
```

Add (after the CLAUDE.md render gate, before MEMORY.md render gate):
```python
# C4=append: emit append_sws_section op (no render_template for CLAUDE.md in this case).
if c4_resolution == "append":
    ops.append(Op(
        kind="append_sws_section",
        dest="CLAUDE.md",
        reason="smart-merge C4 (append SWS section)",
        extra={"short_handle": inputs["short_handle"]},
    ))
```

- [ ] **Step 5: Run test — expect pass.**

- [ ] **Step 6: Commit.**

```
feat: emit append_sws_section op when C4 resolution = append
```

---

## Task 3 — `_execute_op` + `_rollback_op` handle `append_sws_section`

**Files:** `scripts/sws_init_project.py`, `tests/test_init_project.py`

Add execute and rollback branches for the new op kind. Four tests.

- [ ] **Step 1: Write 4 failing tests (add class `TestAppendSwsSection` to `tests/test_init_project.py`).**

```python
class TestAppendSwsSection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.plugin_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, plan):
        return sws_init_project.apply_plan(
            plan, project_root=self.root, plugin_root=self.plugin_root,
        )

    def test_append_sws_section_to_file_without_markers(self):
        from sws_init_project import Op, SWS_MARKER_OPEN, SWS_MARKER_CLOSE
        (self.root / "CLAUDE.md").write_text("# user notes\n\nexisting content\n")
        plan = [Op(kind="append_sws_section", dest="CLAUDE.md",
                   extra={"short_handle": "smith_et_al_2026"})]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        content = (self.root / "CLAUDE.md").read_text()
        self.assertIn("# user notes", content)
        self.assertIn("existing content", content)
        self.assertIn(SWS_MARKER_OPEN, content)
        self.assertIn(SWS_MARKER_CLOSE, content)
        self.assertIn("smith_et_al_2026", content)
        # User content comes before SWS section
        self.assertLess(content.index("existing content"), content.index(SWS_MARKER_OPEN))

    def test_append_sws_section_with_existing_markers_replaces_idempotently(self):
        from sws_init_project import Op, SWS_MARKER_OPEN, SWS_MARKER_CLOSE
        initial = (
            "# user notes\n\n"
            f"{SWS_MARKER_OPEN}\n\nold sws block with old_handle\n\n{SWS_MARKER_CLOSE}\n"
            "\nmore user content below\n"
        )
        (self.root / "CLAUDE.md").write_text(initial)
        plan = [Op(kind="append_sws_section", dest="CLAUDE.md",
                   extra={"short_handle": "new_handle_2027"})]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        content = (self.root / "CLAUDE.md").read_text()
        # Old block content gone
        self.assertNotIn("old sws block with old_handle", content)
        # New short_handle in
        self.assertIn("new_handle_2027", content)
        # User content surrounding the markers preserved
        self.assertIn("# user notes", content)
        self.assertIn("more user content below", content)
        # Exactly one open marker and one close marker
        self.assertEqual(content.count(SWS_MARKER_OPEN), 1)
        self.assertEqual(content.count(SWS_MARKER_CLOSE), 1)

    def test_append_sws_section_rollback_restores_original(self):
        from sws_init_project import Op
        original = "# original user content\n"
        (self.root / "CLAUDE.md").write_text(original)
        plan = [
            Op(kind="append_sws_section", dest="CLAUDE.md",
               extra={"short_handle": "smith_2026"}),
            # Force a failure on a subsequent op so rollback kicks in
            Op(kind="mv", source="nonexistent", dest="anywhere"),
        ]
        ok, log = self._run(plan)
        self.assertFalse(ok)
        # CLAUDE.md restored to original
        self.assertEqual((self.root / "CLAUDE.md").read_text(), original)

    def test_append_sws_section_fails_if_claude_md_missing(self):
        from sws_init_project import Op
        plan = [Op(kind="append_sws_section", dest="CLAUDE.md",
                   extra={"short_handle": "smith_2026"})]
        ok, log = self._run(plan)
        self.assertFalse(ok)
        # The error message should mention CLAUDE.md or that the file is missing
        self.assertTrue(any("CLAUDE.md" in line or "not found" in line for line in log),
                        f"Expected failure log to mention missing file; got {log}")
```

- [ ] **Step 2: Run tests — expect 4 failures.**

```bash
$DEV_PY -m unittest tests.test_init_project.TestAppendSwsSection -v
```

- [ ] **Step 3: Add execute branch in `_execute_op`.**

Add after the `write_json` branch, before the `else: raise`:

```python
elif op.kind == "append_sws_section":
    target = project_root / op.dest
    if not target.exists():
        raise FileNotFoundError(
            f"CLAUDE.md not found at {op.dest}; C4=append requires it to exist"
        )
    original_content = target.read_text()
    block = _build_sws_section(op.extra["short_handle"])
    if SWS_MARKER_OPEN in original_content and SWS_MARKER_CLOSE in original_content:
        # Replace existing SWS-managed section in place
        start = original_content.index(SWS_MARKER_OPEN)
        end = original_content.index(SWS_MARKER_CLOSE) + len(SWS_MARKER_CLOSE)
        new_content = original_content[:start] + block + original_content[end:]
    else:
        # Append at end with a single blank-line separator
        sep = "\n\n" if not original_content.endswith("\n") else (
            "\n" if not original_content.endswith("\n\n") else ""
        )
        new_content = original_content + sep + block + "\n"
    target.write_text(new_content)
    op.extra["_original_content"] = original_content
    undo.append(op)
```

- [ ] **Step 4: Add rollback branch in `_rollback_op`.**

Add after the `write_json` branch:

```python
elif op.kind == "append_sws_section":
    target = project_root / op.dest
    original = op.extra.get("_original_content")
    if original is not None and target.exists():
        target.write_text(original)
```

- [ ] **Step 5: Run tests — expect 4 passes.**

- [ ] **Step 6: Run full test suite — expect 67 total.**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -5
```

- [ ] **Step 7: Commit.**

```
feat: handle append_sws_section in apply_plan with rollback
```

---

## Task 4 — `SKILL.md` Step c update

**Files:** `skills/init-project/SKILL.md`

Replace the C4 description and update the v0.2 backlog note.

- [ ] **Step 1: Replace the C4 block in Step c.**

Find:
```
For **C4 (existing CLAUDE.md)** the options are `[r]eplace / [s]kip`:
  - `replace` = overwrite user's CLAUDE.md with the SWS per-paper template.
  - `skip` = leave user's CLAUDE.md untouched. SWS still writes the marker (`.sws-project.local.md`) so the project is recognized; the user's existing CLAUDE.md remains the source of project context. SWS-aware sessions auto-load CLAUDE.md, so this is the safe default if the user has hand-curated notes.
```

Replace with:
```
For **C4 (existing CLAUDE.md)** the options are `[r]eplace / [a]ppend / [s]kip`:
  - `replace` = overwrite user's CLAUDE.md with the SWS per-paper template. The user's existing content is lost (no automatic backup in v0.1).
  - `append` = preserve the user's CLAUDE.md verbatim and append a marker-delimited `## SWS-managed` section at the end (cross-refs to plugin canonical references; pointer to `.sws-project.local.md` for project metadata). Idempotent on re-run: the HTML-comment markers let SWS replace the existing section instead of duplicating it. Recommended for hand-curated CLAUDE.md files.
  - `skip` = leave the user's CLAUDE.md entirely untouched. SWS still writes the marker (`.sws-project.local.md`); agents reading via session auto-load get the user's existing CLAUDE.md as primary context.
```

- [ ] **Step 2: Replace the v0.2 backlog note.**

Find:
```
**Note (v0.2 backlog):** Smarter merges — `[a]ppend` for C4 (preserve user CLAUDE.md and append an SWS-managed section, exploiting Claude Code's auto-loaded CLAUDE.md context for in-session merge), and `[m]ove` for C5 (rotate claude_memory/ to claude_memory/_archive/ then write fresh) — are deferred. The v0.1 binary choice ([replace] vs [skip]/[keep]) is data-loss-safe by default.
```

Replace with:
```
**Note (v0.2 backlog):** Smarter merges deferred to v0.2 — `[m]ove` for C5 (rotate `claude_memory/` to `claude_memory/_archive/` then write fresh), frontmatter merge for existing YAML in user's CLAUDE.md, content-aware section placement. The v0.1 options ship the data-loss-safe defaults plus the `[a]ppend` smart-merge for the typical case (existing CLAUDE.md with hand-curated content).
```

- [ ] **Step 3: Commit.**

```
docs(skill): document C4 append option in init-project SKILL.md
```

---

## Task 5 — Smoke test, backlog update, push, PR

- [ ] **Step 1: Run full unit test suite.**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -5
```

Expected: `Ran 67 tests in Xs` with `OK`.

- [ ] **Step 2: End-to-end smoke test (C4=append with idempotency check).**

See Task 5b in the cycle scope doc. Verify:
- After first apply: user content present, SWS section appended, `smith_et_al_2026` in file.
- After second apply: section count == 1 (marker-replace, not duplicate).

- [ ] **Step 3: Update `claude_memory/project_v02_backlog.md`.**

Find the `init-project smart-merge (deferred 2026-05-12)` entry. Add note that C4 append shipped in cycle #3 on 2026-05-12.

- [ ] **Step 4: Push branch and open PR.**

```bash
git push -u origin cycle/03-claude-md-append
```

PR title: `Cycle #3: init-project C4 append (smart-merge promote from v0.2)`

---

## Self-review checklist

- [ ] No new imports added to `sws_init_project.py`
- [ ] `SWS_MARKER_OPEN` and `SWS_MARKER_CLOSE` are module-level constants (importable by tests)
- [ ] `_build_sws_section` is module-level (not nested inside `_execute_op`)
- [ ] E2 partial-markers edge case: code uses `if OPEN in content and CLOSE in content` — both must be present for replace path; otherwise append path fires
- [ ] Rollback: `op.extra["_original_content"]` is set BEFORE `target.write_text(new_content)` in `_execute_op` (defensive ordering matches design)
- [ ] Test count: 61 (cycle #2) + 6 (cycle #3) = 67
- [ ] SKILL.md: no stale reference to `[a]ppend` in the v0.2 backlog note
- [ ] No AI-writing tells in spec body, plan body, or SKILL.md edits
