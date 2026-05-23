"""Verify cycle-10 D14 activation matrix: style-calibrator active in 7 profiles,
inactive in editorial + commentary-reply."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

ACTIVE_PROFILES = [
    "full-article",
    "communication",
    "perspective",
    "review-paper",
    "mini-review",
    "methodological-paper",
    "funding-proposal",
]
INACTIVE_PROFILES = ["editorial", "commentary-reply"]


def _load_frontmatter(profile_id: str) -> dict:
    text = (PROFILES_DIR / f"{profile_id}.md").read_text()
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


@pytest.mark.parametrize("profile_id", ACTIVE_PROFILES)
def test_calibrator_active(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "style-calibrator" in active, f"style-calibrator must be ACTIVE in {profile_id}"
    assert "style-calibrator" not in inactive


@pytest.mark.parametrize("profile_id", INACTIVE_PROFILES)
def test_calibrator_inactive(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "style-calibrator" in inactive, f"style-calibrator must be INACTIVE in {profile_id}"
    assert "style-calibrator" not in active
