# SWS Cycle #4 — Auto-resolve safe defaults + post-apply summary

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drop per-conflict prompts from `/sws:init-project`. Auto-resolve all 6 conflict classes with data-loss-safe defaults. Surface the resolutions at the plan-presentation step (the single remaining user review point). Add a "What SWS did with your existing files" section to the post-apply summary.

**Architecture:** Utility layer gains `SAFE_DEFAULTS` dict + `default_resolutions()` function + `defaults` CLI subcommand. Skill prose gains 6 `--c1..--c6` override flags, rewrites Step c (auto-resolve + override merge), extends Step e (auto-resolutions header), and extends Step g (user-file summary).

**Tech stack:** Pure stdlib. No new imports.

**Working directory:** `$REPO_ROOT/`.

**Branch:** `cycle/04-auto-resolve-defaults`.

**Source-of-truth references:**
- Spec: `docs/superpowers/specs/2026-05-12-cycle-04-auto-resolve-defaults-design.md`
- Script under edit: `scripts/sws_init_project.py`
- Tests under edit: `tests/test_init_project.py`
- Skill under edit: `skills/init-project/SKILL.md`

**Reference Python interpreter:** `$DEV_PY`

---

## Task 1 — `default_resolutions` helper + `defaults` CLI subcommand

**Files:** `scripts/sws_init_project.py`, `tests/test_init_project.py`

Add `SAFE_DEFAULTS` dict and `default_resolutions()` function near the existing helpers. Wire a new `defaults` CLI subcommand.

- [ ] **Step 1: Write 9 failing tests in new class `TestDefaultResolutions`.**

```python
class TestDefaultResolutions(unittest.TestCase):
    """Verify safe-default resolution for each conflict class.

    Defaults are data-loss-safe: accept/append/keep/proceed only.
    Destructive options (replace) never appear in defaults.
    """
    def _conflict(self, cls, **kwargs):
        from sws_init_project import Conflict
        defaults = {"path": "x", "suggested_action": "x", "options": []}
        defaults.update(kwargs)
        return Conflict(cls=cls, **defaults)

    def test_C1_defaults_to_accept(self):
        d = sws_init_project.default_resolutions([self._conflict("C1")])
        self.assertEqual(d, {"C1": "accept"})

    def test_C2_defaults_to_accept(self):
        d = sws_init_project.default_resolutions([self._conflict("C2")])
        self.assertEqual(d, {"C2": "accept"})

    def test_C3_defaults_to_accept(self):
        d = sws_init_project.default_resolutions([self._conflict("C3")])
        self.assertEqual(d, {"C3": "accept"})

    def test_C4_defaults_to_append_not_replace(self):
        d = sws_init_project.default_resolutions([self._conflict("C4")])
        self.assertEqual(d, {"C4": "append"})
        self.assertNotEqual(d["C4"], "replace")

    def test_C5_defaults_to_keep_not_replace(self):
        d = sws_init_project.default_resolutions([self._conflict("C5")])
        self.assertEqual(d, {"C5": "keep"})
        self.assertNotEqual(d["C5"], "replace")

    def test_C6_defaults_to_proceed(self):
        d = sws_init_project.default_resolutions([self._conflict("C6")])
        self.assertEqual(d, {"C6": "proceed"})

    def test_all_six_classes_together(self):
        d = sws_init_project.default_resolutions([
            self._conflict("C1"), self._conflict("C2"), self._conflict("C3"),
            self._conflict("C4"), self._conflict("C5"), self._conflict("C6"),
        ])
        self.assertEqual(d, {
            "C1": "accept", "C2": "accept", "C3": "accept",
            "C4": "append", "C5": "keep", "C6": "proceed",
        })

    def test_empty_conflicts_returns_empty_dict(self):
        self.assertEqual(sws_init_project.default_resolutions([]), {})

    def test_unknown_class_is_omitted(self):
        """Forward-compat: a class not in SAFE_DEFAULTS is skipped, not raised."""
        d = sws_init_project.default_resolutions([self._conflict("C99")])
        self.assertEqual(d, {})
```

- [ ] **Step 2: Run tests — expect 9 failures.**

```bash
$DEV_PY -m unittest tests.test_init_project.TestDefaultResolutions -v
```

- [ ] **Step 3: Add `SAFE_DEFAULTS` and `default_resolutions()` to `scripts/sws_init_project.py` near the `_marker_vars` / `_claude_md_vars` helpers.**

```python
# Safe-default resolution per conflict class. Defaults are data-loss-safe:
# - accept = reversible mv/rename ops (C1/C2/C3)
# - append = non-destructive merge (C4)
# - keep = leave user files untouched (C5)
# - proceed = re-init flow loads existing values as defaults (C6)
# Destructive options (replace) NEVER appear as defaults; they require
# explicit user opt-in via CLI flag or NL signal.
SAFE_DEFAULTS = {
    "C1": "accept",
    "C2": "accept",
    "C3": "accept",
    "C4": "append",
    "C5": "keep",
    "C6": "proceed",
}


def default_resolutions(conflicts) -> dict:
    """Return the safe-default resolution dict for a list of Conflicts.

    Keyed by conflict class (C1..C6). Any class not listed in SAFE_DEFAULTS
    is omitted from the result (caller should escalate to prompt).
    """
    return {c.cls: SAFE_DEFAULTS[c.cls] for c in conflicts if c.cls in SAFE_DEFAULTS}
```

