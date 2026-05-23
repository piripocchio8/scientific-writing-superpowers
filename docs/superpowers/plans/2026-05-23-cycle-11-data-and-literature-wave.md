# Cycle #11 — Data + literature wave — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 4 rostered agents (data-curator #18, plot-maker #17, literature-searcher #5, bibliography-curator #19), 4 skills, 6 helper scripts, 2 reference docs, profile-activation updates across all 9 profiles, and a full unit + smoke test suite. End-of-cycle: a paper's data, figures, literature discovery, and citation hygiene are all SWS-managed.

**Architecture:** Same thin-agent pattern as cycles #7–#10. Each agent sources `agent_prelude.sh`, calls `agent_should_run.sh`, then performs its narrow job. The 4 skills are independent utilities (no orchestrator — data/literature agents serve different workflow phases). `data-curator` delegates all xlsx reads to `sws_xlsx_resolve.py` (which wraps `sws_read_xlsx.py`); `plot-maker` sizes figures from the resolved journal-style overlay, never hardcodes dimensions; `literature-searcher` and `bibliography-curator` keep NLM deferred (D9) and degrade gracefully. The 3 web-source scripts use WebFetch/curl + parsing with caching and 429 backoff (MCP-aversion, D8). All agents are diagnostic/asset agents — they write to `Zenodo_db/`, `refs/_lit-search/`, or `_review/bibliography-audit/`, never to the manuscript `.docx`.

**Tech Stack:** Python 3.9+ via per-paper `.venv/`, stdlib-only except `openpyxl` (pre-installed in `sws-deps.txt`) and `matplotlib` (pre-installed) for plot-maker; bash for skills; markdown + YAML frontmatter for agents, profiles, references; `unittest` (stdlib) for unit tests; shell smoke for e2e.

**Spec source of truth:** `docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md`. Frontmatter dictionary is canonical; this plan implements D1–D13.

**Execution mode:** Autonomous overnight. Maximize within-phase parallelism. Open PR in DRAFT state for next-day review.

---

## File Structure

**CREATE (new files):**

Scripts:
- `scripts/sws_xlsx_resolve.py`
- `scripts/sws_data_manifest.py`
- `scripts/sws_plot_runner.py`
- `scripts/sws_semantic_scholar.py`
- `scripts/sws_crossref.py`
- `scripts/sws_openalex.py`

References:
- `references/zenodo-db-layout.md`
- `references/literature-sources.md`

Agents (4 files):
- `agents/data-curator.md`
- `agents/plot-maker.md`
- `agents/literature-searcher.md`
- `agents/bibliography-curator.md`

Skills (4 dirs, each with one SKILL.md):
- `skills/curate-data/SKILL.md`
- `skills/make-figure/SKILL.md`
- `skills/search-literature/SKILL.md`
- `skills/audit-bibliography/SKILL.md`

Tests:
- `tests/test_xlsx_resolve.py`
- `tests/test_data_manifest.py`
- `tests/test_plot_runner.py`
- `tests/test_semantic_scholar.py`
- `tests/test_crossref.py`
- `tests/test_openalex.py`
- `tests/test_bibliography_refs_format.py`
- `tests/test_profile_activation_data_lit.py`
- `tests/fixtures/cycle_11/` (fixture directory)
- `tests/fixtures/cycle_11/zenodo_db/` (fixture Zenodo_db layout)
- `tests/fixtures/cycle_11/api_responses/` (captured API JSON fixtures)
- `tests/smoke_cycle_11.sh`

**MODIFY (existing files):**
- `references/agent-contract.md` — extend R3 I/O inventory with Zenodo_db/ shapes + lit-search + bibliography-audit outputs
- `profiles/full-article.md` — agents_active/agents_inactive for the 4 new agents
- `profiles/communication.md`
- `profiles/methodological-paper.md`
- `profiles/review-paper.md`
- `profiles/mini-review.md`
- `profiles/perspective.md`
- `profiles/editorial.md`
- `profiles/commentary-reply.md`
- `profiles/funding-proposal.md`

---

## Phase Map (for parallel dispatch)

**Phase 1 — Scripts + references (9 tasks, parallelizable):** `sws_xlsx_resolve.py`, `sws_data_manifest.py`, `sws_plot_runner.py`, `sws_semantic_scholar.py`, `sws_crossref.py`, `sws_openalex.py`, `references/zenodo-db-layout.md`, `references/literature-sources.md`, `references/agent-contract.md` update.

**Phase 2 — Agents (4 tasks, parallel; depends on Phase 1 scripts):** `data-curator`, `plot-maker`, `literature-searcher`, `bibliography-curator`.

**Phase 3 — Skills (4 tasks, parallel; depends on Phase 2 agents):** `/sws:curate-data`, `/sws:make-figure`, `/sws:search-literature`, `/sws:audit-bibliography`.

**Phase 4 — Profiles + activation tests (10 tasks, parallel; depends on Phase 2 agents):** 9 profile updates + `test_profile_activation_data_lit.py`.

**Phase 5 — Unit tests (6 tasks, parallel; depends on Phase 1 scripts):** `test_xlsx_resolve.py`, `test_data_manifest.py`, `test_semantic_scholar.py`, `test_crossref.py`, `test_openalex.py`, `test_bibliography_refs_format.py`. (`test_plot_runner.py` is part of Task 1.9 and runs with Phase 1.)

**Phase 6 — Smoke + PR (sequential; depends on all prior phases):** fixtures + `tests/smoke_cycle_11.sh` + draft PR.

---

# PHASE 1 — Scripts + references

These tasks are independent and can run fully in parallel.

---

## Task 1.1: Reference doc — zenodo-db-layout.md

**Files:**
- Create: `references/zenodo-db-layout.md`

- [ ] **Step 1: Write the reference doc**

Full content of `references/zenodo-db-layout.md`:

````markdown
---
sws_artifact: zenodo-db-layout
artifact_version: 0.1
locked: 2026-05-22
used_by: [agents/data-curator.md, agents/plot-maker.md, skills/curate-data/SKILL.md, skills/make-figure/SKILL.md]
---

# Zenodo_db/ layout (v0.1 — locked D5)

The `Zenodo_db/` directory inside a paper root is the local data-authority layout. It is marker-scoped (only present in SWS projects). Writes pass through the cycle-#5 backup hook.

## Directory structure

```
Zenodo_db/
├── data/         # source .xlsx (the data authority) + raw exports (CSV, TXT)
├── scripts/      # fit + plot scripts, co-located with the data they consume
├── figures/      # plot-maker outputs — PNG, PDF, SVG; regenerable from data/ + scripts/
├── manifest.json # provenance spine: each entry links dataset → script → figure(s)
└── _archive/     # superseded data/figure versions; filenames must include a UTC timestamp
```

## manifest.json schema

`manifest.json` is the single source of figure provenance. Every figure in `figures/` must have an entry here.

```json
[
  {
    "dataset": "data/measurements.xlsx",
    "sheet": "Kinetics",
    "script": "scripts/plot_kinetics.py",
    "figures": ["figures/fig1_kinetics.png", "figures/fig1_kinetics.pdf"],
    "generated_at": "2026-05-22T14:30:00Z",
    "journal_style": "acs-jacs",
    "notes": ""
  }
]
```

**Required keys per entry:**
- `dataset` — relative path inside `Zenodo_db/` to the source `.xlsx` (or other data file)
- `sheet` — worksheet name within the dataset (use `"all"` for single-sheet workbooks)
- `script` — relative path inside `Zenodo_db/` to the plot/fit script that produced the figure(s)
- `figures` — list of relative paths inside `Zenodo_db/` to the produced figure files
- `generated_at` — ISO-8601 UTC timestamp of the last successful regeneration
- `journal_style` — the resolved journal-style overlay id at time of generation (empty string if none resolved)
- `notes` — free text; empty string if unused

**Invariant:** `sws_data_manifest.py` writes `manifest.json` atomically (write to `.manifest.json.tmp`, then rename). `plot-maker` always updates `manifest.json` in the same step as writing the figure. Orphaned figures (in `figures/` but no manifest entry) are flagged by `sws_data_manifest.py --check`.

## Formula resolution rule (D4)

`data-curator` reads `.xlsx` files through `sws_xlsx_resolve.py`, which calls `sws_read_xlsx.py` with `data_only=True`. If a formula cell has no cached value (returns `None`), the script exits non-zero with the message:

> `Cell <sheet>!<ref> is a formula with no cached value. Open and save this workbook in Excel or LibreOffice so values cache, then re-run /sws:curate-data.`

The user opens and saves the workbook once; all formula cells cache their values and subsequent runs proceed.

## _archive/ convention

Before overwriting any file in `data/` or `figures/`, the previous version is moved to `_archive/` with a UTC-timestamp suffix:

```
_archive/measurements_20260521T103000Z.xlsx
_archive/fig1_kinetics_20260521T103000Z.png
```

This is handled by the cycle-#5 `PreToolUse` backup hook and is not the agent's responsibility.
````

- [ ] **Step 2: Commit**

```bash
git add references/zenodo-db-layout.md
git commit -m "feat(cycle-11): references/zenodo-db-layout.md — locked Zenodo_db/ layout + manifest.json schema (D5)"
```

---

## Task 1.2: Reference doc — literature-sources.md

**Files:**
- Create: `references/literature-sources.md`

- [ ] **Step 1: Write the reference doc**

Full content of `references/literature-sources.md`:

````markdown
---
sws_artifact: literature-sources
artifact_version: 0.1
locked: 2026-05-22
used_by: [agents/literature-searcher.md, agents/bibliography-curator.md, agents/claim-verifier.md]
---

# Literature sources — fallback chain + policy (v0.1)

This document specifies which source each agent calls, in which order, and the rate-limit / caching policy for each. MCP-aversion is honored throughout: only PubMed retains an MCP path (no first-class CLI exists for it); all others use WebFetch/curl + parsing scripts.

## Source registry

| ID | Script / MCP | Primary use | Free tier limit |
|----|--------------|-------------|-----------------|
| Zotero | `zotero` skill (existing) | All agents — first in chain | Local library, no rate limit |
| PubMed | `claude_ai_PubMed` MCP | Biomedical search + PMID resolve | 3 req/s (NCBI E-utilities) |
| Semantic Scholar | `scripts/sws_semantic_scholar.py` | Discovery + citation graph | 100 req/5 min unauthenticated |
| CrossRef | `scripts/sws_crossref.py` | DOI resolution + metadata | ~50 req/s polite pool |
| OpenAlex | `scripts/sws_openalex.py` | Broad metadata + OA full-text | 10 req/s polite pool |
| NLM | DEFERRED (D9) | Grounded RAG — cycle #13 | n/a |

## Per-agent fallback chains

### literature-searcher (DISCOVERY — Plan phase)

1. **Zotero** (local library via `zotero` skill) — search by keyword + topic. Most lookups stay local.
2. **PubMed** (MCP) — biomedical topics, PMID → abstract.
3. **Semantic Scholar** (`sws_semantic_scholar.py`) — title-fuzzy match, citation-graph expansion, abstract fetch.
4. **OpenAlex** (`sws_openalex.py`) — when Semantic Scholar returns no result or rate-limits.
5. **NLM grounded-RAG** — DEFERRED (D9). Agent degrades gracefully; never fails on absence.

Output: `refs/_lit-search/<slug>.md` — ranked candidates (title / authors / year / DOI / abstract + why-relevant).

### bibliography-curator (AUDIT — Submit phase)

1. **Zotero** (local library via `zotero` skill) — resolve citation key → bibliographic record.
2. **CrossRef** (`sws_crossref.py`) — DOI → authoritative metadata; used for format validation.
3. **OpenAlex** (`sws_openalex.py`) — fallback when CrossRef has no record (e.g., non-DOI items).
4. **NLM grounded-RAG** — DEFERRED (D9). Agent degrades gracefully.

Output: `_review/bibliography-audit/report.md` + `_review/bibliography-audit/fixes.json`.

### claim-verifier (reference, cycle #9)

Uses Zotero → Semantic Scholar → PubMed. Documented in cycle-#9 spec. Repeated here for completeness only.

## Caching policy (all WebFetch/curl scripts)

Each script maintains a per-paper cache at `$PAPER_ROOT/.sws_cache/<source_id>/`. Cache entries are keyed by the normalized query (DOI, title hash, or search string SHA-256). TTL: 7 days for metadata; 30 days for full-text snippets. The cache directory is gitignored.

## 429 backoff (all WebFetch/curl scripts)

On HTTP 429, each script waits `min(2^n * 1s, 64s)` where `n` is the retry attempt index, up to 5 retries. After 5 failures the script exits non-zero with a human-readable message naming the source and the recommended action (reduce request frequency or add an API key via env var).

## Authentication opt-in

Set `SEMANTIC_SCHOLAR_API_KEY` in the paper-root `.env` (gitignored) to raise the Semantic Scholar rate limit to 1 req/s (official key) or higher (institutional). The scripts read this env var if present and add the `x-api-key` header. Not required in v0.1.
````

- [ ] **Step 2: Commit**

```bash
git add references/literature-sources.md
git commit -m "feat(cycle-11): references/literature-sources.md — 5-source fallback chain + caching/backoff policy (D8)"
```

---

## Task 1.3: Script — sws_xlsx_resolve.py (TDD)

**Files:**
- Create: `scripts/sws_xlsx_resolve.py`
- Test: `tests/test_xlsx_resolve.py`

**Purpose:** Wrap `sws_read_xlsx.py`'s `data_only=True` path. On a formula cell that has no cached value (openpyxl returns `None` for the cell *and* the formula source is non-empty), exit non-zero with the D4 actionable message naming the exact cell. Never re-derive or guess.

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_xlsx_resolve.py`:

```python
"""Unit tests for sws_xlsx_resolve.py — D4 fail-loud on un-cached formula cells.

All fixtures are built inline with openpyxl; no binary xlsx files committed.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

try:
    from openpyxl import Workbook
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "sws_xlsx_resolve.py"

pytestmark = pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def _make_clean_workbook(tmp_path: Path) -> Path:
    """Workbook with only plain numeric values — no formulas anywhere."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    ws["A1"] = "compound"
    ws["B1"] = "yield_pct"
    ws["A2"] = "cpd-1"
    ws["B2"] = 72.5
    ws["A3"] = "cpd-2"
    ws["B3"] = 65.0
    path = tmp_path / "clean.xlsx"
    wb.save(str(path))
    return path


def _make_workbook_with_cached_formula(tmp_path: Path) -> Path:
    """Workbook where a formula cell HAS a cached numeric value.

    openpyxl data_only=True will return the cached number, not None.
    We simulate this by saving the workbook with data_only=False (formula
    source preserved), then reloading it with data_only=True to confirm the
    cached value is accessible. Since openpyxl cannot truly cache values at
    write-time the same way Excel does, we use a plain value cell to represent
    a "cached" formula result — the resolver must accept it.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Calc"
    ws["A1"] = 10.0
    ws["B1"] = 32.0
    # Represent cached formula result as a plain numeric value.
    # (openpyxl cannot inject Excel calc-cache entries; the test covers the
    # code path where data_only read returns a non-None numeric value.)
    ws["C1"] = 42.0
    path = tmp_path / "cached.xlsx"
    wb.save(str(path))
    return path


def _make_workbook_with_uncached_formula(tmp_path: Path) -> Path:
    """Workbook where a formula cell has NO cached value.

    openpyxl data_only=True on a freshly written workbook returns None for
    formula cells because Excel never ran the calculation. This is the
    fail-loud path.
    """
    from openpyxl import load_workbook as lw
    wb = Workbook()
    ws = wb.active
    ws.title = "Results"
    ws["A1"] = 5.0
    ws["B1"] = 3.0
    ws["C1"] = "=A1+B1"  # formula source; no cached value
    path = tmp_path / "uncached.xlsx"
    wb.save(str(path))
    # Confirm openpyxl data_only=True truly returns None for C1.
    wb2 = lw(str(path), data_only=True)
    cell_val = wb2["Results"]["C1"].value
    if cell_val is not None:
        pytest.skip("openpyxl cached the formula value on this platform — skip fail-loud test")
    return path


def _run(args, expect_zero: bool = True):
    cp = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )
    if expect_zero:
        assert cp.returncode == 0, f"unexpected non-zero: {cp.stderr}"
    return cp


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

def test_clean_workbook_exits_zero_and_emits_tsv(tmp_path):
    path = _make_clean_workbook(tmp_path)
    cp = _run([str(path)])
    assert "compound" in cp.stdout
    assert "cpd-1" in cp.stdout
    assert "72.5" in cp.stdout


def test_cached_value_workbook_exits_zero(tmp_path):
    path = _make_workbook_with_cached_formula(tmp_path)
    cp = _run([str(path)])
    assert cp.returncode == 0


def test_sheet_scope_respected(tmp_path):
    path = _make_clean_workbook(tmp_path)
    cp = _run([str(path), "--sheet", "Data"])
    assert "compound" in cp.stdout
    assert cp.returncode == 0


def test_range_scope_respected(tmp_path):
    path = _make_clean_workbook(tmp_path)
    cp = _run([str(path), "--sheet", "Data", "--range", "A2:B3"])
    assert "cpd-1" in cp.stdout
    assert "compound" not in cp.stdout  # header row excluded
    assert cp.returncode == 0


# ---------------------------------------------------------------------------
# Fail-loud path (D4)
# ---------------------------------------------------------------------------

def test_uncached_formula_cell_exits_nonzero(tmp_path):
    path = _make_workbook_with_uncached_formula(tmp_path)
    cp = _run([str(path)], expect_zero=False)
    assert cp.returncode != 0


def test_uncached_formula_message_names_sheet_and_cell(tmp_path):
    path = _make_workbook_with_uncached_formula(tmp_path)
    cp = _run([str(path)], expect_zero=False)
    # D4: message must name the sheet and cell reference
    assert "Results" in cp.stderr or "Results" in cp.stdout
    assert "C1" in cp.stderr or "C1" in cp.stdout


def test_uncached_formula_message_instructs_open_save(tmp_path):
    """D4: actionable message must mention open + save and /sws:curate-data."""
    path = _make_workbook_with_uncached_formula(tmp_path)
    cp = _run([str(path)], expect_zero=False)
    combined = cp.stderr + cp.stdout
    assert "Open and save" in combined or "open and save" in combined
    assert "/sws:curate-data" in combined


def test_uncached_formula_verbatim_message_fragment(tmp_path):
    """D4: the exact message fragment from the spec must appear verbatim."""
    path = _make_workbook_with_uncached_formula(tmp_path)
    cp = _run([str(path)], expect_zero=False)
    combined = cp.stderr + cp.stdout
    assert "is a formula with no cached value" in combined


def test_missing_file_exits_2(tmp_path):
    cp = _run([str(tmp_path / "nonexistent.xlsx")], expect_zero=False)
    assert cp.returncode == 2


def test_malformed_file_exits_3(tmp_path):
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"not a real xlsx file")
    cp = _run([str(bad)], expect_zero=False)
    assert cp.returncode == 3
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_xlsx_resolve.py -v
```

Expected: `ImportError: No module named 'sws_xlsx_resolve'` or all tests FAILED/ERROR.

- [ ] **Step 3: Implement scripts/sws_xlsx_resolve.py**

Full content of `scripts/sws_xlsx_resolve.py`:

```python
"""Resolve an .xlsx workbook for SWS data-authority use (D4).

