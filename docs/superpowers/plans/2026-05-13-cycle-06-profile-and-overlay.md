# SWS Cycle #6 — Profile system + journal-style/call-rules overlay layer

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the v0.1 profile + overlay layer: 9 profile files, the 3-layer resolver (schema < profile < overlay), 3 new slash commands (`/sws:set-profile`, `/sws:resolve-journal-style`, `/sws:resolve-call-rules`) + 1 supporting (`/sws:install-deps`), per-paper `.venv/` discipline, and the SessionStart missing-profile nudge.

**Architecture:** `scripts/resolve_overlay.py` is the single source of truth for the 3-layer merge; all agents shell out via `scripts/agent_prelude.sh` and never walk the layers themselves. Profiles live in the plugin repo at `profiles/<id>.md`; overlays are written by the user paper at `<paper>/Manuscript/_journal-style/<slug>.md` and `<paper>/Manuscript/_call/<slug>.md`. Init-project (extended) creates `<paper>/.venv/` from `requirements/sws-deps.txt`; all plugin Python invokes via `$PAPER_ROOT/.venv/bin/python` through `scripts/sws_python.sh` — never the dev's mamba env.

**Tech stack:** Python 3.9+. PyYAML for overlay synthesis (in `.venv/`). Pure stdlib for hook utilities. Bash for thin wrappers. Sonnet subagent for guide-for-authors → frontmatter synthesis.

**Working directory:** `$REPO_ROOT/`.

