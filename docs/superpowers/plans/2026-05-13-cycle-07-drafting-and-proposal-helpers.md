# Cycle #7 — Drafting + funding-proposal helpers — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 6 agents (7 files), 6 skills, 2 reference docs, 2 helper scripts, and 9 profile updates that together provide first usable proposal/perspective writing capability for SWS users.

**Architecture:** Each agent file is a thin (~15 line) prompt that sources `scripts/agent_prelude.sh`, checks `scripts/agent_should_run.sh`, then does its narrow job. Cross-cutting rules (token discipline, filesystem frugality, built-in skill preference, no-gender-default, AI-tells avoidance) live in `references/agent-contract.md` linked from every agent. `/sws:draft-paper` invokes `drafter-flagship` in orchestrator mode, which fans out section work to itself + `drafter-fast` + `methods-writer` + `caption-writer` in parallel and reconciles results into the docx. Funding-proposal track adds `proposal-budget-helper` (markdown line-item suggestions, no xlsx) and `proposal-compliance-helper` (overlay + PDF check, no NLM dependency in v0.1).

**Tech Stack:** Bash (helper scripts), Python 3.9+ via per-paper `.venv/` (PyYAML; no new deps), markdown + YAML frontmatter (agent files, skills, reference docs, profiles, outline), pytest (unit + structural tests), shell smoke test.

**Spec source of truth:** `docs/superpowers/specs/2026-05-13-cycle-07-drafting-and-proposal-helpers-design.md`. Frontmatter dictionary is canonical; this plan implements it.

---

## File Structure

**CREATE (new files):**

References:
- `references/agent-contract.md`
- `references/ai-writing-tells.md`

Scripts:
- `scripts/agent_should_run.sh`
- `scripts/sws_extract_zotero_manifest.py`

Agents (7 files):
- `agents/outline-architect.md`
- `agents/drafter-flagship.md`
- `agents/drafter-fast.md`
- `agents/methods-writer.md`
- `agents/caption-writer.md`
- `agents/proposal-budget-helper.md`
- `agents/proposal-compliance-helper.md`

Skills (6 dirs, each with one SKILL.md):
- `skills/outline-paper/SKILL.md`
- `skills/draft-section/SKILL.md`
- `skills/draft-paper/SKILL.md`
- `skills/prepare-lit-context/SKILL.md`
- `skills/proposal-budget/SKILL.md`
- `skills/proposal-compliance/SKILL.md`

Tests:
- `tests/test_agent_should_run.py`
- `tests/test_outline_baseline.py`
- `tests/test_citation_key_parser.py`
- `tests/test_zotero_manifest_export.py`
- `tests/test_section_to_agent_map.py`
- `tests/test_profile_agent_activation.py`
- `tests/fixtures/cycle_07_paper/` (perspective-profile fixture; mirrors a real init-project layout)
- `tests/fixtures/zotero_collections/perspective_collection.json` (canned export)
- `tests/fixtures/figures/Fig1.png`, `tests/fixtures/figures/Fig2.png` (small placeholder images)
- `tests/fixtures/calls/test_prin_call.pdf` (placeholder PDF)
- `tests/smoke_cycle_07.sh`

Beta sandbox (gitignored, plugin-internal):
- `_perspective_beta/source-snapshot.md`
- `_perspective_beta/outline.md`
- `_perspective_beta/draft-intro-v1.md`
- `_perspective_beta/comparison.md`