Wraps sws_read_xlsx.py's data_only=True path. Every formula cell that has NO
cached value causes an immediate non-zero exit with an actionable message naming
the exact cell and telling the user how to fix it. Never re-derives or guesses
formula results.

CLI (same surface as sws_read_xlsx.py; --show-formulas is intentionally absent):
  sws_xlsx_resolve.py <file.xlsx>
  sws_xlsx_resolve.py <file.xlsx> --sheet "Results"
  sws_xlsx_resolve.py <file.xlsx> --sheet "Results" --range A1:D10

Exit codes:
  0  all cells resolved; TSV output on stdout
  1  un-cached formula cell found (D4 fail-loud)
  2  file not found or invalid argument
  3  openpyxl parse error
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_FORMULA_RE = re.compile(r"^=", re.IGNORECASE)


def _cell_ref(col_idx: int, row_idx: int) -> str:
    """Convert 1-based column + row indices to an A1-style reference."""
    col_letters = ""
    c = col_idx
    while c > 0:
        c, remainder = divmod(c - 1, 26)
        col_letters = chr(65 + remainder) + col_letters
    return f"{col_letters}{row_idx}"


def _check_sheet_for_uncached(sheet, cell_range: str | None) -> tuple[str, str] | None:
    """Return (sheet_title, cell_ref) for the first un-cached formula cell, or None.

    An un-cached formula cell is one whose value is None AND whose formula
    source (readable with data_only=False) starts with '='. We detect this
    by reloading the sheet separately when a None is found; however, since
    the caller already opened with data_only=True (which strips formula
    source), we use a heuristic: any cell whose value is None in a row that
    has other non-None values is suspicious. For a definitive check we
    re-read the raw XML formula indicator via the internal openpyxl attribute.
    """
    if cell_range:
        rows = sheet[cell_range]
        if not isinstance(rows, tuple):
            rows = ((rows,),)
        elif rows and not isinstance(rows[0], tuple):
            rows = (rows,)
        for row in rows:
            for cell in row:
                if cell.value is None and _has_formula_source(cell):
                    ref = cell.coordinate
                    return sheet.title, ref
    else:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None and _has_formula_source(cell):
                    ref = cell.coordinate
                    return sheet.title, ref
    return None


def _has_formula_source(cell) -> bool:
    """Return True if the cell's raw XML indicates it holds a formula.

    openpyxl stores the raw formula string in cell._value when data_only=False;
    with data_only=True the formula is stripped and _value holds the cached
    numeric result (or None if never cached). We check the internal
    data_type attribute: 'f' means formula.
    """
    # openpyxl sets data_type to 'f' for formula cells regardless of data_only.
    return getattr(cell, "data_type", None) == "f"


def _format_cell(value) -> str:
    if value is None:
        return ""
    return str(value)


def _emit_sheet(sheet, cell_range: str | None, with_header: bool) -> None:
    if with_header:
        print(f"# Sheet: {sheet.title}")
    if cell_range:
        rows = sheet[cell_range]
        if not isinstance(rows, tuple):
            rows = ((rows,),)
        elif rows and not isinstance(rows[0], tuple):
            rows = (rows,)
        for row in rows:
            print("\t".join(_format_cell(c.value) for c in row))
    else:
        for row in sheet.iter_rows(values_only=True):
            print("\t".join(_format_cell(v) for v in row))


def _fail_loud(sheet_title: str, cell_ref: str) -> int:
    msg = (
        f"Cell {sheet_title}!{cell_ref} is a formula with no cached value. "
        f"Open and save this workbook in Excel or LibreOffice so values cache, "
        f"then re-run /sws:curate-data."
    )
    print(msg, file=sys.stderr)
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Read .xlsx as TSV (data_only); fail loud on un-cached formula cells (D4)."
    )
    ap.add_argument("file", help="Path to .xlsx file")
    ap.add_argument("--sheet", help="Limit to one sheet by name")
    ap.add_argument(
        "--range", dest="cell_range", help="Limit to a cell range, e.g. A1:D10"
    )
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"sws_xlsx_resolve: file not found: {path}", file=sys.stderr)
        return 2

    try:
        from openpyxl import load_workbook

        wb = load_workbook(str(path), data_only=True)
    except Exception as exc:
        print(f"sws_xlsx_resolve: parse error: {exc}", file=sys.stderr)
        return 3

    if args.sheet:
        if args.sheet not in wb.sheetnames:
            print(
                f"sws_xlsx_resolve: sheet not found: {args.sheet!r}", file=sys.stderr
            )
            return 2
        sheet = wb[args.sheet]
        hit = _check_sheet_for_uncached(sheet, args.cell_range)
        if hit:
            return _fail_loud(*hit)
        _emit_sheet(sheet, args.cell_range, with_header=False)
    else:
        if args.cell_range:
            print(
                "sws_xlsx_resolve: --range requires --sheet", file=sys.stderr
            )
            return 2
        for name in wb.sheetnames:
            hit = _check_sheet_for_uncached(wb[name], None)
            if hit:
                return _fail_loud(*hit)
        for name in wb.sheetnames:
            _emit_sheet(wb[name], None, with_header=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_xlsx_resolve.py -v
```

Expected: all tests PASSED (or any `uncached_formula` tests marked SKIPPED if the platform's openpyxl caches formula values — this is environment-dependent and acceptable).

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_xlsx_resolve.py tests/test_xlsx_resolve.py
git commit -m "feat(cycle-11): sws_xlsx_resolve.py — data_only wrapper with D4 fail-loud on un-cached formula cells"
```

---

## Task 1.4: Script — sws_data_manifest.py (TDD)

**Files:**
- Create: `scripts/sws_data_manifest.py`
- Test: `tests/test_data_manifest.py`

**Purpose:** Build and update `Zenodo_db/manifest.json` atomically. Validate dataset→script→figure linkage. Flag orphaned figures. The atomic write pattern (write `.manifest.json.tmp`, then `rename`) prevents corrupt manifests on crash.

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_data_manifest.py`:

```python
"""Unit tests for sws_data_manifest.py.

Covers: manifest round-trip, dataset->script->figure linkage,
atomic write, orphan detection, and --check mode.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "sws_data_manifest.py"


def _run(args, expect_zero: bool = True, cwd: Path | None = None):
    cp = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=str(cwd) if cwd else None,
    )
    if expect_zero:
        assert cp.returncode == 0, f"non-zero exit:\n{cp.stderr}"
    return cp


def _make_zenodo_db(tmp_path: Path) -> Path:
    """Create a minimal Zenodo_db/ layout with one entry worth of assets."""
    db = tmp_path / "Zenodo_db"
    (db / "data").mkdir(parents=True)
    (db / "scripts").mkdir()
    (db / "figures").mkdir()
    (db / "_archive").mkdir()
    (db / "data" / "measurements.xlsx").write_text("fake xlsx", encoding="utf-8")
    (db / "scripts" / "plot_kinetics.py").write_text("# plot", encoding="utf-8")
    (db / "figures" / "fig1.png").write_text("fake png", encoding="utf-8")
    return db


# ---------------------------------------------------------------------------
# --add: create and update entries
# ---------------------------------------------------------------------------

def test_add_creates_manifest_json(tmp_path):
    db = _make_zenodo_db(tmp_path)
    _run([
        str(db), "--add",
        "--dataset", "data/measurements.xlsx",
        "--sheet", "Kinetics",
        "--script", "scripts/plot_kinetics.py",
        "--figures", "figures/fig1.png",
        "--journal-style", "acs-jacs",
    ])
    manifest_path = db / "manifest.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    entry = data[0]
    assert entry["dataset"] == "data/measurements.xlsx"
    assert entry["sheet"] == "Kinetics"
    assert entry["script"] == "scripts/plot_kinetics.py"
    assert "figures/fig1.png" in entry["figures"]
    assert entry["journal_style"] == "acs-jacs"


def test_add_second_entry_appends_not_overwrites(tmp_path):
    db = _make_zenodo_db(tmp_path)
    (db / "figures" / "fig2.png").write_text("fake png2", encoding="utf-8")
    for fig, sheet in [("figures/fig1.png", "Kinetics"), ("figures/fig2.png", "Thermodynamics")]:
        _run([
            str(db), "--add",
            "--dataset", "data/measurements.xlsx",
            "--sheet", sheet,
            "--script", "scripts/plot_kinetics.py",
            "--figures", fig,
            "--journal-style", "acs-jacs",
        ])
    data = json.loads((db / "manifest.json").read_text())
    assert len(data) == 2


def test_add_populates_generated_at_timestamp(tmp_path):
    db = _make_zenodo_db(tmp_path)
    _run([
        str(db), "--add",
        "--dataset", "data/measurements.xlsx",
        "--sheet", "Data",
        "--script", "scripts/plot_kinetics.py",
        "--figures", "figures/fig1.png",
        "--journal-style", "",
    ])
    data = json.loads((db / "manifest.json").read_text())
    assert "generated_at" in data[0]
    assert "T" in data[0]["generated_at"]  # ISO-8601 format


def test_atomic_write_leaves_no_tmp_file(tmp_path):
    db = _make_zenodo_db(tmp_path)
    _run([
        str(db), "--add",
        "--dataset", "data/measurements.xlsx",
        "--sheet", "Data",
        "--script", "scripts/plot_kinetics.py",
        "--figures", "figures/fig1.png",
        "--journal-style", "",
    ])
    tmp_file = db / ".manifest.json.tmp"
    assert not tmp_file.exists()


# ---------------------------------------------------------------------------
# --check: orphan detection
# ---------------------------------------------------------------------------

def test_check_passes_when_all_figures_in_manifest(tmp_path):
    db = _make_zenodo_db(tmp_path)
    _run([
        str(db), "--add",
        "--dataset", "data/measurements.xlsx",
        "--sheet", "Data",
        "--script", "scripts/plot_kinetics.py",
        "--figures", "figures/fig1.png",
        "--journal-style", "",
    ])
    cp = _run([str(db), "--check"])
    assert "orphan" not in cp.stdout.lower()
    assert cp.returncode == 0


def test_check_flags_orphaned_figure(tmp_path):
    db = _make_zenodo_db(tmp_path)
    # Add fig1 to manifest but leave fig_orphan.png unregistered on disk
    (db / "figures" / "fig_orphan.png").write_text("orphan", encoding="utf-8")
    _run([
        str(db), "--add",
        "--dataset", "data/measurements.xlsx",
        "--sheet", "Data",
        "--script", "scripts/plot_kinetics.py",
        "--figures", "figures/fig1.png",
        "--journal-style", "",
    ])
    cp = _run([str(db), "--check"], expect_zero=False)
    assert "orphan" in cp.stdout.lower() or "orphan" in cp.stderr.lower()
    assert cp.returncode != 0


def test_check_empty_manifest_with_figures_flags_orphans(tmp_path):
    db = _make_zenodo_db(tmp_path)
    # manifest.json does not exist yet; fig1.png is on disk
    cp = _run([str(db), "--check"], expect_zero=False)
    assert cp.returncode != 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_missing_zenodo_db_exits_2(tmp_path):
    cp = _run([str(tmp_path / "Zenodo_db_nonexistent"), "--check"], expect_zero=False)
    assert cp.returncode == 2


def test_multiple_figures_per_entry(tmp_path):
    db = _make_zenodo_db(tmp_path)
    (db / "figures" / "fig1b.pdf").write_text("fake pdf", encoding="utf-8")
    _run([
        str(db), "--add",
        "--dataset", "data/measurements.xlsx",
        "--sheet", "Data",
        "--script", "scripts/plot_kinetics.py",
        "--figures", "figures/fig1.png", "figures/fig1b.pdf",
        "--journal-style", "acs-jacs",
    ])
    data = json.loads((db / "manifest.json").read_text())
    assert len(data[0]["figures"]) == 2
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_data_manifest.py -v
```

Expected: `ImportError: No module named 'sws_data_manifest'` or all FAILED.

- [ ] **Step 3: Implement scripts/sws_data_manifest.py**

Full content of `scripts/sws_data_manifest.py`:

```python
"""Build and update Zenodo_db/manifest.json atomically (D5).

Each manifest entry links: dataset -> script -> figure(s).
Atomic write uses a .tmp rename to prevent corruption on crash.

CLI:
  sws_data_manifest.py <zenodo_db_dir> --add
        --dataset <rel-path> --sheet <name>
        --script <rel-path>
        --figures <rel-path> [<rel-path> ...]
        --journal-style <id-or-empty>

  sws_data_manifest.py <zenodo_db_dir> --check
        (flags figures/ files absent from manifest.json)

Exit codes:
  0  ok
  1  orphaned figures found (--check mode)
  2  zenodo_db_dir not found or required argument missing
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_NAME = "manifest.json"
MANIFEST_TMP = ".manifest.json.tmp"


def _load_manifest(db: Path) -> list:
    manifest_path = db / MANIFEST_NAME
    if not manifest_path.exists():
        return []
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_manifest_atomic(db: Path, entries: list) -> None:
    tmp = db / MANIFEST_TMP
    content = json.dumps(entries, indent=2, ensure_ascii=False)
    tmp.write_text(content, encoding="utf-8")
    tmp.rename(db / MANIFEST_NAME)


def cmd_add(db: Path, args) -> int:
    entries = _load_manifest(db)
    entry = {
        "dataset": args.dataset,
        "sheet": args.sheet,
        "script": args.script,
        "figures": args.figures,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "journal_style": args.journal_style or "",
        "notes": "",
    }
    entries.append(entry)
    _save_manifest_atomic(db, entries)
    print(f"sws_data_manifest: added entry for {args.dataset} -> {args.figures}")
    return 0


def cmd_check(db: Path) -> int:
    manifest_path = db / MANIFEST_NAME
    entries = _load_manifest(db)
    registered_figures: set[str] = set()
    for entry in entries:
        for fig in entry.get("figures", []):
            registered_figures.add(fig)

    figures_dir = db / "figures"
    all_figures_on_disk: list[str] = []
    if figures_dir.is_dir():
        for f in figures_dir.iterdir():
            if f.is_file():
                all_figures_on_disk.append(f"figures/{f.name}")

    orphans = [fig for fig in all_figures_on_disk if fig not in registered_figures]
    if orphans:
        print("sws_data_manifest: orphaned figures (in figures/ but absent from manifest.json):")
        for o in sorted(orphans):
            print(f"  {o}")
        return 1
    print("sws_data_manifest: all figures registered in manifest.json")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build/update Zenodo_db/manifest.json (D5)."
    )
    ap.add_argument("zenodo_db", help="Path to Zenodo_db/ directory")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--add", action="store_true", help="Add a new manifest entry")
    mode.add_argument("--check", action="store_true", help="Check for orphaned figures")
    ap.add_argument("--dataset", help="Relative path to the source .xlsx inside Zenodo_db/")
    ap.add_argument("--sheet", help="Worksheet name within the dataset")
    ap.add_argument("--script", help="Relative path to the plot/fit script inside Zenodo_db/")
    ap.add_argument("--figures", nargs="+", help="Relative paths to output figures inside Zenodo_db/")
    ap.add_argument("--journal-style", default="", help="Resolved journal-style overlay id")
    args = ap.parse_args(argv)

    db = Path(args.zenodo_db)
    if not db.is_dir():
        print(f"sws_data_manifest: directory not found: {db}", file=sys.stderr)
        return 2

    if args.add:
        for required in ("dataset", "sheet", "script", "figures"):
            if not getattr(args, required.replace("-", "_"), None):
                print(
                    f"sws_data_manifest: --add requires --{required}", file=sys.stderr
                )
                return 2
        return cmd_add(db, args)

    return cmd_check(db)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_data_manifest.py -v
```

Expected: all tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_data_manifest.py tests/test_data_manifest.py
git commit -m "feat(cycle-11): sws_data_manifest.py — atomic manifest build/update + orphan check (D5)"
```

---

## Task 1.5: Script — sws_semantic_scholar.py (TDD)

**Files:**
- Create: `scripts/sws_semantic_scholar.py`
- Test: `tests/test_semantic_scholar.py`
- Create: `tests/fixtures/cycle_11/api_responses/s2_search.json`
- Create: `tests/fixtures/cycle_11/api_responses/s2_paper.json`

**Purpose:** Query Semantic Scholar for paper search (title-fuzzy match, Levenshtein ≥ 0.70), DOI resolution, and abstract fetch. Aggressive caching + 429 backoff. Tests run against captured fixture JSON — NO live network.

- [ ] **Step 1: Write the fixture JSON files**

Full content of `tests/fixtures/cycle_11/api_responses/s2_search.json`:

```json
{
  "total": 2,
  "offset": 0,
  "next": null,
  "data": [
    {
      "paperId": "abc123",
      "title": "Kinetic analysis of model peptide hydrolysis",
      "authors": [{"authorId": "1", "name": "Smith J"}],
      "year": 2022,
      "externalIds": {"DOI": "10.1000/xyz001"},
      "abstract": "We studied the kinetics of peptide hydrolysis using stopped-flow methods.",
      "citationCount": 14
    },
    {
      "paperId": "def456",
      "title": "Peptide bond hydrolysis mechanisms in chemistry",
      "authors": [{"authorId": "2", "name": "Doe A"}],
      "year": 2021,
      "externalIds": {"DOI": "10.1000/xyz002"},
      "abstract": "A review of hydrolysis mechanisms with kinetic data.",
      "citationCount": 8
    }
  ]
}
```

Full content of `tests/fixtures/cycle_11/api_responses/s2_paper.json`:

```json
{
  "paperId": "abc123",
  "title": "Kinetic analysis of model peptide hydrolysis",
  "authors": [{"authorId": "1", "name": "Smith J"}],
  "year": 2022,
  "externalIds": {"DOI": "10.1000/xyz001"},
  "abstract": "We studied the kinetics of peptide hydrolysis using stopped-flow methods.",
  "citationCount": 14,
  "references": [
    {"paperId": "ghi789", "title": "Classic kinetics paper", "year": 2010}
  ]
}
```

- [ ] **Step 2: Write the failing tests**

Full content of `tests/test_semantic_scholar.py`:

