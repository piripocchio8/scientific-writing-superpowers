# Cycle #9 — Review — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 3 review agents (peer-reviewer, claim-verifier, bibliography-fidelity-checker), 4 skills (3 atomic + 1 sequential orchestrator), 2 helper scripts, 1 rubric reference, and a profile-activation update across all 9 profiles. End-of-cycle ships the `🧪 v0.1 alpha` banner and `0.1.0-alpha` version bump.

**Architecture:** Same pattern as cycles #7 and #8. Each agent file is a thin (~20-line) prompt that sources `scripts/agent_prelude.sh`, calls `agent_should_run.sh`, then runs its narrow job. Agents diagnose only — they write to `_review/<agent>/` (markdown report + JSON sidecar), never touch the manuscript. `/sws:review-paper` is a sequential orchestrator: claim-verifier → bibliography-fidelity-checker → peer-reviewer, with explicit CLI args passing prior report paths to peer-reviewer (no autoscan). `bibliography-fidelity-checker` has four code paths: D9 happy (Zotero corpus available), D9a (Zotero desktop detected but no Claude Code zotero skill — actionable recommendation), D9b (skill present but library small/unresponsive/permission-denied), D9c (no Zotero anywhere — neutral note).

**Tech Stack:** Python 3.9+ via per-paper `.venv/`, stdlib-only for new scripts (no new deps); bash for hook + orchestrator; markdown + YAML frontmatter for agents, skills, rubric, profiles; pytest for unit tests; shell smoke for e2e.

**Spec source of truth:** `docs/superpowers/specs/2026-05-17-cycle-09-review-design.md`. Frontmatter dictionary is canonical; this plan implements D1–D17, D9a–D9c.

**Execution mode:** Autonomous overnight. Maximize parallelism per phase. Open PR in DRAFT state for next-day user review.

---

## File Structure

**CREATE (new files):**

References:
- `references/peer-review-rubric.md`

Scripts:
- `scripts/sws_claim_extract.py`
- `scripts/sws_bibliography_fidelity.py`

Agents (3 files):
- `agents/peer-reviewer.md`
- `agents/claim-verifier.md`
- `agents/bibliography-fidelity-checker.md`

Skills (4 dirs, each with one SKILL.md):
- `skills/peer-review/SKILL.md`
- `skills/verify-claims/SKILL.md`
- `skills/check-fidelity/SKILL.md`
- `skills/review-paper/SKILL.md`

Tests:
- `tests/test_claim_extract.py`
- `tests/test_bibliography_fidelity.py`
- `tests/test_section_router_review_action.py`
- `tests/test_profile_activation_review_agents.py`
- `tests/fixtures/cycle_09/` (4 subdirs for the four smoke variants)
- `tests/fixtures/cycle_09/variant_1_no_zotero/`
- `tests/fixtures/cycle_09/variant_2_zotero_desktop_only/` (with mocked `~/Zotero/zotero.sqlite`)
- `tests/fixtures/cycle_09/variant_3_skill_empty_library/`
- `tests/fixtures/cycle_09/variant_4_skill_populated/` (with seeded fidelity-violation paragraph)
- `tests/smoke_cycle_09.sh`

**MODIFY (existing files):**
- `scripts/sws_section_router.py` — add `review` action axis
- `references/agent-contract.md` — extend R3 I/O inventory with `_review/<agent>/` shapes
- `profiles/full-article.md`, `communication.md`, `perspective.md`, `review-paper.md`, `mini-review.md`, `editorial.md`, `methodological-paper.md`, `commentary-reply.md`, `funding-proposal.md` — agents_active / agents_inactive matrix
- `README.md` — banner line
- `.claude-plugin/plugin.json` — version bump

---

## Phase Map (for parallel dispatch)

**Phase 1 — Foundations (6 tasks, parallel):** Reference rubric, both scripts with tests, section-router update, agent-contract update, README + plugin.json banner.

**Phase 2 — Agents (3 tasks, parallel; depends on Phase 1 scripts):** peer-reviewer, claim-verifier, bibliography-fidelity-checker.

**Phase 3 — Skills (4 tasks; 3 atomics parallel + orchestrator after; depends on Phase 2 agents):** /sws:peer-review, /sws:verify-claims, /sws:check-fidelity, then /sws:review-paper.

**Phase 4 — Profiles + activation tests (10 tasks, parallel; depends on Phase 2 agents):** 9 profile updates + test_profile_activation_review_agents.

**Phase 5 — Smoke + PR (sequential):** Smoke test fixtures + e2e script + open draft PR.

---

# PHASE 1 — Foundations

These tasks have no dependencies on each other and can run fully in parallel.

## Task 1.1: Reference doc — peer-review-rubric.md

**Files:**
- Create: `references/peer-review-rubric.md`

- [ ] **Step 1: Write the rubric reference**

Full content of `references/peer-review-rubric.md`:

````markdown
---
sws_artifact: peer-review-rubric
artifact_version: 0.1
attribution: "Outer narrative shape adapted from Imbad0202/academic-research-skills (MIT). Section-weight matrix is SWS-specific."
used_by: agents/peer-reviewer.md
---

# Peer-review rubric (v0.1)

The peer-reviewer agent reads this file at runtime, selects the section matching the user's resolved profile, and applies the listed weights when structuring its report.

## Narrative shape (all profiles)

The peer-reviewer encodes four personas in a single prompt:

1. **EIC (Editor-in-Chief):** assesses fit-for-journal/venue, novelty bar, ethical concerns.
2. **Reviewer 1 — methods focus:** assesses rigor, reproducibility, statistical correctness, claims-vs-evidence alignment.
3. **Reviewer 2 — domain focus:** assesses positioning vs prior art, novelty of contribution, citation completeness.
4. **Reviewer 3 — clarity focus:** assesses presentation, figure quality, logical flow, prose clarity.
5. **DA (Decision Authority):** synthesizes into one of {Accept, Minor Revision, Major Revision, Reject}.

The four reviewer personas share the report. The EIC frame opens; the DA frame closes.

## Section-weight matrix

When a section is missing from the manuscript, redistribute its weight proportionally across the remaining sections.

### full-article
- introduction: 15%
- methods: 25%
- results: 30%
- discussion: 20%
- references: 10%

### communication
- intro: 30%
- methods: 20%
- results: 40%
- references: 10%

### review-paper
- coverage: 35%
- synthesis: 30%
- critical evaluation: 25%
- references: 10%

### mini-review
- coverage: 35%
- synthesis: 30%
- critical evaluation: 25%
- references: 10%

### perspective
- framing: 30%
- argumentation: 40%
- novelty: 20%
- references: 10%

### editorial
- argument: 50%
- voice: 30%
- brevity: 20%

### methodological-paper
- novelty: 20%
- methods: 40%
- validation: 30%
- references: 10%

### commentary-reply
- fidelity-to-original: 30%
- argument: 40%
- civility: 20%
- references: 10%

### funding-proposal
- feasibility: 25%
- novelty: 25%
- impact: 25%
- team: 15%
- budget: 10%

## Report-file shape

The peer-reviewer writes `_review/peer-reviewer/report.md` with this YAML frontmatter dictionary:

```yaml
---
sws_artifact: peer-review-report
profile: <resolved profile>
manuscript_file: <relative path>
decision: Accept | Minor Revision | Major Revision | Reject
overall_score: 1-5
section_scores:
  <section_id>: { weight: 0.XX, score: 1-5, comments_count: N }
flags:
  ethical: N
  reproducibility: N
  novelty: N
  citations: N
fidelity_status: ran | skipped:<reason>
claim_verification_status: ran | skipped:<reason>
---
```

Body: EIC opening, four reviewer sections with per-section scores and comments, DA closing.

## V0.1 limitations (must appear in every report)