**Branch:** `cycle/06-profile-and-overlay` (created from main after cycle #5 merge).

**Source-of-truth references:**
- Spec: `docs/superpowers/specs/2026-05-13-cycle-06-profile-and-overlay-design.md` (NOTE: spec was locked 2026-05-12; spec filename uses the lock date)
- Architecture sketch §4: `docs/superpowers/specs/2026-05-08-architecture-sketch-design.md`
- Cycle #5 patterns: `tests/test_sws_hook_utils.py`, `scripts/sws_hook_utils.py`
- Agent roster: `claude_memory/project_roster_v0.1.md`

**Spec corrections to honor in every task:**
- D19/D20: NO `dev-env name` references in any committed plugin file (scripts/, skills/, profiles/, hooks/). The dev's mamba env is only for running the dev test suite locally; do not name it in any artifact that ships to users.
- D17/D18: Overlay key present (including explicit `null`) wins. Synthesizer asks user-confirm on every field where source is silent.
- D14: List-typed overlay fields replace profile lists entirely.
- D15/D16: Re-resolve archives the prior overlay to `_archive/<slug>-YYYYMMDD-HHMMSS.md` and prints a diff summary.

**Reference Python interpreter (for running the dev test suite ONLY — never named in plugin code):** `$DEV_PY`. Substitute `$DEV_PY` for it in commands below if you prefer.

---

## Task 1 — Branch + plan-tracking commit

**Files:** none modified yet; this task creates the branch and commits the plan.

- [ ] **Step 1: Confirm cycle #5 has merged on main.**

```bash
git fetch origin
gh pr view 8 --json state,mergedAt
```

Expected: `"state": "MERGED"`.

- [ ] **Step 2: Branch from main.**

```bash
git checkout main
git pull origin main
git checkout -b cycle/06-profile-and-overlay
```

- [ ] **Step 3: Stage and commit the spec + plan (already on disk from brainstorming).**

```bash
git add docs/superpowers/specs/2026-05-13-cycle-06-profile-and-overlay-design.md \
        docs/superpowers/plans/2026-05-13-cycle-06-profile-and-overlay.md \
        claude_memory/project_v02_backlog.md
git commit -m "docs(cycle-06): spec + plan + v0.2 backlog updates"
```

---

## Task 2 — Requirements file + venv wrapper + `/sws:install-deps` skill

**Files:**
- Create: `requirements/sws-deps.txt`
- Create: `scripts/sws_python.sh`
- Create: `skills/install-deps/SKILL.md`
- Test: `tests/test_sws_python_wrapper.py`

- [ ] **Step 1: Write `requirements/sws-deps.txt`.**

```
# SWS v0.1 default Python deps for <paper>/.venv/.
# Installed by /sws:install-deps (called by /sws:init-project on first run).
PyYAML>=6.0
python-docx>=1.1
pdfplumber>=0.10
lxml>=5.0
openpyxl>=3.1
pytest>=8.0
```

- [ ] **Step 2: Write `scripts/sws_python.sh`.**

```bash
#!/usr/bin/env bash
# Resolves the per-paper Python interpreter at <paper>/.venv/bin/python.
# Usage: sws_python.sh <paper-root> <python-script> [args...]
# Exits 2 with one-line instruction if venv is missing.
set -eu
PAPER_ROOT="${1:?usage: sws_python.sh <paper-root> <script> [args...]}"
shift
PY="$PAPER_ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
    echo "sws: per-paper venv not found at $PY — run /sws:install-deps to bootstrap deps" >&2
    exit 2
fi
exec "$PY" "$@"
```

- [ ] **Step 3: `chmod +x scripts/sws_python.sh`.**

- [ ] **Step 4: Write failing test in `tests/test_sws_python_wrapper.py`.**

```python
import subprocess, tempfile, os, pathlib, unittest

WRAPPER = pathlib.Path(__file__).parent.parent / "scripts" / "sws_python.sh"

class TestSwsPythonWrapper(unittest.TestCase):
    def test_exits_2_when_venv_missing(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([str(WRAPPER), d, "-c", "print(1)"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("/sws:install-deps", r.stderr)

    def test_invokes_python_when_venv_present(self):
        with tempfile.TemporaryDirectory() as d:
            venv_bin = pathlib.Path(d) / ".venv" / "bin"
            venv_bin.mkdir(parents=True)
            py = venv_bin / "python"
            py.write_text('#!/usr/bin/env bash\necho "OK $@"\n')
            py.chmod(0o755)
            r = subprocess.run([str(WRAPPER), d, "-c", "print(1)"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            self.assertIn("OK", r.stdout)
```

- [ ] **Step 5: Run tests — expect 2 failures (then 2 passes after the wrapper file is in place).**

```bash
$DEV_PY -m unittest tests.test_sws_python_wrapper -v
```

- [ ] **Step 6: Write `skills/install-deps/SKILL.md`.**

Document the slash command: `/sws:install-deps` reads `${CLAUDE_PLUGIN_ROOT}/requirements/sws-deps.txt`, creates `<paper>/.venv/` if absent using the system `python3 -m venv`, runs `<paper>/.venv/bin/pip install -r ${CLAUDE_PLUGIN_ROOT}/requirements/sws-deps.txt`. Marker check guards against running outside an SWS project. If `marker.format == "latex"`, also install `pylatexenc>=2.10`.

Skill steps use `${CLAUDE_PLUGIN_ROOT}` for plugin paths and `$PAPER_ROOT` (resolved from the marker) for paper paths. No `dev-env name` references.

- [ ] **Step 7: Commit.**

```
feat(deps): per-paper venv discipline — sws_python.sh + install-deps skill + sws-deps.txt
```

---

## Task 3 — Extend `sws_hook_utils.py` with marker-write helper

**Files:**
- Modify: `scripts/sws_hook_utils.py` (add `write_marker_field`)
- Modify: `tests/test_sws_hook_utils.py` (add 4 tests)

- [ ] **Step 1: Add 4 failing tests to `tests/test_sws_hook_utils.py`.**

```python
class TestWriteMarkerField(unittest.TestCase):
    def test_writes_new_field_to_frontmatter(self): ...
    def test_overwrites_existing_field(self): ...
    def test_preserves_other_fields_and_body(self): ...
    def test_creates_frontmatter_block_if_absent(self): ...
```

Each test writes a temp marker, calls `write_marker_field(path, key, value)`, asserts on the resulting file.

- [ ] **Step 2: Run tests — expect 4 failures.**

```bash
$DEV_PY -m unittest tests.test_sws_hook_utils -v
```

- [ ] **Step 3: Implement `write_marker_field(path: Path, key: str, value: str|bool|int|None) -> None` in `sws_hook_utils.py`.**

Behavior: open the marker, locate the leading `---` … `---` block, parse to a dict using existing `parse_marker`, set `dict[key] = value`, re-render the block back as `key: value` lines (preserving line order where possible; appending new keys at the end), write the file atomically (write to `<path>.tmp` then `os.replace`).

For value serialization: `None → null`, `True → true`, `False → false`, strings → bare (no quoting needed since marker is line-scoped, see cycle #5 parser).

- [ ] **Step 4: Run tests — expect 4 passes; full suite stays green (~104 tests).**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -5
```

- [ ] **Step 5: Commit.**

```
feat(hooks): add write_marker_field to sws_hook_utils for profile mutations
```

---

## Task 4 — `scripts/resolve_overlay.py` core merge logic (TDD)

**Files:**
- Create: `scripts/resolve_overlay.py`
- Create: `tests/test_resolve_overlay.py`
- Create: `tests/fixtures/profiles/` (mirrors plugin's `profiles/` with 1 fixture each)
- Create: `tests/fixtures/overlays/` (4–6 fixture overlays)

This task implements the merge function only (no skills, no agent gating yet).

- [ ] **Step 1: Write fixtures.**

`tests/fixtures/profiles/full-article.md` and `communication.md` — minimal but valid, both with `sections`, `ref_cap`, `agents_inactive` set.

`tests/fixtures/overlays/chembiochem-replace-sections.md` — has `sections` list (replaces profile list per D14).
`tests/fixtures/overlays/jacs-drops-refcap.md` — sets `ref_cap: null` explicitly (D17 drop).
`tests/fixtures/overlays/empty.md` — frontmatter present but with no override fields.
`tests/fixtures/overlays/malformed.md` — invalid YAML (for E8 exercise).

- [ ] **Step 2: Write the first 12 failing tests in `tests/test_resolve_overlay.py`.**

```python
import json, subprocess, pathlib, unittest, shutil, tempfile

RESOLVER = pathlib.Path(__file__).parent.parent / "scripts" / "resolve_overlay.py"
FIXTURES = pathlib.Path(__file__).parent / "fixtures"

def run_resolver(paper_root, *args):
    r = subprocess.run(["python", str(RESOLVER), "--paper", str(paper_root), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr

def make_paper(d: pathlib.Path, marker_lines: list[str], overlays: dict | None = None):
    (d / ".sws-project.local.md").write_text("---\n" + "\n".join(marker_lines) + "\n---\n")
    if overlays:
        for path, content in overlays.items():
            full = d / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)

class TestResolverProfileLayer(unittest.TestCase):
    def test_emits_profile_set_false_for_null_profile(self): ...
    def test_emits_profile_set_true_for_valid_profile(self): ...
    def test_exits_4_when_marker_missing(self): ...
    def test_exits_2_when_profile_file_missing(self): ...

class TestResolverScalarMerge(unittest.TestCase):
    def test_profile_scalar_used_when_overlay_omits_field(self): ...
    def test_overlay_scalar_overrides_profile(self): ...
    def test_overlay_explicit_null_drops_profile_value(self): ...  # D17

class TestResolverListMerge(unittest.TestCase):
    def test_overlay_sections_replaces_profile_sections(self): ...  # D14
    def test_overlay_empty_sections_replaces_profile(self): ...  # D14 corner case
    def test_overlay_absent_sections_inherits_profile(self): ...

class TestResolverDiagnostics(unittest.TestCase):
    def test_missing_journal_overlay_is_warning_not_error(self): ...
    def test_malformed_overlay_exits_3(self): ...
```

- [ ] **Step 3: Run tests — expect 12 failures.**

- [ ] **Step 4: Implement `resolve_overlay.py` core.**

Structure (single file, no submodules):

```python
#!/usr/bin/env python3
"""Resolve the 3-layer profile/overlay contract for SWS agents.

Layers (low → high precedence): schema_defaults < profile < overlay.
List-typed fields are REPLACE (overlay wins entirely if it sets them).
Scalar fields: explicit null in overlay drops the profile value (D17).
"""

import argparse, json, sys, yaml
from pathlib import Path

SCHEMA_DEFAULTS = {
    "inherits": None,
    "ref_cap": None, "word_total": None, "figures_max": None, "tables_max": None,
    "abstract_style": "unstructured",
    "disclosure_required": False, "cover_letter_required": False,
    "supplementary_allowed": True, "refs_style": "numbered",
    "agents_active": [], "agents_inactive": [],
}

LIST_FIELDS = {"sections", "agents_active", "agents_inactive"}

def parse_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"): return {}
    end = text.find("---", 3)
    if end < 0: return {}
    return yaml.safe_load(text[3:end]) or {}

def merge(base: dict, overlay: dict) -> dict:
    """overlay wins per-key; lists replace; overlay key present (incl null) wins."""
    result = dict(base)
    for k, v in overlay.items():
        if k in LIST_FIELDS:
            result[k] = v  # replace (D14)
        else:
            result[k] = v  # last writer wins (incl explicit null per D17)
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--agent", default=None)
    args = ap.parse_args()

    marker = args.paper / ".sws-project.local.md"
    if not marker.exists():
        print(json.dumps({"error": "marker not found"}), file=sys.stderr)
        sys.exit(4)

    m = parse_frontmatter(marker)
    profile_id = m.get("profile")
    if not profile_id:
        print(json.dumps({"profile_set": False, "profile_id": None,
                          "profile_path": None, "journal_overlay_path": None,
                          "call_overlay_path": None, "resolved_frontmatter": None,
                          "should_run": None,
                          "diagnostics": {"warnings": ["no profile set"]}}))
        sys.exit(0)

    plugin_root = Path(__file__).resolve().parent.parent
    profile_path = plugin_root / "profiles" / f"{profile_id}.md"
    if not profile_path.exists():
        print(json.dumps({"error": f"unknown profile: {profile_id}"}), file=sys.stderr)
        sys.exit(2)

    profile_fm = parse_frontmatter(profile_path)

    # journal overlay
    journal_slug = m.get("journal")
    journal_overlay_path = None
    journal_fm = {}
    if journal_slug:
        p = args.paper / "Manuscript" / "_journal-style" / f"{journal_slug}.md"
        if p.exists():
            journal_overlay_path = str(p)
            journal_fm = parse_frontmatter(p)

    # call overlay
    call_slug = m.get("call")
    call_overlay_path = None
    call_fm = {}
    if call_slug:
        p = args.paper / "Manuscript" / "_call" / f"{call_slug}.md"
        if p.exists():
            call_overlay_path = str(p)
            call_fm = parse_frontmatter(p)

    resolved = merge(merge(merge(SCHEMA_DEFAULTS, profile_fm), journal_fm), call_fm)

    should_run = None
    if args.agent:
        active = resolved.get("agents_active") or []
        inactive = resolved.get("agents_inactive") or []
        should_run = (args.agent not in inactive) and (
            not active or args.agent in active
        )

    diagnostics = {"warnings": [], "missing_journal_overlay": journal_slug and not journal_overlay_path,
                   "missing_call_overlay": call_slug and not call_overlay_path}

    print(json.dumps({
        "profile_set": True, "profile_id": profile_id,
        "profile_path": str(profile_path),
        "journal_overlay_path": journal_overlay_path,
        "call_overlay_path": call_overlay_path,
        "resolved_frontmatter": resolved,
        "should_run": should_run,
        "diagnostics": diagnostics,
    }))

if __name__ == "__main__":
    try: main()
    except yaml.YAMLError as e:
        print(json.dumps({"error": "malformed YAML", "details": str(e)}), file=sys.stderr)
        sys.exit(3)
```

- [ ] **Step 5: Run tests — expect 12 passes.**

```bash
$DEV_PY -m unittest tests.test_resolve_overlay -v
```

- [ ] **Step 6: Commit.**

```
feat(resolver): add resolve_overlay.py core 3-layer merge logic
```

---

## Task 5 — Resolver edge cases + `should_run` matrix tests

**Files:**
- Create: `tests/fixtures/agent_activation_matrix.yaml`
- Modify: `tests/test_resolve_overlay.py` (add ~30 tests)

- [ ] **Step 1: Write `tests/fixtures/agent_activation_matrix.yaml`.**

Mirrors the spec's `agent_activation_matrix.per_profile_inactive`. One key per profile, list of inactive agent ids.

```yaml
full-article: [proposal-budget-helper, proposal-compliance-helper]
communication: [proposal-budget-helper, proposal-compliance-helper]
perspective: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator, plot-maker]
review-paper: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator]
mini-review: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator]
editorial: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator, plot-maker, caption-writer]
methodological-paper: [proposal-budget-helper, proposal-compliance-helper]
commentary-reply: [proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator]
funding-proposal: [response-to-reviewers]
```

- [ ] **Step 2: Add 30 failing tests covering the should_run matrix (9 profiles × 3–4 representative agents each).**

```python
import yaml