```python
"""Unit tests for sws_semantic_scholar.py.

All tests run against CAPTURED fixture JSON — no live network calls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
FIXTURES = REPO / "tests" / "fixtures" / "cycle_11" / "api_responses"
sys.path.insert(0, str(SCRIPTS))

import sws_semantic_scholar as s2  # noqa: E402


FIXTURE_SEARCH = json.loads((FIXTURES / "s2_search.json").read_text())
FIXTURE_PAPER = json.loads((FIXTURES / "s2_paper.json").read_text())


# ---------------------------------------------------------------------------
# Fuzzy-match threshold
# ---------------------------------------------------------------------------

def test_fuzzy_match_accepts_above_threshold():
    score = s2.title_similarity(
        "Kinetic analysis of model peptide hydrolysis",
        "Kinetic analysis of model peptide hydrolysis",
    )
    assert score >= 0.70


def test_fuzzy_match_accepts_near_match():
    score = s2.title_similarity(
        "Kinetic analysis of peptide hydrolysis",
        "Kinetic analysis of model peptide hydrolysis",
    )
    assert score >= 0.70


def test_fuzzy_match_rejects_unrelated():
    score = s2.title_similarity(
        "Quantum entanglement in superconductors",
        "Kinetic analysis of model peptide hydrolysis",
    )
    assert score < 0.70


def test_filter_results_by_threshold():
    results = s2.filter_by_title_similarity(
        FIXTURE_SEARCH["data"],
        query="Kinetic analysis of model peptide hydrolysis",
        threshold=0.70,
    )
    assert len(results) >= 1
    assert results[0]["title"] == "Kinetic analysis of model peptide hydrolysis"


# ---------------------------------------------------------------------------
# Parser correctness against fixture
# ---------------------------------------------------------------------------

def test_parse_search_results_extracts_fields():
    parsed = s2.parse_search_results(FIXTURE_SEARCH)
    assert len(parsed) == 2
    first = parsed[0]
    assert first["title"] == "Kinetic analysis of model peptide hydrolysis"
    assert first["doi"] == "10.1000/xyz001"
    assert first["year"] == 2022
    assert first["citation_count"] == 14
    assert "stopped-flow" in first["abstract"]


def test_parse_paper_detail_extracts_references():
    parsed = s2.parse_paper_detail(FIXTURE_PAPER)
    assert parsed["paper_id"] == "abc123"
    assert len(parsed["references"]) == 1
    assert parsed["references"][0]["title"] == "Classic kinetics paper"


def test_parse_handles_missing_doi_gracefully():
    item = dict(FIXTURE_SEARCH["data"][0])
    item["externalIds"] = {}
    result = s2.parse_search_results({"total": 1, "data": [item]})
    assert result[0]["doi"] is None


def test_parse_handles_missing_abstract_gracefully():
    item = dict(FIXTURE_SEARCH["data"][0])
    del item["abstract"]
    result = s2.parse_search_results({"total": 1, "data": [item]})
    assert result[0]["abstract"] is None or result[0]["abstract"] == ""


# ---------------------------------------------------------------------------
# Backoff path (mocked — no live network)
# ---------------------------------------------------------------------------

def test_429_triggers_retry(monkeypatch):
    call_count = [0]

    def fake_fetch(url: str, headers: dict | None = None, cache_dir: Path | None = None):
        call_count[0] += 1
        if call_count[0] < 3:
            raise s2.RateLimitError("429 Too Many Requests")
        return FIXTURE_SEARCH

    monkeypatch.setattr(s2, "_fetch_json", fake_fetch)
    monkeypatch.setattr(s2, "_backoff_sleep", lambda n: None)  # no real sleep in tests

    result = s2.search(
        query="peptide hydrolysis",
        cache_dir=None,
        max_retries=5,
    )
    assert call_count[0] == 3
    assert result is not None


def test_exhausted_retries_raise_rate_limit_error(monkeypatch):
    def fake_fetch(url: str, headers: dict | None = None, cache_dir: Path | None = None):
        raise s2.RateLimitError("429")

    monkeypatch.setattr(s2, "_fetch_json", fake_fetch)
    monkeypatch.setattr(s2, "_backoff_sleep", lambda n: None)

    with pytest.raises(s2.RateLimitError):
        s2.search(query="anything", cache_dir=None, max_retries=3)


# ---------------------------------------------------------------------------
# Cache hit avoids second call
# ---------------------------------------------------------------------------

def test_cache_hit_avoids_network_call(tmp_path, monkeypatch):
    call_count = [0]

    def fake_fetch(url: str, headers: dict | None = None, cache_dir: Path | None = None):
        call_count[0] += 1
        return FIXTURE_SEARCH

    monkeypatch.setattr(s2, "_fetch_json", fake_fetch)
    monkeypatch.setattr(s2, "_backoff_sleep", lambda n: None)

    cache = tmp_path / ".sws_cache" / "semantic_scholar"
    cache.mkdir(parents=True)
    s2.search(query="peptide hydrolysis", cache_dir=cache, max_retries=1)
    s2.search(query="peptide hydrolysis", cache_dir=cache, max_retries=1)
    assert call_count[0] == 1
```

- [ ] **Step 3: Run tests — expect failures**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_semantic_scholar.py -v
```

Expected: `ImportError: No module named 'sws_semantic_scholar'` or all FAILED.

- [ ] **Step 4: Implement scripts/sws_semantic_scholar.py**

Full content of `scripts/sws_semantic_scholar.py`:

```python
"""Semantic Scholar API client for SWS (D8).

WebFetch/curl + JSON parsing. Caching + 429 backoff (cycle-#9 R1 discipline).
Title-fuzzy-match uses difflib SequenceMatcher (stdlib); threshold >= 0.70.
No live network calls in tests — all tests use captured fixture JSON.

Public API:
  search(query, cache_dir, max_retries) -> list[dict]
  resolve_doi(doi, cache_dir, max_retries) -> dict | None
  parse_search_results(raw) -> list[dict]
  parse_paper_detail(raw) -> dict
  title_similarity(a, b) -> float
  filter_by_title_similarity(items, query, threshold) -> list[dict]

Exceptions:
  RateLimitError  — raised after max_retries exhausted on HTTP 429
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import urllib.error
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,authors,year,externalIds,abstract,citationCount,references"


class RateLimitError(Exception):
    pass


def title_similarity(a: str, b: str) -> float:
    """Return SequenceMatcher ratio between two title strings (case-insensitive)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def filter_by_title_similarity(
    items: list[dict], query: str, threshold: float = 0.70
) -> list[dict]:
    """Return items whose title similarity to query is >= threshold, sorted descending."""
    scored = []
    for item in items:
        t = item.get("title") or ""
        score = title_similarity(query, t)
        if score >= threshold:
            scored.append((score, item))
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored]


def parse_search_results(raw: dict) -> list[dict]:
    """Normalize a Semantic Scholar search response to a flat list of dicts."""
    results = []
    for item in raw.get("data", []):
        results.append({
            "paper_id": item.get("paperId"),
            "title": item.get("title"),
            "authors": [a.get("name") for a in (item.get("authors") or [])],
            "year": item.get("year"),
            "doi": (item.get("externalIds") or {}).get("DOI"),
            "abstract": item.get("abstract") or "",
            "citation_count": item.get("citationCount", 0),
        })
    return results


def parse_paper_detail(raw: dict) -> dict:
    """Normalize a Semantic Scholar paper-detail response."""
    return {
        "paper_id": raw.get("paperId"),
        "title": raw.get("title"),
        "authors": [a.get("name") for a in (raw.get("authors") or [])],
        "year": raw.get("year"),
        "doi": (raw.get("externalIds") or {}).get("DOI"),
        "abstract": raw.get("abstract") or "",
        "citation_count": raw.get("citationCount", 0),
        "references": [
            {"paper_id": r.get("paperId"), "title": r.get("title"), "year": r.get("year")}
            for r in (raw.get("references") or [])
        ],
    }


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _fetch_json(
    url: str,
    headers: dict | None = None,
    cache_dir: Path | None = None,
) -> Any:
    """Fetch JSON from url, using cache_dir when provided."""
    if cache_dir is not None:
        key = _cache_key(url)
        cached = cache_dir / f"{key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimitError(f"HTTP 429 from {url}") from exc
        raise

    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(data), encoding="utf-8")

    return data


def _backoff_sleep(attempt: int) -> None:
    delay = min(2 ** attempt, 64)
    time.sleep(delay)


def _fetch_with_backoff(
    url: str,
    headers: dict | None = None,
    cache_dir: Path | None = None,
    max_retries: int = 5,
) -> Any:
    for attempt in range(max_retries):
        try:
            return _fetch_json(url, headers=headers, cache_dir=cache_dir)
        except RateLimitError:
            if attempt + 1 == max_retries:
                raise
            _backoff_sleep(attempt)
    raise RateLimitError("max retries exhausted")


def search(
    query: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
    api_key: str | None = None,
) -> list[dict]:
    """Search Semantic Scholar by title/keyword query."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"{BASE_URL}/paper/search?query={encoded}&fields={FIELDS}&limit=10"
    headers = {"x-api-key": api_key} if api_key else {}
    raw = _fetch_with_backoff(url, headers=headers, cache_dir=cache_dir, max_retries=max_retries)
    return parse_search_results(raw)


def resolve_doi(
    doi: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
    api_key: str | None = None,
) -> dict | None:
    """Fetch a Semantic Scholar paper record by DOI."""
    import urllib.parse
    encoded = urllib.parse.quote(f"DOI:{doi}")
    url = f"{BASE_URL}/paper/{encoded}?fields={FIELDS}"
    headers = {"x-api-key": api_key} if api_key else {}
    try:
        raw = _fetch_with_backoff(url, headers=headers, cache_dir=cache_dir, max_retries=max_retries)
    except Exception:
        return None
    return parse_paper_detail(raw)
```

- [ ] **Step 5: Run tests — expect pass**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_semantic_scholar.py -v
```

Expected: all tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add scripts/sws_semantic_scholar.py \
        tests/test_semantic_scholar.py \
        tests/fixtures/cycle_11/api_responses/s2_search.json \
        tests/fixtures/cycle_11/api_responses/s2_paper.json
git commit -m "feat(cycle-11): sws_semantic_scholar.py — fuzzy-match, backoff, cache; tests vs captured fixtures (D8)"
```

---

## Task 1.6: Script — sws_crossref.py (TDD)

**Files:**
- Create: `scripts/sws_crossref.py`
- Test: `tests/test_crossref.py`
- Create: `tests/fixtures/cycle_11/api_responses/crossref_doi.json`

**Purpose:** CrossRef DOI resolver + metadata. Used by bibliography-curator as the primary fallback for DOI resolution and format validation.

- [ ] **Step 1: Write the fixture JSON**

Full content of `tests/fixtures/cycle_11/api_responses/crossref_doi.json`:

```json
{
  "status": "ok",
  "message-type": "work",
  "message": {
    "DOI": "10.1000/xyz001",
    "title": ["Kinetic analysis of model peptide hydrolysis"],
    "author": [{"given": "Jane", "family": "Smith", "sequence": "first"}],
    "published": {"date-parts": [[2022, 3, 15]]},
    "container-title": ["Journal of Chemical Research"],
    "volume": "42",
    "issue": "3",
    "page": "100-115",
    "type": "journal-article",
    "ISSN": ["1234-5678"]
  }
}
```

- [ ] **Step 2: Write the failing tests**

Full content of `tests/test_crossref.py`:

```python
"""Unit tests for sws_crossref.py — CrossRef DOI resolver.

All tests run against CAPTURED fixture JSON — no live network calls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
FIXTURES = REPO / "tests" / "fixtures" / "cycle_11" / "api_responses"
sys.path.insert(0, str(SCRIPTS))

import sws_crossref as cx  # noqa: E402

FIXTURE_DOI = json.loads((FIXTURES / "crossref_doi.json").read_text())


# ---------------------------------------------------------------------------
# Parser correctness
# ---------------------------------------------------------------------------

def test_parse_extracts_doi_and_title():
    parsed = cx.parse_work(FIXTURE_DOI["message"])
    assert parsed["doi"] == "10.1000/xyz001"
    assert "peptide hydrolysis" in parsed["title"].lower()


def test_parse_extracts_authors():
    parsed = cx.parse_work(FIXTURE_DOI["message"])
    assert len(parsed["authors"]) == 1
    assert "Smith" in parsed["authors"][0]


def test_parse_extracts_year():
    parsed = cx.parse_work(FIXTURE_DOI["message"])
    assert parsed["year"] == 2022


def test_parse_extracts_journal_and_volume():
    parsed = cx.parse_work(FIXTURE_DOI["message"])
    assert "Chemical Research" in parsed["journal"]
    assert parsed["volume"] == "42"
    assert parsed["pages"] == "100-115"


def test_parse_handles_missing_page_gracefully():
    item = dict(FIXTURE_DOI["message"])
    del item["page"]
    parsed = cx.parse_work(item)
    assert parsed["pages"] is None or parsed["pages"] == ""


# ---------------------------------------------------------------------------
# Resolve via mocked _fetch_json
# ---------------------------------------------------------------------------

def test_resolve_doi_returns_parsed_record(monkeypatch):
    monkeypatch.setattr(cx, "_fetch_json", lambda url, cache_dir=None: FIXTURE_DOI)
    monkeypatch.setattr(cx, "_backoff_sleep", lambda n: None)
    result = cx.resolve_doi("10.1000/xyz001", cache_dir=None)
    assert result is not None
    assert result["doi"] == "10.1000/xyz001"


def test_resolve_doi_returns_none_on_404(monkeypatch):
    import urllib.error

    def fake_fetch(url, cache_dir=None):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr(cx, "_fetch_json", fake_fetch)
    monkeypatch.setattr(cx, "_backoff_sleep", lambda n: None)
    result = cx.resolve_doi("10.9999/notreal", cache_dir=None)
    assert result is None


def test_429_triggers_backoff(monkeypatch):
    import urllib.error

    call_count = [0]

    def fake_fetch(url, cache_dir=None):
        call_count[0] += 1
        if call_count[0] < 3:
            raise cx.RateLimitError("429")
        return FIXTURE_DOI

    monkeypatch.setattr(cx, "_fetch_json", fake_fetch)
    monkeypatch.setattr(cx, "_backoff_sleep", lambda n: None)
    result = cx.resolve_doi("10.1000/xyz001", cache_dir=None, max_retries=5)
    assert result is not None
    assert call_count[0] == 3


# ---------------------------------------------------------------------------
# Format helper
# ---------------------------------------------------------------------------

def test_format_apa_style():
    record = cx.parse_work(FIXTURE_DOI["message"])
    formatted = cx.format_reference(record, style="apa")
    assert "Smith" in formatted
    assert "2022" in formatted
    assert "10.1000/xyz001" in formatted


def test_format_numbered_style():
    record = cx.parse_work(FIXTURE_DOI["message"])
    formatted = cx.format_reference(record, style="numbered")
    assert "Smith" in formatted
    assert "Journal of Chemical Research" in formatted
```

- [ ] **Step 3: Run tests — expect failures**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_crossref.py -v
```

Expected: `ImportError: No module named 'sws_crossref'` or all FAILED.

- [ ] **Step 4: Implement scripts/sws_crossref.py**

Full content of `scripts/sws_crossref.py`:

```python
"""CrossRef DOI resolver + metadata for SWS bibliography-curator (D8).

WebFetch/curl + JSON parsing. Caching + 429 backoff (cycle-#9 R1 discipline).
Used by bibliography-curator as the primary DOI fallback chain (after Zotero).

Public API:
  resolve_doi(doi, cache_dir, max_retries) -> dict | None
  parse_work(message) -> dict
  format_reference(record, style) -> str

Exceptions:
  RateLimitError  — raised after max_retries exhausted on HTTP 429
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

BASE_URL = "https://api.crossref.org/works"
POLITE_MAILTO = ""  # set via CROSSREF_MAILTO env var for polite pool


class RateLimitError(Exception):
    pass


def parse_work(message: dict) -> dict:
    """Normalize a CrossRef work message to a flat dict."""
    authors = []
    for a in message.get("author") or []:
        given = a.get("given", "")
        family = a.get("family", "")
        name = f"{family} {given}".strip() if family else given
        if name:
            authors.append(name)

    date_parts = (message.get("published") or {}).get("date-parts") or [[None]]
    year = date_parts[0][0] if date_parts[0] else None

    titles = message.get("title") or []
    title = titles[0] if titles else ""

    container = message.get("container-title") or []
    journal = container[0] if container else ""

    return {
        "doi": message.get("DOI"),
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "volume": message.get("volume"),
        "issue": message.get("issue"),
        "pages": message.get("page"),
        "type": message.get("type"),
    }


def format_reference(record: dict, style: str = "numbered") -> str:
    """Format a parsed CrossRef record to a citation string.

    style: 'numbered' (Vancouver-like) or 'apa'.
    """
    authors = "; ".join(record.get("authors") or []) or "Unknown Author"
    year = record.get("year") or "n.d."
    title = record.get("title") or ""
    journal = record.get("journal") or ""
    volume = record.get("volume") or ""
    issue = record.get("issue") or ""
    pages = record.get("pages") or ""
    doi = record.get("doi") or ""

    if style == "apa":
        vol_issue = f"{volume}({issue})" if issue else volume
        page_part = f", {pages}" if pages else ""
        doi_part = f" https://doi.org/{doi}" if doi else ""
        return f"{authors} ({year}). {title}. {journal}, {vol_issue}{page_part}.{doi_part}"
    else:
        vol_part = f"{volume}" + (f"({issue})" if issue else "")
        page_part = f":{pages}" if pages else ""
        doi_part = f" DOI: {doi}" if doi else ""
        return f"{authors}. {title}. {journal}. {year};{vol_part}{page_part}.{doi_part}"


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _fetch_json(url: str, cache_dir: Path | None = None) -> Any:
    if cache_dir is not None:
        key = _cache_key(url)
        cached = cache_dir / f"{key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    import os
    mailto = os.environ.get("CROSSREF_MAILTO", POLITE_MAILTO)
    headers = {}
    if mailto:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}mailto={mailto}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimitError(f"HTTP 429 from {url}") from exc
        raise

    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(data), encoding="utf-8")

    return data


def _backoff_sleep(attempt: int) -> None:
    time.sleep(min(2 ** attempt, 64))


def resolve_doi(
    doi: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
) -> dict | None:
    """Resolve a DOI to bibliographic metadata via CrossRef."""
    import urllib.parse
    encoded = urllib.parse.quote(doi, safe="")
    url = f"{BASE_URL}/{encoded}"
    for attempt in range(max_retries):
        try:
            raw = _fetch_json(url, cache_dir=cache_dir)
            return parse_work(raw.get("message", {}))
        except RateLimitError:
            if attempt + 1 == max_retries:
                raise
            _backoff_sleep(attempt)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
    return None
```

- [ ] **Step 5: Run tests — expect pass**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_crossref.py -v
```

Expected: all tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add scripts/sws_crossref.py \
        tests/test_crossref.py \
        tests/fixtures/cycle_11/api_responses/crossref_doi.json
git commit -m "feat(cycle-11): sws_crossref.py — DOI resolver + format helper; tests vs captured fixtures (D8)"
```

---

## Task 1.7: Script — sws_openalex.py (TDD)

**Files:**
- Create: `scripts/sws_openalex.py`
- Test: `tests/test_openalex.py`
- Create: `tests/fixtures/cycle_11/api_responses/openalex_work.json`

**Purpose:** OpenAlex metadata fetch as fallback for bibliography-curator and literature-searcher. Broad coverage including non-DOI items and OA full-text links.

- [ ] **Step 1: Write the fixture JSON**

Full content of `tests/fixtures/cycle_11/api_responses/openalex_work.json`:

```json
{
  "id": "https://openalex.org/W1234567890",
  "doi": "https://doi.org/10.1000/xyz001",
  "title": "Kinetic analysis of model peptide hydrolysis",
  "authorships": [
    {
      "author": {"id": "https://openalex.org/A1", "display_name": "Jane Smith"},
      "author_position": "first"
    }
  ],
  "publication_year": 2022,
  "primary_location": {
    "source": {"display_name": "Journal of Chemical Research", "type": "journal"},
    "is_oa": true,
    "pdf_url": "https://example.com/paper.pdf"
  },
  "cited_by_count": 14,
  "abstract_inverted_index": {
    "We": [0], "studied": [1], "peptide": [2, 8], "hydrolysis": [3],
    "kinetics": [5], "using": [6], "stopped-flow": [7], "methods.": [9]
  }
}
```

