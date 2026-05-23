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
