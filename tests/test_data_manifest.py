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