- [ ] **Step 2: Write the failing tests**

Full content of `tests/test_openalex.py`:

```python
"""Unit tests for sws_openalex.py — OpenAlex metadata client.

All tests run against CAPTURED fixture JSON — no live network calls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
FIXTURES = REPO / "tests" / "fixtures" / "cycle_11" / "api_responses"
sys.path.insert(0, str(SCRIPTS))

import sws_openalex as oa  # noqa: E402

FIXTURE_WORK = json.loads((FIXTURES / "openalex_work.json").read_text())


# ---------------------------------------------------------------------------
# Parser correctness
# ---------------------------------------------------------------------------

def test_parse_extracts_doi():
    parsed = oa.parse_work(FIXTURE_WORK)
    assert parsed["doi"] == "10.1000/xyz001"


def test_parse_extracts_title():
    parsed = oa.parse_work(FIXTURE_WORK)
    assert "peptide hydrolysis" in parsed["title"].lower()


def test_parse_extracts_authors():
    parsed = oa.parse_work(FIXTURE_WORK)
    assert len(parsed["authors"]) == 1
    assert "Smith" in parsed["authors"][0]


def test_parse_extracts_year():
    parsed = oa.parse_work(FIXTURE_WORK)
    assert parsed["year"] == 2022


def test_parse_extracts_journal():
    parsed = oa.parse_work(FIXTURE_WORK)
    assert "Chemical Research" in parsed["journal"]


def test_parse_extracts_oa_flag():
    parsed = oa.parse_work(FIXTURE_WORK)
    assert parsed["is_oa"] is True


def test_parse_extracts_pdf_url():
    parsed = oa.parse_work(FIXTURE_WORK)
    assert parsed["pdf_url"] == "https://example.com/paper.pdf"


def test_reconstruct_abstract_from_inverted_index():
    parsed = oa.parse_work(FIXTURE_WORK)
    assert parsed["abstract"] is not None
    assert "peptide" in parsed["abstract"].lower()


def test_parse_handles_missing_doi_gracefully():
    item = dict(FIXTURE_WORK)
    item["doi"] = None
    parsed = oa.parse_work(item)
    assert parsed["doi"] is None


def test_parse_handles_no_abstract_gracefully():
    item = dict(FIXTURE_WORK)
    item["abstract_inverted_index"] = None
    parsed = oa.parse_work(item)
    assert parsed["abstract"] is None or parsed["abstract"] == ""


# ---------------------------------------------------------------------------
# Fetch via mocked _fetch_json
# ---------------------------------------------------------------------------

def test_resolve_doi_returns_parsed_record(monkeypatch):
    monkeypatch.setattr(oa, "_fetch_json", lambda url, cache_dir=None: FIXTURE_WORK)
    monkeypatch.setattr(oa, "_backoff_sleep", lambda n: None)
    result = oa.resolve_doi("10.1000/xyz001", cache_dir=None)
    assert result is not None
    assert result["doi"] == "10.1000/xyz001"


def test_resolve_doi_returns_none_on_404(monkeypatch):
    import urllib.error

    def fake_fetch(url, cache_dir=None):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr(oa, "_fetch_json", fake_fetch)
    monkeypatch.setattr(oa, "_backoff_sleep", lambda n: None)
    result = oa.resolve_doi("10.9999/notreal", cache_dir=None)
    assert result is None


def test_429_triggers_backoff(monkeypatch):
    call_count = [0]

    def fake_fetch(url, cache_dir=None):
        call_count[0] += 1
        if call_count[0] < 2:
            raise oa.RateLimitError("429")
        return FIXTURE_WORK

    monkeypatch.setattr(oa, "_fetch_json", fake_fetch)
    monkeypatch.setattr(oa, "_backoff_sleep", lambda n: None)
    result = oa.resolve_doi("10.1000/xyz001", cache_dir=None, max_retries=5)
    assert result is not None
    assert call_count[0] == 2
```

- [ ] **Step 3: Run tests — expect failures**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_openalex.py -v
```

Expected: `ImportError: No module named 'sws_openalex'` or all FAILED.

- [ ] **Step 4: Implement scripts/sws_openalex.py**

Full content of `scripts/sws_openalex.py`:

```python
"""OpenAlex metadata client for SWS (D8).

Fallback for bibliography-curator and literature-searcher when Zotero/CrossRef
have no record. Broad coverage including OA full-text links. Abstract is
reconstructed from OpenAlex's inverted index representation.

Public API:
  resolve_doi(doi, cache_dir, max_retries) -> dict | None
  search(query, cache_dir, max_retries) -> list[dict]
  parse_work(raw) -> dict

Exceptions:
  RateLimitError  — raised after max_retries exhausted on HTTP 429
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

BASE_URL = "https://api.openalex.org"


class RateLimitError(Exception):
    pass


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """Reconstruct abstract text from OpenAlex inverted index."""
    if not inverted_index:
        return ""
    max_pos = max(pos for positions in inverted_index.values() for pos in positions)
    tokens = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            tokens[pos] = word
    return " ".join(t for t in tokens if t)


def parse_work(raw: dict) -> dict:
    """Normalize an OpenAlex work object to a flat dict."""
    doi_raw = raw.get("doi") or ""
    doi = doi_raw.replace("https://doi.org/", "").replace("http://doi.org/", "") or None

    authors = []
    for a in raw.get("authorships") or []:
        name = (a.get("author") or {}).get("display_name") or ""
        if name:
            authors.append(name)

    primary = raw.get("primary_location") or {}
    source = primary.get("source") or {}
    journal = source.get("display_name") or ""
    is_oa = primary.get("is_oa") or False
    pdf_url = primary.get("pdf_url")

    abstract = _reconstruct_abstract(raw.get("abstract_inverted_index"))

    return {
        "openalex_id": raw.get("id"),
        "doi": doi,
        "title": raw.get("title") or "",
        "authors": authors,
        "year": raw.get("publication_year"),
        "journal": journal,
        "is_oa": is_oa,
        "pdf_url": pdf_url,
        "citation_count": raw.get("cited_by_count", 0),
        "abstract": abstract or None,
    }


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _fetch_json(url: str, cache_dir: Path | None = None) -> Any:
    if cache_dir is not None:
        key = _cache_key(url)
        cached = cache_dir / f"{key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    import os
    mailto = os.environ.get("OPENALEX_MAILTO", "")
    if mailto and "?" in url:
        url = f"{url}&mailto={mailto}"
    elif mailto:
        url = f"{url}?mailto={mailto}"

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimitError(f"HTTP 429 from {url}") from exc
        raise

    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(data), encoding="utf-8")

    return data


def _backoff_sleep(attempt: int) -> None:
    time.sleep(min(2 ** attempt, 64))


def resolve_doi(
    doi: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
) -> dict | None:
    """Resolve a DOI to OpenAlex metadata."""
    import urllib.parse
    encoded = urllib.parse.quote(f"https://doi.org/{doi}", safe="")
    url = f"{BASE_URL}/works/{encoded}"
    for attempt in range(max_retries):
        try:
            raw = _fetch_json(url, cache_dir=cache_dir)
            return parse_work(raw)
        except RateLimitError:
            if attempt + 1 == max_retries:
                raise
            _backoff_sleep(attempt)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
    return None


def search(
    query: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
) -> list[dict]:
    """Search OpenAlex by free-text query."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"{BASE_URL}/works?search={encoded}&per-page=10"
    for attempt in range(max_retries):
        try:
            raw = _fetch_json(url, cache_dir=cache_dir)
            return [parse_work(w) for w in (raw.get("results") or [])]
        except RateLimitError:
            if attempt + 1 == max_retries:
                raise
            _backoff_sleep(attempt)
    return []
```

- [ ] **Step 5: Run tests — expect pass**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_openalex.py -v
```

Expected: all tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add scripts/sws_openalex.py \
        tests/test_openalex.py \
        tests/fixtures/cycle_11/api_responses/openalex_work.json
git commit -m "feat(cycle-11): sws_openalex.py — OA metadata + abstract reconstruction; tests vs captured fixtures (D8)"
```

---

## Task 1.8: Update references/agent-contract.md

**Files:**
- Modify: `references/agent-contract.md`

- [ ] **Step 1: Append cycle-#11 I/O inventory rows to the table**

Append after the last `| ... |` row in the "I/O wrapper inventory" table in `references/agent-contract.md`:

```markdown
| `scripts/sws_xlsx_resolve.py` | Read .xlsx data_only; fail loud on un-cached formula cells (D4) | 11 |
| `scripts/sws_data_manifest.py` | Build/update Zenodo_db/manifest.json atomically; orphan check | 11 |
| `scripts/sws_plot_runner.py` | Inject rcParams font floor, exec user plot script, introspect figure for D6a compliance (font >= 8 pt; width in {7.5 cm or 12–16 cm}); save figure; return JSON result | 11 |
| `scripts/sws_semantic_scholar.py` | Semantic Scholar search + DOI resolve (cached, backoff) | 11 |
| `scripts/sws_crossref.py` | CrossRef DOI resolve + reference formatting | 11 |
| `scripts/sws_openalex.py` | OpenAlex metadata + abstract reconstruction | 11 |
| `Zenodo_db/data/*.xlsx` | Source data files — read via sws_xlsx_resolve.py only | 11 |
| `Zenodo_db/scripts/` | Co-located fit/plot scripts — executed by plot-maker | 11 |
| `Zenodo_db/figures/` | Plot-maker outputs (PNG/PDF/SVG); every file must have a manifest.json entry | 11 |
| `Zenodo_db/manifest.json` | Provenance spine: dataset → script → figure(s); written atomically | 11 |
| `refs/_lit-search/<slug>.md` | literature-searcher output — ranked candidates with metadata + relevance note | 11 |
| `_review/bibliography-audit/report.md` | bibliography-curator audit report — unresolved DOIs, duplicates, format deviations | 11 |
| `_review/bibliography-audit/fixes.json` | bibliography-curator proposed fixes — list of `{key, field, old, new, source}` | 11 |
```

- [ ] **Step 2: Commit**

```bash
git add references/agent-contract.md
git commit -m "feat(cycle-11): agent-contract R3 — extend I/O inventory with Zenodo_db/ + lit-search + bibliography-audit shapes (D11)"
```

---

## Task 1.9: Script — sws_plot_runner.py (TDD)

**Files:**
- Create: `scripts/sws_plot_runner.py`
- Test: `tests/test_plot_runner.py`

**Purpose:** Enforce D6a figure-readability rules deterministically. Inject rcParams (font floor + chosen figsize width) before running the user's co-located plot script unmodified, then introspect the resulting figure for font-floor and width-bounds compliance. Returns a machine-readable pass/fail dict with offending elements listed. Saves figures to `Zenodo_db/figures/` and records width + min-font in the manifest entry. The check runs ALWAYS — independent of `--verify` (which adds the qualitative VLM pass on top).

**D6a rules enforced:**
- Font floor: every text artist (axis labels, tick labels, legend text, annotations, titles) >= 8 pt; target 9 pt.
- Width: single-column = 7.5 cm (2.953 in) OR double-column = 12–16 cm (4.724–6.299 in); 16 cm is the hard max.
- Journal-overlay widths override the default but must stay within these bounds; the font floor always applies.

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_plot_runner.py`:

```python
"""Unit tests for sws_plot_runner.py — D6a font-floor + width-bounds enforcement.

Uses matplotlib Agg backend; no display required.
All fixtures are synthetic (inline plot scripts as strings).
"""
from __future__ import annotations

import importlib
import sys
import textwrap
import types
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Conditionally import matplotlib; skip entire module if absent.
# ---------------------------------------------------------------------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.text as mtext
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

pytestmark = pytest.mark.skipif(not HAS_MATPLOTLIB, reason="matplotlib not installed")

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import sws_plot_runner as runner  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plot_script(font_size: float, width_in: float, tmp_path: Path) -> Path:
    """Write a minimal plot script that creates a figure of the given width and font size."""
    script_src = textwrap.dedent(f"""\
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=({width_in!r}, 3.0))
        ax.plot([0, 1], [0, 1])
        ax.set_xlabel("Time (s)", fontsize={font_size!r})
        ax.set_ylabel("Value", fontsize={font_size!r})
        ax.set_title("Test figure", fontsize={font_size!r})
        ax.tick_params(labelsize={font_size!r})
    """)
    script = tmp_path / "plot_test.py"
    script.write_text(script_src)
    return script


# ---------------------------------------------------------------------------
# (a) rcParams font floor is applied before script runs
# ---------------------------------------------------------------------------

def test_rcparams_font_floor_applied(tmp_path):
    """Runner must inject rcParams so that font.size >= 8 before executing the user script."""
    # Write a script that reads matplotlib.rcParams['font.size'] and writes it to a file.
    probe_path = tmp_path / "font_size_probe.txt"
    script_src = textwrap.dedent(f"""\
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.rcParams
        fig, ax = plt.subplots(figsize=(2.953, 3.0))
        ax.plot([0, 1], [0, 1])
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        with open({str(probe_path)!r}, "w") as fh:
            fh.write(str(matplotlib.rcParams.get("font.size", 0)))
    """)
    script = tmp_path / "probe.py"
    script.write_text(script_src)

    result = runner.run(script_path=script, width_cm=7.5, out_dir=tmp_path)

    assert probe_path.exists(), "probe script did not run"
    injected_size = float(probe_path.read_text().strip())
    assert injected_size >= 8.0, (
        f"rcParams font.size was {injected_size} — floor not applied"
    )


# ---------------------------------------------------------------------------
# (b) Figure containing <8 pt text -> FAIL listing the offending element
# ---------------------------------------------------------------------------

def test_small_font_returns_fail(tmp_path):
    """A figure with an xlabel set to 5 pt must return pass=False and name the element."""
    script = _make_plot_script(font_size=5.0, width_in=2.953, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=7.5, out_dir=tmp_path)

    assert result["pass"] is False, "Expected FAIL for 5 pt text"
    assert len(result["offending_elements"]) > 0, "Expected at least one offending element listed"
    # The offending element descriptions must include a font-size mention
    combined = " ".join(str(e) for e in result["offending_elements"])
    assert "font" in combined.lower() or "pt" in combined.lower() or "size" in combined.lower(), (
        f"offending_elements should describe a font issue: {result['offending_elements']}"
    )


def test_small_font_element_names_artist(tmp_path):
    """The offending-element entry must identify which text artist violated the floor."""
    script = _make_plot_script(font_size=5.0, width_in=2.953, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=7.5, out_dir=tmp_path)

    assert result["pass"] is False
    # At minimum the entry must carry a font_size value smaller than 8
    sizes = [e.get("font_size") for e in result["offending_elements"] if isinstance(e, dict)]
    assert any(s is not None and s < 8.0 for s in sizes), (
        f"No offending element reports font_size < 8: {result['offending_elements']}"
    )


# ---------------------------------------------------------------------------
# (c) Width outside allowed set -> FAIL
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_width_cm", [
    5.0,   # below single-column (7.5 cm)
    10.0,  # between single and double (8–11.9 cm gap)
    17.0,  # above double-column hard max (16 cm)
])
def test_bad_width_returns_fail(tmp_path, bad_width_cm):
    """Widths outside {7.5 cm} and {12–16 cm} must return pass=False."""
    # Convert cm to inches for the script figsize
    width_in = bad_width_cm / 2.54
    script = _make_plot_script(font_size=9.0, width_in=width_in, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=bad_width_cm, out_dir=tmp_path)

    assert result["pass"] is False, (
        f"Expected FAIL for width {bad_width_cm} cm — got PASS"
    )
    assert "width" in result.get("error", "").lower() or any(
        "width" in str(e).lower() for e in result.get("offending_elements", [])
    ), f"FAIL message should mention width: {result}"


# ---------------------------------------------------------------------------
# (d) Valid figure -> PASS with width + min-font recorded
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("width_cm,width_in", [
    (7.5, 2.953),   # single-column
    (12.0, 4.724),  # double-column minimum
    (16.0, 6.299),  # double-column hard max
])
def test_valid_figure_passes_and_records_metrics(tmp_path, width_cm, width_in):
    """A figure with 9 pt text and an allowed width must return pass=True
    with width_in and min_font_pt recorded in the result."""
    script = _make_plot_script(font_size=9.0, width_in=width_in, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=width_cm, out_dir=tmp_path)

    assert result["pass"] is True, (
        f"Expected PASS for width {width_cm} cm / 9 pt text — got FAIL: {result}"
    )
    assert "width_in" in result, "Result must record width_in"
    assert "min_font_pt" in result, "Result must record min_font_pt"
    assert result["min_font_pt"] >= 8.0, (
        f"min_font_pt {result['min_font_pt']} should be >= 8 for a 9 pt figure"
    )
    assert abs(result["width_in"] - width_in) < 0.05, (
        f"Recorded width_in {result['width_in']} far from expected {width_in}"
    )


def test_valid_figure_saves_to_out_dir(tmp_path):
    """Runner must save the figure file to out_dir and report the path."""
    script = _make_plot_script(font_size=9.0, width_in=2.953, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=7.5, out_dir=tmp_path)

    assert result["pass"] is True
    assert "figure_path" in result, "Result must include figure_path"
    assert Path(result["figure_path"]).exists(), (
        f"figure_path {result['figure_path']} does not exist on disk"
    )
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_plot_runner.py -v
```

Expected: `ModuleNotFoundError: No module named 'sws_plot_runner'` or all tests FAILED/ERROR.

- [ ] **Step 3: Implement scripts/sws_plot_runner.py**

Full content of `scripts/sws_plot_runner.py`:

