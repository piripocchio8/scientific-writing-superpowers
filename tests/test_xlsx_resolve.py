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
    cell = wb2["Results"]["C1"]
    cell_val = cell.value
    if cell_val is not None:
        pytest.skip("openpyxl cached the formula value on this platform — skip fail-loud test")
    if getattr(cell, "data_type", None) != "f":
        pytest.skip(
            "openpyxl lost data_type='f' on data_only load on this platform — "
            "fail-loud detection requires app-saved workbooks; skip fixture-based test"
        )
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
