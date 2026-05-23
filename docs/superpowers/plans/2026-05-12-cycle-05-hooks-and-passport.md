# SWS Cycle #5 — Three MVP hooks + passport.json schema

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the three marker-scoped hooks (pre-edit backup, Stop passport append, SessionStart nudge) plus the passport.json schema. These are the cycle-memory and data-safety primitives called out as SWS differentiators in the architecture sketch.

**Architecture:** Shared `sws_hook_utils.py` with `check_marker()` + `parse_marker()`. Three hook scripts. Hook config at `hooks/hooks.json` (plugin wrapper format). All pure stdlib.

**Tech stack:** Python 3.9+ stdlib only. No pyyaml.

**Working directory:** `$REPO_ROOT/`.

**Branch:** `cycle/05-hooks-and-passport`.

**Source-of-truth references:**
- Spec: `docs/superpowers/specs/2026-05-12-cycle-05-hooks-and-passport-design.md`
- Architecture sketch §5: `docs/superpowers/specs/2026-05-08-architecture-sketch-design.md`
- Test style: `tests/test_init_project.py`

**Reference Python interpreter:** `$DEV_PY`

---

## Task 1 — `scripts/sws_hook_utils.py` + tests

**Files:** `scripts/sws_hook_utils.py` (new), `tests/test_sws_hook_utils.py` (new)

- [ ] **Step 1: Write 6 failing tests in `tests/test_sws_hook_utils.py`.**

```python
class TestCheckMarker(unittest.TestCase):
    def test_check_marker_returns_none_when_absent(self): ...
    def test_check_marker_returns_dict_when_present(self): ...

class TestParseMarker(unittest.TestCase):
    def test_parse_marker_extracts_top_level_scalars(self): ...
    def test_parse_marker_handles_null_values(self): ...
    def test_parse_marker_handles_booleans(self): ...
    def test_parse_marker_returns_empty_dict_on_no_frontmatter(self): ...
```

- [ ] **Step 2: Run tests — expect 6 failures.**

```bash
$DEV_PY -m unittest tests.test_sws_hook_utils -v
```

- [ ] **Step 3: Write `scripts/sws_hook_utils.py`.**

- [ ] **Step 4: Run tests — expect 6 passes.**

- [ ] **Step 5: Run full suite — expect 82 total.**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -5
```

- [ ] **Step 6: Commit.**

```
feat(hooks): add sws_hook_utils with check_marker + parse_marker
```

---

## Task 2 — `scripts/sws_hook_pre_edit_backup.py` + tests

**Files:** `scripts/sws_hook_pre_edit_backup.py` (new), `tests/test_sws_hook_pre_edit_backup.py` (new)

- [ ] **Step 1: Write 7 failing tests in `tests/test_sws_hook_pre_edit_backup.py`.**

```python
class TestPreEditBackup(unittest.TestCase):
    def test_no_op_when_no_marker(self): ...
    def test_backs_up_docx_when_marker_present(self): ...
    def test_no_op_for_unrelated_extension(self): ...
    def test_backs_up_tex_when_format_latex(self): ...
    def test_no_op_for_tex_when_format_docx(self): ...
    def test_no_op_when_target_does_not_exist(self): ...
    def test_returns_nonzero_when_backup_fails(self): ...
```

Tests use `subprocess.run` to invoke the hook with a JSON event piped to stdin. Run in a `tempfile.TemporaryDirectory`.

- [ ] **Step 2: Run tests — expect 7 failures.**

- [ ] **Step 3: Write `scripts/sws_hook_pre_edit_backup.py`.**

- [ ] **Step 4: Run tests — expect 7 passes.**

- [ ] **Step 5: Run full suite — expect 89 total.**

- [ ] **Step 6: Commit.**

```
feat(hooks): add pre-edit backup hook (PreToolUse Edit|Write)
```

---

## Task 3 — `scripts/sws_hook_stop_passport.py` + tests

**Files:** `scripts/sws_hook_stop_passport.py` (new), `tests/test_sws_hook_stop_passport.py` (new)

- [ ] **Step 1: Write 6 failing tests in `tests/test_sws_hook_stop_passport.py`.**

```python
class TestStopPassport(unittest.TestCase):
    def test_no_op_when_no_marker(self): ...
    def test_no_op_when_passport_missing(self): ...
    def test_no_op_when_no_files_modified(self): ...
    def test_appends_entry_with_modified_files(self): ...
    def test_increments_cycle_number(self): ...
    def test_handles_corrupt_passport_gracefully(self): ...