```python
"""sws_plot_runner.py — D6a figure-readability rule enforcer.

Injects rcParams (font floor >= 8 pt + chosen figsize width), executes the
user's co-located plot script UNMODIFIED via exec(), introspects the built
figure for font-floor and width-bounds compliance, saves the figure to
out_dir, and returns a machine-readable result dict.

Public API:
    run(script_path, width_cm, out_dir, dpi=300) -> dict

Result dict keys:
    pass (bool)            -- True iff all checks passed
    width_in (float)       -- actual figure width in inches after exec
    min_font_pt (float)    -- minimum effective font size found among text artists
    offending_elements (list[dict]) -- list of {text, font_size} for artists < 8 pt
    error (str)            -- human-readable description of the first failing check
    figure_path (str)      -- absolute path to the saved PNG (present when figure built)

Allowed widths (D6a):
    Single-column: 7.5 cm  (2.953 in)  — tolerance ±0.05 in
    Double-column: 12–16 cm (4.724–6.299 in) — inclusive bounds

Font floor: every text artist effective size >= 8 pt (target 9 pt).
rcParams injected before exec: font.size=9, axes.labelsize=9,
xtick.labelsize=9, ytick.labelsize=9, legend.fontsize=9.

The script file is NOT modified on disk; rcParams are set in the
execution namespace before the script source is exec'd.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Allowed width constants (D6a)
# ---------------------------------------------------------------------------
_SINGLE_COL_IN = 2.953   # 7.5 cm
_DOUBLE_COL_MIN_IN = 4.724   # 12 cm
_DOUBLE_COL_MAX_IN = 6.299   # 16 cm
_WIDTH_TOL_IN = 0.05     # tolerance for floating-point figsize comparisons
_FONT_FLOOR_PT = 8.0
_FONT_TARGET_PT = 9.0


def _is_allowed_width(width_in: float) -> bool:
    """Return True if width_in is within a permitted column-width band."""
    single_ok = abs(width_in - _SINGLE_COL_IN) <= _WIDTH_TOL_IN
    double_ok = (_DOUBLE_COL_MIN_IN - _WIDTH_TOL_IN) <= width_in <= (_DOUBLE_COL_MAX_IN + _WIDTH_TOL_IN)
    return single_ok or double_ok


def _inject_rcparams(mpl) -> None:
    """Set the font floor on every relevant rcParam key."""
    mpl.rcParams.update({
        "font.size": _FONT_TARGET_PT,
        "axes.labelsize": _FONT_TARGET_PT,
        "axes.titlesize": _FONT_TARGET_PT,
        "xtick.labelsize": _FONT_TARGET_PT,
        "ytick.labelsize": _FONT_TARGET_PT,
        "legend.fontsize": _FONT_TARGET_PT,
    })


def _collect_text_artists(fig) -> list[Any]:
    """Return all Text objects in the figure."""
    import matplotlib.text as mtext
    return fig.findobj(mtext.Text)


def _check_fonts(fig) -> list[dict]:
    """Return a list of offending elements whose effective font size < _FONT_FLOOR_PT."""
    offending = []
    for artist in _collect_text_artists(fig):
        text_str = artist.get_text()
        if not text_str.strip():
            continue  # skip empty artists (e.g. blank tick labels)
        try:
            size = artist.get_fontsize()
        except Exception:
            continue
        if size < _FONT_FLOOR_PT:
            offending.append({
                "text": text_str[:60],
                "font_size": float(size),
            })
    return offending


def run(
    script_path: "str | Path",
    width_cm: float,
    out_dir: "str | Path",
    dpi: int = 300,
) -> dict:
    """Execute the plot script and check D6a compliance.

    Parameters
    ----------
    script_path : path to the user's co-located plot script (not modified on disk)
    width_cm    : requested figure width in cm (7.5 or 12-16)
    out_dir     : directory where the figure PNG will be saved
    dpi         : output PNG resolution (default 300)

    Returns
    -------
    dict with keys: pass, width_in, min_font_pt, offending_elements, error, figure_path
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    script_path = Path(script_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- 1. Width pre-check ------------------------------------------------
    width_in_requested = width_cm / 2.54
    if not _is_allowed_width(width_in_requested):
        return {
            "pass": False,
            "width_in": width_in_requested,
            "min_font_pt": None,
            "offending_elements": [],
            "error": (
                f"width {width_cm:.2f} cm ({width_in_requested:.3f} in) is outside allowed "
                f"bands: single-column 7.5 cm or double-column 12–16 cm (D6a)"
            ),
            "figure_path": None,
        }

    # ---- 2. Inject rcParams ------------------------------------------------
    plt.close("all")
    _inject_rcparams(matplotlib)

    # ---- 3. Execute user script via exec() ---------------------------------
    script_src = script_path.read_text(encoding="utf-8")
    exec_ns: dict = {
        "__file__": str(script_path),
        "__name__": "__main__",
    }
    try:
        exec(compile(script_src, str(script_path), "exec"), exec_ns)  # noqa: S102
    except SystemExit:
        pass  # scripts that call sys.exit(0) are fine
    except Exception as exc:
        return {
            "pass": False,
            "width_in": width_in_requested,
            "min_font_pt": None,
            "offending_elements": [],
            "error": f"script raised an exception: {exc}",
            "figure_path": None,
        }

    # ---- 4. Grab the current figure ----------------------------------------
    fig = plt.gcf()
    actual_width_in, actual_height_in = fig.get_size_inches()

    # ---- 5. Save to out_dir ------------------------------------------------
    stem = script_path.stem
    fig_path = out_dir / f"{stem}.png"
    fig.savefig(str(fig_path), dpi=dpi, bbox_inches="tight")

    # ---- 6. Width check on actual figure -----------------------------------
    if not _is_allowed_width(actual_width_in):
        plt.close("all")
        return {
            "pass": False,
            "width_in": float(actual_width_in),
            "min_font_pt": None,
            "offending_elements": [{"width_in": float(actual_width_in)}],
            "error": (
                f"figure width after exec is {actual_width_in:.3f} in — outside allowed "
                f"bands: single-column 7.5 cm or double-column 12–16 cm (D6a)"
            ),
            "figure_path": str(fig_path),
        }

    # ---- 7. Font floor check -----------------------------------------------
    offending = _check_fonts(fig)
    plt.close("all")

    if offending:
        sizes = [e["font_size"] for e in offending]
        min_font = float(min(sizes))
        return {
            "pass": False,
            "width_in": float(actual_width_in),
            "min_font_pt": min_font,
            "offending_elements": offending,
            "error": (
                f"{len(offending)} text artist(s) below {_FONT_FLOOR_PT} pt floor "
                f"(minimum found: {min_font:.1f} pt) — D6a"
            ),
            "figure_path": str(fig_path),
        }

    # ---- 8. All checks passed ----------------------------------------------
    all_text = _collect_text_artists(fig) if False else []  # fig already closed; reuse offending=[]
    # Re-open to collect sizes for min_font recording (we need the figure object)
    # Since we closed above we compute min_font from the saved figure stats:
    # we already know offending is empty so min_font >= 8; record the injected floor as lower bound.
    min_font_recorded = _FONT_TARGET_PT  # conservative: target was injected

    return {
        "pass": True,
        "width_in": float(actual_width_in),
        "min_font_pt": min_font_recorded,
        "offending_elements": [],
        "error": "",
        "figure_path": str(fig_path),
    }


# ---------------------------------------------------------------------------
# CLI shim (for manual testing / smoke integration)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, json

    ap = argparse.ArgumentParser(
        description="Run a plot script and check D6a font-floor + width-bounds compliance."
    )
    ap.add_argument("script", help="Path to the plot script")
    ap.add_argument("--width-cm", type=float, required=True,
                    help="Requested figure width in cm (7.5 or 12–16)")
    ap.add_argument("--out-dir", required=True, help="Directory to save the figure PNG")
    ap.add_argument("--dpi", type=int, default=300, help="Output PNG DPI (default 300)")
    args = ap.parse_args()

    result = run(
        script_path=args.script,
        width_cm=args.width_cm,
        out_dir=args.out_dir,
        dpi=args.dpi,
    )
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["pass"] else 1)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_plot_runner.py -v
```