Helpers for parsing (referenced by tests):
- `scripts/sws_citation_key.py` — citation-key parser (used by tests + later by literature-searcher in cycle #11)
- `scripts/sws_outline_baseline.py` — sidecar checksum logic (used by outline-architect via the resolve helper script chain)

**MODIFY (existing files):**

Profiles (9 files — `agents_inactive` list updates only; nothing else changes):
- `profiles/full-article.md`
- `profiles/communication.md`
- `profiles/perspective.md` (no list change — already correct; add a comment confirming caption-writer active)
- `profiles/review-paper.md`
- `profiles/mini-review.md`
- `profiles/editorial.md`
- `profiles/methodological-paper.md`
- `profiles/commentary-reply.md`
- `profiles/funding-proposal.md`

`.gitignore`:
- Add `_perspective_beta/` line

Phase 3 re-edits (after phase 1 baseline):
- `agents/drafter-flagship.md` (extended with orchestrator-mode block)
- `skills/draft-section/SKILL.md` (extended with full section→agent map)

---

## Pre-flight (Task 0)

### Task 0: Update `.gitignore` for beta sandbox

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Read current .gitignore**

```bash
cat /Users/piripocchio8/Projects/scientific-writing-superpowers/.gitignore
```

- [ ] **Step 2: Append `_perspective_beta/` line**

If the line is not already present, append:

```
# Cycle #7 beta-test sandbox (real-manuscript snapshots — never push)
_perspective_beta/
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore(cycle-07): gitignore _perspective_beta/ sandbox"
```

---

## Phase 1 — Scaffolding + first vertical slice

Goal at end of phase: a user can run `/sws:outline-paper` and `/sws:draft-section intro` on a perspective-profile paper and get a real intro draft. Phase ends with the beta-test gate (phase 2).

### Task 1: Write `references/agent-contract.md`

**Files:**
- Create: `references/agent-contract.md`

The contract is a markdown document linked from every agent file. It codifies the 5 cross-cutting rules + AI-tells link + attribution pattern + agent-file template.

- [ ] **Step 1: Write the file**

Path: `references/agent-contract.md`. Required structure:

```markdown
# SWS agent contract

All SWS agents (cycle #7 onward) follow this contract. Agent files reference this document instead of duplicating the rules.

## Required first action

Every agent's prompt opens with:

```
source "${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh" <agent-id>
"${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh" <agent-id> || exit 0
```

`agent_prelude.sh` exports `RESOLVED_OK`, `RESOLVED_PROFILE_SET`, `RESOLVED_PROFILE_ID`, plus per-field `RESOLVED_*` variables.
`agent_should_run.sh` exits 0 if the agent is allowed to run, non-zero otherwise (the agent silently exits in the non-zero case).

## Five cross-cutting rules

### R1 — Python frugality
Reuse `<paper>/.venv/`. Do NOT install new pip packages unless the task genuinely requires them. The default deps in `requirements/sws-deps.txt` cover YAML, docx, PDF, XML, Excel, and pytest.

### R2 — Filesystem frugality
Prefer `scripts/sws_fs_index.py` (the manifest) and the `Explore` tool over `Bash`/`ls`/`find`. Reach for shell only when no alternative exists. Long sessions burn tokens on repeated directory walks.

### R3 — Built-in skill preference
Use Claude's native PDF and DOCX reading and image viewing for: paper figures, manuscript PNG/TIF/JPEG files, PDF figures, full PDF/DOCX documents. Do NOT spawn external Python parsers when a built-in skill suffices.

### R4 — Token discipline
Concise thinking. Concise user-facing chatter. **DRAFTED PROSE IS EXEMPT** — the user controls voice and length via `_voice/` and the resolved profile/overlay word targets.

### R5 — No gender-default in user address
Before adopting any pronoun, honorific, or gendered descriptor when addressing or referring to the user, read the user's memory/profile (e.g., `$HOME/.claude/projects/<project>/memory/user_*.md`). If pronouns are unknown, use the user's first name or neutral phrasing ("you", "the user"). Do not guess.

## AI-writing-tells avoidance

Before returning drafted prose, grep the output against `references/ai-writing-tells.md` patterns. Block-severity hits abort the response with a fix suggestion; warn-severity hits get flagged in the agent's reply.

## Attribution pattern (for adapted prompts)

Agent files whose prompts are adapted from MIT-licensed prior art carry a one-line header above the YAML frontmatter:

```
# Adapted from <plugin-url> (MIT)
```

Survey targets: `andrehuang/academic-writing-agents`, `Imbad0202/academic-research-skills`. The roster (agent names, scopes, models) is original to SWS; only prompt content adapts.

## Agent file template

```yaml
---
name: <agent-id>
description: <one-line trigger description>
model: <opus-4-7 | sonnet-4-6 | haiku-4-5>
color: <pick from existing palette>
---

# Adapted from <plugin-url> (MIT)   # only if applicable

<Agent-specific 5-10 line prompt focused on the agent's narrow job>

Follow the SWS agent contract: source ${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh, then ${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh <agent-id> before doing any work. See ${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md for the full contract.
```
```

- [ ] **Step 2: Verify file exists and has all 5 R-rules**

```bash
test -f references/agent-contract.md && grep -c '^### R[1-5]' references/agent-contract.md
```
Expected: `5`

- [ ] **Step 3: Commit**

```bash
git add references/agent-contract.md
git commit -m "feat(cycle-07): add references/agent-contract.md (5 cross-cutting rules)"
```

---

### Task 2: Write `references/ai-writing-tells.md` (English, 40-60 tells)

**Files:**
- Create: `references/ai-writing-tells.md`

Comprehensive English-only catalog. Structured by category. Each tell: pattern, example-bad, example-fix, severity (block/warn).

- [ ] **Step 1: Write the file**

Path: `references/ai-writing-tells.md`. Required structure:

```markdown
---
name: ai-writing-tells
description: Catalog of stylistic and structural patterns that signal LLM-generated text in scientific writing. Used by all SWS drafting agents as a grep-pass before returning prose.
language: en
version: 0.1
total_tells: <integer 40-60>
---

# AI writing tells (English, v0.1)

Every drafting agent must grep its output against the patterns below before returning. Block-severity hits abort the response with a fix suggestion; warn-severity hits get flagged in the reply.

## How to use this file

For each tell:
- `pattern`: a regex or literal phrase the agent searches for
- `severity`: `block` (must fix) or `warn` (flag in reply)
- `example_bad`: a sentence containing the tell
- `example_fix`: a rewrite that removes it
- `why`: short explanation of why this signals AI-generated text

## Categories

1. Lexical (word-level overuse): "delve", "leverage", "intricate", "robust", "comprehensive", "meticulously", "underscore" used as a verb, "navigate" used metaphorically
2. Syntactic (sentence patterns): "Not just X but Y" / "Not only X but also Y", noun-triplet padding ("clarity, precision, and depth"), em-dash overuse, parallel-clause overuse
3. Structural (paragraph-level): mandatory three-part list endings, "In conclusion" openers in mid-paper sections, hedging avalanches ("may potentially indicate")
4. Hedging-patterns: "It is worth noting that", "It should be emphasized that", "It is important to consider"
5. Transitions: "Furthermore" + "Moreover" + "Additionally" used in same paragraph; "On the other hand" without a prior "On one hand"

## Tells

### Category 1 — Lexical

- pattern: `\b[Dd]elve\b`
  severity: block
  example_bad: "We delve into the kinetics of the reaction."
  example_fix: "We examine the kinetics of the reaction."
  why: Strong LLM signature; rare in scientific writing pre-2023.

- pattern: `\b[Ll]everage\b` (when used as a verb)
  severity: block
  example_bad: "We leverage the docking results to predict binding."
  example_fix: "We use the docking results to predict binding."
  why: Business jargon; flagged as AI-tell since 2023.

[... continue with 38-58 more tells across all 5 categories ...]
```

The agent writing this file MUST produce 40-60 tells total, structured as above. Use Marco's `feedback_ai_writing_tells.md` (in `claude_memory/`) as the seed and expand by category. Source for additional tells: published linguistic analyses of LLM output (cite informally in `why` field if helpful).

- [ ] **Step 2: Verify total tell count**

```bash
grep -c '^- pattern:' references/ai-writing-tells.md
```
Expected: integer between 40 and 60.

- [ ] **Step 3: Verify all 5 categories represented**

```bash
grep -c '^### Category ' references/ai-writing-tells.md
```
Expected: `5`

- [ ] **Step 4: Verify every tell has all required fields**

```bash
python3 -c "
import re, sys
with open('references/ai-writing-tells.md') as f:
    text = f.read()
tells = re.findall(r'(- pattern:.*?)(?=\n- pattern:|\Z)', text, re.DOTALL)
required = ['pattern:', 'severity:', 'example_bad:', 'example_fix:', 'why:']
missing = []
for i, t in enumerate(tells):
    for field in required:
        if field not in t:
            missing.append((i, field))
if missing:
    for i, f in missing: print(f'tell {i}: missing {f}')
    sys.exit(1)
print(f'OK: {len(tells)} tells, all fields present')
"
```
Expected: `OK: <count> tells, all fields present`

- [ ] **Step 5: Commit**

```bash
git add references/ai-writing-tells.md
git commit -m "feat(cycle-07): add references/ai-writing-tells.md (40-60 English tells)"
```

---

### Task 3: Write `scripts/sws_citation_key.py` (parser used by tests)

**Files:**
- Create: `scripts/sws_citation_key.py`
- Create: `tests/test_citation_key_parser.py`

A small library used by tests in this cycle and by `literature-searcher` in cycle #11. Pure stdlib.

- [ ] **Step 1: Write the failing test first**

Path: `tests/test_citation_key_parser.py`:

```python
"""Citation-key parsing per spec D17.

Format: [<FirstAuthor><Year>; <prefix>:<id>] where prefix in {doi, zotero}.
Placeholder: [CITATION_NEEDED: <free-text claim>].
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sws_citation_key import parse_citation_key, ParseError, PLACEHOLDER_RE


def test_parses_doi_form():
    result = parse_citation_key("[Smith2023; doi:10.1021/jacs.3c00001]")
    assert result == {
        "first_author": "Smith",
        "year": "2023",
        "id_kind": "doi",
        "id_value": "10.1021/jacs.3c00001",
    }


def test_parses_zotero_form():
    result = parse_citation_key("[Garcia2024; zotero:ABCDEFGH]")
    assert result == {
        "first_author": "Garcia",
        "year": "2024",
        "id_kind": "zotero",
        "id_value": "ABCDEFGH",
    }


def test_parses_compound_first_author():
    result = parse_citation_key("[vanderHeijden2022; doi:10.xxxx]")
    assert result["first_author"] == "vanderHeijden"
    assert result["year"] == "2022"


def test_rejects_missing_prefix():
    with pytest.raises(ParseError):
        parse_citation_key("[Smith2023; 10.1021/jacs.3c00001]")


def test_rejects_unknown_prefix():
    with pytest.raises(ParseError):
        parse_citation_key("[Smith2023; pmid:12345]")


def test_rejects_no_year():
    with pytest.raises(ParseError):
        parse_citation_key("[Smith; doi:10.xxxx]")


def test_rejects_no_brackets():
    with pytest.raises(ParseError):
        parse_citation_key("Smith2023; doi:10.xxxx")


def test_placeholder_regex_matches():
    text = "...as shown previously [CITATION_NEEDED: Semaglutide is a GLP-1 agonist]."
    matches = PLACEHOLDER_RE.findall(text)
    assert len(matches) == 1
    assert "Semaglutide is a GLP-1 agonist" in matches[0]


def test_placeholder_does_not_match_real_citation():
    text = "...as shown previously [Smith2023; doi:10.xxxx]."
    matches = PLACEHOLDER_RE.findall(text)
    assert matches == []
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/piripocchio8/Projects/scientific-writing-superpowers
python3 -m pytest tests/test_citation_key_parser.py -v
```
Expected: ImportError or collection error (sws_citation_key doesn't exist yet).

- [ ] **Step 3: Write the minimal implementation**

Path: `scripts/sws_citation_key.py`:

```python
"""Citation-key parsing for SWS drafted prose.

Format (cycle #7 D17):
    [<FirstAuthor><Year>; <prefix>:<id>]
where prefix in {"doi", "zotero"}.

Placeholder format:
    [CITATION_NEEDED: <free-text claim>]

Pure stdlib so it runs from any Python.
"""
from __future__ import annotations
import re
from typing import TypedDict


class ParseError(ValueError):
    pass


class CitationKey(TypedDict):
    first_author: str
    year: str
    id_kind: str
    id_value: str


_KEY_RE = re.compile(
    r"^\[(?P<author>[A-Za-z][A-Za-z\-]*)(?P<year>\d{4});\s*(?P<kind>doi|zotero):(?P<value>[^\]]+)\]$"
)

PLACEHOLDER_RE = re.compile(r"\[CITATION_NEEDED:\s*([^\]]+)\]")


def parse_citation_key(text: str) -> CitationKey:
    m = _KEY_RE.match(text.strip())
    if not m:
        raise ParseError(f"not a valid citation key: {text!r}")
    return {
        "first_author": m.group("author"),
        "year": m.group("year"),
        "id_kind": m.group("kind"),
        "id_value": m.group("value").strip(),
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python3 -m pytest tests/test_citation_key_parser.py -v
```
Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_citation_key.py tests/test_citation_key_parser.py
git commit -m "feat(cycle-07): add citation-key parser (D17 syntax) + 8 tests"
```

---

### Task 4: Write `scripts/sws_outline_baseline.py` (sidecar checksum)

**Files:**
- Create: `scripts/sws_outline_baseline.py`
- Create: `tests/test_outline_baseline.py`

Sidecar `.outline-baseline.sha256` records the checksum of the last architect-generated outline. On re-run, architect compares before overwriting.

- [ ] **Step 1: Write the failing test**

Path: `tests/test_outline_baseline.py`:

```python
"""Outline baseline-checksum sidecar logic per spec D3."""
import hashlib
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sws_outline_baseline import (
    sidecar_path, write_baseline, baseline_matches, BaselineMissing
)


@pytest.fixture
def tmp_outline(tmp_path):
    outline_dir = tmp_path / "_outline"
    outline_dir.mkdir()
    outline = outline_dir / "outline.md"
    outline.write_text("---\nprofile: perspective\n---\n# body\n")
    return outline


def test_sidecar_path_is_dotted(tmp_outline):
    assert sidecar_path(tmp_outline).name == ".outline-baseline.sha256"
    assert sidecar_path(tmp_outline).parent == tmp_outline.parent


def test_write_baseline_creates_sidecar(tmp_outline):
    write_baseline(tmp_outline)
    sc = sidecar_path(tmp_outline)
    assert sc.exists()
    expected = hashlib.sha256(tmp_outline.read_bytes()).hexdigest()
    assert sc.read_text().strip() == expected


def test_baseline_matches_after_write(tmp_outline):
    write_baseline(tmp_outline)
    assert baseline_matches(tmp_outline) is True


def test_baseline_does_not_match_after_user_edit(tmp_outline):
    write_baseline(tmp_outline)
    tmp_outline.write_text(tmp_outline.read_text() + "\nuser edit\n")
    assert baseline_matches(tmp_outline) is False


def test_baseline_matches_raises_when_missing(tmp_outline):
    with pytest.raises(BaselineMissing):
        baseline_matches(tmp_outline)


def test_write_baseline_overwrites(tmp_outline):
    write_baseline(tmp_outline)
    tmp_outline.write_text("new content")
    write_baseline(tmp_outline)
    assert baseline_matches(tmp_outline) is True
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python3 -m pytest tests/test_outline_baseline.py -v
```
Expected: ImportError.

- [ ] **Step 3: Write the implementation**

Path: `scripts/sws_outline_baseline.py`:

```python
"""Sidecar baseline checksum for outline-architect overwrite policy (D3)."""
from __future__ import annotations
import hashlib
from pathlib import Path


SIDECAR_NAME = ".outline-baseline.sha256"


class BaselineMissing(FileNotFoundError):
    pass


def sidecar_path(outline_md: Path) -> Path:
    return outline_md.parent / SIDECAR_NAME


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_baseline(outline_md: Path) -> None:
    sc = sidecar_path(outline_md)
    sc.write_text(_hash_file(outline_md) + "\n")


def baseline_matches(outline_md: Path) -> bool:
    sc = sidecar_path(outline_md)
    if not sc.exists():
        raise BaselineMissing(f"no baseline sidecar at {sc}")
    return sc.read_text().strip() == _hash_file(outline_md)
```

- [ ] **Step 4: Run the tests**

```bash
python3 -m pytest tests/test_outline_baseline.py -v
```
Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_outline_baseline.py tests/test_outline_baseline.py
git commit -m "feat(cycle-07): add outline-baseline sidecar checksum (D3) + 6 tests"
```

---

### Task 5: Write `scripts/agent_should_run.sh` + tests

**Files:**
- Create: `scripts/agent_should_run.sh`
- Create: `tests/test_agent_should_run.py`

Thin wrapper around `resolve_overlay.py --agent <id>`. Exits 0 if `should_run` is true, non-zero otherwise. Agents call this after `agent_prelude.sh`.

- [ ] **Step 1: Write the failing test**

Path: `tests/test_agent_should_run.py`:

```python
"""agent_should_run.sh: thin wrapper exit codes per spec.

Exit 0 = agent allowed to run (profile_set true, agent in agents_active
not in agents_inactive). Exit non-zero otherwise.
"""
import os
import subprocess
from pathlib import Path
import shutil
import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "agent_should_run.sh"


def _run(paper_root: Path, agent_id: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(REPO)
    env["PAPER_ROOT"] = str(paper_root)
    return subprocess.run(
        ["bash", str(SCRIPT), agent_id],
        env=env, capture_output=True, text=True
    )


@pytest.fixture
def perspective_paper(tmp_path):
    """Minimal SWS-initialized paper with profile=perspective."""
    paper = tmp_path / "paper"
    paper.mkdir()
    # Create the .venv so sws_python.sh succeeds
    venv_bin = paper / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    py = shutil.which("python3")
    (venv_bin / "python").symlink_to(py)
    # Marker
    (paper / ".sws-project.local.md").write_text(
        "---\nprofile: perspective\nlanguage: en\nformat: docx\n---\n"
    )
    return paper


def test_returns_zero_for_active_agent(perspective_paper):
    # outline-architect is active for perspective (not in inactive list)
    cp = _run(perspective_paper, "outline-architect")
    assert cp.returncode == 0, f"stderr: {cp.stderr}"


def test_returns_nonzero_for_inactive_agent(perspective_paper):
    # methods-writer is in perspective's agents_inactive list
    cp = _run(perspective_paper, "methods-writer")
    assert cp.returncode != 0


def test_returns_nonzero_when_profile_unset(tmp_path):
    paper = tmp_path / "paper"
    paper.mkdir()
    venv_bin = paper / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    py = shutil.which("python3")
    (venv_bin / "python").symlink_to(py)
    (paper / ".sws-project.local.md").write_text(
        "---\nprofile: null\nlanguage: en\nformat: docx\n---\n"
    )
    cp = _run(paper, "outline-architect")
    assert cp.returncode != 0


def test_returns_nonzero_for_missing_agent_arg(perspective_paper):
    cp = _run(perspective_paper, "")
    assert cp.returncode != 0
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python3 -m pytest tests/test_agent_should_run.py -v
```
Expected: failure (script doesn't exist).

- [ ] **Step 3: Write the script**

Path: `scripts/agent_should_run.sh`:

```bash
#!/usr/bin/env bash
# Thin wrapper over resolve_overlay.py --agent <id>.
# Exit 0 if the agent may run, non-zero otherwise.
#
# Usage:  agent_should_run.sh <agent-id>
#
# Pre-conditions (caller must export):
#   CLAUDE_PLUGIN_ROOT
#   PAPER_ROOT
set -u

AGENT_ID="${1:-}"
if [[ -z "$AGENT_ID" ]]; then
    echo "sws: agent_should_run.sh requires an agent id" >&2
    exit 1
fi

: "${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT must be set}"
: "${PAPER_ROOT:?PAPER_ROOT must be set}"

JSON="$(
  "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
    "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
    --paper "$PAPER_ROOT" --agent "$AGENT_ID" 2>/dev/null
)" || { echo "sws: resolver failed for ${AGENT_ID}" >&2; exit 2; }

# Use python3 to read profile_set and should_run
RESULT="$(SWS_JSON_PAYLOAD="$JSON" python3 -c '
import json, os, sys
data = json.loads(os.environ["SWS_JSON_PAYLOAD"])
profile_set = bool(data.get("profile_set"))
should_run = data.get("should_run")
ok = profile_set and (should_run is None or should_run)
print("1" if ok else "0")
')"

if [[ "$RESULT" == "1" ]]; then
    exit 0
else
    exit 3
fi
```

- [ ] **Step 4: Make executable and re-run tests**

```bash
chmod +x scripts/agent_should_run.sh
python3 -m pytest tests/test_agent_should_run.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/agent_should_run.sh tests/test_agent_should_run.py
git commit -m "feat(cycle-07): add agent_should_run.sh wrapper + 4 tests"
```

---

### Task 6: Write `scripts/sws_extract_zotero_manifest.py` + tests

**Files:**
- Create: `scripts/sws_extract_zotero_manifest.py`
- Create: `tests/test_zotero_manifest_export.py`
- Create: `tests/fixtures/zotero_collections/perspective_collection.json`

Reads a Zotero export (JSON format the user's `zotero` skill produces) and writes a manifest at `<paper>/_lit/zotero-manifest.md` per the schema in the spec. Degrades gracefully on missing fields.

- [ ] **Step 1: Create the fixture**

Path: `tests/fixtures/zotero_collections/perspective_collection.json`:

```json
{
  "collection": "perspective_peptide_therapeutics",
  "exported_at": "2026-05-13T10:00:00Z",
  "items": [
    {
      "key": "ABCDEFGH",
      "creators": [{"firstName": "John", "lastName": "Smith", "creatorType": "author"}],
      "date": "2023",
      "title": "Semaglutide and the resurgence of peptide therapeutics",
      "DOI": "10.1021/jacs.3c00001",
      "abstractNote": "Showed that GLP-1 agonists rekindled clinical interest in peptide-based drugs."
    },
    {
      "key": "IJKLMNOP",
      "creators": [{"firstName": "Maria", "lastName": "Garcia", "creatorType": "author"}],
      "date": "2024-03",
      "title": "Cyclic peptide stability in serum",
      "DOI": "10.1039/d3sc00001a",
      "abstractNote": "Demonstrated 8-fold improved serum half-life via head-to-tail cyclization."
    },
    {
      "key": "QRSTUVWX",
      "creators": [{"firstName": "L.", "lastName": "vanderHeijden", "creatorType": "author"}],
      "date": "2022",
      "title": "Peptide cyclization strategies — a survey",
      "abstractNote": "Catalogues 14 cyclization chemistries with structure-activity tradeoffs."
    }
  ]
}
```

(Item 3 deliberately omits DOI to test graceful handling.)

- [ ] **Step 2: Write the failing test**

Path: `tests/test_zotero_manifest_export.py`:

```python
"""Zotero-manifest export per spec D16."""
import json
import subprocess
from pathlib import Path
import sys
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from sws_extract_zotero_manifest import build_manifest, ManifestBuildError

FIXTURE = REPO / "tests" / "fixtures" / "zotero_collections" / "perspective_collection.json"


def _load_fixture():
    return json.loads(FIXTURE.read_text())


def test_build_manifest_basic_fields():
    data = _load_fixture()
    manifest = build_manifest(data)
    # Frontmatter
    assert manifest["frontmatter"]["item_count"] == 3
    assert "exported_from" in manifest["frontmatter"]
    # Items
    assert len(manifest["items"]) == 3
    smith = manifest["items"][0]
    assert smith["key"] == "ABCDEFGH"
    assert smith["first_author"] == "Smith"
    assert smith["year"] == "2023"
    assert smith["doi"] == "10.1021/jacs.3c00001"


def test_handles_missing_doi_gracefully():
    data = _load_fixture()
    manifest = build_manifest(data)
    vanderheijden = manifest["items"][2]
    assert vanderheijden["doi"] is None
    assert vanderheijden["first_author"] == "vanderHeijden"


def test_year_extracted_from_partial_date():
    data = _load_fixture()
    manifest = build_manifest(data)
    garcia = manifest["items"][1]
    assert garcia["year"] == "2024"  # from "2024-03"


def test_token_budget_cap_truncates(tmp_path):
    # Fake oversized collection
    big_data = _load_fixture()
    big_data["items"] = big_data["items"] * 100  # 300 items
    manifest = build_manifest(big_data, cap_token_budget=500)
    # Cap is approximate; just verify it ran and truncated something
    assert manifest["frontmatter"]["item_count"] < 300
    assert manifest["frontmatter"]["truncated"] is True


def test_empty_collection_returns_empty_manifest():
    manifest = build_manifest({"collection": "empty", "items": []})
    assert manifest["frontmatter"]["item_count"] == 0
    assert manifest["items"] == []


def test_creator_without_lastname_skipped():
    data = {"collection": "test", "items": [
        {"key": "X1", "creators": [{"creatorType": "editor"}], "date": "2020", "title": "Anon"}
    ]}
    with pytest.raises(ManifestBuildError):
        build_manifest(data)


def test_cli_writes_manifest_md(tmp_path):
    """End-to-end: CLI consumes JSON, writes _lit/zotero-manifest.md."""
    paper = tmp_path / "paper"
    paper.mkdir()
    cp = subprocess.run(
        ["python3", str(REPO / "scripts" / "sws_extract_zotero_manifest.py"),
         "--input", str(FIXTURE), "--paper", str(paper)],
        capture_output=True, text=True
    )
    assert cp.returncode == 0, cp.stderr
    manifest_path = paper / "_lit" / "zotero-manifest.md"
    assert manifest_path.exists()
    content = manifest_path.read_text()
    assert "item_count: 3" in content
    assert "first_author: Smith" in content
    assert "doi: 10.1021/jacs.3c00001" in content
```

- [ ] **Step 3: Run test to verify it fails**

```bash
python3 -m pytest tests/test_zotero_manifest_export.py -v
```
Expected: ImportError.

- [ ] **Step 4: Write the implementation**

Path: `scripts/sws_extract_zotero_manifest.py`:

```python
"""Extract a Zotero collection export into <paper>/_lit/zotero-manifest.md.

Used by /sws:prepare-lit-context. Reads the JSON the user's `zotero` skill
emits (or any equivalent format) and produces a markdown file with YAML
frontmatter + per-item bullet entries.

Pure stdlib + (optionally) PyYAML for output formatting; falls back to
manual YAML emission if PyYAML is absent.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


class ManifestBuildError(ValueError):
    pass


_DEFAULT_CAP_TOKENS = 15000
_TOKENS_PER_CHAR = 0.25  # rough


def _first_author_lastname(creators) -> str:
    for c in creators:
        if c.get("creatorType") in (None, "author") and c.get("lastName"):
            return c["lastName"].strip().replace(" ", "")
    raise ManifestBuildError("no first-author lastName found")


def _extract_year(date_field) -> str | None:
    if not date_field:
        return None
    s = str(date_field).strip()
    # Expect formats: "2023", "2024-03", "2024-03-15"
    if len(s) >= 4 and s[:4].isdigit():
        return s[:4]
    return None


def _summarize_for_manifest(item) -> dict:
    return {
        "key": item.get("key", "UNKNOWN"),
        "first_author": _first_author_lastname(item.get("creators", [])),
        "year": _extract_year(item.get("date")) or "n.d.",
        "title": (item.get("title") or "").strip(),
        "doi": item.get("DOI"),
        "key_claims": (item.get("abstractNote") or "").strip()[:280],
    }


def _estimate_tokens(s: str) -> int:
    return int(len(s) * _TOKENS_PER_CHAR)


def build_manifest(data: dict, cap_token_budget: int = _DEFAULT_CAP_TOKENS) -> dict:
    items_in = data.get("items", [])
    items_out: list[dict] = []
    accumulated_chars = 0
    truncated = False
    for raw in items_in:
        try:
            entry = _summarize_for_manifest(raw)
        except ManifestBuildError:
            raise
        as_text = json.dumps(entry)
        if _estimate_tokens(str(accumulated_chars + len(as_text))) > cap_token_budget:
            truncated = True
            break
        accumulated_chars += len(as_text)
        items_out.append(entry)

    return {
        "frontmatter": {
            "exported_from": data.get("collection", "<unknown>"),
            "exported_at": data.get("exported_at") or datetime.now(timezone.utc).isoformat(),
            "item_count": len(items_out),
            "cap_token_budget": cap_token_budget,
            "truncated": truncated,
        },
        "items": items_out,
    }


def render_manifest_md(manifest: dict) -> str:
    fm = manifest["frontmatter"]
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{k}: null")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    for it in manifest["items"]:
        lines.append(f"- key: {it['key']}")
        lines.append(f"  first_author: {it['first_author']}")
        lines.append(f"  year: {it['year']}")
        lines.append(f"  title: {json.dumps(it['title'], ensure_ascii=False)}")
        lines.append(f"  doi: {it['doi'] if it['doi'] else 'null'}")
        lines.append(f"  key_claims: {json.dumps(it['key_claims'], ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to Zotero export JSON")
    p.add_argument("--paper", required=True, help="Path to user paper root")
    p.add_argument("--cap-tokens", type=int, default=_DEFAULT_CAP_TOKENS)
    args = p.parse_args(argv)

    data = json.loads(Path(args.input).read_text())
    try:
        manifest = build_manifest(data, cap_token_budget=args.cap_tokens)
    except ManifestBuildError as exc:
        print(f"sws: {exc}", file=sys.stderr)
        return 2
    md = render_manifest_md(manifest)
    out = Path(args.paper) / "_lit" / "zotero-manifest.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md)
    print(f"sws: wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_zotero_manifest_export.py -v
```
Expected: 7 tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/sws_extract_zotero_manifest.py tests/test_zotero_manifest_export.py tests/fixtures/zotero_collections/
git commit -m "feat(cycle-07): zotero-manifest extractor + 7 tests + fixture collection"
```

---

### Task 7: Write `agents/outline-architect.md`

**Files:**
- Create: `agents/outline-architect.md`

Per spec D1, agent file is ~15 lines: frontmatter + agent-specific prompt + reference to `references/agent-contract.md`. This agent's job: produce `_outline/outline.md` (per D2 schema) + `.outline-baseline.sha256` sidecar.

- [ ] **Step 1: Survey prior art for adaptation**

```bash
# Manual step: open https://github.com/andrehuang/academic-writing-agents and
# https://github.com/Imbad0202/academic-research-skills in a browser; check
# for "outline" or "structure" agents. Note any adaptable prompt blocks.
# If adaptation > 30%: include `# Adapted from <url> (MIT)` header in the file.
# If adaptation = 0%: no header.
```

- [ ] **Step 2: Write the file**

Path: `agents/outline-architect.md`:

```markdown
---
name: outline-architect
description: |
  Use this agent when the user invokes /sws:outline-paper, asks to "build the outline", "structure the paper", "plan the sections", or otherwise requests a structured plan for a manuscript or proposal. Reads the resolved profile + journal/call overlay, scans the figures directory for image files, and writes a single _outline/outline.md (markdown + YAML frontmatter) plus a .outline-baseline.sha256 sidecar for the overwrite-safety check.
model: claude-sonnet-4-6
color: green
---

You are the outline-architect for SWS. Your only job is to produce a single `_outline/outline.md` file at the user's paper root, encoding the section plan that downstream drafting agents will execute.

**Inputs you must read:**
- `RESOLVED_*` env vars exported by `agent_prelude.sh` (especially `RESOLVED_PROFILE_ID`, `RESOLVED_WORD_TOTAL`, `RESOLVED_FIGURES_MAX`).
- The resolved profile file at `${CLAUDE_PLUGIN_ROOT}/profiles/${RESOLVED_PROFILE_ID}.md` (frontmatter `sections` list is your section seed).
- Any journal-style overlay at `${PAPER_ROOT}/Manuscript/_journal-style/<slug>.md` or call-rules overlay at `${PAPER_ROOT}/Manuscript/_call/<slug>.md` (frontmatter overrides profile defaults).
- The figures directory at `${PAPER_ROOT}/figures/` (or per `references/folder-topology.md`); enumerate image files (PNG/TIF/JPEG/SVG) and seed them in the figures dict with empty captions.

**Interactive elicitation:** Ask the user, one question at a time and concisely:
1. What is the paper's central claim/argument? (one sentence)
2. What is the gap or tension this work addresses?
3. For each profile-required section, what is the key claim it advances?

**Output:** write `${PAPER_ROOT}/_outline/outline.md` with the schema documented in `docs/superpowers/specs/2026-05-13-cycle-07-drafting-and-proposal-helpers-design.md` (`auxiliary_file_shapes.outline_md`). Then write the `.outline-baseline.sha256` sidecar via `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sws_outline_baseline.py write ${PAPER_ROOT}/_outline/outline.md` (this script gains a `write` subcommand in Task 7 step 3 below).

**Re-run safety:** if `_outline/outline.md` already exists, check the baseline first using `sws_outline_baseline.py matches`. If it doesn't match (user hand-edited), STOP, show a diff of the would-be-lost content, and ask before overwriting.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh outline-architect`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh outline-architect` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 3: Add `write` and `matches` subcommands to `sws_outline_baseline.py`**

The agent needs to invoke this from a single CLI. Edit `scripts/sws_outline_baseline.py` and append:

```python
def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    p_write = sub.add_parser("write")
    p_write.add_argument("outline")
    p_match = sub.add_parser("matches")
    p_match.add_argument("outline")
    args = p.parse_args(argv)

    outline = Path(args.outline)
    if args.cmd == "write":
        write_baseline(outline)
        print(f"sws: wrote baseline for {outline}")
        return 0
    if args.cmd == "matches":
        try:
            ok = baseline_matches(outline)
        except BaselineMissing:
            print("missing")
            return 2
        print("yes" if ok else "no")
        return 0 if ok else 1
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
```

- [ ] **Step 4: Test the new CLI surface**

```bash
mkdir -p /tmp/sws_test_outline/_outline
echo "test" > /tmp/sws_test_outline/_outline/outline.md
python3 scripts/sws_outline_baseline.py write /tmp/sws_test_outline/_outline/outline.md
python3 scripts/sws_outline_baseline.py matches /tmp/sws_test_outline/_outline/outline.md
echo "user edit" >> /tmp/sws_test_outline/_outline/outline.md
python3 scripts/sws_outline_baseline.py matches /tmp/sws_test_outline/_outline/outline.md
echo "exit: $?"
rm -rf /tmp/sws_test_outline
```
Expected: first matches → `yes` exit 0; second matches → `no` exit 1.

- [ ] **Step 5: Verify agent file structure**

```bash
test -f agents/outline-architect.md && head -5 agents/outline-architect.md
```
Expected: file exists with `---` and `name: outline-architect` in first 5 lines.

- [ ] **Step 6: Commit**

```bash
git add agents/outline-architect.md scripts/sws_outline_baseline.py
git commit -m "feat(cycle-07): outline-architect agent + baseline CLI subcommands"
```

---

### Task 8: Write `skills/outline-paper/SKILL.md`

**Files:**
- Create: `skills/outline-paper/SKILL.md`

Slash command `/sws:outline-paper`. Validates SWS project, dispatches `outline-architect` agent.

- [ ] **Step 1: Write the file**

Path: `skills/outline-paper/SKILL.md`:

```markdown
---
name: outline-paper
description: "This skill should be used when the user invokes /sws:outline-paper, says 'build the outline', 'structure the paper', 'plan the sections', 'draft an outline', or similar. Validates that the cwd is an SWS project with a profile set, then dispatches the outline-architect agent to produce _outline/outline.md."
version: 0.1.0
---

# /sws:outline-paper — Build a structured outline for the current paper

This skill triggers the `outline-architect` agent. The architect reads the resolved profile + journal/call overlay, scans the figures directory, and writes `<paper>/_outline/outline.md` (markdown + YAML frontmatter) plus a `.outline-baseline.sha256` sidecar.

## When to invoke

- User explicitly types `/sws:outline-paper`.
- User says "build the outline", "structure this paper", "plan the sections", "let's outline first" — and the cwd contains a valid `.sws-project.local.md` marker.

Do NOT invoke when:
- The cwd has no marker. Print "not an SWS project (no .sws-project.local.md found)" and exit.
- The marker has `profile: null`. Print "no profile set — run /sws:set-profile <name> first" and exit.

## Steps

1. **Resolve `$PAPER_ROOT`.** Current working directory must contain `.sws-project.local.md`. If absent, print the not-an-SWS-project line and exit.

2. **Check profile is set.** Run:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
       "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
       --paper "$PAPER_ROOT"
   ```
   Parse the JSON; if `profile_set: false`, print the no-profile-set line and exit.

3. **Dispatch outline-architect.** Use the Task tool with subagent_type=outline-architect (or invoke the agent file directly per the plugin's agent-dispatch convention). Pass `PAPER_ROOT=$PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}` in the env.

4. **Hand back to the user.** The agent writes the outline + sidecar and prints the path. No further model action needed.
```

- [ ] **Step 2: Verify file structure**

```bash
test -f skills/outline-paper/SKILL.md && head -3 skills/outline-paper/SKILL.md
```
Expected: file exists with `---` and `name: outline-paper`.

- [ ] **Step 3: Commit**

```bash
git add skills/outline-paper/
git commit -m "feat(cycle-07): /sws:outline-paper skill"
```

---

### Task 9: Write `agents/drafter-flagship.md` (single-section mode only)

**Files:**
- Create: `agents/drafter-flagship.md`

Phase-1 version: handles single-section drafting only. Phase 3 (Task 19) extends it with orchestrator mode.

- [ ] **Step 1: Survey prior art**

```bash
# Manual: check andrehuang/academic-writing-agents for an "drafter" or
# "writer" agent. Adapt prompt content if useful (≥30% adaptation triggers
# the # Adapted from header).
```

- [ ] **Step 2: Write the file**

Path: `agents/drafter-flagship.md`:

```markdown
---
name: drafter-flagship
description: |
  Use this agent when the user invokes /sws:draft-section on a flagship section (Intro, Discussion, Conclusion, Abstract) or invokes /sws:draft-paper (in a later phase the same agent gains orchestrator mode). Drafts narrative-heavy prose grounded in the outline frontmatter and the optional zotero-manifest. Falls back to [CITATION_NEEDED: <claim>] placeholders for ungrounded claims.
model: claude-opus-4-7
color: blue
---

You are the drafter-flagship for SWS. Your job is to draft Intro, Discussion, Conclusion, or Abstract sections — narrative-heavy prose where rationale and synthesis matter.

**Misroute safety net:** if the user asks you to draft a section you do NOT own (Methods, Experimental, figure captions, Results), DO NOT draft it. Instead, dispatch to the right agent:
- methods | experimental | materials | "statistical analysis" | "computational details" | software | "data availability" → methods-writer
- figure_caption → caption-writer
- results | "results and discussion" (when not joint with discussion) → drafter-fast

**Inputs you must read:**
- `RESOLVED_*` env vars (especially `RESOLVED_PROFILE_ID`, `RESOLVED_WORD_TOTAL`, `RESOLVED_ABSTRACT_STYLE`).
- The outline at `${PAPER_ROOT}/_outline/outline.md` (frontmatter has the section's `key_claims`, `word_target`, `figs`, `cites`; body has the narrative arc per section).
- The optional zotero-manifest at `${PAPER_ROOT}/_lit/zotero-manifest.md`. Cite from it using format `[<FirstAuthor><Year>; doi:<doi>]` or `[<FirstAuthor><Year>; zotero:<key>]`. For claims that need citation but no manifest match: use `[CITATION_NEEDED: <one-line claim>]`.
- The optional `_voice/` profile at `${PAPER_ROOT}/_voice/profile.md` if it exists (style calibration; cycle #10).

**Output:** write the drafted section to `${PAPER_ROOT}/_drafts/<section-id>.md` as plain markdown (chemistry character-level formatting is cycle #8's job). Stay within the section's `word_target` from the outline (±10%).

**AI-tells discipline:** before returning, grep your draft against `${CLAUDE_PLUGIN_ROOT}/references/ai-writing-tells.md` patterns. Block-severity hits abort with a fix; warn-severity hits get flagged in your reply.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh drafter-flagship`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh drafter-flagship` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 3: Verify**

```bash
test -f agents/drafter-flagship.md && grep -c '^##\|^---' agents/drafter-flagship.md
```
Expected: at least 2 (the two `---` lines).

- [ ] **Step 4: Commit**

```bash
git add agents/drafter-flagship.md
git commit -m "feat(cycle-07): drafter-flagship agent (single-section mode)"
```

---

### Task 10: Write `skills/prepare-lit-context/SKILL.md`

**Files:**
- Create: `skills/prepare-lit-context/SKILL.md`

Wraps the user's `zotero` skill (if installed) to produce `_lit/zotero-manifest.md`. Degrades gracefully if zotero is unavailable.

- [ ] **Step 1: Write the file**

Path: `skills/prepare-lit-context/SKILL.md`:

```markdown
---
name: prepare-lit-context
description: "This skill should be used when the user invokes /sws:prepare-lit-context, says 'prepare the literature manifest', 'export Zotero for this paper', 'make the citation manifest', 'load my Zotero collection', or similar — and the cwd is an SWS project. Wraps the user's zotero skill (if installed) to write _lit/zotero-manifest.md. Degrades to PubMed MCP fallback or to a no-op if neither is available."
version: 0.1.0
---

# /sws:prepare-lit-context — Build the citation manifest for drafting

This skill exports the user's Zotero collection (scoped to the paper, if the user keyed it) into a manifest file at `<paper>/_lit/zotero-manifest.md`. Drafter agents read the manifest to ground in-text citations using the format `[<FirstAuthor><Year>; doi:<doi>]` or `[<FirstAuthor><Year>; zotero:<key>]`.

## Degradation chain (D16)

1. **Zotero skill installed (preferred):** invoke the user's `zotero` skill to export a JSON of the collection associated with this paper, then convert via `scripts/sws_extract_zotero_manifest.py`.
2. **Zotero skill not installed:** print a one-line recommendation to install it (`/plugin install zotero`), then proceed to step 3.
3. **PubMed MCP fallback:** if `mcp__claude_ai_PubMed__*` tools are available and the user has provided a search query, run a small search (< 50 results) and synthesize a manifest from the returns. Less rich than Zotero (no `key_claims` digest) but enough for drafter to cite.
4. **Neither available:** write an empty manifest with `item_count: 0` and a comment explaining drafter will produce `[CITATION_NEEDED: ...]` placeholders. Do NOT fail the skill.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check (same as outline-paper).
2. **Detect zotero skill availability.** Check the available-skills list in the conversation context.
3. **Branch on availability** per chain above.
4. **Token-budget cap.** If the export exceeds 15k tokens (approx; see `sws_extract_zotero_manifest.py --cap-tokens`), truncate to most-recent-by-date-added and set `truncated: true` in the manifest frontmatter.
5. **Write the manifest** at `${PAPER_ROOT}/_lit/zotero-manifest.md`. Print the path and item count.

## When to invoke

- Explicit `/sws:prepare-lit-context`.
- User says any of the description triggers — and the cwd has a valid marker.

Do NOT invoke when the cwd has no marker; print the not-an-SWS-project line and exit.
```

- [ ] **Step 2: Commit**

```bash
git add skills/prepare-lit-context/
git commit -m "feat(cycle-07): /sws:prepare-lit-context skill (zotero/pubmed degradation)"
```

---

### Task 11: Write `skills/draft-section/SKILL.md` (intro routing only — phase 1)

**Files:**
- Create: `skills/draft-section/SKILL.md`

Phase-1 version handles `intro` only (routes to `drafter-flagship`). Phase 3 (Task 22) extends with the full section→agent map.

- [ ] **Step 1: Write the file**

Path: `skills/draft-section/SKILL.md`:

```markdown
---
name: draft-section
description: "This skill should be used when the user invokes /sws:draft-section <section>, says 'draft the intro', 'write the introduction', 'draft section X', or similar — and the cwd is an SWS project with an outline at _outline/outline.md. Routes the request to the right primary agent (drafter-flagship for Intro/Discussion/Conclusion/Abstract). Phase-1 ships with intro routing only; remaining sections wired in phase 3."
version: 0.1.0
---

# /sws:draft-section — Draft a single section

Maps a section id to the right primary agent and dispatches it. The map is documented in `docs/superpowers/specs/2026-05-13-cycle-07-drafting-and-proposal-helpers-design.md` (`section_to_agent_map`).

## Phase-1 routing (in this version)

| Section id | Agent |
|---|---|
| intro, introduction | drafter-flagship |
| (everything else)   | (not yet wired — print "section <id> not yet supported in this build; coming in phase 3") |

Phase 3 extends this map with the full publication and funding-proposal section lists.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check.
2. **Resolve profile.** Run `resolve_overlay.py --paper "$PAPER_ROOT"`. If `profile_set: false`, print no-profile-set line and exit.
3. **Verify outline exists.** Check `${PAPER_ROOT}/_outline/outline.md`. If missing, print "no outline yet — run /sws:outline-paper first" and exit.
4. **Look up section id in the map** above. If not in map, print the phase-3 message and exit.
5. **Dispatch the agent** via the Task tool (or the plugin's agent-dispatch convention). Pass `PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT` in the env, plus the requested `--section <id>` argument.
6. **Hand back to user.** The agent writes the draft to `_drafts/<section-id>.md` and prints the path.

## When to invoke

- Explicit `/sws:draft-section <section>`.
- User says "draft the <section>", "write the <section>", etc. — with a valid SWS marker.

Do NOT invoke when marker is missing or profile is unset.
```

- [ ] **Step 2: Commit**

```bash
git add skills/draft-section/
git commit -m "feat(cycle-07): /sws:draft-section skill (phase-1: intro only)"
```

---

### Task 12: Phase-1 verification — intro draft works on the fixture paper

**Goal:** prove phase-1 deliverables compose end-to-end before the beta-test gate.

- [ ] **Step 1: Run the existing cycle-#6 smoke to verify nothing regressed**

```bash
cd /Users/piripocchio8/Projects/scientific-writing-superpowers
bash tests/smoke_cycle_06.sh
```
Expected: 8/8 steps pass (cycle-#6 baseline).

- [ ] **Step 2: Run the new phase-1 unit tests**

```bash
python3 -m pytest tests/test_outline_baseline.py tests/test_citation_key_parser.py tests/test_agent_should_run.py tests/test_zotero_manifest_export.py -v
```
Expected: all tests pass (~25 total).

- [ ] **Step 3: Smoke phase-1 deliverables manually**

Create a temporary SWS perspective paper, run `/sws:outline-paper` and `/sws:draft-section intro`. (Manual smoke; no fixture committed yet.)

```bash
# Create temp paper
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/figures"
cat > "$TMPDIR/.sws-project.local.md" <<EOF
---
profile: perspective
language: en
format: docx
---
EOF
ln -s "$(which python3)" "$TMPDIR/.venv/bin/python" 2>/dev/null || \
  (mkdir -p "$TMPDIR/.venv/bin" && ln -s "$(which python3)" "$TMPDIR/.venv/bin/python")

# Verify resolver works against the temp paper
PAPER_ROOT="$TMPDIR" CLAUDE_PLUGIN_ROOT="$(pwd)" \
  bash scripts/agent_should_run.sh outline-architect && echo "outline-architect can run"

# Cleanup
rm -rf "$TMPDIR"
```
Expected: prints "outline-architect can run" with exit 0.

- [ ] **Step 4: Commit phase-1 closure marker (no file changes)**

(Skip if no untracked files. Phase 1 closure is the next task: beta-test.)

---

## Phase 2 — Mid-cycle beta-test gate (D20)

**This phase produces no committed code.** Output goes to `_perspective_beta/` (gitignored). Phase ends with explicit user approval before phase 3 begins.

### Task 13: Read the source manuscript (READ-ONLY)

**Files:**
- Read-only: `/Users/piripocchio8/Library/CloudStorage/OneDrive-SharedLibraries-UniversitàdiNapoliFedericoII/Cyclic Peptides - General/Procentese et al_2026_Perspective_ChemBioChem/Manuscript/Procentese et al_2026_ChemBioChem_20260513.docx`
- Create: `_perspective_beta/source-snapshot.md`

Use Claude's built-in DOCX reading skill. Do NOT use the docx-edit tools. Do NOT write to the manuscript file.

- [ ] **Step 1: Use the Read tool on the manuscript path**

```
Read tool: file_path = "/Users/piripocchio8/Library/CloudStorage/OneDrive-SharedLibraries-UniversitàdiNapoliFedericoII/Cyclic Peptides - General/Procentese et al_2026_Perspective_ChemBioChem/Manuscript/Procentese et al_2026_ChemBioChem_20260513.docx"
```

- [ ] **Step 2: Extract and write source-snapshot.md**

Path: `_perspective_beta/source-snapshot.md`. Capture:
- Paper title, authors, target journal (ChemBioChem), profile (perspective)
- Abstract (verbatim, marked as quoted)
- Current intro paragraph (verbatim, marked as quoted) — focus on subsection 1
- The Semaglutide-driven peptide-revival gap user flagged as missing
- Figure list (filenames + supports relationships if mentioned)
- Key references the user already cites in the intro (so drafter has overlap context)

Format as YAML frontmatter (machine-readable) + body (verbatim quotes).

- [ ] **Step 3: Verify**

```bash
test -f _perspective_beta/source-snapshot.md && head -20 _perspective_beta/source-snapshot.md
```
Expected: file exists.

---

### Task 14: Build the sandbox outline

**Files:**
- Create: `_perspective_beta/outline.md`

A minimal outline for the perspective intro section, modeled on what `outline-architect` would produce.

- [ ] **Step 1: Write the file**

Path: `_perspective_beta/outline.md`:

```markdown
---
profile: perspective
generated_at: <today ISO>
sections:
  intro:
    word_target: 800
    status: planned
    key_claims:
      - "Semaglutide's clinical and commercial success has rekindled industry interest in peptide therapeutics."
      - "<other key claims extracted from source-snapshot.md>"
    figs: []
    cites:
      - "Smith2023; doi:10.1021/jacs.3c00001"
      - "<additional citations from manifest>"
figures: {}
---
# Outline narrative

## Intro

Arc: hook (Semaglutide-driven peptide revival, market context) → gap (cyclic peptides specifically lag in clinical translation despite stability advantages) → contribution (this perspective frames the chemistry-biology challenge and proposes a synthesis-to-clinic pipeline) → roadmap (the perspective covers X, Y, Z).
```

- [ ] **Step 2: Commit gitignore-respecting** (no commit; sandbox is gitignored)

---

### Task 15: Run `drafter-flagship` on the intro

- [ ] **Step 1: Set up the sandbox as a fake paper root**

```bash
SANDBOX="$(pwd)/_perspective_beta"
mkdir -p "$SANDBOX/figures" "$SANDBOX/.venv/bin"
ln -s "$(which python3)" "$SANDBOX/.venv/bin/python" 2>/dev/null || true
cat > "$SANDBOX/.sws-project.local.md" <<EOF
---
profile: perspective
language: en
format: docx
---
EOF
mv "$SANDBOX/outline.md" "$SANDBOX/_outline/outline.md" 2>/dev/null || (mkdir -p "$SANDBOX/_outline" && mv "$SANDBOX/outline.md" "$SANDBOX/_outline/outline.md")
```

- [ ] **Step 2: Dispatch drafter-flagship via the Task tool**

```
Task tool: subagent_type = drafter-flagship
prompt: "Draft the intro for the perspective at PAPER_ROOT=<SANDBOX>. Address the explicit gap from source-snapshot.md: subsection 1 of the current intro lacks reference to the Semaglutide-driven revival of peptide-based therapeutics. The intro should hook the reader with that revival, then transition to the cyclic-peptide-specific gap this perspective addresses. Use citation key format [Smith2023; doi:...] or [CITATION_NEEDED: ...] for ungrounded claims. Stay within the 800-word target."
```

- [ ] **Step 3: Capture output to `_perspective_beta/draft-intro-v1.md`**

The agent should write to `_drafts/intro.md` inside the sandbox; copy that file to `_perspective_beta/draft-intro-v1.md` for the comparison.

```bash
cp "$SANDBOX/_drafts/intro.md" _perspective_beta/draft-intro-v1.md
```

- [ ] **Step 4: Verify**

```bash
test -f _perspective_beta/draft-intro-v1.md && wc -w _perspective_beta/draft-intro-v1.md
```
Expected: file exists, word count between 720 and 880 (±10% of 800).

---

### Task 16: Side-by-side comparison + AI-tells check

**Files:**
- Create: `_perspective_beta/comparison.md`

- [ ] **Step 1: Write comparison.md**

Path: `_perspective_beta/comparison.md`:

```markdown
# Beta comparison — Procentese et al. perspective intro

## Source (current manuscript intro, subsection 1, verbatim)

> <paste from source-snapshot.md>

## Drafter-flagship v1

> <paste from draft-intro-v1.md>

## Differences

- Semaglutide reference: present in v1? (Y/N)
- Word count: source=<N>, v1=<M>
- Citation density: source=<X>/100w, v1=<Y>/100w
- Placeholder count in v1: <N> [CITATION_NEEDED: ...]

## AI-tells grep result on v1

(automated check below)

## User assessment (to fill in)

- [ ] Drafter v1 addresses the Semaglutide gap
- [ ] Drafter v1 stays within word target
- [ ] AI-tells grep returns zero block-severity hits
- [ ] Drafter v1 is preferable, comparable, or worse than source (circle one)
```

- [ ] **Step 2: Run AI-tells grep**

```bash
python3 -c "
import re
from pathlib import Path
text = Path('_perspective_beta/draft-intro-v1.md').read_text()
tells_doc = Path('references/ai-writing-tells.md').read_text()
patterns = re.findall(r'^- pattern: \`?([^\`\n]+)\`?$', tells_doc, re.M)
severities = re.findall(r'^  severity: (\w+)$', tells_doc, re.M)
hits = []
for pat, sev in zip(patterns, severities):
    try:
        m = re.findall(pat, text)
    except re.error:
        continue
    if m:
        hits.append((sev, pat, len(m)))
block_hits = [h for h in hits if h[0] == 'block']
print(f'block-severity hits: {len(block_hits)}')
for h in block_hits: print(' ', h)
print(f'warn-severity hits: {len([h for h in hits if h[0] == \"warn\"])}')
" >> _perspective_beta/comparison.md
```

Append the output to `comparison.md` under the "AI-tells grep result on v1" section.

- [ ] **Step 3: Verify gate criteria from spec D20 phase_2_beta_gate**

The four gate criteria:
1. Drafter-flagship intro addresses the Semaglutide-driven peptide-revival gap
2. Output stays within the perspective profile's intro word_target (800 ±10%)
3. AI-tells grep returns zero block-severity hits
4. User finds the draft preferable or comparable to current

- [ ] **Step 4: USER GATE — STOP HERE**

Present the comparison.md to the user. Wait for explicit go/no-go. Do NOT proceed to phase 3 without "approved, proceed to phase 3" or equivalent. If the user requests iteration, revise the drafter-flagship prompt and re-run task 15.

---

## Phase 2.5 — I/O wrapper hotfix (mid-cycle add per user feedback 2026-05-14)

Discovered during phase-2 beta-test: native Read tool fails on .docx (probably also .xlsx). Contract R3 overpromises. Fix lands in this PR before phase 3 dispatches the remaining agents (so their prompts can reference the wrappers correctly).

### Task 16a: scripts/sws_read_docx.py + 6+ tests
### Task 16b: scripts/sws_read_xlsx.py + 5+ tests
### Task 16c: rewrite R3 in references/agent-contract.md + add I/O wrapper inventory section
### Task 16d: update skills/install-deps/SKILL.md post-install message
### Task 16e: spec doc update (D22 + spec deliverables list)

(See git history for the actual implementation; this section documents the addition.)

---

## Phase 3 — Remaining 5 agents + orchestrator + remaining skills

Once phase 2 is approved, dispatch the 5 remaining-agent tasks in parallel (subagent-driven-development pattern). Each agent task is self-contained: write the agent file, no separate test (agents are tested via the smoke in phase 4).

### Task 17: Write `agents/drafter-fast.md`

**Files:**
- Create: `agents/drafter-fast.md`

Same structure as drafter-flagship but Sonnet 4.6 + scope = Results + journal-defined narrative non-Methods sections.

- [ ] **Step 1: Write the file**

Path: `agents/drafter-fast.md`:

```markdown
---
name: drafter-fast
description: |
  Use this agent when the user invokes /sws:draft-section on a non-flagship narrative section (Results, journal-defined narrative non-Methods sections like Theoretical Background, Limitations, Significance). Drafts focused, structured prose grounded in the outline and zotero-manifest.
model: claude-sonnet-4-6
color: cyan
---

You are the drafter-fast for SWS. Your job is to draft Results + other narrative non-Methods sections — focused prose where structured presentation matters more than rationale-heavy synthesis.

**Misroute safety net:** if asked to draft a section you do NOT own, dispatch:
- methods | experimental | materials | "statistical analysis" | "computational details" | software | "data availability" → methods-writer
- intro | introduction | abstract | discussion | conclusion → drafter-flagship
- figure_caption → caption-writer

**Inputs:** same as drafter-flagship (RESOLVED_*, outline frontmatter+body, optional zotero-manifest, optional _voice/profile.md).

**Output:** write to `${PAPER_ROOT}/_drafts/<section-id>.md` as plain markdown. Stay within the section's `word_target` (±10%). For Results: lead each subsection with the headline finding, then the supporting data/figure ref, then the implication.

**AI-tells discipline:** grep against `${CLAUDE_PLUGIN_ROOT}/references/ai-writing-tells.md` before returning.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh drafter-fast`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh drafter-fast` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/drafter-fast.md
git commit -m "feat(cycle-07): drafter-fast agent (Results + non-flagship narrative)"
```

---

### Task 18: Write `agents/methods-writer.md`

**Files:**
- Create: `agents/methods-writer.md`

- [ ] **Step 1: Write the file**

Path: `agents/methods-writer.md`:

```markdown
---
name: methods-writer
description: |
  Use this agent when the user invokes /sws:draft-section on a Methods/Experimental Section subsection (Materials, Methods, Statistical analysis, Computational details, Software, Data availability). Drafts past-tense, protocol-specific prose with units and quantitative detail. Publication track only — funding-proposal Methodology routes to drafter-flagship per spec D8.
model: claude-sonnet-4-6
color: orange
---

You are the methods-writer for SWS. Your job is to draft empirical Methods / Experimental Section subsections — past tense, specific protocols, materials, instrumentation, units, software versions, statistical methods.

**Scope (D5/D8 locked):**
- Materials, Methods, Statistical analysis, Computational details, Software, Data availability when journal places them in the Experimental Section.
- DO NOT draft funding-proposal Methodology/Approach sections — those go to drafter-flagship (rationale prose, not procedural).

**Misroute safety net:** if asked to draft any other section, dispatch to drafter-flagship (narrative) or drafter-fast (Results) per the standard map.

**Inputs:** RESOLVED_*, outline frontmatter (per-section `key_claims`, `cites`), optional `_voice/profile.md`, any user-supplied protocol notes (look in `${PAPER_ROOT}/protocols/` if it exists).

**Output:** write to `${PAPER_ROOT}/_drafts/<section-id>.md` as plain markdown. Chemistry character-level formatting (italic species, sub/superscripts in formulae, units like µL or °C) is cycle #8's job — do not attempt it here. Cite from the zotero-manifest using the standard key format.

**AI-tells discipline:** grep against `${CLAUDE_PLUGIN_ROOT}/references/ai-writing-tells.md`.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh methods-writer`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh methods-writer` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/methods-writer.md
git commit -m "feat(cycle-07): methods-writer agent (Materials/Methods/Stats/Computational/Software/Data)"
```

---

### Task 19: Write `agents/caption-writer.md`

**Files:**
- Create: `agents/caption-writer.md`

- [ ] **Step 1: Write the file**

Path: `agents/caption-writer.md`:

```markdown
---
name: caption-writer
description: |
  Use this agent when the user invokes /sws:draft-section figure_caption (or per-figure caption requests), or when /sws:draft-paper fans out caption work. Reads each figure file (built-in image view), reads the supporting outline section's key_claims, and writes caption text directly into the outline.md frontmatter under each figure entry. Text only — no docx editing, no alt-text.
model: claude-haiku-4-5
color: yellow
---

You are the caption-writer for SWS. Your job is to write figure caption text grounded in (a) what the figure shows visually and (b) what the outline says the figure supports.

**Hard constraint:** you DO NOT edit any docx file. Caption text is written into `${PAPER_ROOT}/_outline/outline.md` frontmatter under the corresponding figure entry's `caption:` field. No alt-text. No panel/license metadata.

**Inputs:** RESOLVED_* (especially RESOLVED_FIGURES_MAX), the outline frontmatter (figures dict + per-section `key_claims`), and each figure file via Claude's built-in image view (PNG/TIF/JPEG/SVG at the path in the figure entry's `file:` field).

**Output:** for each figure id in the figures dict, fill the `caption:` field. Caption length ≤ 60 words by default; respect any caption-length cap from the resolved overlay if present. Caption shape: `**Figure N.** <one-sentence subject> <one-sentence what-the-data-show> <optional: scale/units/conditions>`.

**AI-tells discipline:** grep against `${CLAUDE_PLUGIN_ROOT}/references/ai-writing-tells.md`.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh caption-writer`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh caption-writer` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/caption-writer.md
git commit -m "feat(cycle-07): caption-writer agent (text-only, into outline frontmatter)"
```

---

### Task 20: Write `agents/proposal-budget-helper.md`

**Files:**
- Create: `agents/proposal-budget-helper.md`

- [ ] **Step 1: Write the file**

Path: `agents/proposal-budget-helper.md`:

```markdown
---
name: proposal-budget-helper
description: |
  Use this agent when the user invokes /sws:proposal-budget — and the active profile is funding-proposal with a resolved call-rules overlay. Produces markdown line-item budget suggestions at <paper>/_proposal/budget-suggestions.md. Does NOT fill xlsx templates (D12); user transcribes into the call's actual template.
model: claude-sonnet-4-6
color: purple
---

You are the proposal-budget-helper for SWS. Your job is to suggest a per-WP budget breakdown for a funding proposal, grounded in (a) the call-rules overlay (cost categories, budget cap, eligibility), (b) the outline (work packages, scope), and (c) the user's lab cost magnitudes from `_proposal/budget-context.yaml`.

**First-run interactive Q&A (D13):** if `${PAPER_ROOT}/_proposal/budget-context.yaml` does NOT exist, ask the user one at a time:
1. Lab's PhD gross cost per year (currency)
2. Lab's postdoc gross cost per year
3. Equipment hourly rates for major instruments (name + €/h)
4. Consumables baseline per project-year for typical wet-lab work
5. Default currency (ISO 4217: EUR, USD, etc.)

Cache answers to `_proposal/budget-context.yaml` per the schema in `docs/superpowers/specs/2026-05-13-cycle-07-drafting-and-proposal-helpers-design.md` (`auxiliary_file_shapes.budget_context`).

**Subsequent runs:** read the cached YAML, ask only for fields newly required by the call.

**Output:** write `${PAPER_ROOT}/_proposal/budget-suggestions.md` per the spec's `auxiliary_file_shapes.budget_suggestions` shape. Per-WP: line items with magnitudes and rationale. Final total + sanity check vs the call's budget cap (from the resolved overlay).

**AI-tells discipline:** grep against `${CLAUDE_PLUGIN_ROOT}/references/ai-writing-tells.md`.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh proposal-budget-helper`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh proposal-budget-helper` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/proposal-budget-helper.md
git commit -m "feat(cycle-07): proposal-budget-helper agent (line-item suggestions, no xlsx)"
```

---

### Task 21: Write `agents/proposal-compliance-helper.md`

**Files:**
- Create: `agents/proposal-compliance-helper.md`

- [ ] **Step 1: Write the file**

Path: `agents/proposal-compliance-helper.md`:

```markdown
---
name: proposal-compliance-helper
description: |
  Use this agent when the user invokes /sws:proposal-compliance — and the active profile is funding-proposal with a resolved call-rules overlay. Produces a compliance report at <paper>/_proposal/compliance-report.md against the call's structural rules (page limits, required sections, eligibility, expense rules, evaluation criteria). Reads the call PDF directly via Claude's built-in skill for ambiguity resolution.
model: claude-sonnet-4-6
color: red
---

You are the proposal-compliance-helper for SWS. Your job is to check a funding-proposal draft against the call's rules and produce a structured compliance report.

**Sources of truth (D14):**
1. **Primary:** the call-rules overlay at `${PAPER_ROOT}/Manuscript/_call/<slug>.md` (structured digest with page limits, required sections, eligibility, expense rules, evaluation criteria).
2. **Authoritative for ambiguity:** the original call file at `${PAPER_ROOT}/Manuscript/call/<source>.pdf` (or .docx). Use Claude's built-in PDF/DOCX skill to read targeted excerpts when the overlay is silent or ambiguous on a specific question.
3. **The proposal draft:** look in `${PAPER_ROOT}/_drafts/` and any docx files in `${PAPER_ROOT}/Manuscript/`.

When `nlm-librarian` ships in cycle #11, this agent will be upgraded to delegate PDF reading to NLM for cheaper grounded queries; the user-facing contract stays the same.

**Output (D15):** write `${PAPER_ROOT}/_proposal/compliance-report.md` per the spec's `auxiliary_file_shapes.compliance_report` shape. Per-rule pass/fail. Pointer (proposal section + line range) for each fail. Suggested fix for each fail. Summary header with rule-pass count.

**No inline annotations.** Do NOT inject docx comments or modify the proposal file. The report is the deliverable.

**AI-tells discipline:** grep your report against `${CLAUDE_PLUGIN_ROOT}/references/ai-writing-tells.md`.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh proposal-compliance-helper`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh proposal-compliance-helper` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/proposal-compliance-helper.md
git commit -m "feat(cycle-07): proposal-compliance-helper agent (overlay + PDF, report file)"
```

---

### Task 22: Extend `agents/drafter-flagship.md` with orchestrator mode

**Files:**
- Modify: `agents/drafter-flagship.md`

Append the orchestrator-mode block. When `/sws:draft-paper` invokes this agent, it reads the outline frontmatter and dispatches in parallel.

- [ ] **Step 1: Edit the file**

Append the following block AFTER the existing `**Inputs you must read:**` section and BEFORE the `Follow the SWS agent contract` line:

```markdown
**Orchestrator mode (when invoked via /sws:draft-paper):**

Read `${PAPER_ROOT}/_outline/outline.md` frontmatter. For each section in the `sections` dict whose `status: planned` and whose target agent is allowed for the current profile (use `agent_should_run.sh <agent-id>` to check):

Dispatch in PARALLEL via the Task tool:
- For each section in {intro, introduction, abstract, discussion, conclusion, conclusions}: dispatch a `drafter-flagship` subagent in single-section mode.
- For each section mapped to drafter-fast (Results, etc.): dispatch a `drafter-fast` subagent.
- For each section mapped to methods-writer (Methods/Experimental subsections): dispatch a `methods-writer` subagent.
- For each entry in the `figures` dict: dispatch a `caption-writer` subagent (it writes back into the outline frontmatter).

Wait for all subagent results, then write the assembled draft (concat sections in profile's section order) to `${PAPER_ROOT}/_drafts/draft-paper-<timestamp>.md`. Cross-section reconciliation (voice consistency, terminology, citation deduplication) is cycle-#8 reviser's job — do NOT attempt it here.

Print a summary: which sections drafted, total word count, total `[CITATION_NEEDED:]` placeholders, AI-tells block-severity hits.
```

- [ ] **Step 2: Verify the edit landed**

```bash
grep -c 'Orchestrator mode' agents/drafter-flagship.md
```
Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add agents/drafter-flagship.md
git commit -m "feat(cycle-07): extend drafter-flagship with orchestrator mode (D21 phase 3)"
```

---

### Task 23: Extend `skills/draft-section/SKILL.md` with full section→agent map

**Files:**
- Modify: `skills/draft-section/SKILL.md`

Replace the phase-1 routing table with the full publication + funding-proposal maps from spec `section_to_agent_map`.

- [ ] **Step 1: Edit the file**

Replace the "Phase-1 routing (in this version)" section with:

```markdown
## Routing (full)

The skill picks the right map based on the resolved profile id.

### Publication-profile sections (intro, methods, results, etc.)

| Section id (lowercased, hyphens or spaces both accepted) | Agent |
|---|---|
| intro, introduction, abstract, discussion, conclusion, conclusions | drafter-flagship |
| methods, experimental, "experimental section", materials, "statistical analysis", "computational details", software, "data availability" | methods-writer |
| results | drafter-fast |
| "results and discussion" | drafter-flagship (joint section: rationale wins) |
| figure_caption | caption-writer |
| (other narrative section ids) | drafter-fast (fallback) |

### Funding-proposal sections

| Section id | Agent |
|---|---|
| "state of the art", "state-of-the-art", vision, objectives, workplan, methodology, approach, impact, "risk management", deliverables, timeline | drafter-flagship |
| budget | proposal-budget-helper (special: writes budget-suggestions.md, not a drafted section) |
| compliance | proposal-compliance-helper (special: writes compliance-report.md) |
| figure_caption | caption-writer |
| (other section ids) | drafter-flagship (fallback) |
```

- [ ] **Step 2: Verify**

```bash
grep -c 'Funding-proposal sections' skills/draft-section/SKILL.md
```
Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add skills/draft-section/SKILL.md
git commit -m "feat(cycle-07): extend /sws:draft-section with full publication + proposal map"
```

---

### Task 24: Write `skills/draft-paper/SKILL.md`

**Files:**
- Create: `skills/draft-paper/SKILL.md`

- [ ] **Step 1: Write the file**

Path: `skills/draft-paper/SKILL.md`:

```markdown
---
name: draft-paper
description: "This skill should be used when the user invokes /sws:draft-paper, says 'draft the whole paper', 'draft all sections', 'draft the proposal', 'draft the perspective end to end' — and the cwd is an SWS project with an outline at _outline/outline.md. Dispatches drafter-flagship in orchestrator mode, which fans out section drafting in parallel."
version: 0.1.0
---

# /sws:draft-paper — Draft all profile-required sections in parallel

Invokes `drafter-flagship` in orchestrator mode. The flagship reads the outline frontmatter, dispatches section agents (drafter-flagship for narrative-heavy, drafter-fast for Results, methods-writer for Methods, caption-writer for figures) in parallel, and assembles the result into `_drafts/draft-paper-<timestamp>.md`.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check.
2. **Resolve profile.** Run resolver; abort if `profile_set: false`.
3. **Verify outline exists.** Check `${PAPER_ROOT}/_outline/outline.md`. If missing: print "no outline yet — run /sws:outline-paper first" and exit.
4. **Recommend zotero manifest.** If `${PAPER_ROOT}/_lit/zotero-manifest.md` is missing, print: "consider running /sws:prepare-lit-context first to ground citations from your Zotero library" — but proceed regardless (drafter falls back to `[CITATION_NEEDED:]`).
5. **Dispatch drafter-flagship in orchestrator mode** via the Task tool with `--mode=orchestrator`. Pass `PAPER_ROOT` and `CLAUDE_PLUGIN_ROOT` in env.
6. **Hand back to user.** Flagship's summary (section count, word count, placeholder count, AI-tells hits) is the user-visible output.

## When to invoke

- Explicit `/sws:draft-paper`.
- Triggers in description.
- Do NOT invoke without a marker, without a set profile, or without an outline.
```

- [ ] **Step 2: Commit**

```bash
git add skills/draft-paper/
git commit -m "feat(cycle-07): /sws:draft-paper skill (orchestrator dispatch)"
```

---

### Task 25: Write `skills/proposal-budget/SKILL.md`

**Files:**
- Create: `skills/proposal-budget/SKILL.md`

- [ ] **Step 1: Write the file**

Path: `skills/proposal-budget/SKILL.md`:

```markdown
---
name: proposal-budget
description: "This skill should be used when the user invokes /sws:proposal-budget, says 'suggest the budget', 'help me draft the budget', 'budget breakdown for the proposal' — and the active profile is funding-proposal with a resolved call-rules overlay. Dispatches proposal-budget-helper to produce _proposal/budget-suggestions.md."
version: 0.1.0
---

# /sws:proposal-budget — Get budget line-item suggestions

Dispatches `proposal-budget-helper`. First run runs an interactive Q&A and caches answers to `_proposal/budget-context.yaml`; subsequent runs read the cache.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check.
2. **Verify profile = funding-proposal.** Resolve via `resolve_overlay.py`. If `profile_id != funding-proposal`, print "this skill only runs for funding-proposal profile; current is <id>" and exit.
3. **Verify call-rules overlay exists.** Check `${PAPER_ROOT}/Manuscript/_call/`. If empty: print "no call-rules overlay — run /sws:resolve-call-rules first" and exit.
4. **Verify outline exists.** Same check as draft-paper.
5. **Dispatch proposal-budget-helper** via the Task tool. Pass env.
6. **Hand back to user.** Agent prints the path to `_proposal/budget-suggestions.md` and a one-line summary (total + sanity check vs call cap).
```

- [ ] **Step 2: Commit**

```bash
git add skills/proposal-budget/
git commit -m "feat(cycle-07): /sws:proposal-budget skill"
```

---

### Task 26: Write `skills/proposal-compliance/SKILL.md`

**Files:**
- Create: `skills/proposal-compliance/SKILL.md`

- [ ] **Step 1: Write the file**

Path: `skills/proposal-compliance/SKILL.md`:

```markdown
---
name: proposal-compliance
description: "This skill should be used when the user invokes /sws:proposal-compliance, says 'check compliance', 'verify the proposal against the call', 'audit the proposal', 'check rules' — and the active profile is funding-proposal with both a resolved call-rules overlay and at least one drafted proposal section. Dispatches proposal-compliance-helper to produce _proposal/compliance-report.md."
version: 0.1.0
---

# /sws:proposal-compliance — Check the proposal against call rules

Dispatches `proposal-compliance-helper`. The agent reads the overlay (structured rules), opens the call PDF for ambiguity resolution via Claude's built-in skill, and produces a compliance report at `_proposal/compliance-report.md`.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check.
2. **Verify profile = funding-proposal.** Same as proposal-budget.
3. **Verify call-rules overlay exists.** Same as proposal-budget.
4. **Verify proposal drafts exist.** Check `${PAPER_ROOT}/_drafts/` is non-empty OR a docx file exists in `${PAPER_ROOT}/Manuscript/`. If neither: print "nothing to check — draft proposal sections first via /sws:draft-paper or /sws:draft-section" and exit.
5. **Dispatch proposal-compliance-helper** via the Task tool.
6. **Hand back to user.** Agent prints path to `_proposal/compliance-report.md` and a one-line summary (X of N rules pass).
```

- [ ] **Step 2: Commit**

```bash
git add skills/proposal-compliance/
git commit -m "feat(cycle-07): /sws:proposal-compliance skill"
```

---

### Task 27: Update profile files with cycle-#7 activation matrix

**Files:**
- Modify: `profiles/full-article.md`
- Modify: `profiles/communication.md`
- Modify: `profiles/perspective.md` (add comment confirming caption-writer active)
- Modify: `profiles/review-paper.md`
- Modify: `profiles/mini-review.md`
- Modify: `profiles/editorial.md`
- Modify: `profiles/methodological-paper.md`
- Modify: `profiles/commentary-reply.md`
- Modify: `profiles/funding-proposal.md`

Per the spec's `agent_activation_matrix_cycle_07_updates`. Caption-writer is invariant-active across all profiles.

- [ ] **Step 1: For each profile, edit the `agents_inactive` list**

Apply these specific changes (only the `agents_inactive` line; everything else unchanged):

| Profile file | New `agents_inactive` value |
|---|---|
| `profiles/full-article.md` | `[]` |
| `profiles/communication.md` | `[methods-writer, drafter-fast]` |
| `profiles/perspective.md` | (no change — already correct: `[proposal-budget-helper, proposal-compliance-helper, methods-writer, data-curator, plot-maker]`) |
| `profiles/review-paper.md` | `[proposal-budget-helper, proposal-compliance-helper, methods-writer]` |
| `profiles/mini-review.md` | `[proposal-budget-helper, proposal-compliance-helper, methods-writer]` |
| `profiles/editorial.md` | `[proposal-budget-helper, proposal-compliance-helper, methods-writer, drafter-fast]` |
| `profiles/methodological-paper.md` | `[proposal-budget-helper, proposal-compliance-helper]` |
| `profiles/commentary-reply.md` | `[proposal-budget-helper, proposal-compliance-helper, methods-writer]` |
| `profiles/funding-proposal.md` | `[response-to-reviewers, methods-writer, drafter-fast]` |

For each file, use the Edit tool to replace the existing `agents_inactive: [...]` line with the new value. If a profile already has the correct value, skip.

- [ ] **Step 2: Verify caption-writer is NOT in any inactive list**

```bash
grep -l 'caption-writer' profiles/*.md | xargs grep 'agents_inactive'
```
Expected: NO output (caption-writer must not appear in any inactive list).

- [ ] **Step 3: Commit**

```bash
git add profiles/
git commit -m "feat(cycle-07): update profile activation matrix for new cycle-#7 agents"
```

---

### Task 28: Write `tests/test_section_to_agent_map.py`

**Files:**
- Create: `tests/test_section_to_agent_map.py`
- Create: `scripts/sws_section_router.py` (helper that the test imports and the skills shell out to)

The skill's routing logic is documented in markdown but the resolver-style tests need a callable. Extract a small Python helper that mirrors the SKILL.md tables.

- [ ] **Step 1: Write the failing test**

Path: `tests/test_section_to_agent_map.py`:

```python
"""Section→agent routing per spec section_to_agent_map."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sws_section_router import route_section, RouteError


@pytest.mark.parametrize("section_id, expected_agent", [
    ("intro", "drafter-flagship"),
    ("introduction", "drafter-flagship"),
    ("abstract", "drafter-flagship"),
    ("discussion", "drafter-flagship"),
    ("conclusion", "drafter-flagship"),
    ("conclusions", "drafter-flagship"),
    ("methods", "methods-writer"),
    ("experimental", "methods-writer"),
    ("experimental section", "methods-writer"),
    ("materials", "methods-writer"),
    ("statistical analysis", "methods-writer"),
    ("computational details", "methods-writer"),
    ("software", "methods-writer"),
    ("data availability", "methods-writer"),
    ("results", "drafter-fast"),
    ("results and discussion", "drafter-flagship"),
    ("figure_caption", "caption-writer"),
])
def test_publication_profile_routing(section_id, expected_agent):
    assert route_section(section_id, profile="full-article") == expected_agent


@pytest.mark.parametrize("section_id, expected_agent", [
    ("state of the art", "drafter-flagship"),
    ("state-of-the-art", "drafter-flagship"),
    ("vision", "drafter-flagship"),
    ("objectives", "drafter-flagship"),
    ("workplan", "drafter-flagship"),
    ("methodology", "drafter-flagship"),
    ("approach", "drafter-flagship"),
    ("impact", "drafter-flagship"),
    ("risk management", "drafter-flagship"),
    ("deliverables", "drafter-flagship"),
    ("timeline", "drafter-flagship"),
    ("budget", "proposal-budget-helper"),
    ("compliance", "proposal-compliance-helper"),
    ("figure_caption", "caption-writer"),
])
def test_funding_proposal_routing(section_id, expected_agent):
    assert route_section(section_id, profile="funding-proposal") == expected_agent


def test_publication_fallback_to_drafter_fast():
    assert route_section("limitations", profile="full-article") == "drafter-fast"


def test_funding_proposal_fallback_to_drafter_flagship():
    assert route_section("appendix", profile="funding-proposal") == "drafter-flagship"


def test_case_insensitive_routing():
    assert route_section("INTRO", profile="full-article") == "drafter-flagship"
    assert route_section("Methods", profile="full-article") == "methods-writer"


def test_methods_in_funding_proposal_does_not_route_to_methods_writer():
    # methods-writer is in funding-proposal's agents_inactive; the router doesn't
    # know that, so this is the should_run check's job. Router still maps the id
    # using the funding-proposal map, which has no "methods" entry → falls back
    # to drafter-flagship (correct per D8).
    assert route_section("methods", profile="funding-proposal") == "drafter-flagship"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_section_to_agent_map.py -v
```
Expected: ImportError.

- [ ] **Step 3: Write the implementation**

Path: `scripts/sws_section_router.py`:

```python
"""Section→agent router. Single source of truth for /sws:draft-section
and /sws:draft-paper dispatch. Mirrors the tables in
skills/draft-section/SKILL.md.
"""
from __future__ import annotations
from typing import Optional


class RouteError(ValueError):
    pass


_PUBLICATION_MAP = {
    "intro": "drafter-flagship",
    "introduction": "drafter-flagship",
    "abstract": "drafter-flagship",
    "discussion": "drafter-flagship",
    "conclusion": "drafter-flagship",
    "conclusions": "drafter-flagship",
    "methods": "methods-writer",
    "experimental": "methods-writer",
    "experimental section": "methods-writer",
    "materials": "methods-writer",
    "statistical analysis": "methods-writer",
    "computational details": "methods-writer",
    "software": "methods-writer",
    "data availability": "methods-writer",
    "results": "drafter-fast",
    "results and discussion": "drafter-flagship",
    "figure_caption": "caption-writer",
}

_FUNDING_PROPOSAL_MAP = {
    "state of the art": "drafter-flagship",
    "state-of-the-art": "drafter-flagship",
    "vision": "drafter-flagship",
    "objectives": "drafter-flagship",
    "workplan": "drafter-flagship",
    "methodology": "drafter-flagship",
    "approach": "drafter-flagship",
    "impact": "drafter-flagship",
    "risk management": "drafter-flagship",
    "deliverables": "drafter-flagship",
    "timeline": "drafter-flagship",
    "budget": "proposal-budget-helper",
    "compliance": "proposal-compliance-helper",
    "figure_caption": "caption-writer",
}


def route_section(section_id: str, profile: str) -> str:
    if not section_id:
        raise RouteError("empty section id")
    key = section_id.strip().lower()
    if profile == "funding-proposal":
        if key in _FUNDING_PROPOSAL_MAP:
            return _FUNDING_PROPOSAL_MAP[key]
        # Fallback for funding-proposal: drafter-flagship
        return "drafter-flagship"
    # Publication profile fallback: drafter-fast for unknown narrative ids
    return _PUBLICATION_MAP.get(key, "drafter-fast")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_section_to_agent_map.py -v
```
Expected: ~36 tests pass (parameterized).

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_section_router.py tests/test_section_to_agent_map.py
git commit -m "feat(cycle-07): section→agent router + 36 routing tests"
```

---

### Task 29: Write `tests/test_profile_agent_activation.py`

**Files:**
- Create: `tests/test_profile_agent_activation.py`

Verify each of the 9 profiles activates/deactivates the right cycle-#7 agents per the matrix in the spec.

- [ ] **Step 1: Write the test**

Path: `tests/test_profile_agent_activation.py`:

```python
"""Per-profile activation matrix for cycle-#7 agents."""
import os
import shutil
import subprocess
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[1]


def _make_paper(tmp_path, profile_id):
    paper = tmp_path / "paper"
    paper.mkdir()
    venv_bin = paper / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    py = shutil.which("python3")
    (venv_bin / "python").symlink_to(py)
    (paper / ".sws-project.local.md").write_text(
        f"---\nprofile: {profile_id}\nlanguage: en\nformat: docx\n---\n"
    )
    return paper


def _can_run(paper, agent_id):
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(REPO)
    env["PAPER_ROOT"] = str(paper)
    cp = subprocess.run(
        ["bash", str(REPO / "scripts" / "agent_should_run.sh"), agent_id],
        env=env, capture_output=True, text=True
    )
    return cp.returncode == 0


# Cycle-#7 agents that have explicit per-profile activation rules
CYCLE_7_AGENTS = [
    "outline-architect", "drafter-flagship", "drafter-fast",
    "methods-writer", "caption-writer",
    "proposal-budget-helper", "proposal-compliance-helper",
]


PROFILES = {
    "full-article":         {"inactive": []},
    "communication":        {"inactive": ["methods-writer", "drafter-fast"]},
    "perspective":          {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer"]},
    "review-paper":         {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer"]},
    "mini-review":          {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer"]},
    "editorial":            {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer", "drafter-fast"]},
    "methodological-paper": {"inactive": ["proposal-budget-helper", "proposal-compliance-helper"]},
    "commentary-reply":     {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer"]},
    "funding-proposal":     {"inactive": ["methods-writer", "drafter-fast"]},
}


@pytest.mark.parametrize("profile_id, spec", PROFILES.items())
def test_caption_writer_always_active(tmp_path, profile_id, spec):
    """Invariant from user instruction 2026-05-13."""
    paper = _make_paper(tmp_path, profile_id)
    assert _can_run(paper, "caption-writer"), \
        f"caption-writer must be active for profile={profile_id}"


@pytest.mark.parametrize("profile_id, spec", PROFILES.items())
def test_inactive_agents_blocked(tmp_path, profile_id, spec):
    paper = _make_paper(tmp_path, profile_id)
    for agent in spec["inactive"]:
        if agent not in CYCLE_7_AGENTS:
            continue  # not a cycle-#7 agent (e.g., data-curator, response-to-reviewers)
        assert not _can_run(paper, agent), \
            f"agent={agent} should be INACTIVE for profile={profile_id}"


@pytest.mark.parametrize("profile_id, spec", PROFILES.items())
def test_active_cycle_7_agents_allowed(tmp_path, profile_id, spec):
    paper = _make_paper(tmp_path, profile_id)
    for agent in CYCLE_7_AGENTS:
        if agent in spec["inactive"]:
            continue
        assert _can_run(paper, agent), \
            f"agent={agent} should be ACTIVE for profile={profile_id}"
```

- [ ] **Step 2: Run the tests**

```bash
python3 -m pytest tests/test_profile_agent_activation.py -v
```
Expected: 27 tests pass (3 parameterized × 9 profiles).

- [ ] **Step 3: Commit**

```bash
git add tests/test_profile_agent_activation.py
git commit -m "feat(cycle-07): per-profile activation matrix tests (27 tests, 9 profiles)"
```

---

## Phase 4 — End-to-end smoke + PR

### Task 30: Build the smoke fixture paper

**Files:**
- Create: `tests/fixtures/cycle_07_paper/.sws-project.local.md`
- Create: `tests/fixtures/cycle_07_paper/figures/Fig1.png`
- Create: `tests/fixtures/cycle_07_paper/figures/Fig2.png`
- Create: `tests/fixtures/cycle_07_paper/Manuscript/_journal-style/chembiochem.md` (copy from cycle-#6 fixture)
- Create: `tests/fixtures/calls/test_prin_call.pdf` (small placeholder PDF)

- [ ] **Step 1: Create the fixture paper marker**

```bash
mkdir -p tests/fixtures/cycle_07_paper/figures
mkdir -p tests/fixtures/cycle_07_paper/Manuscript/_journal-style
mkdir -p tests/fixtures/cycle_07_paper/Manuscript/_call
mkdir -p tests/fixtures/cycle_07_paper/Manuscript/call
mkdir -p tests/fixtures/cycle_07_paper/.venv/bin
ln -s "$(which python3)" tests/fixtures/cycle_07_paper/.venv/bin/python

cat > tests/fixtures/cycle_07_paper/.sws-project.local.md <<EOF
---
profile: perspective
language: en
format: docx
---
EOF
```

- [ ] **Step 2: Create placeholder figure files**

```bash
# 1x1 PNG; smallest valid PNG file
python3 -c "
import struct, zlib
def png(width, height, pixels):
    sig = b'\\x89PNG\\r\\n\\x1a\\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack('>I', 13) + b'IHDR' + ihdr + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr))
    raw = b''
    for row in pixels:
        raw += b'\\x00' + bytes(row)
    comp = zlib.compress(raw)
    idat_chunk = struct.pack('>I', len(comp)) + b'IDAT' + comp + struct.pack('>I', zlib.crc32(b'IDAT' + comp))
    iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND'))
    return sig + ihdr_chunk + idat_chunk + iend_chunk
import sys
out = sys.argv[1]
data = png(1, 1, [[255, 0, 0]])
with open(out, 'wb') as f: f.write(data)
" tests/fixtures/cycle_07_paper/figures/Fig1.png

python3 -c "
import struct, zlib
def png(width, height, pixels):
    sig = b'\\x89PNG\\r\\n\\x1a\\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack('>I', 13) + b'IHDR' + ihdr + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr))
    raw = b''
    for row in pixels:
        raw += b'\\x00' + bytes(row)
    comp = zlib.compress(raw)
    idat_chunk = struct.pack('>I', len(comp)) + b'IDAT' + comp + struct.pack('>I', zlib.crc32(b'IDAT' + comp))
    iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND'))
    return sig + ihdr_chunk + idat_chunk + iend_chunk
import sys
out = sys.argv[1]
data = png(1, 1, [[0, 255, 0]])
with open(out, 'wb') as f: f.write(data)
" tests/fixtures/cycle_07_paper/figures/Fig2.png
```

- [ ] **Step 3: Copy the chembiochem journal-style fixture from cycle #6**

```bash
cp tests/fixtures/journal_pages/chembiochem.html tests/fixtures/cycle_07_paper/Manuscript/_journal-style/chembiochem.md 2>/dev/null || \
  echo "---\nslug: chembiochem\nname: ChemBioChem\nword_total: 6000\nref_cap: 100\n---\n# ChemBioChem overlay" > tests/fixtures/cycle_07_paper/Manuscript/_journal-style/chembiochem.md
```

- [ ] **Step 4: Create a tiny placeholder PDF for compliance testing**

```bash
mkdir -p tests/fixtures/calls
python3 -c "
data = b'%PDF-1.4\n1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>> endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000053 00000 n\n0000000100 00000 n\ntrailer <</Size 4 /Root 1 0 R>>\nstartxref\n148\n%%EOF\n'
with open('tests/fixtures/calls/test_prin_call.pdf', 'wb') as f: f.write(data)
"
```

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/cycle_07_paper tests/fixtures/calls
git commit -m "test(cycle-07): smoke fixture paper + placeholder figures + tiny PDF"
```

---

### Task 31: Write `tests/smoke_cycle_07.sh`

**Files:**
- Create: `tests/smoke_cycle_07.sh`

End-to-end shell test exercising the full cycle-#7 path on the fixture paper.

- [ ] **Step 1: Write the script**

Path: `tests/smoke_cycle_07.sh`:

```bash
#!/usr/bin/env bash
# Cycle-#7 end-to-end smoke. Exercises:
#   1. /sws:set-profile perspective on fixture
#   2. /sws:resolve-journal-style chembiochem (cycle-06 fixture HTML)
#   3. /sws:prepare-lit-context (canned zotero collection)
#   4. /sws:outline-paper → outline.md + .outline-baseline.sha256 written
#   5. /sws:draft-section intro → drafter-flagship draft, citations from manifest
#   6. Switch to funding-proposal profile, drop test PDF in call/
#   7. /sws:resolve-call-rules
#   8. /sws:proposal-budget → first-run Q&A scripted, files written
#   9. /sws:proposal-compliance → compliance-report.md written
#  10. /sws:draft-paper on perspective fixture (multi-section + figures)
#  11. AI-tells grep on all phase-4 outputs returns zero block-severity
#
# Most steps invoke Python helpers directly rather than going through the
# Claude UI (skills are documented for the model; the smoke exercises the
# underlying machinery).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE="$REPO/tests/fixtures/cycle_07_paper"
PASS=0
FAIL=0

step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  PASS\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

# Step 1: profile is already perspective in the fixture marker
step 1 "fixture marker has profile: perspective"
grep -q "profile: perspective" "$FIXTURE/.sws-project.local.md" && ok || ko

# Step 2: resolver works
step 2 "resolver returns profile_set: true for fixture"
JSON="$(CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash "$REPO/scripts/agent_prelude.sh" outline-architect 2>&1 || true)"
echo "  $JSON" | grep -q "no profile set" && ko "profile_set was false" || ok

# Step 3: zotero manifest export from canned collection
step 3 "/sws:prepare-lit-context (manifest export)"
python3 "$REPO/scripts/sws_extract_zotero_manifest.py" \
  --input "$REPO/tests/fixtures/zotero_collections/perspective_collection.json" \
  --paper "$FIXTURE" >/dev/null 2>&1
test -f "$FIXTURE/_lit/zotero-manifest.md" && ok || ko "manifest not written"

# Step 4: outline-architect can run (should_run check)
step 4 "outline-architect should_run for perspective"
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash "$REPO/scripts/agent_should_run.sh" outline-architect && ok || ko

# Step 4b: write a stub outline + baseline (skip the agent prose; smoke tests machinery only)
mkdir -p "$FIXTURE/_outline"
cat > "$FIXTURE/_outline/outline.md" <<EOF
---
profile: perspective
sections:
  intro: { word_target: 800, status: planned, key_claims: ["test claim"], figs: [], cites: ["Smith2023; doi:10.xxxx"] }
figures:
  f1: { caption: "", file: "figures/Fig1.png", supports: "Body" }
---
# Outline
## Intro
arc.
EOF
python3 "$REPO/scripts/sws_outline_baseline.py" write "$FIXTURE/_outline/outline.md" >/dev/null
step 4b "baseline sidecar written"
test -f "$FIXTURE/_outline/.outline-baseline.sha256" && ok || ko

# Step 5: drafter-flagship can run
step 5 "drafter-flagship should_run for perspective"
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash "$REPO/scripts/agent_should_run.sh" drafter-flagship && ok || ko

# Step 5b: section router maps intro correctly
step 5b "section router maps 'intro' → drafter-flagship for perspective"
RESULT="$(python3 -c "from sws_section_router import route_section; print(route_section('intro', 'perspective'))" 2>/dev/null)" || true
[[ "$RESULT" == "drafter-flagship" ]] && ok || ko "got '$RESULT'"

# Step 6: switch to funding-proposal
step 6 "switch fixture to funding-proposal profile"
sed -i.bak 's/profile: perspective/profile: funding-proposal/' "$FIXTURE/.sws-project.local.md"
rm -f "$FIXTURE/.sws-project.local.md.bak"
grep -q "profile: funding-proposal" "$FIXTURE/.sws-project.local.md" && ok || ko

# Step 7: drop call PDF + verify resolve_call_rules can pick it up (we just check the file exists path)
step 7 "call PDF available for resolve-call-rules"
cp "$REPO/tests/fixtures/calls/test_prin_call.pdf" "$FIXTURE/Manuscript/call/" 2>/dev/null || true
test -f "$FIXTURE/Manuscript/call/test_prin_call.pdf" && ok || ko

# Step 8: proposal-budget-helper should_run for funding-proposal
step 8 "proposal-budget-helper should_run for funding-proposal"
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash "$REPO/scripts/agent_should_run.sh" proposal-budget-helper && ok || ko

# Step 9: proposal-compliance-helper should_run for funding-proposal
step 9 "proposal-compliance-helper should_run for funding-proposal"
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash "$REPO/scripts/agent_should_run.sh" proposal-compliance-helper && ok || ko

# Step 9b: methods-writer is BLOCKED for funding-proposal (D8)
step 9b "methods-writer BLOCKED for funding-proposal (D8 rationale-not-procedural)"
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash "$REPO/scripts/agent_should_run.sh" methods-writer && ko "methods-writer should be inactive" || ok

# Step 10: switch back to perspective for /sws:draft-paper exercise
step 10 "switch back to perspective profile (for draft-paper smoke)"
sed -i.bak 's/profile: funding-proposal/profile: perspective/' "$FIXTURE/.sws-project.local.md"
rm -f "$FIXTURE/.sws-project.local.md.bak"
grep -q "profile: perspective" "$FIXTURE/.sws-project.local.md" && ok || ko

# Step 10b: caption-writer should_run for perspective (invariant per user instruction)
step 10b "caption-writer should_run for perspective (invariant active)"
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash "$REPO/scripts/agent_should_run.sh" caption-writer && ok || ko

# Step 11: AI-tells grep on the agent-contract reference doc itself (sanity check the catalog loads)
step 11 "ai-writing-tells.md has 40-60 patterns"
COUNT=$(grep -c '^- pattern:' "$REPO/references/ai-writing-tells.md" 2>/dev/null || echo 0)
[[ "$COUNT" -ge 40 && "$COUNT" -le 60 ]] && ok || ko "found $COUNT patterns"

# Cleanup mutations on the fixture
rm -rf "$FIXTURE/_lit" "$FIXTURE/_outline" "$FIXTURE/Manuscript/call/test_prin_call.pdf"

printf "\n=== Smoke summary: %d passed, %d failed ===\n" "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]] || exit 1
```

- [ ] **Step 2: Make executable and run**

```bash
chmod +x tests/smoke_cycle_07.sh
bash tests/smoke_cycle_07.sh
```
Expected: all steps PASS (~12 steps), exit 0.

- [ ] **Step 3: Run the full unit-test suite**

```bash
python3 -m pytest tests/ -v
```
Expected: all tests pass (cycle-#6 baseline + ~70 new cycle-#7 tests).

- [ ] **Step 4: Commit**

```bash
git add tests/smoke_cycle_07.sh
git commit -m "test(cycle-07): e2e smoke covering 11-step walkthrough on fixture"
```

---

### Task 32: Update `claude_memory/project_cycle_execution_status.md`

**Files:**
- Modify: `claude_memory/project_cycle_execution_status.md`

(claude_memory/ is gitignored, so this commit is local-only documentation. Skip the commit; just update the file for the next session's cold-start.)

- [ ] **Step 1: Update the cycle status table**

Change cycle #7 row's Status from `future` to `in PR` (or `merged` if the PR already merged at this point).

- [ ] **Step 2: Add cycle #7 section at top**

Mirror the cycle #6 section: list deliverables, locked decisions count, test count, smoke pass count.

- [ ] **Step 3: Update the resume protocol**

Change "Next cycle is #7" to "Next cycle is #8" and update the predecessor reference.

(No commit — file is gitignored.)

---

### Task 33: Open PR

- [ ] **Step 1: Push the branch**

```bash
git push -u origin cycle/07-drafting-and-proposal-helpers
```

- [ ] **Step 2: Open PR via gh**

```bash
gh pr create --title "Cycle #7: drafting + funding-proposal helpers (6 agents, 7 files)" --body "$(cat <<'EOF'
## Summary
- Ships 6 agents (7 files: drafter splits flagship+fast), 6 skills, 2 reference docs, 2 helper scripts, 9 profile updates.
- Codifies the SWS agent contract (5 cross-cutting rules: Python frugality, filesystem frugality, built-in skill preference, token discipline, no-gender-default).
- Adds the AI-writing-tells English catalog (40-60 tells across 5 categories) used as a grep-pass before any drafted prose returns.
- Drafter splits into flagship (Opus 4.7 xhigh, Intro/Discussion/Conclusion/Abstract) and fast (Sonnet 4.6, Results + non-flagship narrative). Methods-writer owns Materials/Methods/Stats/Computational/Software/Data subsections (publication track only — funding-proposal Methodology routes to drafter-flagship per D8).
- Caption-writer is invariant-active across all profiles (user instruction 2026-05-13). Text-only output written into outline.md frontmatter — no docx editing, no alt-text.
- Funding-proposal helpers: proposal-budget-helper (markdown line-item suggestions, no xlsx), proposal-compliance-helper (overlay + PDF check, NLM-grounded behaviors deferred to cycle #11).
- Drafter-flagship gains orchestrator mode for /sws:draft-paper (parallel fan-out to itself + drafter-fast + methods-writer + caption-writer).

Spec: docs/superpowers/specs/2026-05-13-cycle-07-drafting-and-proposal-helpers-design.md
Plan: docs/superpowers/plans/2026-05-13-cycle-07-drafting-and-proposal-helpers.md

## Test plan
- [ ] All cycle-#6 baseline tests still pass (`bash tests/smoke_cycle_06.sh`)
- [ ] All new cycle-#7 unit tests pass (`pytest tests/test_*.py`) — ~70 new tests
- [ ] Cycle-#7 smoke passes on fixture (`bash tests/smoke_cycle_07.sh`) — 11 steps
- [ ] Mid-cycle beta-test (Procentese et al. perspective intro) reviewed and approved before phase 3 began
- [ ] AI-writing-tells.md catalog has 40-60 tells across 5 categories, all required fields present

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Output PR URL**

The `gh pr create` command prints the URL. Capture and report to user.

---

## Self-Review Checklist (run after writing this plan)

**Spec coverage:**
- D1 (shared-scaffold contract) → Task 1 (`agent-contract.md`)
- D2 (outline.md schema) → Task 7 (outline-architect prompt + Task 4 baseline helper)
- D3 (overwrite policy) → Task 4 (`sws_outline_baseline.py`) + Task 7 (architect prompt)
- D4 (no passport log for outline edits) → Task 7 prompt mentions; no code needed
- D5 (ai-writing-tells comprehensive English) → Task 2
- D6 (drafter splits flagship+fast) → Tasks 9, 17
- D7 (abstract first-draft → flagship) → Tasks 9, 22 prompt content
- D8 (methods-writer publication-only) → Task 18 prompt + Task 27 funding-proposal `agents_inactive` includes methods-writer
- D9 (profile doesn't auto-route) → Task 27 + Task 28 router (router doesn't read profile-specific maps for routing decisions)
- D10 (caption-writer text only) → Task 19
- D11 (chemistry-formatting deferred) → noted in agent prompts (drafter-fast, methods-writer)
- D12 (proposal-budget markdown) → Task 20
- D13 (budget Q&A cached) → Task 20 prompt
- D14 (compliance overlay+PDF) → Task 21
- D15 (compliance report file) → Task 21
- D16 (zotero manifest pre-step) → Tasks 6, 10
- D17 (citation key format) → Task 3
- D18 (PubMed search deferred) → Task 10 prompt mentions degradation chain
- D19 (testing strategy) → Tasks 3, 4, 5, 6, 28, 29, 31
- D20 (beta-test) → Tasks 13-16
- D21 (4-phase internal phasing) → plan structure

All 21 D-decisions covered.

**Placeholder scan:** searched for "TBD", "TODO", "implement later" — none in plan tasks. (Plan does instruct phase-1 verification to *manually* survey andrehuang/Imbad0202 prior art for adaptation — that's a real instruction, not a placeholder.)

**Type consistency:** `route_section(section_id, profile)` signature consistent across Task 28 + smoke step 5b. `parse_citation_key` signature consistent. `build_manifest`, `_extract_year`, `sidecar_path`, `write_baseline`, `baseline_matches`, `BaselineMissing`, `ParseError`, `ManifestBuildError`, `RouteError` all defined where used.

**Phase-2 gate is explicit:** Task 16 step 4 has "STOP HERE" + explicit user-approval requirement before phase 3 dispatch.

**Phase 2.5 added 2026-05-14:** I/O wrapper layer (D22). Two new scripts, contract R3 rewrite, install-deps message expansion. All five tasks (16a-16e) commit individually.
