"""Zotero-manifest export per spec D16."""
import json
import subprocess
import sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from sws_extract_zotero_manifest import build_manifest, ManifestBuildError

FIXTURE = REPO / "tests" / "fixtures" / "zotero_collections" / "perspective_collection.json"


def _load_fixture():
    return json.loads(FIXTURE.read_text())


def test_build_manifest_basic_fields():
    data = _load_fixture()
    manifest = build_manifest(data)
    # Frontmatter
    assert manifest["frontmatter"]["item_count"] == 3
    assert "exported_from" in manifest["frontmatter"]
    # Items
    assert len(manifest["items"]) == 3
    smith = manifest["items"][0]
    assert smith["key"] == "ABCDEFGH"
    assert smith["first_author"] == "Smith"
    assert smith["year"] == "2023"
    assert smith["doi"] == "10.1021/jacs.3c00001"


def test_handles_missing_doi_gracefully():
    data = _load_fixture()
    manifest = build_manifest(data)
    vanderheijden = manifest["items"][2]
    assert vanderheijden["doi"] is None
    assert vanderheijden["first_author"] == "vanderHeijden"


def test_year_extracted_from_partial_date():
    data = _load_fixture()
    manifest = build_manifest(data)
    garcia = manifest["items"][1]
    assert garcia["year"] == "2024"  # from "2024-03"


def test_token_budget_cap_truncates(tmp_path):
    # Fake oversized collection
    big_data = _load_fixture()
    big_data["items"] = big_data["items"] * 100  # 300 items
    manifest = build_manifest(big_data, cap_token_budget=500)
    # Cap is approximate; just verify it ran and truncated something
    assert manifest["frontmatter"]["item_count"] < 300
    assert manifest["frontmatter"]["truncated"] is True


def test_empty_collection_returns_empty_manifest():
    manifest = build_manifest({"collection": "empty", "items": []})
    assert manifest["frontmatter"]["item_count"] == 0
    assert manifest["items"] == []


def test_creator_without_lastname_skipped():
    data = {"collection": "test", "items": [
        {"key": "X1", "creators": [{"creatorType": "editor"}], "date": "2020", "title": "Anon"}
    ]}
    with pytest.raises(ManifestBuildError):
        build_manifest(data)


def test_cli_writes_manifest_md(tmp_path):
    """End-to-end: CLI consumes JSON, writes _lit/zotero-manifest.md."""
    paper = tmp_path / "paper"
    paper.mkdir()
    cp = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "sws_extract_zotero_manifest.py"),
         "--input", str(FIXTURE), "--paper", str(paper)],
        capture_output=True, text=True
    )
    assert cp.returncode == 0, cp.stderr
    manifest_path = paper / "_lit" / "zotero-manifest.md"
    assert manifest_path.exists()
    content = manifest_path.read_text()
    assert "item_count: 3" in content
    assert "first_author: Smith" in content
    assert "doi: 10.1021/jacs.3c00001" in content
