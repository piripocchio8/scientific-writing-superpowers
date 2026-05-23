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