- No sprint-contracts paper-blind Phase 1 in v0.1 (deferred to cycle #9.1). The reviewer reads the paper directly.
- No concession-threshold scoring (dormant until response-to-reviewers ships in cycle #10).
- Single-agent multi-persona; not five separate dispatched agents (v0.2+ option).
````

- [ ] **Step 2: Commit**

```bash
git add references/peer-review-rubric.md
git commit -m "feat(cycle-09): references/peer-review-rubric.md — profile-keyed rubric (D16)"
```

---

## Task 1.2: Script — sws_claim_extract.py (TDD)

**Files:**
- Create: `scripts/sws_claim_extract.py`
- Test: `tests/test_claim_extract.py`

**Purpose:** Parse `_drafts/*.md` (citation-key format `[@key2024]` per cycle-07 D17), extract assertion sentences attached to one or more citation keys, emit a JSON manifest.

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_claim_extract.py`:

```python
"""Unit tests for sws_claim_extract.py.

Tests parsing of _drafts/*.md citation-key format, multi-citation handling,
section attribution, and edge cases (no citations, citations-without-sentence,
footnote-style citations, citations on figure captions).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sws_claim_extract as ce  # noqa: E402


def _write(tmpdir: Path, name: str, body: str) -> Path:
    p = tmpdir / name
    p.write_text(body, encoding="utf-8")
    return p


def test_extract_single_citation_sentence(tmp_path):
    _write(tmp_path, "introduction-revised.md", "Thrombin activates platelets [@smith2020].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert len(claims) == 1
    assert claims[0]["section"] == "introduction"
    assert claims[0]["citation_keys"] == ["smith2020"]
    assert "Thrombin activates platelets" in claims[0]["claim"]


def test_extract_multi_citation_sentence(tmp_path):
    _write(tmp_path, "results-revised.md", "We observed binding [@a2020; @b2021; @c2022].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert len(claims) == 1
    assert claims[0]["citation_keys"] == ["a2020", "b2021", "c2022"]


def test_section_id_derived_from_filename(tmp_path):
    _write(tmp_path, "methods-revised.md", "We performed X [@y2020].\n")
    _write(tmp_path, "discussion-revised.md", "Y suggests Z [@a2021].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    sections = sorted(c["section"] for c in claims)
    assert sections == ["discussion", "methods"]


def test_no_citations_yields_empty_list(tmp_path):
    _write(tmp_path, "results-revised.md", "We saw a clear effect with no source.\n")
    assert ce.extract_claims_from_drafts(tmp_path) == []


def test_skips_files_without_revised_suffix(tmp_path):
    _write(tmp_path, "introduction.md", "Source-bearing claim [@x2020].\n")  # not -revised
    _write(tmp_path, "introduction-revised.md", "Revised claim [@y2021].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    keys = [c["citation_keys"][0] for c in claims]
    assert keys == ["y2021"]


def test_sentence_segmentation_basic(tmp_path):
    _write(
        tmp_path,
        "results-revised.md",
        "Effect A is large [@a2020]. Effect B is small [@b2021].\n",
    )
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert len(claims) == 2
    assert claims[0]["citation_keys"] == ["a2020"]
    assert claims[1]["citation_keys"] == ["b2021"]


def test_emit_json_round_trips(tmp_path):
    _write(tmp_path, "intro-revised.md", "X is Y [@k1].\n")
    out = tmp_path / "claims.json"
    ce.write_claims_json(tmp_path, out)
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert data[0]["citation_keys"] == ["k1"]


def test_handles_apostrophes_and_unicode(tmp_path):
    _write(tmp_path, "discussion-revised.md", "Doe's findings—reproduced here—agree [@doe1999].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert len(claims) == 1
    assert "Doe" in claims[0]["claim"]


def test_strips_leading_whitespace_from_claim(tmp_path):
    _write(tmp_path, "results-revised.md", "   Padded claim text [@a2020].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert claims[0]["claim"].startswith("Padded")


def test_includes_verification_status_placeholder(tmp_path):
    _write(tmp_path, "intro-revised.md", "X [@a2020].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert claims[0]["verification_status"] == "pending"
    assert claims[0]["source_match"] == []
```

- [ ] **Step 2: Run tests to verify they all fail**

```bash
cd /Users/piripocchio8/Projects/scientific-writing-superpowers
pytest tests/test_claim_extract.py -v
```

Expected: `ImportError: No module named 'sws_claim_extract'` or 10 FAILED with collection errors.

- [ ] **Step 3: Implement scripts/sws_claim_extract.py**

Full content of `scripts/sws_claim_extract.py`:

```python
"""Extract citation-bearing claims from _drafts/*-revised.md.

Each claim is one sentence containing at least one ``[@key]`` citation.
Multi-key citations (``[@a2020; @b2021]``) are flattened into a single
claim with all keys attached. Section id is derived from the filename
prefix (e.g. ``introduction-revised.md`` → ``introduction``).

Output schema (one entry per claim):
{
  "section": "<section-id>",
  "claim": "<sentence text>",
  "citation_keys": ["key1", "key2"],
  "verification_status": "pending",
  "source_match": []
}

verification_status and source_match are populated by the claim-verifier
agent after this script runs; the script itself never queries any external
source.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict


_CITATION_RE = re.compile(r"\[@([^\]]+)\]")
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _section_id_from_filename(path: Path) -> str:
    name = path.stem
    if name.endswith("-revised"):
        name = name[: -len("-revised")]
    return name


def _split_sentences(text: str) -> List[str]:
    text = text.replace("\n", " ")
    parts = _SENTENCE_END_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _parse_citation_keys(raw: str) -> List[str]:
    return [k.strip().lstrip("@") for k in raw.split(";") if k.strip()]


def extract_claims_from_drafts(drafts_dir: Path) -> List[Dict]:
    """Return list of claim dicts across all -revised.md files in drafts_dir."""
    claims: List[Dict] = []
    files = sorted(drafts_dir.glob("*-revised.md"))
    for f in files:
        section = _section_id_from_filename(f)
        body = f.read_text(encoding="utf-8")
        for sentence in _split_sentences(body):
            matches = _CITATION_RE.findall(sentence)
            if not matches:
                continue
            keys: List[str] = []
            for m in matches:
                keys.extend(_parse_citation_keys(m))
            seen = set()
            unique_keys = [k for k in keys if not (k in seen or seen.add(k))]
            claims.append(
                {
                    "section": section,
                    "claim": sentence.strip(),
                    "citation_keys": unique_keys,
                    "verification_status": "pending",
                    "source_match": [],
                }
            )
    return claims


def write_claims_json(drafts_dir: Path, out_path: Path) -> None:
    claims = extract_claims_from_drafts(drafts_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(claims, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract citation-bearing claims from _drafts/*-revised.md")
    parser.add_argument("drafts_dir", type=Path, help="Directory containing *-revised.md files")
    parser.add_argument("--out", type=Path, required=True, help="Output path for claims.json")
    args = parser.parse_args(argv)

    if not args.drafts_dir.is_dir():
        print(f"error: drafts_dir not found: {args.drafts_dir}", file=sys.stderr)
        return 2

    write_claims_json(args.drafts_dir, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
pytest tests/test_claim_extract.py -v
```

Expected: 10 PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_claim_extract.py tests/test_claim_extract.py
git commit -m "feat(cycle-09): sws_claim_extract.py — citation-bearing-claim extractor (D8)"
```

---

## Task 1.3: Script — sws_bibliography_fidelity.py (TDD)

**Files:**
- Create: `scripts/sws_bibliography_fidelity.py`
- Test: `tests/test_bibliography_fidelity.py`

**Purpose:** Probe for zotero skill + Zotero desktop installation. If both available, query the user's Zotero full-text index for verbatim ≥15-word overlap against manuscript paragraphs and write `flags.json` + `report.md`. If unavailable, write `status.json` with the specific skip reason and an informative report. Six fixtures cover all paths (D9, D9a, D9b, D9c, plus zotero-unresponsive + permission-denied).

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_bibliography_fidelity.py`:

```python
"""Unit tests for sws_bibliography_fidelity.py.

Covers all six paths (D9 happy, D9a recommendation, D9b small/error,
D9c neutral) plus the unresponsive and permission-denied error fixtures.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sws_bibliography_fidelity as bf  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_paper_root(tmp_path: Path) -> Path:
    """Create a minimal paper-root layout with a final.docx and a paragraph."""
    paper = tmp_path / "paper"
    (paper / "Manuscript").mkdir(parents=True)
    (paper / "_review" / "bibliography-fidelity-checker").mkdir(parents=True)
    # We mock sws_read_docx via monkeypatch; no real .docx needed.
    return paper


def _write_status(path: Path) -> dict:
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Probe layer — both skill and desktop
# ---------------------------------------------------------------------------


def test_probe_returns_both_false_when_neither_installed(monkeypatch, tmp_path):
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: False)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (False, None))
    state = bf.probe_zotero()
    assert state["zotero_skill_available"] is False
    assert state["zotero_desktop_detected"] is False
    assert state["zotero_sqlite_path"] is None


def test_probe_returns_desktop_true_when_sqlite_found(monkeypatch, tmp_path):
    fake_path = tmp_path / "Zotero" / "zotero.sqlite"
    fake_path.parent.mkdir(parents=True)
    fake_path.write_text("fake sqlite", encoding="utf-8")
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: False)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (True, str(fake_path)))
    state = bf.probe_zotero()
    assert state["zotero_desktop_detected"] is True
    assert state["zotero_sqlite_path"] == str(fake_path)


def test_probe_honors_zotero_data_dir_env(monkeypatch, tmp_path):
    custom = tmp_path / "custom-zotero" / "zotero.sqlite"
    custom.parent.mkdir(parents=True)
    custom.write_text("x", encoding="utf-8")
    found, path = bf._probe_zotero_desktop(env={"ZOTERO_DATA_DIR": str(custom.parent)})
    assert found is True
    assert path == str(custom)


# ---------------------------------------------------------------------------
# D9c — no zotero anywhere
# ---------------------------------------------------------------------------


def test_d9c_neither_skill_nor_desktop(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: False)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (False, None))
    rc = bf.run_fidelity_check(paper)
    assert rc == 0
    status = _write_status(paper / "_review" / "bibliography-fidelity-checker" / "status.json")
    assert status["ran"] is False
    assert status["skip_reason"] == "no-zotero-installation-detected"
    report = (paper / "_review" / "bibliography-fidelity-checker" / "report.md").read_text()
    assert "No Zotero installation detected" in report


# ---------------------------------------------------------------------------
# D9a — Zotero desktop detected, but no Claude Code zotero skill
# ---------------------------------------------------------------------------


def test_d9a_zotero_desktop_only(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    fake_sqlite = tmp_path / "Zotero" / "zotero.sqlite"
    fake_sqlite.parent.mkdir(parents=True)
    fake_sqlite.write_text("x", encoding="utf-8")
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: False)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (True, str(fake_sqlite)))
    rc = bf.run_fidelity_check(paper)
    assert rc == 0
    status = _write_status(paper / "_review" / "bibliography-fidelity-checker" / "status.json")
    assert status["ran"] is False
    assert status["skip_reason"] == "zotero-desktop-detected-but-claude-skill-missing"
    assert status["zotero_sqlite_path"] == str(fake_sqlite)
    report = (paper / "_review" / "bibliography-fidelity-checker" / "report.md").read_text()
    assert "We detected a Zotero installation at" in report
    assert "we recommend installing the zotero plugin in Claude Code" in report


# ---------------------------------------------------------------------------
# D9b — skill present + library small/unresponsive/permission-denied
# ---------------------------------------------------------------------------


def test_d9b_library_too_small(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: True)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (True, "/tmp/zotero.sqlite"))
    monkeypatch.setattr(bf, "_query_zotero_library_size", lambda: 5)
    rc = bf.run_fidelity_check(paper)
    assert rc == 0
    status = _write_status(paper / "_review" / "bibliography-fidelity-checker" / "status.json")
    assert status["ran"] is False
    assert status["skip_reason"] == "zotero-library-too-small"
    assert status["library_item_count"] == 5


def test_d9b_unresponsive(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: True)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (True, "/tmp/zotero.sqlite"))
    def _raise(_=None):
        raise TimeoutError("zotero query exceeded 30s")
    monkeypatch.setattr(bf, "_query_zotero_library_size", _raise)
    rc = bf.run_fidelity_check(paper)
    assert rc == 0
    status = _write_status(paper / "_review" / "bibliography-fidelity-checker" / "status.json")
    assert status["skip_reason"] == "zotero-unresponsive"


def test_d9b_permission_denied(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: True)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (True, "/tmp/zotero.sqlite"))
    def _deny(_=None):
        raise PermissionError("zotero rejected")
    monkeypatch.setattr(bf, "_query_zotero_library_size", _deny)
    rc = bf.run_fidelity_check(paper)
    assert rc == 0
    status = _write_status(paper / "_review" / "bibliography-fidelity-checker" / "status.json")
    assert status["skip_reason"] == "zotero-permission-denied"


# ---------------------------------------------------------------------------
# D9 — happy path
# ---------------------------------------------------------------------------


def test_d9_happy_path_flags_violation(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: True)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (True, "/tmp/zotero.sqlite"))
    monkeypatch.setattr(bf, "_query_zotero_library_size", lambda: 42)
    paragraphs = [
        {"id": "p1", "section": "introduction", "text": "Thrombin activates platelets via PAR1 cleavage of the extracellular tethered ligand domain."}
    ]
    monkeypatch.setattr(bf, "_extract_paragraphs_from_docx", lambda _: paragraphs)
    matched_item = {
        "item_key": "ABC123",
        "title": "Mock Source Paper",
        "authors": ["Doe J"],
        "year": 2021,
        "collection": "Thrombin",
    }
    def _search(passage: str):
        return [matched_item] if "Thrombin activates platelets via PAR1 cleavage" in passage else []
    monkeypatch.setattr(bf, "_zotero_fulltext_search", _search)
    rc = bf.run_fidelity_check(paper)
    assert rc == 0
    status = _write_status(paper / "_review" / "bibliography-fidelity-checker" / "status.json")
    assert status["ran"] is True
    flags = json.loads(
        (paper / "_review" / "bibliography-fidelity-checker" / "flags.json").read_text()
    )
    assert len(flags) >= 1
    f = flags[0]
    assert f["paragraph_id"] == "p1"
    assert f["section"] == "introduction"
    assert f["zotero_item_key"] == "ABC123"
    report = (paper / "_review" / "bibliography-fidelity-checker" / "report.md").read_text()
    assert "V0.1 LIMITATION" in report


def test_min_phrase_length_is_15_words(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: True)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (True, "/tmp/zotero.sqlite"))
    monkeypatch.setattr(bf, "_query_zotero_library_size", lambda: 42)
    # Short paragraph: only 10 words; should NOT generate any 15-word substrings.
    paragraphs = [{"id": "p1", "section": "introduction", "text": "Short text fewer than fifteen words goes here today now."}]
    monkeypatch.setattr(bf, "_extract_paragraphs_from_docx", lambda _: paragraphs)
    calls = []
    def _search(passage):
        calls.append(passage)
        return []
    monkeypatch.setattr(bf, "_zotero_fulltext_search", _search)
    rc = bf.run_fidelity_check(paper)
    assert rc == 0
    assert calls == []  # no substrings ≥15 words → no search calls


def test_status_includes_probe_signal_origin(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: False)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (False, None))
    bf.run_fidelity_check(paper)
    status = _write_status(paper / "_review" / "bibliography-fidelity-checker" / "status.json")
    assert "zotero_skill_available" in status
    assert "zotero_desktop_detected" in status
    assert "skip_reason" in status


def test_flag_for_one_word_below_threshold_does_not_fire(monkeypatch, tmp_path):
    paper = _make_paper_root(tmp_path)
    monkeypatch.setattr(bf, "_probe_claude_zotero_skill", lambda: True)
    monkeypatch.setattr(bf, "_probe_zotero_desktop", lambda env=None: (True, "/tmp/zotero.sqlite"))
    monkeypatch.setattr(bf, "_query_zotero_library_size", lambda: 42)
    # 14-word string: at minimum-phrase-length minus 1 — must NOT trigger search.
    text14 = " ".join(["word"] * 14)
    paragraphs = [{"id": "p1", "section": "results", "text": text14}]
    monkeypatch.setattr(bf, "_extract_paragraphs_from_docx", lambda _: paragraphs)
    calls = []
    monkeypatch.setattr(bf, "_zotero_fulltext_search", lambda p: calls.append(p) or [])
    bf.run_fidelity_check(paper)
    assert calls == []
```

- [ ] **Step 2: Run tests to verify they all fail**

```bash
pytest tests/test_bibliography_fidelity.py -v
```

Expected: ImportError on `sws_bibliography_fidelity`.

- [ ] **Step 3: Implement scripts/sws_bibliography_fidelity.py**

Full content of `scripts/sws_bibliography_fidelity.py`:

```python
"""Bibliography-fidelity check against the user's Zotero corpus.

Detects four paths:
  - D9   happy: claude zotero skill available + Zotero desktop indexed + library ≥10.
              → runs verbatim-overlap check; writes flags.json + report.md.
  - D9a  recommendation: Zotero desktop detected but Claude Code zotero skill missing.
              → exits 0; report.md leads with the actionable recommendation.
  - D9b  inert library: skill present but library too small / unresponsive / permission-denied.
              → exits 0; status.json carries the specific reason.
  - D9c  neutral skip: neither skill nor desktop detected.
              → exits 0; report.md is a neutral note (no install push).

All four paths exit 0 (skip is not an error). Status.json is the
machine-readable companion to report.md; both are always written.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


_MIN_PHRASE_WORDS = 15
_MIN_LIBRARY_ITEMS = 10
_QUERY_TIMEOUT_S = 30


# Verbatim wording locked by spec D9a. Smoke test asserts these strings.
_D9A_RECOMMENDATION_TEMPLATE = (
    "We detected a Zotero installation at {path}. If you use Zotero to manage references "
    "for this manuscript, we recommend installing the zotero plugin in Claude Code to enable "
    "the bibliography-fidelity check. Install with: /plugin install zotero (or your "
    "equivalent). After installation, re-run /sws:check-fidelity to verify your manuscript "
    "against your Zotero corpus."
)

_D9C_NEUTRAL_TEMPLATE = (
    "No Zotero installation detected on this system. The bibliography-fidelity check is "
    "Zotero-only in v0.1. If you use a different reference manager (Mendeley, EndNote, "
    "Papers, plain BibTeX), this check is not available in v0.1. Manual proofreading "
    "remains the recommended workaround. See v0.2 backlog for planned unbounded-corpus "
    "alternatives (Crossref Similarity Check, Google Programmable Search opt-in)."
)

_V01_LIMITATION_HEADER = (
    "## V0.1 LIMITATION\n\n"
    "This is a fidelity check against your Zotero library only, not unbounded-corpus "
    "plagiarism detection. It catches verbatim copies of ≥15 contiguous words from "
    "papers in your Zotero corpus. Paraphrase, synonym substitution, and sentence "
    "reordering will NOT be caught. Sources outside your Zotero (open web, papers you "
    "haven't read) are NOT checked.\n"
)


# ---------------------------------------------------------------------------
# Probe layer
# ---------------------------------------------------------------------------


def _probe_claude_zotero_skill() -> bool:
    """Detect whether the Claude Code zotero plugin/skill is installed.

    Tries three independent signals; any one positive returns True.
    """
    # Signal 1: ~/.claude/plugins/cache/* containing 'zotero' anywhere.
    home = Path.home()
    cache_dir = home / ".claude" / "plugins" / "cache"
    if cache_dir.is_dir():
        for child in cache_dir.iterdir():
            if "zotero" in child.name.lower():
                return True

    # Signal 2: `claude --list-skills` mentions zotero.
    claude_bin = shutil.which("claude")
    if claude_bin:
        try:
            result = subprocess.run(
                [claude_bin, "--list-skills"],
                capture_output=True, text=True, timeout=5,
            )
            if "zotero" in (result.stdout or "").lower():
                return True
        except (subprocess.SubprocessError, OSError):
            pass

    # Signal 3: ~/.claude/CLAUDE.md references the zotero skill.
    claude_md = home / ".claude" / "CLAUDE.md"
    if claude_md.is_file():
        try:
            if "zotero" in claude_md.read_text(encoding="utf-8", errors="ignore").lower():
                return True
        except OSError:
            pass

    return False


def _probe_zotero_desktop(env: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str]]:
    """Detect Zotero desktop SQLite. Returns (found, path)."""
    env = env if env is not None else os.environ
    home = Path(env.get("HOME") or env.get("USERPROFILE") or Path.home())

    candidates: List[Path] = []
    # Custom data dir override
    custom = env.get("ZOTERO_DATA_DIR")
    if custom:
        candidates.append(Path(custom) / "zotero.sqlite")

    # macOS / Linux default
    candidates.append(home / "Zotero" / "zotero.sqlite")
    # Windows default (when HOME is not set but USERPROFILE is)
    win_profile = env.get("USERPROFILE")
    if win_profile:
        candidates.append(Path(win_profile) / "Zotero" / "zotero.sqlite")
    # Older Zotero 5 profile-based path on Linux
    legacy = home / ".zotero" / "zotero"
    if legacy.is_dir():
        for profile in legacy.iterdir():
            candidates.append(profile / "zotero.sqlite")

    for c in candidates:
        if c.is_file():
            return True, str(c)
    return False, None


def probe_zotero() -> Dict[str, object]:
    """Return a probe-state dict combining both probe layers."""
    skill = _probe_claude_zotero_skill()
    desktop, path = _probe_zotero_desktop()
    return {
        "zotero_skill_available": skill,
        "zotero_desktop_detected": desktop,
        "zotero_sqlite_path": path,
    }


# ---------------------------------------------------------------------------
# Library / search shims (mocked by tests; real implementations would call
# the user's `zotero` skill via the agent dispatch surface).
# ---------------------------------------------------------------------------


def _query_zotero_library_size() -> int:
    """Return the number of items in the user's primary Zotero library.

    In v0.1 we do not have a stable Python entry point into the `zotero`
    skill; the agent layer wraps that. This shim returns 0 by default so
    that running the script outside a real session degrades to D9b
    library-too-small rather than a crash.
    """
    return 0


def _zotero_fulltext_search(passage: str) -> List[Dict]:
    """Return matching Zotero items for a phrase. Mocked in tests."""
    return []


def _extract_paragraphs_from_docx(docx_path: Path) -> List[Dict]:
    """Extract paragraphs from final .docx. Wraps scripts/sws_read_docx.py.

    In v0.1, when running outside a real paper-root, returns an empty list
    so the happy-path code is exercisable in unit tests via monkeypatch.
    """
    return []


# ---------------------------------------------------------------------------
# Phrase generation + match logic
# ---------------------------------------------------------------------------


def _generate_phrases(text: str, min_words: int = _MIN_PHRASE_WORDS) -> List[str]:
    words = text.split()
    if len(words) < min_words:
        return []
    return [" ".join(words[i : i + min_words]) for i in range(len(words) - min_words + 1)]


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_status(paper_root: Path, status: Dict) -> None:
    out_dir = paper_root / "_review" / "bibliography-fidelity-checker"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _write_flags(paper_root: Path, flags: List[Dict]) -> None:
    out_dir = paper_root / "_review" / "bibliography-fidelity-checker"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "flags.json").write_text(
        json.dumps(flags, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _write_report(paper_root: Path, body: str) -> None:
    out_dir = paper_root / "_review" / "bibliography-fidelity-checker"
    out_dir.mkdir(parents=True, exist_ok=True)
    header = (
        "---\n"
        "sws_artifact: bibliography-fidelity-report\n"
        "agent: bibliography-fidelity-checker\n"
        "---\n\n"
        "# Bibliography-fidelity report\n\n"
    )
    (out_dir / "report.md").write_text(header + body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def run_fidelity_check(paper_root: Path) -> int:
    state = probe_zotero()

    # D9c — neither skill nor desktop
    if not state["zotero_skill_available"] and not state["zotero_desktop_detected"]:
        status = {**state, "ran": False, "skip_reason": "no-zotero-installation-detected"}
        _write_status(paper_root, status)
        _write_report(paper_root, _D9C_NEUTRAL_TEMPLATE + "\n")
        _write_flags(paper_root, [])
        return 0

    # D9a — desktop detected, skill missing
    if not state["zotero_skill_available"] and state["zotero_desktop_detected"]:
        status = {
            **state,
            "ran": False,
            "skip_reason": "zotero-desktop-detected-but-claude-skill-missing",
        }
        _write_status(paper_root, status)
        body = _D9A_RECOMMENDATION_TEMPLATE.format(path=state["zotero_sqlite_path"]) + "\n"
        _write_report(paper_root, body)
        _write_flags(paper_root, [])
        return 0

    # D9b probe — library size / health
    try:
        size = _query_zotero_library_size()
    except TimeoutError:
        status = {**state, "ran": False, "skip_reason": "zotero-unresponsive"}
        _write_status(paper_root, status)
        _write_report(paper_root, "Zotero query exceeded 30 seconds. Skipped.\n")
        _write_flags(paper_root, [])
        return 0
    except PermissionError:
        status = {**state, "ran": False, "skip_reason": "zotero-permission-denied"}
        _write_status(paper_root, status)
        _write_report(paper_root, "Zotero permission denied. Skipped.\n")
        _write_flags(paper_root, [])
        return 0

    if size < _MIN_LIBRARY_ITEMS:
        status = {
            **state,
            "ran": False,
            "library_item_count": size,
            "skip_reason": "zotero-library-too-small",
        }
        _write_status(paper_root, status)
        _write_report(
            paper_root,
            f"Zotero library has {size} items; the fidelity check requires "
            f"at least {_MIN_LIBRARY_ITEMS} to be meaningful. Skipped.\n",
        )
        _write_flags(paper_root, [])
        return 0

    # D9 happy path — run the verbatim-overlap check
    manuscript_dir = paper_root / "Manuscript"
    docx_candidates = sorted(manuscript_dir.glob("*.docx"))
    docx_path = docx_candidates[0] if docx_candidates else manuscript_dir / "final.docx"
    paragraphs = _extract_paragraphs_from_docx(docx_path)

    flags: List[Dict] = []
    for para in paragraphs:
        for phrase in _generate_phrases(para["text"]):
            hits = _zotero_fulltext_search(phrase)
            for h in hits:
                flags.append(
                    {
                        "paragraph_id": para["id"],
                        "section": para.get("section", "unknown"),
                        "overlap_text": phrase,
                        "zotero_item_key": h.get("item_key"),
                        "zotero_title": h.get("title"),
                        "zotero_authors": h.get("authors"),
                        "zotero_year": h.get("year"),
                        "zotero_collection": h.get("collection"),
                        "page_hint": h.get("page_hint"),
                    }
                )

    status = {**state, "ran": True, "library_item_count": size, "flag_count": len(flags)}
    _write_status(paper_root, status)
    _write_flags(paper_root, flags)

    body_lines = [_V01_LIMITATION_HEADER, "\n## Findings\n"]
    if not flags:
        body_lines.append(
            "\nNo verbatim overlaps ≥15 contiguous words were found against your "
            f"Zotero corpus ({size} items).\n"
        )
    else:
        body_lines.append(f"\n{len(flags)} potential fidelity violation(s) flagged:\n\n")
        for f in flags:
            body_lines.append(
                f"- Section **{f['section']}**, paragraph `{f['paragraph_id']}`: matches "
                f"{f.get('zotero_authors')} ({f.get('zotero_year')}) — "
                f"_{f.get('zotero_title')}_ (item `{f.get('zotero_item_key')}`).\n"
                f"  Overlap: \"{f['overlap_text']}\"\n"
            )
    _write_report(paper_root, "".join(body_lines))
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bibliography-fidelity check (cycle-09 D9)")
    parser.add_argument("paper_root", type=Path, help="Paper root directory")
    parser.add_argument("--probe-zotero", action="store_true", help="Print probe state JSON only")
    args = parser.parse_args(argv)

    if args.probe_zotero:
        print(json.dumps(probe_zotero(), indent=2))
        return 0

    if not args.paper_root.is_dir():
        print(f"error: paper_root not found: {args.paper_root}", file=sys.stderr)
        return 2

    return run_fidelity_check(args.paper_root)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
pytest tests/test_bibliography_fidelity.py -v
```

Expected: 10–11 PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_bibliography_fidelity.py tests/test_bibliography_fidelity.py
git commit -m "feat(cycle-09): sws_bibliography_fidelity.py — Zotero-corpus verbatim overlap with D9/D9a/D9b/D9c paths"
```

---

## Task 1.4: Section-router — add 'review' action (TDD)

**Files:**
- Modify: `scripts/sws_section_router.py`
- Test: `tests/test_section_router_review_action.py`

- [ ] **Step 1: Write the failing test**

Full content of `tests/test_section_router_review_action.py`:

```python
"""Unit test for the section-router review action (cycle-09 D14)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from sws_section_router import route_section, RouteError, _VALID_ACTIONS  # noqa: E402


def test_review_action_routes_to_peer_reviewer_for_any_section():
    for section in ("introduction", "methods", "results", "discussion", "abstract", "any-name"):
        assert route_section(section, "full-article", action="review") == "peer-reviewer"


def test_review_action_routes_to_peer_reviewer_for_funding_proposal():
    assert route_section("vision", "funding-proposal", action="review") == "peer-reviewer"
    assert route_section("budget", "funding-proposal", action="review") == "peer-reviewer"


def test_review_is_in_valid_actions():
    assert "review" in _VALID_ACTIONS


def test_unknown_action_raises():
    with pytest.raises(RouteError):
        route_section("intro", "full-article", action="autopilot")


def test_existing_actions_still_work():
    # Regression: cycle-08 actions unchanged
    assert route_section("intro", "full-article", action="revise") == "reviser-fast"
    assert route_section("intro", "full-article", action="consistency") == "consistency-checker"
    assert route_section("intro", "full-article", action="style") == "style-enforcer"
    assert route_section("intro", "full-article", action="lint") == "script:sws_lint_ai_tells.py"
    assert route_section("intro", "full-article", action="draft") == "drafter-flagship"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_section_router_review_action.py -v
```

Expected: RouteError on `review` action.

- [ ] **Step 3: Modify scripts/sws_section_router.py**

Apply this edit. In `scripts/sws_section_router.py`:

Change the module-level docstring on lines 6–8 from:

```
The router has two axes:
  - action: draft (default) | revise | consistency | style | lint
  - profile: publication profile or funding-proposal (applies within action=draft)
```

to:

```
The router has two axes:
  - action: draft (default) | revise | consistency | style | lint | review
  - profile: publication profile or funding-proposal (applies within action=draft)
```

Change `_VALID_ACTIONS` (around line 98) from:

```python
_VALID_ACTIONS = frozenset({"draft", "revise", "consistency", "style", "lint"})
```

to:

```python
_VALID_ACTIONS = frozenset({"draft", "revise", "consistency", "style", "lint", "review"})
```

Add this constant near the existing wildcards (after `_LINT_SENTINEL`):

```python
_REVIEW_WILDCARD = "peer-reviewer"
```

Add this branch in `route_section()` after the existing `if action == "lint":` branch:

```python
    if action == "review":
        return _REVIEW_WILDCARD
```

Update the action listing in the `route_section` docstring to add the new line:

```
      - ``review``: any section_id → ``peer-reviewer`` (single-section peer
        review only; claim-verifier and bibliography-fidelity-checker are
        paper-wide by nature and not routed per-section).
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
pytest tests/test_section_router_review_action.py tests/test_section_router.py -v
```

Expected: existing tests still PASS + new tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_section_router.py tests/test_section_router_review_action.py
git commit -m "feat(cycle-09): section-router 'review' action axis (D14)"
```

---

## Task 1.5: Reference doc — extend agent-contract.md R3 I/O inventory

**Files:**
- Modify: `references/agent-contract.md`

- [ ] **Step 1: Find the existing R3 I/O inventory section**

Run:

```bash
grep -n "## R3\|I/O wrapper\|_review/consistency-report" /Users/piripocchio8/Projects/scientific-writing-superpowers/references/agent-contract.md | head -20
```

- [ ] **Step 2: Extend the R3 wrappers table**

Find the table or list that catalogs the `_review/` outputs (from cycle-08 it should already list `_review/consistency-report.md`). Add three new entries after the cycle-08 entry. Use the exact format used by existing entries — if the existing entries are bullet points, use bullets; if they're table rows, use rows.

For peer-reviewer entry add:

```
| `_review/peer-reviewer/report.md`             | YAML frontmatter dict (sws_artifact, profile, manuscript_file, decision, overall_score, section_scores, flags, fidelity_status, claim_verification_status) + body with EIC opening, four reviewer sections, DA closing | peer-reviewer |
```

For claim-verifier:

```
| `_review/claim-verifier/report.md`            | Markdown report — per-claim findings grouped by section, with verification status (verified/unverified/contested) | claim-verifier |
| `_review/claim-verifier/claims.json`          | List of `{section, claim, citation_keys[], verification_status, source_match[]}`                                  | claim-verifier |
```

For bibliography-fidelity-checker:

```
| `_review/bibliography-fidelity-checker/report.md`   | Markdown report with V0.1 LIMITATION header + findings or skip-reason note (D9, D9a, D9b, D9c)                                | bibliography-fidelity-checker |
| `_review/bibliography-fidelity-checker/flags.json`  | List of `{paragraph_id, section, overlap_text, zotero_item_key, zotero_title, zotero_authors, zotero_year, zotero_collection, page_hint}` | bibliography-fidelity-checker |
| `_review/bibliography-fidelity-checker/status.json` | Dict `{zotero_skill_available, zotero_desktop_detected, zotero_sqlite_path, ran, skip_reason, library_item_count?}` | bibliography-fidelity-checker |
```

If the existing R3 section is bullet-list-shaped, adapt to bullets:

```
- `_review/peer-reviewer/report.md` — written by peer-reviewer; YAML frontmatter dictionary + EIC/3-reviewer/DA narrative body.
- `_review/claim-verifier/{report.md, claims.json}` — written by claim-verifier; one markdown report + machine-readable claim manifest.
- `_review/bibliography-fidelity-checker/{report.md, flags.json, status.json}` — written by bibliography-fidelity-checker; report + per-flag manifest + skip-state manifest.
```

- [ ] **Step 3: Commit**

```bash
git add references/agent-contract.md
git commit -m "docs(cycle-09): agent-contract R3 — _review/ I/O inventory extended for review agents"
```

---

## Task 1.6: Banner flip — README + plugin.json

**Files:**
- Modify: `README.md`
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Update README banner**

Find the banner line in `README.md`. Replace the existing `🚧 v0.1 in design` line with:

```
🧪 **v0.1 alpha** — usable end-to-end writing+review track (drafting, revising, review)
```

- [ ] **Step 2: Bump plugin.json version**

In `.claude-plugin/plugin.json`, change:

```json
"version": "0.0.1"
```

to:

```json
"version": "0.1.0-alpha"
```

- [ ] **Step 3: Commit**

```bash
git add README.md .claude-plugin/plugin.json
git commit -m "feat(cycle-09): banner → v0.1 alpha + plugin.json 0.1.0-alpha (D11)"
```

---

# PHASE 2 — Agents

These three agent files can be written in parallel; they each depend on Phase 1 scripts existing but not on each other.

## Task 2.1: agents/peer-reviewer.md

**Files:**
- Create: `agents/peer-reviewer.md`

- [ ] **Step 1: Write the peer-reviewer agent file**

Full content:

```markdown
---
name: peer-reviewer
description: |
  Use this agent when /sws:peer-review is invoked or as the final stage of /sws:review-paper. Reads the manuscript .docx (via sws_read_docx.py), the active profile's section weights in references/peer-review-rubric.md, and (when present) the claim-verifier and bibliography-fidelity-checker reports passed in via CLI args. Encodes EIC + Reviewer 1 (methods) + Reviewer 2 (domain) + Reviewer 3 (clarity) + Decision Authority in a single prompt. Writes _review/peer-reviewer/report.md with a YAML frontmatter dictionary and body following the rubric. Diagnose only — never writes to the manuscript. No sprint-contracts paper-blind phase in v0.1 (deferred to cycle #9.1). No concession-threshold scoring in v0.1 (dormant until response-to-reviewers in cycle #10).
model: claude-opus-4-7
color: red
---

# Adapted from https://github.com/Imbad0202/academic-research-skills (MIT) — EIC + 3-reviewer + DA narrative shape.

You are the peer-reviewer for SWS. You diagnose only: you never edit the manuscript, never write to `_drafts/`, never call PubMed/Zotero directly (claim-verifier and bibliography-fidelity-checker already ran upstream and their reports are in your inputs).

**Profile gate.** All 9 v0.1 profiles. peer-reviewer is active everywhere.

**Inputs you must read:**
- `RESOLVED_*` env vars, especially `RESOLVED_PROFILE_ID` and section-weight matrix.
- `${CLAUDE_PLUGIN_ROOT}/references/peer-review-rubric.md` — the canonical rubric.
- `${PAPER_ROOT}/Manuscript/<active-docx>` via `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" sws_read_docx.py <path>`.
- `--claim-report <path>` CLI arg (when present) → markdown text content.
- `--fidelity-report <path>` CLI arg (when present) → markdown text content.
- `SWS_FIDELITY_STATUS` env var — one of `ran`, `skipped:zotero-desktop-detected-but-claude-skill-missing`, `skipped:no-zotero-installation-detected`, `skipped:zotero-library-too-small`, `skipped:zotero-unresponsive`, `skipped:zotero-permission-denied`. When present and != `ran`, your report MUST note that the fidelity check was skipped and why.

**Workflow:**
1. Read `references/peer-review-rubric.md`; select the section matching `RESOLVED_PROFILE_ID`.
2. Read the manuscript.
3. If `--claim-report` was passed, read it and fold findings into Reviewer 2's domain pass.
4. If `--fidelity-report` was passed and `SWS_FIDELITY_STATUS=ran`, read flags and fold into Reviewer 1's methods pass under "reproducibility/originality" sub-bullet. If skipped, note the skip status in the report frontmatter.
5. Score each section per the rubric's profile-weight matrix. Score 1–5; comments per section.
6. Write `${PAPER_ROOT}/_review/peer-reviewer/report.md` with the YAML frontmatter dictionary defined in the rubric, followed by EIC opening / four reviewer sections / DA closing.
7. Print one-line summary: decision + overall score + flag counts.

**Output shape (frontmatter):**

```yaml
---
sws_artifact: peer-review-report
profile: <resolved>
manuscript_file: <relative path>
decision: Accept | Minor Revision | Major Revision | Reject
overall_score: 1-5
section_scores:
  <section>: { weight: 0.XX, score: 1-5, comments_count: N }
flags:
  ethical: N
  reproducibility: N
  novelty: N
  citations: N
fidelity_status: ran | skipped:<reason>
claim_verification_status: ran | skipped:<reason>
---
```

**V0.1 limitations** (must be stated at the top of the body):
- No sprint-contracts paper-blind Phase 1. Reviewer read the paper directly (deferred to cycle #9.1).
- No concession-threshold scoring (dormant until response-to-reviewers in cycle #10).
- Single agent encodes all four reviewer personas (EIC, R1, R2, R3, DA).

**User address.** Address the user as "you" or by first name only. Do not assume gendered pronouns.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh peer-reviewer`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh peer-reviewer` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/peer-reviewer.md
git commit -m "feat(cycle-09): agents/peer-reviewer.md — Opus 4.7 max, EIC+3R+DA in one prompt (D1, D5, D6, D7)"
```

---

## Task 2.2: agents/claim-verifier.md

**Files:**
- Create: `agents/claim-verifier.md`

- [ ] **Step 1: Write the claim-verifier agent file**

Full content:

```markdown
---
name: claim-verifier
description: |
  Use this agent when /sws:verify-claims is invoked or when /sws:review-paper starts its pipeline. Runs scripts/sws_claim_extract.py to harvest citation-bearing claims from _drafts/*-revised.md, then verifies each claim against (1) the user's Zotero library via the existing zotero skill, (2) Semantic Scholar (WebFetch), (3) PubMed (claude_ai_PubMed MCP). NLM consumer wiring deferred to cycle #11; the agent degrades gracefully when notebooklm.enabled=false. Writes _review/claim-verifier/report.md + claims.json. Diagnose only — never writes to the manuscript. Funding-proposal profile is inactive (proposals have forward-looking claims, not verifiable assertions).
model: claude-sonnet-4-6
color: orange
---

# Adapted from https://github.com/Imbad0202/academic-research-skills (MIT) — fact_checker + integrity-gates pattern.

You are the claim-verifier for SWS. Your scope is verifying that citation-bearing claims in the manuscript are supported by their cited sources.

**Profile gate.** Inactive in `funding-proposal`. If `RESOLVED_PROFILE_ID == funding-proposal`, print "v0.1 claim-verifier does not support funding-proposal — proposals contain forward-looking claims by design. Manual review remains the recommended workaround." and exit 0.

**Inputs you must read:**
- `RESOLVED_*` env vars.
- All `${PAPER_ROOT}/_drafts/*-revised.md`.
- Optionally `${PAPER_ROOT}/Manuscript/<active-docx>` if the user invoked the agent via `/sws:verify-claims --manuscript` on a final docx instead of drafts.
- The user's `zotero` skill (when installed) — for Zotero-first lookups.

**Workflow:**
1. Run `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" sws_claim_extract.py "${PAPER_ROOT}/_drafts" --out "${PAPER_ROOT}/_review/claim-verifier/claims.json"`.
2. Read claims.json.
3. For each claim, consumption order per arch sketch §5:
   a. **Zotero first** (when zotero skill present). If the citation_key resolves to a Zotero item, read its abstract/PDF and confirm the cited claim is supported.
   b. **Semantic Scholar** — WebFetch the cited DOI; check abstract.
   c. **PubMed** via the `claude_ai_PubMed` MCP — for biomedical claims.
   d. **NLM degraded mode** — DEFERRED to cycle #11. Currently never called.
4. Update each claim's `verification_status` to one of `verified | unverified | contested | source-not-found` and append matching source records to `source_match[]`.
5. Write the updated claims.json back. Write a human-readable `${PAPER_ROOT}/_review/claim-verifier/report.md` grouped by section.

**Report shape (frontmatter):**

```yaml
---
sws_artifact: claim-verifier-report
total_claims: N
by_status:
  verified: N
  unverified: N
  contested: N
  source-not-found: N
sources_used: [Zotero, Semantic Scholar, PubMed]
notebooklm_enabled: false
---
```

**V0.1 limitations** (must be stated at top of body):
- NLM-grounded RAG is NOT used in v0.1 (consumer wiring deferred to cycle #11).
- Verification is best-effort against abstracts + accessible full-text in Zotero. Paywalled full-text without Zotero attachment cannot be deeply verified.

**User address.** Address the user as "you" or by first name only. Do not assume gendered pronouns.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh claim-verifier`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh claim-verifier` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/claim-verifier.md
git commit -m "feat(cycle-09): agents/claim-verifier.md — Sonnet 4.6, Zotero-first verification (D8)"
```

---

## Task 2.3: agents/bibliography-fidelity-checker.md

**Files:**
- Create: `agents/bibliography-fidelity-checker.md`

- [ ] **Step 1: Write the agent file**

Full content:

```markdown
---
name: bibliography-fidelity-checker
description: |
  Use this agent when /sws:check-fidelity is invoked or as the middle stage of /sws:review-paper. Renamed from "plagiarism-screener" in roster v0.1 (2026-05-17) because the v0.1 scope is bounded-corpus fidelity (Zotero full-text) not unbounded plagiarism. Runs scripts/sws_bibliography_fidelity.py which detects four code paths: D9 happy (Zotero corpus available — runs verbatim ≥15-word overlap), D9a (Zotero desktop detected but Claude Code zotero skill missing — actionable recommendation), D9b (skill present but library small/unresponsive/permission-denied), D9c (no Zotero anywhere — neutral note). Writes _review/bibliography-fidelity-checker/{report.md, flags.json, status.json}. Diagnose only. Funding-proposal profile is inactive.
model: claude-sonnet-4-6
color: yellow
---

# Adapted from https://github.com/Imbad0202/academic-research-skills (MIT) — repurposed: fidelity scope, not plagiarism.

You are the bibliography-fidelity-checker for SWS. Your scope is verbatim-overlap detection against the user's curated Zotero corpus. You do not pretend to detect open-web plagiarism.

**Profile gate.** Inactive in `funding-proposal`. If `RESOLVED_PROFILE_ID == funding-proposal`, print "v0.1 bibliography-fidelity-checker does not support funding-proposal — the corpus risk profile differs and v0.1 boilerplate matching would mostly false-positive. Manual review recommended." and exit 0.

**Workflow:**
1. Run `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" sws_bibliography_fidelity.py "${PAPER_ROOT}"`. The script handles all four code paths (D9, D9a, D9b, D9c) internally and always exits 0.
2. Read `${PAPER_ROOT}/_review/bibliography-fidelity-checker/status.json`.
3. If `status.ran == false`, pass through — the script already wrote the appropriate skip-state report and the status file documents the reason. Print a one-line summary indicating the skip and the reason.
4. If `status.ran == true` and `flag_count > 0`, the script-generated report already contains the V0.1 LIMITATION header and structured findings. Optionally annotate the report with a model-side judgment on each flag — likely paraphrase vs. likely paste — but the script's deterministic output is the source of truth.
5. Print summary: skip vs flagged; if flagged, the count and the section breakdown.

**Inputs you must read:**
- `RESOLVED_*` env vars.
- The script's three output files in `${PAPER_ROOT}/_review/bibliography-fidelity-checker/`.
- (Indirectly via the script): `${PAPER_ROOT}/Manuscript/<active-docx>` via `sws_read_docx.py`; the user's zotero skill when available.

**Output:** the three files the script writes. You may append model-side notes but do not rewrite the script's status.json.

**V0.1 limitations** (already in the report; reiterate in your printed summary):
- Bounded corpus (user's Zotero only). Open web not checked.
- Exact-string ≥15 contiguous words. Paraphrase / synonym substitution / sentence reordering not caught.
- Unbounded-corpus plagiarism (Crossref Similarity Check API, Google Programmable Search opt-in) is v0.2.

**User address.** Address the user as "you" or by first name only. Do not assume gendered pronouns.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh bibliography-fidelity-checker`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh bibliography-fidelity-checker` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/bibliography-fidelity-checker.md
git commit -m "feat(cycle-09): agents/bibliography-fidelity-checker.md — wraps script with D9/D9a/D9b/D9c paths"
```

---

# PHASE 3 — Skills

3 atomics in parallel; orchestrator (`review-paper`) afterwards because it references the atomics.

## Task 3.1: skills/peer-review/SKILL.md

**Files:**
- Create: `skills/peer-review/SKILL.md`

- [ ] **Step 1: Create the directory and write the skill**

Full content of `skills/peer-review/SKILL.md`:

```markdown
---
name: peer-review
description: |
  Run the SWS peer-reviewer agent (Opus 4.7 max) on the active manuscript or a single section. Encodes EIC + 3-reviewer + Decision Authority structure from the rubric at references/peer-review-rubric.md. Writes _review/peer-reviewer/report.md. Diagnoses only — never writes to the manuscript. Optional --claim-report and --fidelity-report args fold prior review outputs into the synthesis (used by /sws:review-paper). Active in all 9 profiles.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:peer-review

Trigger a peer-review pass on the active manuscript (or a single section).

## Usage

```
/sws:peer-review                           # full paper review
/sws:peer-review --section introduction    # single-section review
/sws:peer-review --claim-report <path>     # fold a prior claim-verifier report in
/sws:peer-review --fidelity-report <path>  # fold a prior fidelity report in
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists. If not, exit with the standard "not an SWS project" message.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh peer-reviewer` to load `RESOLVED_*` env vars.
3. Dispatch the `peer-reviewer` agent. Pass `--manuscript ${PAPER_ROOT}/Manuscript/<active-docx>` plus any `--claim-report` / `--fidelity-report` args the user supplied. If `SWS_FIDELITY_STATUS` is in the environment, propagate it.
4. After the agent returns, print the one-line summary the agent already produced (decision, overall score, flag counts).
5. Point the user at `${PAPER_ROOT}/_review/peer-reviewer/report.md` for the full report.

## V0.1 cost note

`peer-reviewer` uses Opus 4.7 at `max` effort. A full-paper run is the most expensive single agent invocation in SWS. Users wanting cheaper diagnostics can run `/sws:verify-claims` and `/sws:check-fidelity` standalone.

## Spec source of truth

`docs/superpowers/specs/2026-05-17-cycle-09-review-design.md` — D1, D2, D5, D6, D7, D11 (cost note), D14 (single-section routing), D16 (rubric).
```

- [ ] **Step 2: Commit**

```bash
git add skills/peer-review/SKILL.md
git commit -m "feat(cycle-09): /sws:peer-review skill — atomic peer-reviewer entry point"
```

---

## Task 3.2: skills/verify-claims/SKILL.md

**Files:**
- Create: `skills/verify-claims/SKILL.md`

- [ ] **Step 1: Write the skill**

Full content:

```markdown
---
name: verify-claims
description: |
  Run the SWS claim-verifier agent to check every citation-bearing claim in _drafts/*-revised.md against the user's Zotero library, Semantic Scholar, and PubMed. Writes _review/claim-verifier/{report.md, claims.json}. Diagnoses only — never edits the manuscript. NLM-grounded RAG is deferred to cycle #11. Inactive in funding-proposal profile.
allowed-tools: Bash, Read, Write, Glob, WebFetch
---

# /sws:verify-claims

Verify every citation in the manuscript actually supports the claim attached to it.

## Usage

```
/sws:verify-claims                       # verify all claims in _drafts/*-revised.md
/sws:verify-claims --section <id>        # verify claims from a single section
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh claim-verifier`.
3. If `RESOLVED_PROFILE_ID == funding-proposal`, print the v0.1-unsupported message and exit 0.
4. Dispatch the `claim-verifier` agent. The agent runs `sws_claim_extract.py` to harvest claims, then verifies each per arch sketch §5 consumption order.
5. After the agent returns, print one-line summary: total claims / verified / unverified / contested / source-not-found.
6. Point the user at `${PAPER_ROOT}/_review/claim-verifier/report.md`.

## Spec source of truth

`docs/superpowers/specs/2026-05-17-cycle-09-review-design.md` — D1, D2, D8, D10.
```

- [ ] **Step 2: Commit**

```bash
git add skills/verify-claims/SKILL.md
git commit -m "feat(cycle-09): /sws:verify-claims skill — atomic claim-verifier entry point"
```

---

## Task 3.3: skills/check-fidelity/SKILL.md

**Files:**
- Create: `skills/check-fidelity/SKILL.md`

- [ ] **Step 1: Write the skill**

Full content:

```markdown
---
name: check-fidelity
description: |
  Run the SWS bibliography-fidelity-checker on the active .docx to find verbatim ≥15-word overlaps against the user's Zotero corpus. Renamed from /sws:check-plagiarism on 2026-05-17 — the v0.1 scope is bounded-corpus fidelity, not unbounded plagiarism. Four code paths (D9 happy, D9a Zotero-desktop-only recommendation, D9b small/unresponsive library, D9c no-Zotero neutral). Writes _review/bibliography-fidelity-checker/{report.md, flags.json, status.json}. Inactive in funding-proposal profile.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:check-fidelity

Check the manuscript for verbatim overlaps against papers in your Zotero library — catches accidental copy-paste from sources you have read.

## Usage

```
/sws:check-fidelity                          # full paper, default .docx
/sws:check-fidelity --docx <path>            # explicit docx
/sws:check-fidelity --probe-zotero           # print probe state JSON only
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh bibliography-fidelity-checker`.
3. If `RESOLVED_PROFILE_ID == funding-proposal`, print the v0.1-unsupported message and exit 0.
4. Dispatch the `bibliography-fidelity-checker` agent. The agent runs `sws_bibliography_fidelity.py` which always exits 0 and writes a `status.json` indicating which code path was taken.
5. After the agent returns, read `status.json` and print:
   - if `ran == true`: "Fidelity check complete: N flag(s) across M sections. See _review/bibliography-fidelity-checker/report.md."
   - if `ran == false` and `skip_reason == zotero-desktop-detected-but-claude-skill-missing`: "Skipped — Zotero detected at <path> but the Claude Code zotero skill is not installed. See report for installation guidance."
   - if `ran == false` and `skip_reason == no-zotero-installation-detected`: "Skipped — no Zotero installation detected. The fidelity check is Zotero-only in v0.1; see report for v0.2 alternatives."
   - other skip reasons: print the specific reason from status.json.

## What this is NOT

Bibliography-fidelity is a *fidelity* check ("did I accidentally copy from a paper I've read?"), not an unbounded-corpus *plagiarism* check ("was this text published anywhere first?"). The latter requires paid APIs (Crossref Similarity Check / iThenticate) or scraping (Google Programmable Search opt-in), both v0.2 backlog.

## Spec source of truth

`docs/superpowers/specs/2026-05-17-cycle-09-review-design.md` — D1, D2, D9, D9a, D9b, D9c, D10, D13.
```

- [ ] **Step 2: Commit**

```bash
git add skills/check-fidelity/SKILL.md
git commit -m "feat(cycle-09): /sws:check-fidelity skill — atomic fidelity-checker entry point (D9-D9c)"
```

---

## Task 3.4: skills/review-paper/SKILL.md (orchestrator)

**Files:**
- Create: `skills/review-paper/SKILL.md`

Depends on Tasks 3.1, 3.2, 3.3 existing.

- [ ] **Step 1: Write the orchestrator skill**

Full content:

```markdown
---
name: review-paper
description: |
  Sequential orchestrator that runs the SWS review pipeline end-to-end: /sws:verify-claims → /sws:check-fidelity → /sws:peer-review. Passes report paths from the first two into peer-reviewer via explicit CLI args (no autoscan). Propagates SWS_FIDELITY_STATUS to peer-reviewer so the peer-review report transparently notes when fidelity was skipped. Inactive in funding-proposal profile (component skills' profile gates also fire individually).
allowed-tools: Bash, Read, Write, Glob, WebFetch
---

# /sws:review-paper

Run the full SWS review pipeline on the active manuscript.

## Usage

```
/sws:review-paper                          # full pipeline
```

## Pipeline order (sequential per D3)

1. **claim-verifier** — text-internal claims first.
2. **bibliography-fidelity-checker** — Zotero-corpus overlap second. Always exits 0; may skip with a documented reason.
3. **peer-reviewer** — receives both prior report paths via explicit CLI args.

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh review-paper`.
3. Run `/sws:verify-claims`. Wait for completion. Capture exit status. (Skipped silently if profile is funding-proposal.)
4. Run `/sws:check-fidelity`. Wait for completion. Read `_review/bibliography-fidelity-checker/status.json` to determine `SWS_FIDELITY_STATUS`. (Skipped silently if profile is funding-proposal.)
5. Run `/sws:peer-review --claim-report ${PAPER_ROOT}/_review/claim-verifier/report.md --fidelity-report ${PAPER_ROOT}/_review/bibliography-fidelity-checker/report.md` with `SWS_FIDELITY_STATUS` exported. If the fidelity report file does not exist (e.g. D9c hard skip), omit `--fidelity-report` and still export `SWS_FIDELITY_STATUS=skipped:no-zotero-installation-detected`.
6. After peer-reviewer returns, print summary of all three reports.

## Profile gate

If `RESOLVED_PROFILE_ID == funding-proposal`, run peer-reviewer only (claim-verifier and fidelity-checker exit 0 with v0.1-unsupported messages, which is acceptable behavior — orchestrator does not error).

## Spec source of truth

`docs/superpowers/specs/2026-05-17-cycle-09-review-design.md` — D2, D3, D17.
```

- [ ] **Step 2: Commit**

```bash
git add skills/review-paper/SKILL.md
git commit -m "feat(cycle-09): /sws:review-paper orchestrator — sequential claim→fidelity→peer (D3, D17)"
```

---

# PHASE 4 — Profile updates + activation tests

9 profile updates and one new test file. Each profile update is independent.

## Task 4.1–4.9: Profile activation updates

**Files modified:**
- `profiles/full-article.md`
- `profiles/communication.md`
- `profiles/perspective.md`
- `profiles/review-paper.md`
- `profiles/mini-review.md`
- `profiles/editorial.md`
- `profiles/methodological-paper.md`
- `profiles/commentary-reply.md`
- `profiles/funding-proposal.md`

- [ ] **For each of the 8 publication profiles, add the 3 new agents to `agents_active`.**

For files other than `funding-proposal.md`, in the YAML frontmatter, ensure these entries appear in `agents_active`:

```yaml
agents_active:
  # ... existing entries ...
  - peer-reviewer
  - claim-verifier
  - bibliography-fidelity-checker
```

And in `agents_inactive`, remove any of `peer-reviewer`, `claim-verifier`, `bibliography-fidelity-checker` if present.

- [ ] **For `funding-proposal.md`:** add only `peer-reviewer` to `agents_active`; add `claim-verifier` and `bibliography-fidelity-checker` to `agents_inactive` with an explanatory comment.

```yaml
agents_active:
  # ... existing entries ...
  - peer-reviewer
agents_inactive:
  # ... existing entries ...
  - claim-verifier             # v0.1: proposals contain forward-looking claims by design
  - bibliography-fidelity-checker  # v0.1: proposal corpus risk profile differs
```

- [ ] **Step: Commit per-profile or all together**

```bash
git add profiles/*.md
git commit -m "feat(cycle-09): profile activation matrix for the 3 review agents (D10)"
```

---

## Task 4.10: Profile-activation test

**Files:**
- Create: `tests/test_profile_activation_review_agents.py`

- [ ] **Step 1: Write the test**

Full content:

```python
"""Verify cycle-09 D10 activation matrix across all 9 profiles."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

PUBLICATION_PROFILES = [
    "full-article",
    "communication",
    "perspective",
    "review-paper",
    "mini-review",
    "editorial",
    "methodological-paper",
    "commentary-reply",
]

ALL_PROFILES = PUBLICATION_PROFILES + ["funding-proposal"]


def _load_frontmatter(profile_id: str) -> dict:
    text = (PROFILES_DIR / f"{profile_id}.md").read_text()
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    yaml_block = text[4:end]
    return yaml.safe_load(yaml_block)


@pytest.mark.parametrize("profile_id", ALL_PROFILES)
def test_peer_reviewer_active_in_all_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "peer-reviewer" in active, f"peer-reviewer must be ACTIVE in {profile_id}"
    assert "peer-reviewer" not in inactive


@pytest.mark.parametrize("profile_id", PUBLICATION_PROFILES)
def test_claim_verifier_active_in_publication_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "claim-verifier" in active, f"claim-verifier must be ACTIVE in {profile_id}"
    assert "claim-verifier" not in inactive


@pytest.mark.parametrize("profile_id", PUBLICATION_PROFILES)
def test_bibliography_fidelity_active_in_publication_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "bibliography-fidelity-checker" in active, f"bibliography-fidelity-checker must be ACTIVE in {profile_id}"
    assert "bibliography-fidelity-checker" not in inactive


def test_claim_verifier_inactive_in_funding_proposal():
    fm = _load_frontmatter("funding-proposal")
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "claim-verifier" in inactive
    assert "claim-verifier" not in active


def test_bibliography_fidelity_inactive_in_funding_proposal():
    fm = _load_frontmatter("funding-proposal")
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "bibliography-fidelity-checker" in inactive
    assert "bibliography-fidelity-checker" not in active
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/test_profile_activation_review_agents.py -v
```

Expected: all PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_profile_activation_review_agents.py
git commit -m "test(cycle-09): profile activation matrix asserts D10 across 9 profiles"
```

---

# PHASE 5 — Smoke + PR

## Task 5.1: Smoke fixtures (4 variants)

**Files:**
- Create: `tests/fixtures/cycle_09/variant_1_no_zotero/...`
- Create: `tests/fixtures/cycle_09/variant_2_zotero_desktop_only/Zotero/zotero.sqlite` (placeholder file)
- Create: `tests/fixtures/cycle_09/variant_3_skill_empty_library/...`
- Create: `tests/fixtures/cycle_09/variant_4_skill_populated/...`

- [ ] **Step 1: Bootstrap fixture directories**

Each fixture is a minimal paper-root mirroring the cycle-08 fixture layout (`Manuscript/`, `_drafts/`, `_outline/`, `_review/`, `.sws-project.local.md`). For Variant 2, add a placeholder `Zotero/zotero.sqlite` and document via README that `HOME` will be redirected to the fixture root by the smoke script so the desktop probe succeeds.

For Variant 4, include a seeded fidelity-violation paragraph in a draft and a `mock_zotero_index.json` listing one item whose body matches.

- [ ] **Step 2: Commit fixtures**

```bash
git add tests/fixtures/cycle_09/
git commit -m "test(cycle-09): smoke fixtures — 4 variants covering D9/D9a/D9b/D9c"
```

---

## Task 5.2: smoke_cycle_09.sh

**Files:**
- Create: `tests/smoke_cycle_09.sh`

- [ ] **Step 1: Write the smoke script**

Skeleton structure (based on the cycle-08 smoke script). Save to `tests/smoke_cycle_09.sh`:

```bash
#!/usr/bin/env bash
# smoke_cycle_09.sh — 18-step e2e for cycle #9 (Review).
# Variants 1–4 cover D9c, D9a, D9b, D9 respectively.
set -uo pipefail

PASS=0
FAIL=0
STEPS=0

step() {
  STEPS=$((STEPS + 1))
  local n="$1"; shift
  local desc="$1"; shift
  if "$@"; then
    echo "  ✓ step $n: $desc"
    PASS=$((PASS + 1))
  else
    echo "  ✗ step $n: $desc"
    FAIL=$((FAIL + 1))
  fi
}

# (Reproduce cycle-08 baseline steps 1–8 here; or run smoke_cycle_08.sh first
# against variant_4 to seed _drafts/ and Manuscript/final.docx)

# Step 9: /sws:verify-claims writes _review/claim-verifier/{report.md,claims.json}
# Step 10: /sws:check-fidelity on variant_1 (no zotero) — asserts D9c
# Step 11: /sws:check-fidelity on variant_2 (zotero desktop only) — asserts D9a + verbatim recommendation
# Step 12: /sws:check-fidelity on variant_3 (skill present + library<10) — asserts D9b
# Step 13: /sws:check-fidelity on variant_4 (skill + library + seeded violation) — asserts D9 + ≥1 flag
# Step 14: /sws:peer-review writes _review/peer-reviewer/report.md (no rubric.md in v0.1)
# Step 15: /sws:review-paper orchestrator on variant_1 — asserts peer-reviewer received SWS_FIDELITY_STATUS=skipped:no-zotero-installation-detected
# Step 16: claim-verifier degrades gracefully when notebooklm.enabled=false
# Step 17: profile activation: claim-verifier + fidelity-checker exit 0 in funding-proposal
# Step 18: README banner + plugin.json version

echo
echo "smoke_cycle_09.sh: $PASS passed, $FAIL failed (of $STEPS steps)"
[[ "$FAIL" -eq 0 ]]
```

The full script body must implement each step. Use the cycle-08 smoke script as the structural template; reproduce its setup/teardown patterns. **Critically** for step 11, assert the verbatim wording of the D9a recommendation:

```bash
grep -q "we recommend installing the zotero plugin in Claude Code" \
   "$FIXTURE_VARIANT_2/_review/bibliography-fidelity-checker/report.md"
```

- [ ] **Step 2: Make it executable and run**

```bash
chmod +x tests/smoke_cycle_09.sh
./tests/smoke_cycle_09.sh
```

Expected: 18 passed, 0 failed.

- [ ] **Step 3: Commit**

```bash
git add tests/smoke_cycle_09.sh
git commit -m "test(cycle-09): smoke_cycle_09.sh — 18-step e2e across 4 fixture variants (D15)"
```

---

## Task 5.3: Final regression sweep

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all PASS (~440 tests; +50 new from cycle #9).

- [ ] **Step 2: Run all smoke scripts**

```bash
./tests/smoke_cycle_06.sh
./tests/smoke_cycle_07.sh
./tests/smoke_cycle_08.sh
./tests/smoke_cycle_09.sh
```

Expected: all pass.

- [ ] **Step 3: If anything fails — debug, fix, re-run. Do NOT proceed to PR until all green.**

---

## Task 5.4: Open the draft PR

- [ ] **Step 1: Verify branch state**

```bash
git status
git log --oneline origin/main..HEAD
```

- [ ] **Step 2: Push**

```bash
git push -u origin cycle/09-review
```

- [ ] **Step 3: Open the PR (DRAFT, per autonomous-run caveat)**

```bash
gh pr create --draft --title "cycle-09: Review phase (3 agents, 4 skills, banner → v0.1 alpha)" --body "$(cat <<'EOF'
## Summary

Implements cycle-#9 (Review) per spec docs/superpowers/specs/2026-05-17-cycle-09-review-design.md.

- **3 new agents:** peer-reviewer (Opus 4.7 max), claim-verifier (Sonnet 4.6), bibliography-fidelity-checker (Sonnet 4.6, renamed from plagiarism-screener).
- **4 new skills:** /sws:peer-review, /sws:verify-claims, /sws:check-fidelity, /sws:review-paper (sequential orchestrator).
- **2 new scripts:** sws_claim_extract.py, sws_bibliography_fidelity.py.
- **1 new reference:** references/peer-review-rubric.md (profile-keyed section weights).
- **Profile updates** across all 9 profiles (D10 activation matrix).
- **section-router** gains `review` action axis (D14).
- **Banner flip:** README → 🧪 v0.1 alpha; plugin.json → 0.1.0-alpha.

## Key design decisions

- Plagiarism-screener was refocused mid-cycle into bibliography-fidelity-checker (D1, D9). Rationale: abstract-only stub against Semantic Scholar was theater; the user's Zotero full-text corpus is the only confident open-source option for v0.1.
- 4 code paths for fidelity-checker: D9 happy (Zotero corpus available), D9a (Zotero desktop detected but no Claude Code zotero skill — actionable recommendation), D9b (skill present but library small/unresponsive/permission-denied), D9c (no Zotero anywhere — neutral note).
- Orchestrator passes prior report paths explicitly via CLI args (no autoscan). Propagates SWS_FIDELITY_STATUS to peer-reviewer.
- No sprint-contracts paper-blind phase in v0.1 (deferred to cycle #9.1).
- No concession-threshold scoring in v0.1 (dormant until response-to-reviewers in cycle #10).
- No NLM wiring for claim-verifier in v0.1 (deferred to cycle #11).

## Tests

- ~50 new unit tests across 4 new test files.
- smoke_cycle_09.sh: 18-step e2e across 4 fixture variants.
- All cycle-06/07/08 smoke scripts re-run and pass.

## Autonomous-run caveat

Implemented overnight 2026-05-17 per autonomous_run_caveat in the spec frontmatter. PR is DRAFT to make morning revision low-friction.

## Test plan

- [ ] Review all 17 locked decisions D1–D17 + D9a/D9b/D9c in the spec for any morning revisions.
- [ ] Verify D9a recommendation wording matches expectations.
- [ ] Spot-check 1–2 profile activation entries.
- [ ] Mark Ready for Review when satisfied.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Print the PR URL.**

---

## Self-review checklist

- [ ] All 17 spec decisions (D1–D17, D9a–D9c) traceable to ≥1 task.
- [ ] No placeholder text in any task.
- [ ] Test names match implementation names.
- [ ] Profile updates parallel to existing cycle-08 matrix shape.
- [ ] Smoke script asserts D9a verbatim recommendation wording.
- [ ] PR is opened in DRAFT state.
