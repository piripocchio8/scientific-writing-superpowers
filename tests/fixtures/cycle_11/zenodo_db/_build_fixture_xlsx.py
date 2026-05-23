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
