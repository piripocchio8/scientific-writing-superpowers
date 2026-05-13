"""Citation-key parsing per spec D17.

Format: [<FirstAuthor><Year>; <prefix>:<id>] where prefix in {doi, zotero}.
Placeholder: [CITATION_NEEDED: <free-text claim>].
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sws_citation_key import parse_citation_key, ParseError, PLACEHOLDER_RE


def test_parses_doi_form():
    result = parse_citation_key("[Smith2023; doi:10.1021/jacs.3c00001]")
    assert result == {
        "first_author": "Smith",
        "year": "2023",
        "id_kind": "doi",
        "id_value": "10.1021/jacs.3c00001",
    }


def test_parses_zotero_form():
    result = parse_citation_key("[Garcia2024; zotero:ABCDEFGH]")
    assert result == {
        "first_author": "Garcia",
        "year": "2024",
        "id_kind": "zotero",
        "id_value": "ABCDEFGH",
    }


def test_parses_compound_first_author():
    result = parse_citation_key("[vanderHeijden2022; doi:10.xxxx]")
    assert result["first_author"] == "vanderHeijden"
    assert result["year"] == "2022"


def test_rejects_missing_prefix():
    with pytest.raises(ParseError):
        parse_citation_key("[Smith2023; 10.1021/jacs.3c00001]")


def test_rejects_unknown_prefix():
    with pytest.raises(ParseError):
        parse_citation_key("[Smith2023; pmid:12345]")


def test_rejects_no_year():
    with pytest.raises(ParseError):
        parse_citation_key("[Smith; doi:10.xxxx]")


def test_rejects_no_brackets():
    with pytest.raises(ParseError):
        parse_citation_key("Smith2023; doi:10.xxxx")


def test_placeholder_regex_matches():
    text = "...as shown previously [CITATION_NEEDED: Semaglutide is a GLP-1 agonist]."
    matches = PLACEHOLDER_RE.findall(text)
    assert len(matches) == 1
    assert "Semaglutide is a GLP-1 agonist" in matches[0]


def test_placeholder_does_not_match_real_citation():
    text = "...as shown previously [Smith2023; doi:10.xxxx]."
    matches = PLACEHOLDER_RE.findall(text)
    assert matches == []