ROSTER = ["brainstormer","planner","outline-architect","style-calibrator",
          "literature-searcher","drafter","methods-writer","caption-writer",
          "reviser","humanizer","style-enforcer","consistency-checker",
          "peer-reviewer","code-reviewer","claim-verifier","plagiarism-screener",
          "plot-maker","data-curator","bibliography-curator","cover-letter-writer",
          "response-to-reviewers","nlm-librarian","proposal-budget-helper",
          "proposal-compliance-helper"]

class TestShouldRunMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = yaml.safe_load(open(FIXTURES / "agent_activation_matrix.yaml"))

    def test_proposal_helpers_inactive_in_full_article(self):
        rc, out, _ = run_with(profile="full-article", agent="proposal-budget-helper")
        self.assertFalse(json.loads(out)["should_run"])

    def test_drafter_active_everywhere(self):
        for profile in self.matrix:
            rc, out, _ = run_with(profile=profile, agent="drafter")
            self.assertTrue(json.loads(out)["should_run"],
                            f"drafter should be active in {profile}")
    # … 28 more
```

- [ ] **Step 3: Run tests — expect 30 failures.**

- [ ] **Step 4: Verify each of the 9 profile files (yet to be written in Task 7) will produce the correct `should_run` outputs by adapting the test helper to use fixture profiles that match the matrix.**

If the resolver core (Task 4) is correct, no resolver changes needed — only the fixture profiles must reflect the matrix.

- [ ] **Step 5: Add 8 more edge-case tests (E1–E10 from spec; subset that doesn't require skills).**

```python
class TestEdgeCases(unittest.TestCase):
    def test_E1_unknown_profile_name_in_marker_exits_2(self): ...
    def test_E6_overlay_present_but_profile_null(self): ...
    def test_E10_overlay_omits_activation_lists_inherits_profile(self): ...
    # …
```

- [ ] **Step 6: Run all resolver tests — expect ~50 passes.**

- [ ] **Step 7: Commit.**

```
test(resolver): add should_run matrix + edge case coverage (50 resolver tests)
```

---

## Task 6 — `scripts/agent_prelude.sh` shared helper

**Files:**
- Create: `scripts/agent_prelude.sh`
- Create: `tests/test_agent_prelude.py`

- [ ] **Step 1: Write `scripts/agent_prelude.sh`.**

```bash
#!/usr/bin/env bash
# Agent prelude: resolves the 3-layer profile/overlay contract and exports
# RESOLVED_* env vars. Source this from any agent prompt's first step.
# Usage: source "${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh" <agent-id>
set -eu
AGENT_ID="${1:?usage: source agent_prelude.sh <agent-id>}"
: "${PAPER_ROOT:?PAPER_ROOT must be set}"

