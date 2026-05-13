"""Outline baseline-checksum sidecar logic per spec D3."""
import hashlib
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sws_outline_baseline import (
    sidecar_path, write_baseline, baseline_matches, BaselineMissing
)


@pytest.fixture
def tmp_outline(tmp_path):
    outline_dir = tmp_path / "_outline"
    outline_dir.mkdir()
    outline = outline_dir / "outline.md"
    outline.write_text("---\nprofile: perspective\n---\n# body\n")
    return outline


def test_sidecar_path_is_dotted(tmp_outline):
    assert sidecar_path(tmp_outline).name == ".outline-baseline.sha256"
    assert sidecar_path(tmp_outline).parent == tmp_outline.parent


def test_write_baseline_creates_sidecar(tmp_outline):
    write_baseline(tmp_outline)
    sc = sidecar_path(tmp_outline)
    assert sc.exists()
    expected = hashlib.sha256(tmp_outline.read_bytes()).hexdigest()
    assert sc.read_text().strip() == expected


def test_baseline_matches_after_write(tmp_outline):
    write_baseline(tmp_outline)
    assert baseline_matches(tmp_outline) is True


def test_baseline_does_not_match_after_user_edit(tmp_outline):
    write_baseline(tmp_outline)
    tmp_outline.write_text(tmp_outline.read_text() + "\nuser edit\n")
    assert baseline_matches(tmp_outline) is False


def test_baseline_matches_raises_when_missing(tmp_outline):
    with pytest.raises(BaselineMissing):
        baseline_matches(tmp_outline)


def test_write_baseline_overwrites(tmp_outline):
    write_baseline(tmp_outline)
    tmp_outline.write_text("new content")
    write_baseline(tmp_outline)
    assert baseline_matches(tmp_outline) is True
