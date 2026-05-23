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