JSON="$(
  "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
    "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
    --paper "$PAPER_ROOT" --agent "$AGENT_ID"
)"

export RESOLVED_OK=1
if ! echo "$JSON" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('profile_set') else 1)"; then
    echo "sws: no profile set — run /sws:set-profile <name>. Agent ${AGENT_ID} exiting." >&2
    export RESOLVED_OK=0
    return 0  # don't kill the shell; agent checks RESOLVED_OK
fi

if ! echo "$JSON" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('should_run') else 1)"; then
    echo "sws: agent ${AGENT_ID} not active for resolved profile." >&2
    export RESOLVED_OK=0
    return 0
fi

# Expose useful fields as RESOLVED_*
eval "$(echo "$JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
fm = d.get('resolved_frontmatter') or {}
for k in ['ref_cap','word_total','figures_max','tables_max','abstract_style',
          'disclosure_required','cover_letter_required','refs_style']:
    v = fm.get(k)
    print(f'export RESOLVED_{k.upper()}={\"null\" if v is None else v}')
print(f'export RESOLVED_PROFILE_ID={d.get(\"profile_id\")}')
")"
```

- [ ] **Step 2: `chmod +x scripts/agent_prelude.sh`.**

- [ ] **Step 3: Write 5 failing tests in `tests/test_agent_prelude.py`.**

```python
class TestAgentPrelude(unittest.TestCase):
    def test_RESOLVED_OK_0_when_no_profile(self): ...
    def test_RESOLVED_OK_0_when_agent_inactive(self): ...
    def test_RESOLVED_OK_1_and_envvars_set_when_active(self): ...
    def test_RESOLVED_REF_CAP_reflects_overlay(self): ...
    def test_RESOLVED_PROFILE_ID_reflects_marker(self): ...
```

Each test sources the prelude in a `bash -c "source ...; env"` subprocess and greps the output.

- [ ] **Step 4: Run tests — iterate to passes.**

- [ ] **Step 5: Commit.**

```
feat(agents): add agent_prelude.sh shared resolver wrapper
```

---

## Task 7 — Write the 9 profile files

**Files:**
- Create: `profiles/full-article.md`
- Create: `profiles/communication.md`
- Create: `profiles/perspective.md`
- Create: `profiles/review-paper.md`
- Create: `profiles/mini-review.md`
- Create: `profiles/editorial.md`
- Create: `profiles/methodological-paper.md`
- Create: `profiles/commentary-reply.md`
- Create: `profiles/funding-proposal.md`
- Create: `tests/test_profiles.py`

- [ ] **Step 1: Write `profiles/full-article.md`.**

```markdown
---
profile: full-article
inherits: null
sections:
  - { id: abstract, label: Abstract, word_limit: 250, required: true }
  - { id: introduction, label: Introduction, word_limit: null, required: true }
  - { id: results, label: Results and Discussion, word_limit: null, required: true }
  - { id: experimental, label: Experimental Section, word_limit: null, required: true }
  - { id: conclusion, label: Conclusions, word_limit: 300, required: true }
  - { id: references, label: References, word_limit: null, required: true }
ref_cap: 80
word_total: null
figures_max: null
tables_max: null
abstract_style: structured
disclosure_required: true
cover_letter_required: true
supplementary_allowed: true
refs_style: numbered
agents_active: [brainstormer, planner, outline-architect, style-calibrator,
                literature-searcher, drafter, methods-writer, caption-writer,
                reviser, humanizer, style-enforcer, consistency-checker,
                peer-reviewer, code-reviewer, claim-verifier, plagiarism-screener,
                plot-maker, data-curator, bibliography-curator, cover-letter-writer,
                response-to-reviewers, nlm-librarian]
agents_inactive: [proposal-budget-helper, proposal-compliance-helper]
---

# Full-article profile

**Audience:** specialist readers in the field; peer reviewers; editors.
**Voice:** measured, evidence-led, no first-person plural unless the field convention allows it.
**Structure discipline:** every claim in Results must trace to a figure, table, or cited prior work.
**Banned patterns:** none beyond the global AI-tells list (`references/ai-writing-tells.md` once that lands).

Drafter notes: Results-and-Discussion sections are tighter than Results-only because every interpretation must sit next to its evidence. Conclusion is short (≤300 words) — synthesis only, no new claims.
```

- [ ] **Step 2: Write `profiles/communication.md`.**

```markdown
---
profile: communication
inherits: null
sections:
  - { id: abstract, label: Abstract, word_limit: 150, required: true }
  - { id: body, label: Communication, word_limit: 3500, required: true }
  - { id: experimental, label: Experimental Section, word_limit: null, required: true }
  - { id: references, label: References, word_limit: null, required: true }
ref_cap: 40
word_total: 3500
figures_max: 4
tables_max: 2
abstract_style: unstructured
disclosure_required: true
cover_letter_required: true
supplementary_allowed: true
refs_style: numbered
agents_active: [brainstormer, planner, outline-architect, style-calibrator,
                literature-searcher, drafter, methods-writer, caption-writer,
                reviser, humanizer, style-enforcer, consistency-checker,
                peer-reviewer, code-reviewer, claim-verifier, plagiarism-screener,
                plot-maker, data-curator, bibliography-curator, cover-letter-writer,
                response-to-reviewers, nlm-librarian]
agents_inactive: [proposal-budget-helper, proposal-compliance-helper]
---

# Communication profile

**Audience:** broad chemistry / chem-bio audience; the headline result must register in the first paragraph.
**Voice:** punchy, present-tense, opinion-restrained.
**Structure discipline:** lead with the result, not the motivation. The opening sentence carries the punchline.
**Banned patterns:** wind-up paragraphs ("Over the past decade, X has been …"); paragraph-long methods recaps in the body.