- [ ] **Step 4: Add `_cli_defaults` function and wire into `main()`.**

```python
def _cli_defaults(args):
    conflicts_data = json.loads(Path(args.conflicts).read_text())
    conflicts = [Conflict(**c) for c in conflicts_data]
    print(json.dumps(default_resolutions(conflicts), indent=2))
    return 0
```

In `main()`:
```python
p_defaults = sub.add_parser("defaults")
p_defaults.add_argument("--conflicts", required=True)
p_defaults.set_defaults(func=_cli_defaults)
```

- [ ] **Step 5: Run tests — expect 9 passes.**

- [ ] **Step 6: Run full test suite — expect 76 total.**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -5
```

- [ ] **Step 7: Commit.**

```
feat: add default_resolutions helper + defaults CLI subcommand
```

---

## Task 2 — SKILL.md Step a — add CLI override flags + extended NL parse

**Files:** `skills/init-project/SKILL.md`

Add 6 new flags to the named-args list. Add NL-parse override signal documentation. Add validation note.

- [ ] **Step 1: In Step a, extend the named-args list to include `--c1` through `--c6`.**

Find:
```
`--article-type, --language, --format, --target-journal, --target-call, --first-author, --year, --co-authors, --notebooklm`
```

Replace with:
```
`--article-type, --language, --format, --target-journal, --target-call, --first-author, --year, --co-authors, --notebooklm, --c1, --c2, --c3, --c4, --c5, --c6`
```

- [ ] **Step 2: Add an override-flags section after the three-tier waterfall block.**

After the three-tier waterfall text and before the slugify line, insert:

```markdown
**Conflict override flags:** `--c1`..`--c6` each take a string value matching that conflict class's `options` list (e.g., `--c4=replace`, `--c4=append`, `--c4=skip`). These override the safe-default resolution computed in Step c. NL-parse counterparts:
- "overwrite my CLAUDE.md" / "replace existing CLAUDE.md" → c4=replace
- "skip the docx move" / "leave paper.docx where it is" → c1=skip
- "replace my memory" / "overwrite claude_memory" → c5=replace
- "skip the claude_material rename" → c3=skip
- similar patterns apply for c2 and c6

**Override validation:** If the user supplies a value not in the conflict's `options` list (e.g., `--c4=foobar`), abort before calling plan with: `Error: --c4=foobar is not a valid override. Valid options for C4: [replace, append, skip].`

**Override for absent conflict:** If the user supplies `--c4=replace` but no CLAUDE.md exists (C4 not detected), silently ignore the override (no harm, no warning). Accepted v0.1 behavior.
```

- [ ] **Step 3: Commit.**

```
docs(skill): add per-conflict override flags + NL parse signals to Step a
```

---

## Task 3 — SKILL.md Step b/c — auto-resolve defaults; remove per-conflict prompts

**Files:** `skills/init-project/SKILL.md`

Rewrite Step c entirely. Add the `defaults` call to Step b.

- [ ] **Step 1: In Step b, add the `defaults` call after the scan.**

In the Step b block, after the `scan --root .` call and before the "If empty, jump straight to step d" sentence, insert:

```markdown
If conflicts were detected, compute safe-default resolutions:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sws_init_project.py" defaults \
  --conflicts /tmp/sws_conflicts.json > /tmp/sws_defaults.json
```
```

- [ ] **Step 2: Rewrite Step c entirely.**

Replace the entire Step c body (everything between `## Step c` heading and `## Step d` heading) with:

```markdown
## Step c — Apply safe defaults + user overrides

For each detected conflict, SWS auto-resolves with a data-loss-safe default. The defaults table (single source of truth: `default_resolutions()` in `scripts/sws_init_project.py`):

| Conflict | Default | What it does |
|---|---|---|
| C1 root `*.docx` | `accept` | Move to `Manuscript/<filename>` (reversible) |
| C2 loose Figures | `accept` | Move loose figs to `Figures/main/` (reversible) |
| C3 `claude_material/` | `accept` | Rename to `scratch/` (reversible) |
| C4 existing CLAUDE.md | `append` | Preserve verbatim; append marker-delimited SWS-managed section (idempotent on re-run) |
| C5 existing `claude_memory/` | `keep` | Leave `claude_memory/` untouched; SWS does NOT write `MEMORY.md` or `passport.json` |
| C6 existing marker | `proceed` | Re-init flow: load existing values as defaults; write merged marker |

If the user passed any `--c1`..`--c6` flag in Step a OR if NL parse picked up an override signal, merge those overrides on top of the defaults:

```bash
# Defaults from step b are at /tmp/sws_defaults.json. Apply overrides if any:
python3 -c "
import json, sys
defaults = json.load(open('/tmp/sws_defaults.json'))
overrides = {}  # populate from Step-a args / NL parse
defaults.update(overrides)
json.dump(defaults, open('/tmp/sws_resolutions.json', 'w'))
"
```

**Validation:** Before writing `/tmp/sws_resolutions.json`, validate each override against the corresponding conflict's `options` list (from the scan output). If a value is invalid, abort with:

```
Error: --c4=foobar is not a valid override. Valid options for C4: [replace, append, skip].
```

**Destructive overrides:** `c4=replace` and `c5=replace` destroy user content. The skill MUST NOT default to these. They only fire when the user explicitly passed the flag or NL parse picked up an unambiguous signal. If the signal is ambiguous, fall back to the safe default and note it in the post-apply summary.

No per-conflict prompts. The plan-presentation step (Step e) gives the user the single consolidated review.

Build a `resolutions` dict at `/tmp/sws_resolutions.json` mapping `cls` → chosen resolution.
```