```

- [ ] **Step 2: Run tests — expect 6 failures.**

- [ ] **Step 3: Write `scripts/sws_hook_stop_passport.py`.**

- [ ] **Step 4: Run tests — expect 6 passes.**

- [ ] **Step 5: Run full suite — expect 95 total.**

- [ ] **Step 6: Commit.**

```
feat(hooks): add Stop hook — passport.json history append
```

---

## Task 4 — `scripts/sws_hook_session_start.py` + tests

**Files:** `scripts/sws_hook_session_start.py` (new), `tests/test_sws_hook_session_start.py` (new)

- [ ] **Step 1: Write 6 failing tests in `tests/test_sws_hook_session_start.py`.**

```python
class TestSessionStart(unittest.TestCase):
    def test_no_op_when_no_marker(self): ...
    def test_prints_passport_summary_when_history_present(self): ...
    def test_no_output_when_history_empty(self): ...
    def test_prints_journal_style_nudge_when_overlay_missing(self): ...
    def test_no_nudge_for_funding_proposal(self): ...
    def test_no_nudge_when_overlay_present(self): ...
```

- [ ] **Step 2: Run tests — expect 6 failures.**

- [ ] **Step 3: Write `scripts/sws_hook_session_start.py`.**

- [ ] **Step 4: Run tests — expect 6 passes.**

- [ ] **Step 5: Run full suite — expect 101 total.**

- [ ] **Step 6: Commit.**

```
feat(hooks): add SessionStart hook — passport summary + journal-style nudge
```

---

## Task 5 — Hook config wiring

**Files:** `hooks/hooks.json` (new), `hooks/__init__.py` (optional)

Hook config format confirmed by `plugin-dev:hook-development`: plugin hooks live in `hooks/hooks.json`
with the wrapper format `{"description": "...", "hooks": {...}}`. The inner `hooks` object uses
event names as keys with arrays of matcher/hooks objects.

- [ ] **Step 1: Create `hooks/` directory and write `hooks/hooks.json`.**

The `$CLAUDE_PLUGIN_ROOT` env var is available in all command hooks for portable paths.

- [ ] **Step 2: Verify the JSON parses and lists 3 hooks.**

```bash
$DEV_PY -c "
import json
data = json.load(open('hooks/hooks.json'))
h = data['hooks']
print('PreToolUse entries:', len(h.get('PreToolUse', [])))
print('Stop entries:', len(h.get('Stop', [])))
print('SessionStart entries:', len(h.get('SessionStart', [])))
"
```

- [ ] **Step 3: Commit.**

```
feat(hooks): wire hook config in hooks/hooks.json
```

---

## Task 6 — Smoke test + cycle wrap + PR

- [ ] **Step 1: Run full unit test suite.**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -5
```

Expected: `Ran 101 tests in Xs` with `OK`.

- [ ] **Step 2: End-to-end smoke for each hook.**

```bash
mkdir -p /tmp/sws_c5_smoke/claude_memory /tmp/sws_c5_smoke/Manuscript
# write marker, passport stub, create a dummy docx
# pipe events to each hook script; verify side effects
```

Full smoke procedure is in the cycle-05 implementation prompt.

- [ ] **Step 3: Outside-marker smoke — silent no-op.**

```bash
mkdir -p /tmp/sws_c5_outside && cd /tmp/sws_c5_outside
echo '{"tool_name": "Edit", "tool_input": {"file_path": "/tmp/sws_c5_outside/whatever.docx"}}' | \
  $DEV_PY \
  $REPO_ROOT/scripts/sws_hook_pre_edit_backup.py
# expect: exit 0, no output, no backup
```

- [ ] **Step 4: Push branch + open PR.**

PR title: `Cycle #5: three MVP hooks + passport.json schema`
