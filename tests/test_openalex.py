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