Drafter notes: 3500-word cap forces ruthless trimming. Methods section is brief — depth lives in Supplementary.
```

- [ ] **Step 3: Write `profiles/perspective.md`, `review-paper.md`, `mini-review.md`, `editorial.md`, `methodological-paper.md`, `commentary-reply.md`, `funding-proposal.md`.**

Each follows the same shape. Per-profile distinctions (drawn from spec's activation matrix and the user's domain expectations):

- **perspective**: opinion-led; long body sections; agents_inactive includes methods-writer, data-curator, plot-maker. Sections: `[abstract, introduction, body, outlook, references]` with `body` word_limit 6000.
- **review-paper**: comprehensive; ref_cap: 200; sections `[abstract, introduction, body, outlook, references]`; agents_inactive: methods-writer, data-curator (no original data).
- **mini-review**: shorter review; ref_cap: 100; word_total: 5000.
- **editorial**: very short opinion; word_total: 1500; ref_cap: 20; agents_inactive includes methods-writer, data-curator, plot-maker, caption-writer.
- **methodological-paper**: methods-heavy; sections `[abstract, introduction, results, experimental, validation, conclusion, references]`; experimental section uncapped; ref_cap: 80.
- **commentary-reply**: response to a published paper; word_total: 2000; ref_cap: 30; agents_inactive: methods-writer, data-curator.
- **funding-proposal**: proposal-specific; sections vary by call but default to `[summary, state-of-the-art, objectives, methodology, workplan, impact, references]`; agents_active includes `proposal-budget-helper` and `proposal-compliance-helper`; agents_inactive: `response-to-reviewers`.

- [ ] **Step 4: Write `tests/test_profiles.py` — 9 tests, one per profile.**

```python
class TestProfiles(unittest.TestCase):
    def test_full_article_parses_and_has_required_fields(self): ...
    # … 8 more, all asserting:
    # - frontmatter parses
    # - `profile` field matches filename
    # - sections list non-empty
    # - agents_active is a subset of the 24-agent roster
    # - agents_inactive is disjoint from agents_active
```

- [ ] **Step 5: Run tests — expect 9 passes.**

- [ ] **Step 6: Commit.**

```
feat(profiles): add 9 v0.1 profile files with full frontmatter + drafter body
```

---

## Task 8 — `/sws:set-profile` skill

**Files:**
- Create: `skills/set-profile/SKILL.md`
- Create: `tests/test_set_profile.py`
- Test fixture: `tests/fixtures/papers/dummy_paper/.sws-project.local.md`

- [ ] **Step 1: Write `skills/set-profile/SKILL.md`.**

Structure (follows cycle #2's SKILL.md pattern):

```markdown
---
name: set-profile
description: Set or change the writing profile for the current SWS paper. Validates against the 9 locked ids. Updates .sws-project.local.md.
---

# /sws:set-profile

## Usage

`/sws:set-profile <name>`

where `<name>` is one of: full-article, communication, perspective, review-paper, mini-review, editorial, methodological-paper, commentary-reply, funding-proposal.

## Steps

1. Resolve `$PAPER_ROOT` — current working directory must contain `.sws-project.local.md`. If absent, print "not an SWS project" and exit.
2. Validate `<name>` is in the 9 locked ids. Read the list from `${CLAUDE_PLUGIN_ROOT}/profiles/` (every `*.md` filename minus extension).
3. Read current `profile:` value from marker via `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" -c "from sws_hook_utils import parse_marker; ..."`.
4. Write the new value via `write_marker_field`.
5. Print one-line confirmation: `profile: <new> (was: <old>)`.
```

- [ ] **Step 2: Write 5 failing tests in `tests/test_set_profile.py`.**

```python
class TestSetProfile(unittest.TestCase):
    def test_valid_name_rewrites_marker(self): ...
    def test_invalid_name_rejected(self): ...
    def test_missing_marker_clear_error(self): ...
    def test_overlays_untouched(self): ...  # D11 / Q12=A
    def test_one_line_confirmation_printed(self): ...
```

Implement via a Python helper (`scripts/sws_set_profile.py`) that the skill calls — easier to test than the SKILL.md prose directly.

- [ ] **Step 3: Implement `scripts/sws_set_profile.py`.**

```python
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from sws_hook_utils import parse_marker, write_marker_field

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--name", required=True)
    args = ap.parse_args()
    valid = sorted(p.stem for p in PROFILES_DIR.glob("*.md"))
    if args.name not in valid:
        print(f"error: '{args.name}' is not a valid profile. Valid: {', '.join(valid)}",
              file=sys.stderr)
        sys.exit(1)
    marker = args.paper / ".sws-project.local.md"
    if not marker.exists():
        print("error: not an SWS project (no .sws-project.local.md found)", file=sys.stderr)
        sys.exit(2)
    old = parse_marker(marker).get("profile")
    write_marker_field(marker, "profile", args.name)
    print(f"profile: {args.name} (was: {old})")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests — expect 5 passes.**

- [ ] **Step 5: Commit.**

```
feat(skills): add /sws:set-profile skill + sws_set_profile.py helper
```

---

## Task 9 — `/sws:resolve-journal-style` skill

**Files:**
- Create: `skills/resolve-journal-style/SKILL.md`
- Create: `scripts/sws_resolve_journal_style.py`
- Create: `references/journal-url-map.yaml` (the 8 initial slugs)
- Create: `tests/test_resolve_journal_style.py`
- Test fixtures: `tests/fixtures/journal_pages/<slug>.html` × 3 (chembiochem, jacs, nat-comm)

- [ ] **Step 1: Write `references/journal-url-map.yaml`.**

```yaml
chembiochem: https://chemistry-europe.onlinelibrary.wiley.com/journal/14397633/homepage/2243_authorguidelines.html
jacs: https://pubs.acs.org/page/jacsat/submission/authors.html
chem-sci: https://www.rsc.org/journals-books-databases/author-and-reviewer-hub/authors-information/prepare-and-format/?journalName=Chemical%20Science
ang-chem: https://onlinelibrary.wiley.com/page/journal/15213773/homepage/2002_authorguidelines.html
nat-comm: https://www.nature.com/ncomms/submission-guidelines
j-chem-inf-mod: https://pubs.acs.org/page/jcisd8/submission/authors.html
biochem-and-biophys-acta: https://www.elsevier.com/journals/biochimica-et-biophysica-acta-general-subjects/0304-4165/guide-for-authors
chemistry-european: https://chemistry-europe.onlinelibrary.wiley.com/journal/15213765/homepage/2111_authorguidelines.html
```

- [ ] **Step 2: Write `scripts/sws_resolve_journal_style.py` shell (synthesizer is a Sonnet subagent dispatched from the SKILL.md, but the wrapper handles URL lookup, archive, write, and diff).**

