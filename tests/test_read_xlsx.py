"""sws_read_xlsx.py — openpyxl wrapper used by drafting + budget agents.

Cycle #7 hotfix (D22). Mirrors sws_read_docx.py: tests build the fixture
inline with openpyxl rather than committing a binary fixture file.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "sws_read_xlsx.py"


def _make_fixture(tmp_path: Path) -> Path:
    """Build a small xlsx with two sheets; sheet2 has a formula cell."""
    from openpyxl import Workbook

    wb = Workbook()
    sheet1 = wb.active
    sheet1.title = "Data"
    sheet1["A1"] = "compound"
    sheet1["B1"] = "yield_pct"
    sheet1["A2"] = "peptide-1"
    sheet1["B2"] = 72
    sheet1["A3"] = "peptide-2"
    sheet1["B3"] = 65

    sheet2 = wb.create_sheet("Calc")
    sheet2["A1"] = 10
    sheet2["B1"] = 32
    sheet2["C1"] = "=A1+B1"   # formula source

    fixture = tmp_path / "fixture.xlsx"
    wb.save(str(fixture))
    return fixture


def _run(args, expect_zero: bool = True):
    cp = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True
    )
    if expect_zero:
        assert cp.returncode == 0, cp.stderr
    return cp


def test_full_read_emits_every_sheet(tmp_path):
    fixture = _make_fixture(tmp_path)
    cp = _run([str(fixture)])
    out = cp.stdout
    assert "Data" in out
    assert "Calc" in out
    assert "compound\tyield_pct" in out
    assert "peptide-1\t72" in out
    assert "peptide-2\t65" in out


def test_sheet_scope_limits_to_one_sheet(tmp_path):
    fixture = _make_fixture(tmp_path)
    cp = _run([str(fixture), "--sheet", "Data"])
    out = cp.stdout
    assert "compound\tyield_pct" in out
    assert "peptide-1\t72" in out
    # The Calc sheet header should not show up.
    assert "Calc" not in out


def test_range_scope_limits_to_specified_cells(tmp_path):
    fixture = _make_fixture(tmp_path)
    cp = _run([str(fixture), "--sheet", "Data", "--range", "A2:A3"])
    out = cp.stdout
    assert "peptide-1" in out
    assert "peptide-2" in out
    # Header row is outside A2:A3, so it should be absent.
    assert "compound" not in out
    # Yield column is outside A2:A3, so it should be absent too.
    assert "72" not in out


def test_show_formulas_emits_formula_source_not_value(tmp_path):
    fixture = _make_fixture(tmp_path)
    cp = _run([str(fixture), "--sheet", "Calc", "--show-formulas"])
    out = cp.stdout
    # The formula source is what we want to preserve for the data-authority
    # workflow (CLAUDE.md item #4) — not the cached numeric value.
    assert "=A1+B1" in out


def test_default_does_not_show_formula_source(tmp_path):
    """Without --show-formulas, formula cells render their cached value."""
    fixture = _make_fixture(tmp_path)
    cp = _run([str(fixture), "--sheet", "Calc"])
    out = cp.stdout
    # The formula source must not leak into the default output.
    assert "=A1+B1" not in out


def test_missing_file_exits_2(tmp_path):
    cp = _run([str(tmp_path / "missing.xlsx")], expect_zero=False)
    assert cp.returncode == 2


def test_malformed_file_exits_3(tmp_path):
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"not a real xlsx file at all")
    cp = _run([str(bad)], expect_zero=False)
    assert cp.returncode == 3