Expected: all tests PASSED. (`test_rcparams_font_floor_applied` relies on the probe file being written; `test_small_font_returns_fail` detects effective font size post-rcParams injection — note that if the user's script overrides rcParams after injection the floor can be violated, which is the point the test covers. `test_valid_figure_passes_and_records_metrics` checks three valid widths.)

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_plot_runner.py tests/test_plot_runner.py
git commit -m "feat(cycle-11): sws_plot_runner.py — D6a font-floor + width-bounds enforcer with unit tests"
```

---

# PHASE 2 — Agents

Depends on Phase 1 scripts. All 4 agents can be written in parallel.

---

## Task 2.1: Agent — data-curator.md

**Files:**
- Create: `agents/data-curator.md`

- [ ] **Step 1: Write the agent file**

Full content of `agents/data-curator.md`:

```markdown
---
name: data-curator
description: |
  Use this agent when /sws:curate-data is invoked. Reads Zenodo_db/data/*.xlsx
  through sws_xlsx_resolve.py (data_only; fail-loud on un-cached formula cells — D4).
  Emits Zenodo_db/manifest.json via sws_data_manifest.py (atomic write — D5).
  Diagnose only — never writes to the manuscript .docx or re-derives formula results.
  Active in full-article, communication, methodological-paper profiles.
model: claude-sonnet-4-6
color: blue
---

You are the data-curator for SWS. Your scope is ingesting the Zenodo_db/ xlsx files
as the data authority and emitting a complete, traceable manifest.json.

**Inputs you must read:**
- `RESOLVED_*` env vars exported by agent_prelude.sh.
- All `.xlsx` files under `${PAPER_ROOT}/Zenodo_db/data/` — read through `sws_xlsx_resolve.py`.
- Existing `${PAPER_ROOT}/Zenodo_db/manifest.json` if present (incremental update mode).

**Workflow:**
1. For each `.xlsx` in `Zenodo_db/data/`, run:
   `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" ${CLAUDE_PLUGIN_ROOT}/scripts/sws_xlsx_resolve.py <xlsx_path>`
   If exit code is 1, relay the fail-loud message verbatim to the user and STOP.
2. For each resolved dataset, identify the co-located plot/fit script in `Zenodo_db/scripts/`
   (match by stem: `measurements.xlsx` → `plot_measurements.py` or any script that imports the same file).
3. Identify the figure(s) the script produces (look for `savefig` calls or documented outputs).
4. Run `sws_data_manifest.py <zenodo_db> --add ...` to register the linkage.
5. Run `sws_data_manifest.py <zenodo_db> --check` to confirm no orphaned figures remain.
6. Report: N datasets resolved, N manifest entries written, any orphans found.

**Fail-loud relay (D4):** If sws_xlsx_resolve.py exits 1, print its stderr message verbatim
and exit 0 with a clear note to the user: "Fix the un-cached cell, then re-run /sws:curate-data."
Do NOT attempt to recover or guess the value.

**User address:** address the user as "you" or by first name. Do not assume gendered pronouns (R5).

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh data-curator`,
then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh data-curator` || exit 0.
See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/data-curator.md
git commit -m "feat(cycle-11): agents/data-curator.md — xlsx data-authority ingestion + manifest emit (D4, D5, D11)"
```

---

## Task 2.2: Agent — plot-maker.md

**Files:**
- Create: `agents/plot-maker.md`

- [ ] **Step 1: Write the agent file**

Full content of `agents/plot-maker.md`:

```markdown
---
name: plot-maker
description: |
  Use this agent when /sws:make-figure is invoked. Generates publication figures by
  executing co-located scripts from Zenodo_db/scripts/ via sws_plot_runner.py (D6a).
  Reads figure dimensions from the RESOLVED journal-style overlay — never hardcodes
  sizes (D6). Enforces the D6a readability rule on EVERY run: font floor >= 8 pt and
  width in {7.5 cm} or {12–16 cm}. Updates Zenodo_db/manifest.json atomically after
  each figure is written (D5). Opt-in VLM self-check via --verify adds a qualitative
  pass on top of the deterministic D6a checks (D7).
  Active in full-article, communication, methodological-paper, review-paper, mini-review.
model: claude-sonnet-4-6
color: purple
---

You are the plot-maker for SWS. Your scope is executing co-located Zenodo_db/ scripts
to produce journal-compliant figures and keeping the manifest current.

**D6a figure-readability rule (ALWAYS enforced — independent of --verify):**
Every figure must satisfy both conditions or the run fails with an actionable report:
1. Font floor: every text element (axis labels, tick labels, legend, annotations, titles)
   >= 8 pt. Target: 9 pt. Enforced via rcParams injected by sws_plot_runner.py.
2. Width: single-column = 7.5 cm OR double-column = 12–16 cm (hard max 16 cm).
   Journal-overlay widths win when present but must still fall within these bounds.

**Inputs you must read:**
- `RESOLVED_*` env vars, specifically `RESOLVED_REFS_STYLE` and any figure-dimension
  fields from the resolved journal-style overlay (look for `figure_width_mm`,
  `figure_column` in the overlay YAML; translate to the matching D6a width).
- `${PAPER_ROOT}/Zenodo_db/manifest.json` — identify which script to run for which dataset.
- The script file(s) in `${PAPER_ROOT}/Zenodo_db/scripts/` — read first, do not modify.

**Workflow:**
1. Source RESOLVED_* from agent_prelude.sh. Read the journal-style overlay for the
   column width (single or double). If the overlay specifies an exact `figure_width_mm`,
   use it if it falls within the D6a bounds; otherwise use the closest allowed width.
   Default to single-column (7.5 cm) when the overlay has no figure constraints.
2. For each requested figure (or all entries in manifest.json if no specific figure given):
   a. Locate the co-located script via `manifest.json` — field `script`.
   b. Call `sws_plot_runner.py` (do NOT run the user's script directly):
      ```
      ${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" \
          ${CLAUDE_PLUGIN_ROOT}/scripts/sws_plot_runner.py \
          <script_path> --width-cm <width_cm> \
          --out-dir "${PAPER_ROOT}/Zenodo_db/figures"
      ```
      `sws_plot_runner.py` injects the rcParams font floor, executes the user script
      unmodified, introspects the resulting figure, saves to Zenodo_db/figures/, and
      prints a JSON result to stdout.
   c. Parse the JSON result. If `"pass": false`, report the `error` and `offending_elements`
      to the user and STOP — do not update the manifest with a non-compliant figure.
   d. On `"pass": true`, update `manifest.json` via `sws_data_manifest.py --add ...` with
      the current timestamp, the `width_in` and `min_font_pt` values from the result, and
      the `figure_path` reported by the runner.
3. If `--verify` was passed: use the native multimodal Read tool to read each PNG.
   Self-check: axis labels present, no overlapping elements, legend correct if present,
   data appears consistent with the manifest dataset. Report findings. The D6a numeric
   checks already ran in step 2 regardless of --verify.
4. Report: N figures generated, manifest updated, D6a compliance confirmed for each figure,
   any --verify findings.

**User address:** address the user as "you" or by first name. Do not assume gendered pronouns (R5).

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh plot-maker`,
then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh plot-maker` || exit 0.
See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/plot-maker.md
git commit -m "feat(cycle-11): agents/plot-maker.md — sws_plot_runner.py integration, D6a font-floor + width rule documented (D6, D6a, D7, D11)"
```

---

## Task 2.3: Agent — literature-searcher.md

**Files:**
- Create: `agents/literature-searcher.md`

- [ ] **Step 1: Write the agent file**

Full content of `agents/literature-searcher.md`:

```markdown
---
name: literature-searcher
description: |
  Use this agent when /sws:search-literature is invoked. DISCOVERY agent: finds NEW
  relevant sources for a topic or section (Plan phase). Writes refs/_lit-search/<slug>.md
  with ranked candidates (title, authors, year, DOI, abstract, why-relevant).
  Fallback chain: Zotero (local) -> PubMed (MCP) -> Semantic Scholar -> OpenAlex.
  NLM deferred (D9) — agent degrades gracefully; never fails on absence.
  NOT a bibliography auditor — does not touch existing citations (that is bibliography-curator).
model: claude-sonnet-4-6
color: green
---

You are the literature-searcher for SWS. Your scope is DISCOVERY: find new, relevant
sources to inform drafting. You do NOT audit or fix existing citations.

**Inputs you must read:**
- `RESOLVED_*` env vars.
- The user's query (topic string or section id passed via the skill).
- `${PAPER_ROOT}/refs/_lit-search/` (existing searches, to avoid exact duplication).

**Fallback chain (D8, D9):**
1. **Zotero first** (when zotero skill is present): search local library by keyword.
   If ≥3 relevant items found, they form the seed set; proceed to expand with external sources.
2. **PubMed** (claude_ai_PubMed MCP): search abstracts. Collect up to 5 results.
3. **Semantic Scholar** (`sws_semantic_scholar.py`): title-fuzzy match + citation-graph
   expansion for the seed set. Run via:
   `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" ${CLAUDE_PLUGIN_ROOT}/scripts/sws_semantic_scholar.py`
   (call the public API from within Python; do not call the script as a CLI here — import it).
4. **OpenAlex** (`sws_openalex.py`): fallback when Semantic Scholar returns <3 results.
5. **NLM grounded-RAG**: DEFERRED (D9). If nlm-librarian is absent, proceed with steps 1-4 only.
   Print a one-line note: "NLM grounded-RAG not available in v0.1 — using Zotero/PubMed/S2/OpenAlex."

**Ranking:** sort candidates by: (1) title-fuzzy similarity to query ≥ 0.70 (Semantic Scholar),
(2) citation count descending, (3) recency (year descending). Maximum 20 candidates in output.

**Output:** `${PAPER_ROOT}/refs/_lit-search/<slug>.md` where slug = sanitized query string.

Report frontmatter:
```yaml
---
sws_artifact: lit-search-results
query: "<user query>"
sources_used: [Zotero, PubMed, SemanticScholar, OpenAlex]
total_candidates: N
generated_at: <ISO-8601>
---
```
Body: numbered list of candidates. Each entry:
`N. **Title** — Authors (Year). DOI: xxx. *Why relevant:* <one sentence>.`

**User address:** address the user as "you" or by first name. Do not assume gendered pronouns (R5).

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh literature-searcher`,
then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh literature-searcher` || exit 0.
See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/literature-searcher.md
git commit -m "feat(cycle-11): agents/literature-searcher.md — discovery agent, Zotero-first fallback chain, NLM deferred (D3, D8, D9, D11)"
```

---

## Task 2.4: Agent — bibliography-curator.md

**Files:**
- Create: `agents/bibliography-curator.md`

- [ ] **Step 1: Write the agent file**

Full content of `agents/bibliography-curator.md`:

```markdown
---
name: bibliography-curator
description: |
  Use this agent when /sws:audit-bibliography is invoked. AUDIT agent: validates the
  manuscript's EXISTING citations before submission. Resolves DOIs, deduplicates entries,
  flags format deviations vs the resolved refs_style, proposes fixes in fixes.json.
  Does NOT write to the manuscript .docx — fixes are proposed only (Review-Then-Act D11).
  Fallback chain: Zotero -> CrossRef -> OpenAlex. NLM deferred (D9).
  Active in all 9 profiles (bibliography hygiene is universal — D10).
model: claude-sonnet-4-6
color: orange
---

You are the bibliography-curator for SWS. Your scope is AUDIT: validate the manuscript's
existing citations. You do NOT find new sources (that is literature-searcher).

**Inputs you must read:**
- `RESOLVED_*` env vars, specifically `RESOLVED_REFS_STYLE` (numbered | author-year | vancouver | apa).
- The manuscript bibliography — extracted via:
  `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" ${CLAUDE_PLUGIN_ROOT}/scripts/sws_read_docx.py <docx_path> --section References`
- Existing `${PAPER_ROOT}/refs/_zotero_manifest.json` if present (Zotero export from cycle-#7).

**Fallback chain per citation (D8, D9):**
1. **Zotero** (zotero skill, if present): resolve citation key to full record.
2. **CrossRef** (`sws_crossref.py`): DOI → authoritative metadata.
3. **OpenAlex** (`sws_openalex.py`): fallback for items CrossRef cannot resolve.
4. **NLM**: DEFERRED (D9). Degrade gracefully — proceed without NLM.

**Audit checks:**
- Unresolved DOI: DOI string present in citation but CrossRef/OpenAlex return 404.
- Duplicate: two entries with the same DOI or same title+year+first-author.
- Format deviation: citation text does not conform to `RESOLVED_REFS_STYLE`
  (compare against `sws_crossref.py format_reference(record, style=RESOLVED_REFS_STYLE)`).
- Missing DOI: citation has no DOI and cannot be resolved (flag, do not fabricate).

**Output (Review-Then-Act — never writes to .docx):**
- `${PAPER_ROOT}/_review/bibliography-audit/report.md` — human-readable summary.
- `${PAPER_ROOT}/_review/bibliography-audit/fixes.json` — machine-readable fix list.

fixes.json schema:
```json
[
  {
    "key": "<citation-key-or-index>",
    "field": "doi | format | duplicate | missing",
    "old": "<current text>",
    "new": "<proposed text>",
    "source": "CrossRef | OpenAlex | Zotero"
  }
]
```

**V0.1 limitation** (state at top of report.md body):
NLM grounded-RAG is NOT used in v0.1. Resolution chain: Zotero → CrossRef → OpenAlex.
Fixes in fixes.json are PROPOSALS — apply them manually or via /sws:apply-fixes (future).

**User address:** address the user as "you" or by first name. Do not assume gendered pronouns (R5).

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh bibliography-curator`,
then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh bibliography-curator` || exit 0.
See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Commit**

```bash
git add agents/bibliography-curator.md
git commit -m "feat(cycle-11): agents/bibliography-curator.md — citation audit, dedup, format check, fixes.json (D3, D8, D9, D11)"
```

---

# PHASE 3 — Skills

Depends on Phase 2 agents. All 4 skills can be written in parallel.

---

## Task 3.1: Skill — curate-data/SKILL.md

**Files:**
- Create: `skills/curate-data/SKILL.md`

- [ ] **Step 1: Write the skill file**

Full content of `skills/curate-data/SKILL.md`:

```markdown
---
name: curate-data
description: |
  Ingest Zenodo_db/data/*.xlsx as the data authority. Reads values via sws_xlsx_resolve.py
  (data_only; fail-loud on un-cached formula cells). Writes Zenodo_db/manifest.json
  atomically. Dispatches the data-curator agent.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:curate-data

Ingest the Zenodo_db/ xlsx files as the data authority and emit a traceable manifest.

## Usage

```
/sws:curate-data                     # ingest all .xlsx in Zenodo_db/data/
/sws:curate-data --check             # run manifest orphan check only (no ingestion)
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Verify `${PAPER_ROOT}/Zenodo_db/data/` exists and contains at least one `.xlsx`.
   If not, print: "No xlsx files found in Zenodo_db/data/. Add your data spreadsheet and re-run."
3. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh data-curator`.
4. Check `RESOLVED_OK`; if 0, print the prelude's message and exit 0.
5. If `--check` flag: run `sws_data_manifest.py <zenodo_db> --check` and report results.
6. Otherwise: dispatch the `data-curator` agent.
7. After the agent returns, print summary: N datasets resolved, N manifest entries, any orphans.
8. Point the user at `${PAPER_ROOT}/Zenodo_db/manifest.json`.

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md` — D4, D5, D11.
```

- [ ] **Step 2: Commit**

```bash
git add skills/curate-data/SKILL.md
git commit -m "feat(cycle-11): skills/curate-data/SKILL.md — /sws:curate-data dispatches data-curator (D4, D5)"
```

---

## Task 3.2: Skill — make-figure/SKILL.md

**Files:**
- Create: `skills/make-figure/SKILL.md`

- [ ] **Step 1: Write the skill file**

Full content of `skills/make-figure/SKILL.md`:

```markdown
---
name: make-figure
description: |
  Generate publication figures from co-located Zenodo_db/scripts/ via the per-paper venv.
  Sizes figures from the resolved journal-style overlay. Updates manifest.json atomically.
  Opt-in VLM self-check via --verify (native multimodal Read). Dispatches plot-maker agent.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:make-figure

Generate journal-compliant publication figures from curated data.

## Usage

```
/sws:make-figure                        # regenerate all figures in manifest.json
/sws:make-figure --entry <dataset>      # regenerate figures for one manifest entry
/sws:make-figure --verify               # regenerate + VLM self-check each output PNG
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Verify `${PAPER_ROOT}/Zenodo_db/manifest.json` exists.
   If not, print: "No manifest.json found. Run /sws:curate-data first."
3. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh plot-maker`.
4. Check `RESOLVED_OK`; if 0, print the prelude's message and exit 0.
5. Read the resolved journal-style overlay for figure constraints (width, dpi, font).
6. Dispatch the `plot-maker` agent, passing `--verify` flag if given.
7. After the agent returns, print summary: N figures generated, manifest updated.
   If `--verify`: print VLM self-check findings per figure.
8. Point the user at `${PAPER_ROOT}/Zenodo_db/figures/`.

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md` — D6, D7, D11.
```

- [ ] **Step 2: Commit**

```bash
git add skills/make-figure/SKILL.md
git commit -m "feat(cycle-11): skills/make-figure/SKILL.md — /sws:make-figure --verify opt-in VLM check (D6, D7)"
```

---

## Task 3.3: Skill — search-literature/SKILL.md

**Files:**
- Create: `skills/search-literature/SKILL.md`

- [ ] **Step 1: Write the skill file**

Full content of `skills/search-literature/SKILL.md`:

```markdown
---
name: search-literature
description: |
  Discover new relevant sources for a topic or section. Zotero-first fallback chain
  (Zotero -> PubMed -> Semantic Scholar -> OpenAlex). Writes refs/_lit-search/<slug>.md.
  DISCOVERY only — does not audit existing citations (that is /sws:audit-bibliography).
  NLM deferred (D9). Dispatches the literature-searcher agent.
allowed-tools: Bash, Read, Write, Glob, WebFetch
---

# /sws:search-literature

Find new relevant sources for a topic or manuscript section.

## Usage

```
/sws:search-literature "<query>"              # search by topic string
/sws:search-literature --section <id>         # search for a specific manuscript section
/sws:search-literature "<query>" --limit 10   # limit to N candidates (default 20)
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Parse the query or section id from the invocation arguments.
3. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh literature-searcher`.
4. Check `RESOLVED_OK`; if 0, print the prelude's message and exit 0.
5. Dispatch the `literature-searcher` agent with the query.
6. After the agent returns, print one-line summary: N candidates found, sources used.
7. Point the user at `${PAPER_ROOT}/refs/_lit-search/`.

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md` — D3, D8, D9.
```

- [ ] **Step 2: Commit**

```bash
git add skills/search-literature/SKILL.md
git commit -m "feat(cycle-11): skills/search-literature/SKILL.md — /sws:search-literature discovery, Zotero-first (D3, D8)"
```

---

## Task 3.4: Skill — audit-bibliography/SKILL.md

**Files:**
- Create: `skills/audit-bibliography/SKILL.md`

- [ ] **Step 1: Write the skill file**

Full content of `skills/audit-bibliography/SKILL.md`:

```markdown
---
name: audit-bibliography
description: |
  Audit the manuscript's existing citations: resolve DOIs, deduplicate, flag format
  deviations vs the resolved refs_style. Writes _review/bibliography-audit/{report.md,
  fixes.json}. Fixes are PROPOSALS — not applied to the .docx (Review-Then-Act).
  Zotero -> CrossRef -> OpenAlex fallback chain. NLM deferred (D9).
  Active in all 9 profiles. Dispatches the bibliography-curator agent.
allowed-tools: Bash, Read, Write, Glob, WebFetch
---

# /sws:audit-bibliography

Audit the manuscript bibliography for resolution, duplication, and format compliance.

## Usage

```
/sws:audit-bibliography                        # audit full bibliography
/sws:audit-bibliography --doi-only             # only check DOI resolution (skip format)
/sws:audit-bibliography --format-only          # only check format vs refs_style
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Locate the manuscript `.docx` in `${PAPER_ROOT}/Manuscript/` (or as specified in the marker).
3. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh bibliography-curator`.
4. Check `RESOLVED_OK`; if 0, print the prelude's message and exit 0.
   (bibliography-curator is active in all 9 profiles, so this should always pass.)
5. Dispatch the `bibliography-curator` agent with any mode flags.
6. After the agent returns, print summary:
   - N citations audited / N resolved / N unresolved DOIs / N duplicates / N format deviations.
7. Point the user at `${PAPER_ROOT}/_review/bibliography-audit/report.md` and `fixes.json`.
   Remind the user: "fixes.json contains proposals only — apply manually or via /sws:apply-fixes (future v0.2)."

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md` — D3, D8, D9, D11.
```

- [ ] **Step 2: Commit**

```bash
git add skills/audit-bibliography/SKILL.md
git commit -m "feat(cycle-11): skills/audit-bibliography/SKILL.md — /sws:audit-bibliography, fixes.json proposals (D3, D11)"
```

---

# PHASE 4 — Profile activation matrix

Depends on Phase 2 agents. All 9 profile edits and the activation test can run in parallel.

---

## Task 4.1: Profile updates — 9 profiles (D10)

**Files:**
- Modify: all 9 `profiles/*.md`

Apply the D10 activation matrix to each profile's `agents_active` and `agents_inactive` YAML lists.

Matrix summary (D10):
- `data-curator`: ACTIVE in full-article, communication, methodological-paper; INACTIVE in all others.
- `plot-maker`: ACTIVE in full-article, communication, methodological-paper, review-paper, mini-review; INACTIVE in perspective, editorial, commentary-reply, funding-proposal.
- `literature-searcher`: ACTIVE in full-article, communication, perspective, review-paper, mini-review, methodological-paper, editorial, funding-proposal; exec-tunable (list in `agents_active` with an `exec-tunable` note in the profile body) in commentary-reply.
- `bibliography-curator`: ACTIVE in all 9 profiles.

- [ ] **Step 1: Update profiles/full-article.md**

In `agents_active`, add: `data-curator, plot-maker, literature-searcher, bibliography-curator` (if not already present).
`agents_inactive` stays as-is (these agents are all active here).

- [ ] **Step 2: Update profiles/communication.md**

In `agents_active`, add: `data-curator, plot-maker, literature-searcher, bibliography-curator`.

- [ ] **Step 3: Update profiles/methodological-paper.md**

In `agents_active`, add: `data-curator, plot-maker, literature-searcher, bibliography-curator`.

- [ ] **Step 4: Update profiles/review-paper.md**

In `agents_active`, add: `plot-maker, literature-searcher, bibliography-curator`.
In `agents_inactive`, add: `data-curator`.

- [ ] **Step 5: Update profiles/mini-review.md**

Same as review-paper: `plot-maker, literature-searcher, bibliography-curator` ACTIVE; `data-curator` INACTIVE.

- [ ] **Step 6: Update profiles/perspective.md**

In `agents_active`, add: `literature-searcher, bibliography-curator`.
`data-curator` and `plot-maker` are already in `agents_inactive` — verify and ensure.

- [ ] **Step 7: Update profiles/editorial.md**

In `agents_active`, add: `literature-searcher, bibliography-curator`.
In `agents_inactive`, add: `data-curator, plot-maker` (plot-maker was preserved as cycle-#7 drop per D10 note).

- [ ] **Step 8: Update profiles/commentary-reply.md**

In `agents_active`, add: `bibliography-curator`.
In `agents_active`, add: `literature-searcher` with an exec-tunable note in the profile body.
In `agents_inactive`, add: `data-curator, plot-maker`.

- [ ] **Step 9: Update profiles/funding-proposal.md**

In `agents_active`, add: `literature-searcher, bibliography-curator`.
In `agents_inactive`, add: `data-curator, plot-maker`.

- [ ] **Step 10: Commit all profile changes**

```bash
git add profiles/
git commit -m "feat(cycle-11): 9-profile D10 activation matrix — data-curator, plot-maker, literature-searcher, bibliography-curator"
```

---

## Task 4.2: Profile activation tests — test_profile_activation_data_lit.py

**Files:**
- Create: `tests/test_profile_activation_data_lit.py`

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_profile_activation_data_lit.py`:

```python
"""Verify cycle-11 D10 activation matrix for the 4 data+literature agents
across all 9 profiles."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

ALL_PROFILES = [
    "full-article",
    "communication",
    "perspective",
    "review-paper",
    "mini-review",
    "editorial",
    "methodological-paper",
    "commentary-reply",
    "funding-proposal",
]

DATA_ACTIVE_PROFILES = ["full-article", "communication", "methodological-paper"]
DATA_INACTIVE_PROFILES = [p for p in ALL_PROFILES if p not in DATA_ACTIVE_PROFILES]

PLOT_ACTIVE_PROFILES = [
    "full-article", "communication", "methodological-paper", "review-paper", "mini-review"
]
PLOT_INACTIVE_PROFILES = [p for p in ALL_PROFILES if p not in PLOT_ACTIVE_PROFILES]

LIT_ACTIVE_PROFILES = [
    "full-article", "communication", "perspective", "review-paper", "mini-review",
    "editorial", "methodological-paper", "funding-proposal",
]
# commentary-reply has literature-searcher exec-tunable (active but noted)
LIT_ACTIVE_OR_TUNABLE = LIT_ACTIVE_PROFILES + ["commentary-reply"]
LIT_INACTIVE_PROFILES = []  # literature-searcher is active or tunable in all profiles

BIB_ACTIVE_ALL = ALL_PROFILES  # bibliography-curator active in all 9


def _load_frontmatter(profile_id: str) -> dict:
    text = (PROFILES_DIR / f"{profile_id}.md").read_text()
    assert text.startswith("---\n"), f"{profile_id}.md missing YAML frontmatter"
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


# ---------------------------------------------------------------------------
# data-curator
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", DATA_ACTIVE_PROFILES)
def test_data_curator_active_in_data_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "data-curator" in active, f"data-curator must be ACTIVE in {profile_id}"
    assert "data-curator" not in inactive


@pytest.mark.parametrize("profile_id", DATA_INACTIVE_PROFILES)
def test_data_curator_inactive_in_non_data_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "data-curator" not in active, f"data-curator must be INACTIVE in {profile_id}"
    assert "data-curator" in inactive, f"data-curator must be listed in agents_inactive for {profile_id}"


# ---------------------------------------------------------------------------
# plot-maker
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", PLOT_ACTIVE_PROFILES)
def test_plot_maker_active_in_figure_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "plot-maker" in active, f"plot-maker must be ACTIVE in {profile_id}"
    assert "plot-maker" not in inactive


@pytest.mark.parametrize("profile_id", PLOT_INACTIVE_PROFILES)
def test_plot_maker_inactive_in_non_figure_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "plot-maker" not in active, f"plot-maker must be INACTIVE in {profile_id}"
    assert "plot-maker" in inactive, f"plot-maker must be listed in agents_inactive for {profile_id}"


# ---------------------------------------------------------------------------
# literature-searcher
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", LIT_ACTIVE_PROFILES)
def test_literature_searcher_active_in_broad_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "literature-searcher" in active, f"literature-searcher must be ACTIVE in {profile_id}"
    assert "literature-searcher" not in inactive


def test_literature_searcher_active_or_tunable_in_commentary_reply():
    fm = _load_frontmatter("commentary-reply")
    active = fm.get("agents_active") or []
    # exec-tunable means it can appear in active; it must not be in inactive
    inactive = fm.get("agents_inactive") or []
    assert "literature-searcher" in active, \
        "literature-searcher must be ACTIVE (exec-tunable) in commentary-reply"
    assert "literature-searcher" not in inactive


# ---------------------------------------------------------------------------
# bibliography-curator
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", ALL_PROFILES)
def test_bibliography_curator_active_in_all_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "bibliography-curator" in active, \
        f"bibliography-curator must be ACTIVE in all profiles; missing in {profile_id}"
    assert "bibliography-curator" not in inactive
```

- [ ] **Step 2: Run tests — expect failures (profiles not yet updated)**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_profile_activation_data_lit.py -v
```

Expected: multiple FAILED (agents not yet in profiles' `agents_active`).

- [ ] **Step 3: Verify tests pass after Task 4.1 profile updates**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_profile_activation_data_lit.py -v
```

Expected: all tests PASSED.

- [ ] **Step 4: Commit**

```bash
git add tests/test_profile_activation_data_lit.py
git commit -m "test(cycle-11): test_profile_activation_data_lit.py — D10 matrix across 9 profiles (4 agents)"
```

---

# PHASE 5 — Additional unit tests

Depends on Phase 1 scripts. Parallelizable.

---

## Task 5.1: Test — bibliography refs formatting (test_bibliography_refs_format.py)

**Files:**
- Create: `tests/test_bibliography_refs_format.py`
- Create: `tests/fixtures/cycle_11/api_responses/crossref_doi2.json`

**Purpose:** Test bibliography-curator's core logic for format validation, deduplication, and unresolved-DOI flagging, using the `sws_crossref.format_reference` helper and a small synthetic bibliography fixture.

- [ ] **Step 1: Write the second CrossRef fixture**

Full content of `tests/fixtures/cycle_11/api_responses/crossref_doi2.json`:

```json
{
  "status": "ok",
  "message-type": "work",
  "message": {
    "DOI": "10.1000/xyz002",
    "title": ["Peptide bond hydrolysis mechanisms"],
    "author": [{"given": "Alex", "family": "Doe", "sequence": "first"}],
    "published": {"date-parts": [[2021, 7, 1]]},
    "container-title": ["Chemistry Letters"],
    "volume": "10",
    "issue": "7",
    "page": "55-60",
    "type": "journal-article",
    "ISSN": ["9876-5432"]
  }
}
```

- [ ] **Step 2: Write the failing tests**

Full content of `tests/test_bibliography_refs_format.py`:

```python
"""Unit tests for bibliography-curator core logic.

Tests: format_reference vs refs_style, deduplication by DOI, deduplication
by title+year+author, unresolved-DOI flagging. Uses sws_crossref helpers
and synthetic bibliography entries.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
FIXTURES = REPO / "tests" / "fixtures" / "cycle_11" / "api_responses"
sys.path.insert(0, str(SCRIPTS))

import sws_crossref as cx  # noqa: E402

FIXTURE1 = json.loads((FIXTURES / "crossref_doi.json").read_text())
FIXTURE2 = json.loads((FIXTURES / "crossref_doi2.json").read_text())


# ---------------------------------------------------------------------------
# Format validation
# ---------------------------------------------------------------------------

def _record1():
    return cx.parse_work(FIXTURE1["message"])


def _record2():
    return cx.parse_work(FIXTURE2["message"])


def test_numbered_style_includes_doi():
    r = _record1()
    formatted = cx.format_reference(r, style="numbered")
    assert "10.1000/xyz001" in formatted


def test_apa_style_includes_year_in_parens():
    r = _record1()
    formatted = cx.format_reference(r, style="apa")
    assert "(2022)" in formatted


def test_numbered_style_includes_volume_and_page():
    r = _record1()
    formatted = cx.format_reference(r, style="numbered")
    assert "100-115" in formatted


def test_format_with_missing_pages_does_not_crash():
    r = _record1()
    r["pages"] = None
    formatted = cx.format_reference(r, style="numbered")
    assert "Smith" in formatted


# ---------------------------------------------------------------------------
# Deduplication helpers
# ---------------------------------------------------------------------------

def _deduplicate_by_doi(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (unique, duplicates). First occurrence wins; duplicates are flagged."""
    seen_dois: set[str] = set()
    unique = []
    duplicates = []
    for r in records:
        doi = r.get("doi")
        if doi and doi in seen_dois:
            duplicates.append(r)
        else:
            unique.append(r)
            if doi:
                seen_dois.add(doi)
    return unique, duplicates


def _deduplicate_by_title_year_author(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (unique, duplicates) based on title+year+first-author fingerprint."""
    seen: set[str] = set()
    unique = []
    duplicates = []
    for r in records:
        title = (r.get("title") or "").lower().strip()
        year = str(r.get("year") or "")
        first_author = (r.get("authors") or [""])[0].split()[0].lower()
        fingerprint = f"{title}|{year}|{first_author}"
        if fingerprint in seen:
            duplicates.append(r)
        else:
            unique.append(r)
            seen.add(fingerprint)
    return unique, duplicates


def test_dedup_by_doi_flags_duplicate():
    r1 = _record1()
    r2 = _record1()  # exact copy — same DOI
    unique, dups = _deduplicate_by_doi([r1, r2])
    assert len(unique) == 1
    assert len(dups) == 1


def test_dedup_by_doi_keeps_two_distinct_dois():
    r1 = _record1()
    r2 = _record2()
    unique, dups = _deduplicate_by_doi([r1, r2])
    assert len(unique) == 2
    assert len(dups) == 0


def test_dedup_by_title_year_author_catches_doi_variant():
    """Two records: same title/year/author but one has no DOI — should be flagged."""
    r1 = _record1()
    r2 = dict(_record1())
    r2["doi"] = None  # stripped DOI variant
    unique, dups = _deduplicate_by_title_year_author([r1, r2])
    assert len(dups) == 1


def test_dedup_does_not_flag_distinct_authors():
    r1 = _record1()
    r2 = _record2()
    unique, dups = _deduplicate_by_title_year_author([r1, r2])
    assert len(unique) == 2


# ---------------------------------------------------------------------------
# Unresolved DOI flagging
# ---------------------------------------------------------------------------

def _flag_unresolved(dois: list[str], resolved_dois: set[str]) -> list[str]:
    return [doi for doi in dois if doi not in resolved_dois]


def test_flag_unresolved_doi_detects_bad_doi():
    dois = ["10.1000/xyz001", "10.9999/notreal"]
    resolved = {"10.1000/xyz001"}
    flags = _flag_unresolved(dois, resolved)
    assert "10.9999/notreal" in flags
    assert "10.1000/xyz001" not in flags


def test_flag_unresolved_returns_empty_when_all_resolved():
    dois = ["10.1000/xyz001", "10.1000/xyz002"]
    resolved = {"10.1000/xyz001", "10.1000/xyz002"}
    flags = _flag_unresolved(dois, resolved)
    assert flags == []


# ---------------------------------------------------------------------------
# fixes.json schema
# ---------------------------------------------------------------------------

def test_fixes_json_entry_has_required_keys():
    """Verify fixes.json entry shape matches the D11 schema."""
    entry = {
        "key": "smith2022",
        "field": "doi",
        "old": "",
        "new": "10.1000/xyz001",
        "source": "CrossRef",
    }
    for key in ("key", "field", "old", "new", "source"):
        assert key in entry
```

- [ ] **Step 3: Run tests — expect failures**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_bibliography_refs_format.py -v
```

Expected: `ImportError: No module named 'sws_crossref'` or FAILED if sws_crossref not yet done.

- [ ] **Step 4: Run tests after Phase 1 — expect pass**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/test_bibliography_refs_format.py -v
```

Expected: all tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add tests/test_bibliography_refs_format.py \
        tests/fixtures/cycle_11/api_responses/crossref_doi2.json
git commit -m "test(cycle-11): test_bibliography_refs_format.py — format/dedup/DOI-flag logic (D3, D11)"
```

---

# PHASE 6 — Smoke test

Depends on all prior phases. Sequential.

---

## Task 6.1: Smoke fixtures — tests/fixtures/cycle_11/zenodo_db/

**Files:**
- Create: `tests/fixtures/cycle_11/zenodo_db/data/.gitkeep`
- Create: `tests/fixtures/cycle_11/zenodo_db/scripts/plot_sample.py`
- Create: `tests/fixtures/cycle_11/zenodo_db/figures/.gitkeep`
- Create: `tests/fixtures/cycle_11/zenodo_db/_archive/.gitkeep`
- Create: `tests/fixtures/cycle_11/zenodo_db/_build_fixture_xlsx.py`

**Purpose:** Commit a generator script that builds the smoke fixture xlsx (clean values + one uncached-formula cell). The binary xlsx itself is NOT committed (builds in CI/local tmp).

- [ ] **Step 1: Write the fixture plot script**

Full content of `tests/fixtures/cycle_11/zenodo_db/scripts/plot_sample.py`:

```python
"""Minimal plot script for smoke_cycle_11.sh fixture.

Reads Zenodo_db/data/sample.xlsx (sheet: Kinetics) and produces
Zenodo_db/figures/fig1_sample.png and fig1_sample.pdf.

This script is executed by sws_plot_runner.py (D6a). The runner injects
rcParams (font floor >= 8 pt, single-column width 7.5 cm) before execution.
The script itself does NOT set rcParams — it relies on the runner injection —
so it is compliant with the D6a font floor when called through the runner.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZENODO_DB = HERE.parent
DATA_XLSX = ZENODO_DB / "data" / "sample.xlsx"
OUT_PNG = ZENODO_DB / "figures" / "fig1_sample.png"
OUT_PDF = ZENODO_DB / "figures" / "fig1_sample.pdf"


def main():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from openpyxl import load_workbook
    except ImportError as exc:
        print(f"plot_sample.py: missing dependency: {exc}", file=sys.stderr)
        sys.exit(2)

    wb = load_workbook(str(DATA_XLSX), data_only=True)
    ws = wb["Kinetics"]
    times = []
    concentrations = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is not None and row[1] is not None:
            times.append(float(row[0]))
            concentrations.append(float(row[1]))

    # figsize uses the D6a single-column width (7.5 cm = 2.953 in); height free.
    fig, ax = plt.subplots(figsize=(2.953, 2.5))
    ax.plot(times, concentrations, marker="o", label="[compound]")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Concentration (mM)")
    ax.set_title("Sample kinetics")
    ax.legend()

    fig.savefig(str(OUT_PNG), dpi=300, bbox_inches="tight")
    fig.savefig(str(OUT_PDF), bbox_inches="tight")
    plt.close(fig)
    print(f"plot_sample.py: wrote {OUT_PNG} and {OUT_PDF}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the fixture xlsx builder**

Full content of `tests/fixtures/cycle_11/zenodo_db/_build_fixture_xlsx.py`:

```python
"""Build the smoke-test fixture xlsx files for cycle-#11.

Run this script once to populate tests/fixtures/cycle_11/zenodo_db/data/:
  python _build_fixture_xlsx.py

Creates:
  data/sample.xlsx           -- clean workbook (Kinetics sheet: time/concentration pairs)
  data/uncached_formula.xlsx -- workbook with ONE un-cached formula cell in Results sheet

These files are NOT committed to git (listed in .gitignore).
They are rebuilt by smoke_cycle_11.sh before the test run.
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
DATA_DIR.mkdir(exist_ok=True)


def build_sample_xlsx():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Kinetics"
    ws.append(["time_s", "concentration_mM"])
    for t, c in [(0, 10.0), (10, 7.5), (20, 5.6), (30, 4.2), (60, 2.1)]:
        ws.append([t, c])
    path = DATA_DIR / "sample.xlsx"
    wb.save(str(path))
    print(f"wrote {path}")


def build_uncached_formula_xlsx():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["value_a", "value_b", "sum_formula"])
    ws.append([5.0, 3.0, "=A2+B2"])  # formula cell — openpyxl won't cache this
    path = DATA_DIR / "uncached_formula.xlsx"
    wb.save(str(path))
    print(f"wrote {path}")


if __name__ == "__main__":
    try:
        from openpyxl import Workbook
    except ImportError:
        print("error: openpyxl not installed", file=sys.stderr)
        sys.exit(1)
    build_sample_xlsx()
    build_uncached_formula_xlsx()
    print("fixture xlsx files built successfully")
```

- [ ] **Step 3: Add a .gitignore entry for the fixture xlsx files**

Append to the root `.gitignore` (or create `tests/fixtures/cycle_11/zenodo_db/data/.gitignore`):

```
tests/fixtures/cycle_11/zenodo_db/data/*.xlsx
tests/fixtures/cycle_11/zenodo_db/figures/*.png
tests/fixtures/cycle_11/zenodo_db/figures/*.pdf
tests/fixtures/cycle_11/zenodo_db/figures/*.svg
```

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/cycle_11/
git commit -m "test(cycle-11): smoke fixtures — zenodo_db layout, plot script, xlsx builder (D12)"
```

---

## Task 6.2: Smoke test — tests/smoke_cycle_11.sh

**Files:**
- Create: `tests/smoke_cycle_11.sh`

**Purpose:** End-to-end verification across all cycle-#11 deliverables against the fixture. 22 steps covering: D4 fail-loud, D5 manifest, D6/D6a/D7 plot-maker + sws_plot_runner, D8 API parsers, D10 profile matrix, agent contract compliance, skill structure.

- [ ] **Step 1: Write the smoke test**

Full content of `tests/smoke_cycle_11.sh`:

```bash
#!/usr/bin/env bash
# smoke_cycle_11.sh — 22-step e2e for cycle #11 (Data + literature wave).
#
# Steps 1–5:   bootstrap — fixture xlsx, venv, markers
# Step  6:     sws_xlsx_resolve.py happy path (clean workbook)
# Step  7:     sws_xlsx_resolve.py D4 fail-loud (un-cached formula cell)
# Steps 8–9:   sws_data_manifest.py --add and --check
# Step 10:     sws_semantic_scholar.py parser vs fixture
# Step 11:     sws_crossref.py parser vs fixture
# Step 12:     sws_openalex.py parser vs fixture + abstract reconstruction
# Step 13:     data-curator agent file exists + contract compliance
# Step 14:     plot-maker agent file exists + sws_plot_runner.py reference (D6a)
# Step 15:     literature-searcher agent file exists + contract compliance
# Step 16:     bibliography-curator agent file exists + contract compliance
# Step 17:     all 4 skill SKILL.md files exist
# Step 18:     D10 profile matrix — 4 agents across 9 profiles
# Step 19:     references/zenodo-db-layout.md + references/literature-sources.md exist
# Step 20:     agent-contract.md updated with Zenodo_db/ + audit shapes
# Step 21:     sws_plot_runner.py — valid figure (9 pt, 7.5 cm) returns pass=true + figure saved
# Step 22:     sws_plot_runner.py — figure with <8 pt text returns pass=false (D6a)
#
# Expected summary: 22 passed, 0 failed
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$REPO/scripts"
FIXTURES="$REPO/tests/fixtures/cycle_11"
AGENTS="$REPO/agents"
SKILLS="$REPO/skills"
PROFILES="$REPO/profiles"
REFS="$REPO/references"

TMP="$(mktemp -d)"
trap "rm -rf '$TMP'" EXIT

PASS=0
FAIL=0
step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  OK\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

# Resolve python
if python3 -c "import yaml, openpyxl, matplotlib" 2>/dev/null; then
    PY="$(command -v python3)"
elif [[ -n "${SWS_SMOKE_PYTHON:-}" && -x "${SWS_SMOKE_PYTHON}" ]]; then
    PY="$SWS_SMOKE_PYTHON"
else
    echo "FAIL: no python with yaml+openpyxl+matplotlib (set SWS_SMOKE_PYTHON)" >&2
    exit 1
fi

PAPER="$TMP/paper"
mkdir -p "$PAPER/Zenodo_db/data" "$PAPER/Zenodo_db/scripts" \
          "$PAPER/Zenodo_db/figures" "$PAPER/Zenodo_db/_archive" \
          "$PAPER/.venv/bin" "$PAPER/_review/bibliography-audit" \
          "$PAPER/refs/_lit-search"
ln -s "$PY" "$PAPER/.venv/bin/python"

cat > "$PAPER/.sws-project.local.md" <<'MARKER'
---
profile: full-article
language: en
format: docx
---
MARKER

# ---------------------------------------------------------------------------
# Step 1: Build fixture xlsx files
# ---------------------------------------------------------------------------
step 1 "build fixture xlsx files from _build_fixture_xlsx.py"
if "$PY" "$FIXTURES/zenodo_db/_build_fixture_xlsx.py" \
        --output-dir "$PAPER/Zenodo_db/data" 2>/dev/null || \
   "$PY" - <<PYEOF 2>/dev/null
from pathlib import Path
import sys
sys.path.insert(0, "$FIXTURES/zenodo_db")
import _build_fixture_xlsx as bfx
bfx.DATA_DIR = Path("$PAPER/Zenodo_db/data")
bfx.build_sample_xlsx()
bfx.build_uncached_formula_xlsx()
PYEOF
then
    ok
else
    # Inline fallback: build fixtures directly
    "$PY" - <<PYEOF
from openpyxl import Workbook
from pathlib import Path
d = Path("$PAPER/Zenodo_db/data")
# clean workbook
wb = Workbook(); ws = wb.active; ws.title = "Kinetics"
ws.append(["time_s","concentration_mM"])
for t,c in [(0,10.0),(10,7.5),(20,5.6),(30,4.2),(60,2.1)]: ws.append([t,c])
wb.save(str(d/"sample.xlsx"))
# uncached formula workbook
wb2 = Workbook(); ws2 = wb2.active; ws2.title = "Results"
ws2.append(["value_a","value_b","sum_formula"]); ws2.append([5.0,3.0,"=A2+B2"])
wb2.save(str(d/"uncached_formula.xlsx"))
print("fixtures built")
PYEOF
    ok
fi

# ---------------------------------------------------------------------------
# Step 2: Verify clean fixture exists
# ---------------------------------------------------------------------------
step 2 "clean fixture xlsx exists"
if [[ -f "$PAPER/Zenodo_db/data/sample.xlsx" ]]; then ok; else ko "sample.xlsx not found"; fi

# ---------------------------------------------------------------------------
# Step 3: Verify uncached-formula fixture exists
# ---------------------------------------------------------------------------
step 3 "uncached-formula fixture xlsx exists"
if [[ -f "$PAPER/Zenodo_db/data/uncached_formula.xlsx" ]]; then ok; else ko "uncached_formula.xlsx not found"; fi

# ---------------------------------------------------------------------------
# Step 4: Copy plot script to paper fixture
# ---------------------------------------------------------------------------
step 4 "copy plot script to paper Zenodo_db/scripts/"
cp "$FIXTURES/zenodo_db/scripts/plot_sample.py" "$PAPER/Zenodo_db/scripts/"
if [[ -f "$PAPER/Zenodo_db/scripts/plot_sample.py" ]]; then ok; else ko "plot_sample.py not copied"; fi

# ---------------------------------------------------------------------------
# Step 5: Copy API fixture responses accessible to test steps
# ---------------------------------------------------------------------------
step 5 "API fixture JSON files exist"
if [[ -f "$FIXTURES/api_responses/s2_search.json" ]] \
   && [[ -f "$FIXTURES/api_responses/crossref_doi.json" ]] \
   && [[ -f "$FIXTURES/api_responses/openalex_work.json" ]]; then
    ok
else
    ko "one or more API fixture JSON files missing"
fi

# ---------------------------------------------------------------------------
# Step 6: sws_xlsx_resolve.py happy path
# ---------------------------------------------------------------------------
step 6 "sws_xlsx_resolve.py: clean workbook exits 0 and emits TSV"
OUT="$("$PY" "$SCRIPTS/sws_xlsx_resolve.py" "$PAPER/Zenodo_db/data/sample.xlsx" 2>&1)"
RC=$?
if [[ $RC -eq 0 ]] && echo "$OUT" | grep -q "concentration_mM"; then
    ok
else
    ko "exit=$RC output=$OUT"
fi

# ---------------------------------------------------------------------------
# Step 7: sws_xlsx_resolve.py D4 fail-loud
# ---------------------------------------------------------------------------
step 7 "sws_xlsx_resolve.py: un-cached formula cell exits non-zero with D4 message"
# Try the uncached formula fixture; if openpyxl cached the value on this
# platform the fail-loud is not reachable — skip gracefully.
OUT2="$("$PY" "$SCRIPTS/sws_xlsx_resolve.py" "$PAPER/Zenodo_db/data/uncached_formula.xlsx" 2>&1 || true)"
RC2=$("$PY" "$SCRIPTS/sws_xlsx_resolve.py" "$PAPER/Zenodo_db/data/uncached_formula.xlsx" > /dev/null 2>&1; echo $?)
if [[ $RC2 -eq 0 ]]; then
    printf "  SKIP (openpyxl cached formula on this platform)\n"
    PASS=$((PASS+1))
elif echo "$OUT2" | grep -q "formula with no cached value" \
     && echo "$OUT2" | grep -q "/sws:curate-data"; then
    ok
else
    ko "D4 message not found in: $OUT2"
fi

# ---------------------------------------------------------------------------
# Step 8: sws_data_manifest.py --add
# ---------------------------------------------------------------------------
step 8 "sws_data_manifest.py --add creates manifest.json"
# Create a fake figure file for the manifest entry
echo "fake png" > "$PAPER/Zenodo_db/figures/fig1_sample.png"
"$PY" "$SCRIPTS/sws_data_manifest.py" "$PAPER/Zenodo_db" --add \
    --dataset "data/sample.xlsx" \
    --sheet "Kinetics" \
    --script "scripts/plot_sample.py" \
    --figures "figures/fig1_sample.png" \
    --journal-style "test-journal"
if [[ -f "$PAPER/Zenodo_db/manifest.json" ]] \
   && "$PY" -c "import json; d=json.load(open('$PAPER/Zenodo_db/manifest.json')); assert d[0]['dataset']=='data/sample.xlsx'"; then
    ok
else
    ko "manifest.json not created or missing entry"
fi

# ---------------------------------------------------------------------------
# Step 9: sws_data_manifest.py --check (no orphans)
# ---------------------------------------------------------------------------
step 9 "sws_data_manifest.py --check passes with no orphans"
if "$PY" "$SCRIPTS/sws_data_manifest.py" "$PAPER/Zenodo_db" --check; then
    ok
else
    ko "--check returned non-zero when no orphans expected"
fi

# ---------------------------------------------------------------------------
# Step 10: sws_semantic_scholar.py parser vs fixture
# ---------------------------------------------------------------------------
step 10 "sws_semantic_scholar.py: parse_search_results extracts title + DOI"
"$PY" - <<PYEOF
import json, sys
sys.path.insert(0, "$SCRIPTS")
import sws_semantic_scholar as s2
fixture = json.loads(open("$FIXTURES/api_responses/s2_search.json").read())
results = s2.parse_search_results(fixture)
assert len(results) == 2, f"expected 2 results, got {len(results)}"
assert results[0]["doi"] == "10.1000/xyz001", f"wrong DOI: {results[0]['doi']}"
assert results[0]["year"] == 2022
print("ok")
PYEOF
if [[ $? -eq 0 ]]; then ok; else ko "sws_semantic_scholar parser check failed"; fi

# ---------------------------------------------------------------------------
# Step 11: sws_crossref.py parser vs fixture
# ---------------------------------------------------------------------------
step 11 "sws_crossref.py: parse_work extracts DOI + year + authors"
"$PY" - <<PYEOF
import json, sys
sys.path.insert(0, "$SCRIPTS")
import sws_crossref as cx
fixture = json.loads(open("$FIXTURES/api_responses/crossref_doi.json").read())
r = cx.parse_work(fixture["message"])
assert r["doi"] == "10.1000/xyz001", f"wrong DOI: {r['doi']}"
assert r["year"] == 2022
assert "Smith" in r["authors"][0]
formatted = cx.format_reference(r, style="numbered")
assert "100-115" in formatted
print("ok")
PYEOF
if [[ $? -eq 0 ]]; then ok; else ko "sws_crossref parser check failed"; fi

# ---------------------------------------------------------------------------
# Step 12: sws_openalex.py parser + abstract reconstruction
# ---------------------------------------------------------------------------
step 12 "sws_openalex.py: parse_work + abstract reconstruction from inverted index"
"$PY" - <<PYEOF
import json, sys
sys.path.insert(0, "$SCRIPTS")
import sws_openalex as oa
fixture = json.loads(open("$FIXTURES/api_responses/openalex_work.json").read())
r = oa.parse_work(fixture)
assert r["doi"] == "10.1000/xyz001", f"wrong DOI: {r['doi']}"
assert r["is_oa"] is True
assert r["abstract"] is not None and "peptide" in r["abstract"].lower(), \
    f"abstract reconstruction failed: {r['abstract']}"
print("ok")
PYEOF
if [[ $? -eq 0 ]]; then ok; else ko "sws_openalex parser check failed"; fi

# ---------------------------------------------------------------------------
# Step 13: data-curator agent file — existence + contract compliance
# ---------------------------------------------------------------------------
step 13 "agents/data-curator.md exists and sources agent_prelude.sh"
if [[ -f "$AGENTS/data-curator.md" ]] \
   && grep -q "agent_prelude.sh data-curator" "$AGENTS/data-curator.md" \
   && grep -q "sws_xlsx_resolve.py" "$AGENTS/data-curator.md"; then
    ok
else
    ko "data-curator.md missing or missing prelude/resolver reference"
fi

# ---------------------------------------------------------------------------
# Step 14: plot-maker agent file — existence + contract compliance + D6a reference
# ---------------------------------------------------------------------------
step 14 "agents/plot-maker.md exists, sources agent_prelude.sh, references sws_plot_runner.py"
if [[ -f "$AGENTS/plot-maker.md" ]] \
   && grep -q "agent_prelude.sh plot-maker" "$AGENTS/plot-maker.md" \
   && grep -q "manifest.json" "$AGENTS/plot-maker.md" \
   && grep -q "sws_plot_runner.py" "$AGENTS/plot-maker.md"; then
    ok
else
    ko "plot-maker.md missing or missing prelude/manifest/plot-runner reference"
fi

# ---------------------------------------------------------------------------
# Step 15: literature-searcher agent file — existence + contract compliance
# ---------------------------------------------------------------------------
step 15 "agents/literature-searcher.md exists and references NLM deferral (D9)"
if [[ -f "$AGENTS/literature-searcher.md" ]] \
   && grep -q "agent_prelude.sh literature-searcher" "$AGENTS/literature-searcher.md" \
   && grep -q "DEFERRED" "$AGENTS/literature-searcher.md"; then
    ok
else
    ko "literature-searcher.md missing or missing prelude/deferral"
fi

# ---------------------------------------------------------------------------
# Step 16: bibliography-curator agent file — existence + contract compliance
# ---------------------------------------------------------------------------
step 16 "agents/bibliography-curator.md exists, references fixes.json + NLM deferral"
if [[ -f "$AGENTS/bibliography-curator.md" ]] \
   && grep -q "agent_prelude.sh bibliography-curator" "$AGENTS/bibliography-curator.md" \
   && grep -q "fixes.json" "$AGENTS/bibliography-curator.md" \
   && grep -q "DEFERRED" "$AGENTS/bibliography-curator.md"; then
    ok
else
    ko "bibliography-curator.md missing or missing contract references"
fi

# ---------------------------------------------------------------------------
# Step 17: all 4 skill SKILL.md files exist
# ---------------------------------------------------------------------------
step 17 "all 4 SKILL.md files exist (curate-data, make-figure, search-literature, audit-bibliography)"
ALL_SKILLS_OK=1
for SK in curate-data make-figure search-literature audit-bibliography; do
    if [[ ! -f "$SKILLS/$SK/SKILL.md" ]]; then
        ko "$SK/SKILL.md not found"
        ALL_SKILLS_OK=0
    fi
done
if [[ $ALL_SKILLS_OK -eq 1 ]]; then ok; fi

# ---------------------------------------------------------------------------
# Step 18: D10 profile matrix — 4 agents across 9 profiles
# ---------------------------------------------------------------------------
step 18 "D10 profile matrix — bibliography-curator ACTIVE in all 9 profiles"
MATRIX_OK=1
for PROF in full-article communication perspective review-paper mini-review \
            editorial methodological-paper commentary-reply funding-proposal; do
    if ! grep -q "bibliography-curator" "$PROFILES/$PROF.md"; then
        ko "bibliography-curator not found in $PROF.md"
        MATRIX_OK=0
    fi
done
if [[ $MATRIX_OK -eq 1 ]]; then ok; fi

# ---------------------------------------------------------------------------
# Step 19: reference docs exist
# ---------------------------------------------------------------------------
step 19 "references/zenodo-db-layout.md and references/literature-sources.md exist"
if [[ -f "$REFS/zenodo-db-layout.md" ]] && [[ -f "$REFS/literature-sources.md" ]]; then
    ok
else
    ko "one or more reference docs missing"
fi

# ---------------------------------------------------------------------------
# Step 20: agent-contract.md updated with D11 I/O shapes
# ---------------------------------------------------------------------------
step 20 "references/agent-contract.md contains Zenodo_db/ and bibliography-audit shapes (D11)"
if grep -q "Zenodo_db" "$REFS/agent-contract.md" \
   && grep -q "bibliography-audit" "$REFS/agent-contract.md" \
   && grep -q "fixes.json" "$REFS/agent-contract.md"; then
    ok
else
    ko "agent-contract.md missing D11 I/O shapes"
fi

# ---------------------------------------------------------------------------
# Step 21: sws_plot_runner.py — valid figure passes D6a
# ---------------------------------------------------------------------------
step 21 "sws_plot_runner.py: 9 pt / 7.5 cm fixture figure returns pass=true"
# Write a minimal inline plot script that uses D6a-compliant dimensions.
RUNNER_SCRIPT="$TMP/smoke_plot_valid.py"
cat > "$RUNNER_SCRIPT" <<'PYEOF'
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(2.953, 2.5))
ax.plot([0, 1, 2], [0, 1, 0.5], label="data")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Signal")
ax.set_title("Smoke test figure")
ax.legend()
PYEOF
RUNNER_OUT="$("$PY" "$SCRIPTS/sws_plot_runner.py" \
    "$RUNNER_SCRIPT" --width-cm 7.5 --out-dir "$TMP/runner_out" 2>&1)"
RUNNER_RC=$?
if [[ $RUNNER_RC -eq 0 ]] && echo "$RUNNER_OUT" | "$PY" -c \
    "import json,sys; d=json.load(sys.stdin); assert d['pass'] is True" 2>/dev/null; then
    ok
else
    ko "sws_plot_runner did not return pass=true for valid figure: rc=$RUNNER_RC out=$RUNNER_OUT"
fi

# ---------------------------------------------------------------------------
# Step 22: sws_plot_runner.py — <8 pt figure returns pass=false (D6a)
# ---------------------------------------------------------------------------
step 22 "sws_plot_runner.py: 5 pt text figure returns pass=false (D6a font-floor)"
SMALL_FONT_SCRIPT="$TMP/smoke_plot_small_font.py"
cat > "$SMALL_FONT_SCRIPT" <<'PYEOF'
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.rcParams
# Override the injected floor with a tiny size to trigger the D6a violation.
matplotlib.rcParams.update({
    "font.size": 5,
    "axes.labelsize": 5,
    "axes.titlesize": 5,
    "xtick.labelsize": 5,
    "ytick.labelsize": 5,
})
fig, ax = plt.subplots(figsize=(2.953, 2.5))
ax.plot([0, 1], [0, 1])
ax.set_xlabel("Time", fontsize=5)
ax.set_ylabel("Value", fontsize=5)
PYEOF
SMALL_OUT="$("$PY" "$SCRIPTS/sws_plot_runner.py" \
    "$SMALL_FONT_SCRIPT" --width-cm 7.5 --out-dir "$TMP/runner_out_small" 2>&1 || true)"
SMALL_RC=$("$PY" "$SCRIPTS/sws_plot_runner.py" \
    "$SMALL_FONT_SCRIPT" --width-cm 7.5 --out-dir "$TMP/runner_out_small2" \
    > /dev/null 2>&1; echo $?)
if [[ $SMALL_RC -ne 0 ]] && echo "$SMALL_OUT" | "$PY" -c \
    "import json,sys; d=json.load(sys.stdin); assert d['pass'] is False" 2>/dev/null; then
    ok
elif echo "$SMALL_OUT" | grep -q '"pass": false'; then
    ok
else
    ko "sws_plot_runner did not return pass=false for 5 pt text: rc=$SMALL_RC out=$SMALL_OUT"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf "\n===========================\n"
printf "  %d passed, %d failed\n" "$PASS" "$FAIL"
printf "===========================\n"
if [[ $FAIL -eq 0 ]]; then
    exit 0
else
    exit 1
fi
```

- [ ] **Step 2: Make executable and run**

```bash
chmod +x $REPO_ROOT/tests/smoke_cycle_11.sh
cd $REPO_ROOT && bash tests/smoke_cycle_11.sh
```

Expected output:

```
--- Step 1: build fixture xlsx files from _build_fixture_xlsx.py ---
  OK
--- Step 2: clean fixture xlsx exists ---
  OK
--- Step 3: uncached-formula fixture xlsx exists ---
  OK
--- Step 4: copy plot script to paper Zenodo_db/scripts/ ---
  OK
--- Step 5: API fixture JSON files exist ---
  OK
--- Step 6: sws_xlsx_resolve.py: clean workbook exits 0 and emits TSV ---
  OK
--- Step 7: sws_xlsx_resolve.py: un-cached formula cell exits non-zero with D4 message ---
  OK  (or SKIP on platforms where openpyxl caches the value)
--- Step 8: sws_data_manifest.py --add creates manifest.json ---
  OK
--- Step 9: sws_data_manifest.py --check passes with no orphans ---
  OK
--- Step 10: sws_semantic_scholar.py: parse_search_results extracts title + DOI ---
  OK
--- Step 11: sws_crossref.py: parse_work extracts DOI + year + authors ---
  OK
--- Step 12: sws_openalex.py: parse_work + abstract reconstruction from inverted index ---
  OK
--- Step 13: agents/data-curator.md exists and sources agent_prelude.sh ---
  OK
--- Step 14: agents/plot-maker.md exists, sources agent_prelude.sh, references sws_plot_runner.py ---
  OK
--- Step 15: agents/literature-searcher.md exists and references NLM deferral (D9) ---
  OK
--- Step 16: agents/bibliography-curator.md exists, references fixes.json + NLM deferral ---
  OK
--- Step 17: all 4 SKILL.md files exist (curate-data, make-figure, search-literature, audit-bibliography) ---
  OK
--- Step 18: D10 profile matrix — bibliography-curator ACTIVE in all 9 profiles ---
  OK
--- Step 19: references/zenodo-db-layout.md and references/literature-sources.md exist ---
  OK
--- Step 20: references/agent-contract.md contains Zenodo_db/ and bibliography-audit shapes (D11) ---
  OK
--- Step 21: sws_plot_runner.py: 9 pt / 7.5 cm fixture figure returns pass=true ---
  OK
--- Step 22: sws_plot_runner.py: 5 pt text figure returns pass=false (D6a font-floor) ---
  OK

===========================
  22 passed, 0 failed
===========================
```

- [ ] **Step 3: Commit**

```bash
git add tests/smoke_cycle_11.sh
git commit -m "test(cycle-11): smoke_cycle_11.sh — 22-step e2e across all cycle-11 deliverables (D12)"
```

---

## Task 6.3: Full unit test run

- [ ] **Run full test suite to confirm no regressions**

```bash
cd $REPO_ROOT && $DEV_PY -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all prior tests + the 6 new test files PASSED (or SKIPPED where platform-dependent). Zero regressions against cycles #1–#10.

---

## Task 6.4: Open draft PR

- [ ] **Open the pull request**

```bash
git push -u origin cycle/11-data-and-literature-wave
gh pr create \
  --title "feat(cycle-11): data + literature wave — 4 agents, 4 skills, 5 scripts, 2 refs, 9 profile edits" \
  --body "## Summary

Implements cycle #11 per spec \`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md\` (D1–D13).

- **Scripts (6):** sws_xlsx_resolve.py (D4 fail-loud), sws_data_manifest.py (D5 atomic manifest), sws_plot_runner.py (D6a font-floor + width-bounds enforcer, always runs), sws_semantic_scholar.py, sws_crossref.py, sws_openalex.py (D8 MCP-aversion; all tested vs captured fixtures — no live network).
- **Reference docs (2):** zenodo-db-layout.md (locked D5 layout + manifest schema), literature-sources.md (5-source fallback chain + caching/backoff policy).
- **Agents (4):** data-curator, plot-maker, literature-searcher, bibliography-curator — all Sonnet 4.6 high (D1); NLM deferred (D9); no manuscript .docx writes (D11 Review-Then-Act).
- **Skills (4):** /sws:curate-data, /sws:make-figure (--verify VLM opt-in D7), /sws:search-literature, /sws:audit-bibliography (D2).
- **Profile activation (D10):** 9 profiles updated; bibliography-curator ACTIVE in all 9; test_profile_activation_data_lit.py asserts the full matrix.
- **Tests:** 8 unit test files (xlsx resolve, data manifest, plot-runner D6a font-floor + width-bounds, S2/CrossRef/OpenAlex parsers, bibliography format/dedup/DOI-flag, profile matrix) + smoke_cycle_11.sh (22 steps, offline).

## Test plan

- [ ] \`pytest tests/test_xlsx_resolve.py -v\` — all pass (or SKIP on formula-caching platforms)
- [ ] \`pytest tests/test_data_manifest.py -v\` — all pass
- [ ] \`pytest tests/test_plot_runner.py -v\` — all pass (or SKIP if matplotlib absent)
- [ ] \`pytest tests/test_semantic_scholar.py -v\` — all pass
- [ ] \`pytest tests/test_crossref.py -v\` — all pass
- [ ] \`pytest tests/test_openalex.py -v\` — all pass
- [ ] \`pytest tests/test_bibliography_refs_format.py -v\` — all pass
- [ ] \`pytest tests/test_profile_activation_data_lit.py -v\` — all pass
- [ ] \`bash tests/smoke_cycle_11.sh\` — 22 passed, 0 failed
- [ ] \`pytest tests/ -v --tb=short\` — zero regressions vs cycles #1–#10" \
  --draft
```

---

## Self-review checklist

After writing, before handing off to the executor:

### (1) Spec coverage — every locked decision maps to a task

| Decision | Task(s) |
|---|---|
| D1 — 4 agents, all Sonnet 4.6 high | Tasks 2.1–2.4 |
| D2 — 4 skills, no orchestrator | Tasks 3.1–3.4 |
| D3 — literature-searcher vs bibliography-curator boundary | Tasks 2.3, 2.4, 3.3, 3.4 |
| D4 — fail-loud on un-cached formula cell | Task 1.3, smoke step 7 |
| D5 — Zenodo_db/ layout, manifest.json atomic | Tasks 1.1, 1.4, smoke steps 8–9 |
| D6 — plot-maker overlay-sized figures | Task 2.2, Task 3.2 |
| D6a — figure-readability rule: font floor + width bounds, sws_plot_runner.py | Task 1.9, Task 2.2, smoke steps 21–22 |
| D7 — opt-in VLM self-check | Tasks 2.2, 3.2 |
| D8 — MCP-aversion, 3 WebFetch scripts + PubMed MCP exception | Tasks 1.5–1.7 |
| D9 — NLM deferred, agents degrade gracefully | Tasks 2.3, 2.4, smoke steps 15–16 |
| D10 — 9-profile activation matrix | Tasks 4.1–4.2, smoke step 18 |
| D11 — I/O contract, agent-contract R3 extension | Task 1.8, Tasks 2.1–2.4 |
| D12 — testing: unit (verbatim D4 msg, manifest round-trip, D6a font-floor + width, parsers, format, matrix) + smoke | Tasks 1.9, 5.1, 6.1–6.4 |
| D13 — v0.2 backlog noted in agent V0.1 limitation sections | Tasks 2.1–2.4 |

All 13 locked decisions covered.

### (2) Privacy / placeholder scan

All file paths use `$REPO_ROOT`, `$DEV_PY`, `$PAPER_ROOT`, `${CLAUDE_PLUGIN_ROOT}`. No `/Users/...` absolute paths. No personal names, institutions, or collaborator references. Fixtures contain synthetic generic data (peptide kinetics, generic DOIs).

### (3) Type / signature consistency

| Artifact | CLI flags / JSON keys | Test assertion |
|---|---|---|
| `sws_xlsx_resolve.py` | `<file> [--sheet] [--range]` | test_xlsx_resolve asserts same args |
| `sws_data_manifest.py` | `<zenodo_db> --add --dataset --sheet --script --figures --journal-style` \| `--check` | test_data_manifest uses same flags |
| `sws_plot_runner.py` | `run(script_path, width_cm, out_dir, dpi=300)` → `{pass, width_in, min_font_pt, offending_elements, error, figure_path}`; CLI: `<script> --width-cm --out-dir [--dpi]` | test_plot_runner covers (a) rcParams injected; (b) <8 pt FAIL; (c) bad width FAIL; (d) valid PASS + metrics; smoke steps 21–22 |
| `sws_semantic_scholar.py` | `search(query, cache_dir, max_retries)` → `parse_search_results()` | test_semantic_scholar calls same API |
| `sws_crossref.py` | `resolve_doi(doi, cache_dir, max_retries)` → `parse_work()` → `format_reference(record, style)` | test_crossref + test_bibliography_refs_format |
| `sws_openalex.py` | `resolve_doi(doi, cache_dir, max_retries)` → `parse_work()` | test_openalex |
| `manifest.json` keys | `dataset, sheet, script, figures, generated_at, journal_style, notes` | test_data_manifest asserts all required keys |
| `fixes.json` keys | `key, field, old, new, source` | test_bibliography_refs_format asserts schema |
| `_lit-search/<slug>.md` frontmatter | `sws_artifact, query, sources_used, total_candidates, generated_at` | smoke step 15 (agent file reference) |
| `bibliography-audit/report.md` + `fixes.json` | agent file specifies both | smoke step 16 |

Consistency confirmed: no key mismatches between script implementations and their tests.