```python
import argparse, sys, json, datetime, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from sws_hook_utils import parse_marker
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
URL_MAP = yaml.safe_load((PLUGIN_ROOT / "references" / "journal-url-map.yaml").read_text())

def archive_and_diff(overlay_path: Path, new_content: str) -> str:
    """Archive prior overlay; return a one-line diff summary string."""
    if not overlay_path.exists():
        return ""
    archive_dir = overlay_path.parent / "_archive"
    archive_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(overlay_path, archive_dir / f"{overlay_path.stem}-{ts}.md")
    old_fm = parse_frontmatter_text(overlay_path.read_text())
    new_fm = parse_frontmatter_text(new_content)
    diff_lines = []
    for k in sorted(set(old_fm) | set(new_fm)):
        if old_fm.get(k) != new_fm.get(k):
            diff_lines.append(f"  {k}: {old_fm.get(k)} → {new_fm.get(k)}")
    return "diff:\n" + "\n".join(diff_lines) if diff_lines else "(no field changes)"
```

The SKILL.md prose orchestrates: validate profile is set; resolve URL; WebFetch; dispatch synthesizer subagent (Sonnet); confirm-on-uncertain UX; call the wrapper to archive + write + print diff.

- [ ] **Step 3: Write `skills/resolve-journal-style/SKILL.md`.**

7 numbered steps matching spec's `skill_inventory.resolve_journal_style.steps`. Each step is one bash + one model action. The synthesizer subagent dispatch uses the `Agent` tool with `subagent_type: general-purpose` and a tightly-scoped prompt that includes the profile schema and the canned guide-for-authors text.

- [ ] **Step 4: Write 8 failing tests in `tests/test_resolve_journal_style.py`.**

```python
class TestResolveJournalStyle(unittest.TestCase):
    def test_url_map_lookup_for_known_slug(self): ...
    def test_unknown_slug_prompts_for_url(self): ...
    def test_aborts_when_profile_unset(self): ...
    def test_archive_created_on_re_resolve(self): ...
    def test_diff_summary_printed_on_re_resolve(self): ...
    def test_no_archive_on_first_resolve(self): ...
    def test_malformed_synthesizer_output_retries_once(self): ...
    def test_uncertain_fields_prompt_user(self): ...  # scripted confirm answers
```

For the synthesizer subagent calls in tests, use a fake synthesizer that reads canned frontmatter from `tests/fixtures/synthesizer_outputs/<slug>.yaml` instead of dispatching.

- [ ] **Step 5: Run tests — iterate to passes.**

- [ ] **Step 6: Commit.**

```
feat(skills): add /sws:resolve-journal-style with archive + diff + confirm-on-uncertain
```

---

## Task 10 — `/sws:resolve-call-rules` skill

**Files:**
- Create: `skills/resolve-call-rules/SKILL.md`
- Create: `scripts/sws_resolve_call_rules.py`
- Create: `tests/test_resolve_call_rules.py`
- Test fixtures: `tests/fixtures/calls/prin_2024.pdf`, `mur_consortium_call.docx`, `erc_starting.md`

- [ ] **Step 1: Write `scripts/sws_resolve_call_rules.py`.**

Functions:
- `scan_call_dir(call_dir: Path) -> list[Path]` — returns non-underscore files matching the 5 extensions.
- `heuristic_extract(text: str) -> dict` — regex extraction for deadline (date patterns), page limit ("12 pages", "max. 15 pages"), budget ("€500,000"). Per D13 (hybrid B+C).
- `qa_wizard() -> dict` — 5 prompts for program/deadline/page-limit/sections/language.
- `archive_and_diff(...)` — reuse from journal-style helper (refactor common path into `sws_overlay_io.py` if it stays clean).

- [ ] **Step 2: Write `skills/resolve-call-rules/SKILL.md`.**

7 steps: abort if profile ≠ funding-proposal; scan `call/`; if hit, parse via hybrid; if miss, Q&A wizard; archive + write + diff.

- [ ] **Step 3: Write 10 failing tests in `tests/test_resolve_call_rules.py`.**

```python
class TestResolveCallRules(unittest.TestCase):
    def test_aborts_when_profile_not_funding_proposal(self): ...
    def test_heuristic_extracts_deadline(self): ...
    def test_heuristic_extracts_page_limit(self): ...
    def test_heuristic_extracts_budget(self): ...
    def test_uncertain_fields_user_confirm(self): ...
    def test_qa_wizard_runs_when_no_source(self): ...
    def test_qa_wizard_collects_5_fields(self): ...
    def test_pdf_source_parsed_via_pdfplumber(self): ...
    def test_docx_source_parsed_via_python_docx(self): ...
    def test_archive_on_re_resolve(self): ...
```

Where the heuristic or LLM-fill is mocked, use a fake that returns canned `(value, uncertain: bool)` tuples.

- [ ] **Step 4: Run tests — iterate to passes.**

- [ ] **Step 5: Commit.**

```
feat(skills): add /sws:resolve-call-rules with hybrid heuristic+LLM+confirm parser
```

---

## Task 11 — Extend `sws_hook_session_start.py` for missing-profile nudge

**Files:**
- Modify: `scripts/sws_hook_session_start.py`
- Modify: `tests/test_sws_hook_session_start.py` (add 3 tests)

- [ ] **Step 1: Add 3 failing tests.**

```python
class TestSessionStartProfileNudge(unittest.TestCase):
    def test_prints_nudge_when_profile_null(self): ...
    def test_no_nudge_when_profile_set(self): ...
    def test_nudge_lists_profile_options(self): ...
```

- [ ] **Step 2: Modify `scripts/sws_hook_session_start.py`.**

Add a new branch (before the existing passport-summary + journal-style nudge):

```python
marker = check_marker(cwd)
if marker is None: return  # cycle-#5 silent no-op
if marker.get("profile") in (None, ""):
    print("No profile set — run /sws:set-profile <name> "
          "(e.g. communication, full-article, funding-proposal). "
          "Agents are paused until set.")
    return  # don't run the existing passport/journal nudges in this case
# … existing cycle-#5 logic unchanged below
```

- [ ] **Step 3: Run tests — expect 3 passes; full suite stays green.**

- [ ] **Step 4: Commit.**

```
feat(hooks): SessionStart prints missing-profile nudge when marker.profile is null
```

---

## Task 12 — Extend `/sws:init-project` for `--c7` + NL parse + venv bootstrap

**Files:**
- Modify: `scripts/sws_init_project.py`
- Modify: `skills/init-project/SKILL.md`
- Modify: `tests/test_init_project.py` (add ~10 tests)

- [ ] **Step 1: Add 10 failing tests.**