- [ ] **Step 3: Commit.**

```
docs(skill): replace per-conflict prompts with auto-resolved safe defaults
```

---

## Task 4 — SKILL.md Step e + Step g — show defaults + post-apply summary

**Files:** `skills/init-project/SKILL.md`

Prepend auto-resolutions header in Step e. Add user-file summary section in Step g.

- [ ] **Step 1: In Step e, add auto-resolutions header before the op list.**

After the `## Step e — Plan presentation` heading and before the "Display the plan" text, insert:

```markdown
Before showing the op list, surface what was auto-resolved:

```
Detected N conflicts; auto-resolved with safe defaults:
  C4=append (preserves your CLAUDE.md; appends SWS-managed section)
  C1=accept (moves paper.docx → Manuscript/paper.docx)
  C3=accept (renames claude_material/ → scratch/)

[If any user-supplied overrides were applied:]
User-supplied overrides:
  C4=replace (will overwrite your CLAUDE.md — confirm in plan below)
```
```

- [ ] **Step 2: In Step g, replace/extend the summary block with a user-file handling section.**

In Step g, replace the existing summary `Print summary:` code block with:

```markdown
Print summary:

```
Bootstrapped <short_handle> at <cwd>.

What SWS did with your existing files:
  - paper.docx → moved to Manuscript/paper.docx (C1=accept)
  - claude_material/ → renamed to scratch/ (C3=accept)
  - CLAUDE.md → preserved verbatim; SWS-managed section appended at end (C4=append)
  [If C5=keep:]
  - claude_memory/ → preserved verbatim; SWS did not write MEMORY.md or passport.json (C5=keep)
  [If no user files were touched, omit this section entirely.]

What SWS created fresh:
  N files (full topology: Manuscript/, Figures/, Tables/, SI/, Zenodo_db/, scratch/, refs/, claude_memory/)
  .sws-project.local.md (marker; canonical project metadata)
  [If C4=replace was used:]  CLAUDE.md (SWS template; your previous CLAUDE.md was overwritten)
  [If C5=replace was used:]  claude_memory/MEMORY.md, claude_memory/passport.json

Configuration: article_type=<...>, language=<...>, format=<...>
Target: target_journal=<...> | target_call=<...>

Next steps (suggested):
  - Run /sws:resolve-journal-style <slug> to cache the venue style overlay (in a later cycle).
  - Drop your manuscript at Manuscript/<short_handle>.docx (or .tex).
  - Start drafting (ships in a later cycle).
```
```

- [ ] **Step 3: Commit.**

```
docs(skill): surface auto-resolutions in plan presentation + user-file summary post-apply
```

---

## Task 5 — Smoke test + cycle wrap + PR

- [ ] **Step 1: Run full unit test suite.**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -5
```

Expected: `Ran 76 tests in Xs` with `OK`.

- [ ] **Step 2: Smoke-test the `defaults` CLI subcommand.**

```bash
set -e
mkdir -p /tmp/sws_c4_smoke
touch /tmp/sws_c4_smoke/paper.docx
mkdir -p /tmp/sws_c4_smoke/claude_material
echo "# user notes" > /tmp/sws_c4_smoke/CLAUDE.md

$DEV_PY \
  $REPO_ROOT/scripts/sws_init_project.py \
  scan --root /tmp/sws_c4_smoke > /tmp/sws_c4_conflicts.json

cat /tmp/sws_c4_conflicts.json

$DEV_PY \
  $REPO_ROOT/scripts/sws_init_project.py \
  defaults --conflicts /tmp/sws_c4_conflicts.json
```

Expected output (sort-order-agnostic):
```json
{
  "C1": "accept",
  "C3": "accept",
  "C4": "append"
}
```

- [ ] **Step 3: Full E2E flow — scan → defaults → plan → apply.**

Expected verifications:
- Defaults output contains exactly C1, C3, C4 keys with accept/accept/append.
- After apply: `# user notes` preserved in CLAUDE.md + SWS-managed section appended.
- `Manuscript/paper.docx` exists.
- `scratch/` exists (from claude_material rename).
- Full topology created.

- [ ] **Step 4: Push branch + open PR.**

PR title: `Cycle #4: auto-resolve safe defaults + post-apply summary`
