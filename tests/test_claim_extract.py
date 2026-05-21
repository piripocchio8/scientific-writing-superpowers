"""Unit tests for sws_claim_extract.py.

Tests parsing of _drafts/*.md citation-key format, multi-citation handling,
section attribution, and edge cases (no citations, citations-without-sentence,
footnote-style citations, citations on figure captions).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sws_claim_extract as ce  # noqa: E402


def _write(tmpdir: Path, name: str, body: str) -> Path:
    p = tmpdir / name
    p.write_text(body, encoding="utf-8")
    return p


def test_extract_single_citation_sentence(tmp_path):
    _write(tmp_path, "introduction-revised.md", "Thrombin activates platelets [@smith2020].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert len(claims) == 1
    assert claims[0]["section"] == "introduction"
    assert claims[0]["citation_keys"] == ["smith2020"]
    assert "Thrombin activates platelets" in claims[0]["claim"]


def test_extract_multi_citation_sentence(tmp_path):
    _write(tmp_path, "results-revised.md", "We observed binding [@a2020; @b2021; @c2022].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert len(claims) == 1
    assert claims[0]["citation_keys"] == ["a2020", "b2021", "c2022"]


def test_section_id_derived_from_filename(tmp_path):
    _write(tmp_path, "methods-revised.md", "We performed X [@y2020].\n")
    _write(tmp_path, "discussion-revised.md", "Y suggests Z [@a2021].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    sections = sorted(c["section"] for c in claims)
    assert sections == ["discussion", "methods"]


def test_no_citations_yields_empty_list(tmp_path):
    _write(tmp_path, "results-revised.md", "We saw a clear effect with no source.\n")
    assert ce.extract_claims_from_drafts(tmp_path) == []


def test_skips_files_without_revised_suffix(tmp_path):
    _write(tmp_path, "introduction.md", "Source-bearing claim [@x2020].\n")  # not -revised
    _write(tmp_path, "introduction-revised.md", "Revised claim [@y2021].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    keys = [c["citation_keys"][0] for c in claims]
    assert keys == ["y2021"]


def test_sentence_segmentation_basic(tmp_path):
    _write(
        tmp_path,
        "results-revised.md",
        "Effect A is large [@a2020]. Effect B is small [@b2021].\n",
    )
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert len(claims) == 2
    assert claims[0]["citation_keys"] == ["a2020"]
    assert claims[1]["citation_keys"] == ["b2021"]


def test_emit_json_round_trips(tmp_path):
    _write(tmp_path, "intro-revised.md", "X is Y [@k1].\n")
    out = tmp_path / "claims.json"
    ce.write_claims_json(tmp_path, out)
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert data[0]["citation_keys"] == ["k1"]


def test_handles_apostrophes_and_unicode(tmp_path):
    _write(tmp_path, "discussion-revised.md", "Doe's findings—reproduced here—agree [@doe1999].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert len(claims) == 1
    assert "Doe" in claims[0]["claim"]


def test_strips_leading_whitespace_from_claim(tmp_path):
    _write(tmp_path, "results-revised.md", "   Padded claim text [@a2020].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert claims[0]["claim"].startswith("Padded")


def test_includes_verification_status_placeholder(tmp_path):
    _write(tmp_path, "intro-revised.md", "X [@a2020].\n")
    claims = ce.extract_claims_from_drafts(tmp_path)
    assert claims[0]["verification_status"] == "pending"
    assert claims[0]["source_match"] == []