```python
class TestC7ProfileFlag(unittest.TestCase):
    def test_c7_flag_writes_profile_to_marker(self): ...
    def test_c7_validates_against_9_ids(self): ...
    def test_c7_invalid_name_rejects(self): ...
    def test_no_c7_leaves_profile_null(self): ...
    def test_nl_parse_communication(self): ...     # "for a Communication paper"
    def test_nl_parse_funding_proposal(self): ...  # "this is a funding proposal"
    def test_nl_parse_explicit_c7_wins(self): ...

class TestVenvBootstrap(unittest.TestCase):
    def test_creates_paper_venv_on_init(self): ...
    def test_skips_venv_if_already_exists(self): ...
    def test_venv_has_sws_deps_installed(self): ...  # mock pip
```

- [ ] **Step 2: Implement.**

In `sws_init_project.py`:
- Add `--c7=<profile-name>` to the argparser.
- Add `parse_natural_language(text)` that returns `{c1..c7: value}` overrides — extend the existing cycle-#4 NL parser to recognize:
  - "Communication"/"Comm"/"Letter" → c7=communication
  - "Perspective"/"Viewpoint" → c7=perspective
  - "Review" + "mini" → mini-review; "Review" alone → review-paper
  - "Editorial" → editorial
  - "Method" + paper/article → methodological-paper
  - "Reply"/"Comment on" → commentary-reply
  - "Proposal"/"PRIN"/"MUR"/"ERC"/"Horizon Europe"/"funding" → funding-proposal
  - "Article"/"full"/"original" → full-article
- Add op kind `bootstrap_venv` that runs `python3 -m venv <paper>/.venv` then `<paper>/.venv/bin/pip install -r ${CLAUDE_PLUGIN_ROOT}/requirements/sws-deps.txt`. Idempotent: if `.venv/bin/python` already exists, skip.
- Write `profile:` field to marker frontmatter (null if no c7 resolved).

In `skills/init-project/SKILL.md`: update args list to document `--c7`; update the steps list to include the venv-bootstrap op.

- [ ] **Step 3: Run tests — expect 10 passes.**

- [ ] **Step 4: Commit.**

```
feat(init): extend init-project with --c7 profile flag, NL parsing, and venv bootstrap
```

---

## Task 13 — E2E smoke `tests/smoke_cycle_06.sh`

**Files:**
- Create: `tests/smoke_cycle_06.sh`
- Create: `tests/fixtures/papers/dummy_paper/` skeleton + `.venv/` placeholder

- [ ] **Step 1: Write `tests/smoke_cycle_06.sh` implementing the 7-step walkthrough from spec.**

```bash
#!/usr/bin/env bash
# Cycle #6 e2e smoke.
# Exits non-zero on any unexpected behavior. Prints PASS/FAIL per step.
set -eu
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap "rm -rf $TMP" EXIT

# Bootstrap a dummy paper (minimal: marker + .venv stub + call/ dir)
cp -r "$PLUGIN_ROOT/tests/fixtures/papers/dummy_paper/." "$TMP/"
export PAPER_ROOT="$TMP"
export CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT"

# Step 1: set-profile communication
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
  "$PLUGIN_ROOT/scripts/sws_set_profile.py" --paper "$PAPER_ROOT" --name communication \
  | grep -q "profile: communication" && echo "PASS step 1" || { echo "FAIL step 1"; exit 1; }

# Step 2: resolve-journal-style chembiochem (using fixture HTML)
SWS_TEST_FIXTURE_HTML="$PLUGIN_ROOT/tests/fixtures/journal_pages/chembiochem.html" \
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
  "$PLUGIN_ROOT/scripts/sws_resolve_journal_style.py" \
  --paper "$PAPER_ROOT" --slug chembiochem --noninteractive

[[ -f "$PAPER_ROOT/Manuscript/_journal-style/chembiochem.md" ]] && echo "PASS step 2" || { echo "FAIL step 2"; exit 1; }
[[ ! -d "$PAPER_ROOT/Manuscript/_journal-style/_archive" ]] && echo "PASS step 2b" || { echo "FAIL step 2b (archive should be empty on first resolve)"; exit 1; }

# Step 3: re-run with different fixture
SWS_TEST_FIXTURE_HTML="$PLUGIN_ROOT/tests/fixtures/journal_pages/chembiochem-alt.html" \
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
  "$PLUGIN_ROOT/scripts/sws_resolve_journal_style.py" \
  --paper "$PAPER_ROOT" --slug chembiochem --noninteractive

ls "$PAPER_ROOT/Manuscript/_journal-style/_archive/" | grep -q "chembiochem-" \
  && echo "PASS step 3" || { echo "FAIL step 3"; exit 1; }

# Step 4: dummy agent sources agent_prelude.sh
bash -c "source '$PLUGIN_ROOT/scripts/agent_prelude.sh' drafter && [[ \$RESOLVED_OK -eq 1 ]] && [[ -n \$RESOLVED_REF_CAP ]]" \
  && echo "PASS step 4" || { echo "FAIL step 4"; exit 1; }

# Step 5: chemistry-validator is hypothetical (not in roster). Use real example:
# response-to-reviewers is in agents_inactive for funding-proposal but active for communication.
bash -c "source '$PLUGIN_ROOT/scripts/agent_prelude.sh' response-to-reviewers && [[ \$RESOLVED_OK -eq 1 ]]" \
  && echo "PASS step 5 (response-to-reviewers active in communication)" || { echo "FAIL step 5"; exit 1; }

# Step 6: set profile null → agent aborts
python3 -c "
import sys; sys.path.insert(0,'$PLUGIN_ROOT/scripts')
from sws_hook_utils import write_marker_field
from pathlib import Path
write_marker_field(Path('$PAPER_ROOT/.sws-project.local.md'), 'profile', None)
"
bash -c "source '$PLUGIN_ROOT/scripts/agent_prelude.sh' drafter; [[ \$RESOLVED_OK -eq 0 ]]" \
  && echo "PASS step 6" || { echo "FAIL step 6"; exit 1; }

# Step 7: switch to funding-proposal, drop fixture call PDF, resolve-call-rules
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
  "$PLUGIN_ROOT/scripts/sws_set_profile.py" --paper "$PAPER_ROOT" --name funding-proposal
cp "$PLUGIN_ROOT/tests/fixtures/calls/prin_2024.pdf" "$PAPER_ROOT/Manuscript/call/"
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
  "$PLUGIN_ROOT/scripts/sws_resolve_call_rules.py" --paper "$PAPER_ROOT" --noninteractive
[[ -f "$PAPER_ROOT/Manuscript/_call/prin_2024.md" ]] && echo "PASS step 7" || { echo "FAIL step 7"; exit 1; }

echo "smoke PASS"
```

