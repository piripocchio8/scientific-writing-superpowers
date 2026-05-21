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
        {"id": "p1", "section": "introduction", "text": "Thrombin activates platelets via PAR1 cleavage of the extracellular tethered ligand domain in human coagulation cascade studies under controlled laboratory conditions over multiple replicates."}
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