- [ ] **Step 2: `chmod +x tests/smoke_cycle_06.sh`.**

- [ ] **Step 3: Run smoke — expect all 7 steps PASS.**

```bash
PAPER_ROOT_TMP=$(mktemp -d) tests/smoke_cycle_06.sh
```

- [ ] **Step 4: Commit.**

```
test(cycle-06): add e2e smoke covering 7-step walkthrough
```

---

## Task 14 — Documentation + memory updates

**Files:**
- Modify: `CLAUDE.md` (the plugin's, not user-paper's) — update "Where things go" section if needed; note cycle #6 done.
- Modify: `claude_memory/project_cycle_execution_status.md` — mark cycle #6 status.
- Modify: `claude_memory/project_profiles.md` — drop the "TBD" notes (now resolved by the design doc).
- Modify: `templates/manuscript-claude-md.template` — add a section about `/sws:set-profile`.

- [ ] **Step 1: Update `claude_memory/project_cycle_execution_status.md`.**

In the cycle table, change cycle #6 row to: `**PR open** (awaiting beta-test merge)` (or `merged` if PR has been merged by user before this task runs — check `gh pr view` first).

Add a "Cycle #6 — what's in flight" section at the bottom following the cycle-#5 pattern: summarize what shipped (9 profiles, 3+1 skills, resolver, agent prelude, venv discipline, SessionStart extension, ~150 tests, smoke).

- [ ] **Step 2: Update `claude_memory/project_profiles.md`.**

Remove the "TBD" line about fetcher-mechanism (resolved as slash command per D2). Update the "Frontmatter schema (draft — finalize before plan)" header to "Frontmatter schema (final — locked in cycle #6 D4)" and point to the spec for the canonical version.

- [ ] **Step 3: Update `CLAUDE.md` "Critical rules" → step 2 to point to the new resume protocol (cycle #6 done → cycle #7 next).**

- [ ] **Step 4: Update `templates/manuscript-claude-md.template`.**

Add a paragraph: "Run `/sws:set-profile <name>` to set your writing profile. Run `/sws:resolve-journal-style <slug>` for journal-targeted overrides. Run `/sws:resolve-call-rules` for funding-proposal call constraints."

- [ ] **Step 5: Commit.**

```
docs(cycle-06): update CLAUDE.md, cycle-status, profiles memory, init template
```

---

## Task 15 — Run full suite + open PR

- [ ] **Step 1: Run the entire dev test suite.**

```bash
$DEV_PY -m unittest discover tests -v 2>&1 | tail -10
```

Expected: ~150 tests pass (cycle #5 baseline of ~104 + ~46 new from cycle #6).

- [ ] **Step 2: Run the e2e smoke.**

```bash
tests/smoke_cycle_06.sh
```

Expected: all 7 PASS lines + final `smoke PASS`.

- [ ] **Step 3: Push branch and open PR.**

```bash
git push -u origin cycle/06-profile-and-overlay
gh pr create --title "Cycle #6: profile + overlay layer (9 profiles, resolver, 3+1 skills)" \
  --body "$(cat <<'EOF'
## Summary
- 9 profile files (`profiles/<id>.md`) with locked frontmatter schema (D4)
- Resolver `scripts/resolve_overlay.py` — 3-layer merge with replace-on-list (D14) and explicit-null-drops-scalar (D17)
- 3 new slash commands: `/sws:set-profile`, `/sws:resolve-journal-style`, `/sws:resolve-call-rules`
- 1 supporting: `/sws:install-deps`
- Init-project extended with `--c7` flag, NL parse, and per-paper `.venv/` bootstrap (D19, D20)
- SessionStart hook extended for missing-profile nudge (D7)
- ~46 new tests + e2e smoke covering 7-step walkthrough

Spec: `docs/superpowers/specs/2026-05-13-cycle-06-profile-and-overlay-design.md`
Plan: `docs/superpowers/plans/2026-05-13-cycle-06-profile-and-overlay.md`

## Test plan
- [x] All dev unit tests pass (~150 total)
- [x] E2E smoke passes
- [ ] Beta test on a real manuscript: set profile, resolve journal-style, check that drafter prelude reads correct caps

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Report PR URL to the user.**

---

## Self-review checklist (run after writing the plan; not part of execution)

**Spec coverage map:**

| Spec D | Covered by task |
|---|---|
| D1 (3 entry points) | T8 + T12 + T11 |
| D2 (journal-style slash command) | T9 |
| D3 (call-rules slash command + pre-step) | T10 |
| D4 (md+frontmatter format) | T7 + T9 + T10 |
| D5 (storage paths) | T9 + T10 |
| D6 (no auto-refresh) | T9 (deliberately omitted from skill) |
| D7 (missing-profile soft-fail) | T11 + T6 |
| D8 (body loading by drafter only) | T6 (RESOLVED_* doesn't include body) + drafter notes in T7 |
| D9 (helper script, no per-agent walk) | T4 + T5 + T6 |
| D10 (call-rules Q&A scope) | T10 |
| D11 (set-profile mechanics) | T8 |
| D12 (init-project --c7 hybrid) | T12 |
| D13 (call-rules hybrid B+C parser) | T10 |
| D14 (list-replace) | T4 + T5 |
| D15 (archive on re-resolve) | T9 + T10 |
| D16 (diff summary) | T9 + T10 |
| D17 (explicit null drops scalar) | T4 + T5 |
| D18 (synthesizer emits only confirmed fields) | T9 + T10 |
| D19 (no dev-env name in published code) | called out at top + every task uses `${CLAUDE_PLUGIN_ROOT}` and `$DEV_PY` only |
| D20 (per-paper venv) | T2 + T12 |

Activation matrix covered in T5 + T7. E1–E10 edge cases covered in T5 + T9 + T10. Smoke covers integration in T13.

**Risk callouts:**
- The synthesizer subagent dispatch in T9/T10 needs a deterministic test path. Use environment-variable `SWS_TEST_FIXTURE_HTML` / `SWS_TEST_FIXTURE_SYNTH_OUTPUT` to bypass live model calls in tests. Make sure tests never make real WebFetch or Agent calls.
- The venv bootstrap in T12 calls `pip install` — slow. Mock in tests; only the smoke creates a real venv (and a minimal one — install nothing or skip `pip install` when `SWS_TEST_SKIP_PIP=1`).
- The `agent_prelude.sh` eval-of-python-output pattern (T6) is sensitive to JSON-escape gotchas if any RESOLVED_* value contains shell metacharacters. Test with values that include spaces and quotes.
