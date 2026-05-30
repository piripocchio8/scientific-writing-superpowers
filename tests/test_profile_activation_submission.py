"""Verify cycle-12 D8 activation matrix for cover-letter-writer +
response-to-reviewers across all 9 profiles."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

ALL_PROFILES = [
    "full-article",
    "communication",
    "perspective",
    "review-paper",
    "mini-review",
    "editorial",
    "methodological-paper",
    "commentary-reply",
    "funding-proposal",
]

# D8 matrix:
COVER_LETTER_ACTIVE = [
    "full-article", "communication", "perspective", "review-paper",
    "mini-review", "methodological-paper", "editorial", "commentary-reply",
]
COVER_LETTER_INACTIVE = ["funding-proposal"]

RESPONSE_ACTIVE = [
    "full-article", "communication", "perspective", "review-paper",
    "mini-review", "methodological-paper", "commentary-reply",
]
RESPONSE_INACTIVE = ["editorial", "funding-proposal"]


def _load_frontmatter(profile_id: str) -> dict:
    text = (PROFILES_DIR / f"{profile_id}.md").read_text()
    assert text.startswith("---\n"), f"{profile_id}.md missing YAML frontmatter"
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


# ---------------------------------------------------------------------------
# cover-letter-writer
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", COVER_LETTER_ACTIVE)
def test_cover_letter_writer_active(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "cover-letter-writer" in active, \
        f"cover-letter-writer must be ACTIVE in {profile_id}"
    assert "cover-letter-writer" not in inactive


@pytest.mark.parametrize("profile_id", COVER_LETTER_INACTIVE)
def test_cover_letter_writer_inactive(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "cover-letter-writer" not in active, \
        f"cover-letter-writer must be INACTIVE in {profile_id}"
    assert "cover-letter-writer" in inactive, \
        f"cover-letter-writer must be listed in agents_inactive for {profile_id}"


# ---------------------------------------------------------------------------
# response-to-reviewers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", RESPONSE_ACTIVE)
def test_response_to_reviewers_active(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "response-to-reviewers" in active, \
        f"response-to-reviewers must be ACTIVE in {profile_id}"
    assert "response-to-reviewers" not in inactive


@pytest.mark.parametrize("profile_id", RESPONSE_INACTIVE)
def test_response_to_reviewers_inactive(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "response-to-reviewers" not in active, \
        f"response-to-reviewers must be INACTIVE in {profile_id}"
    assert "response-to-reviewers" in inactive, \
        f"response-to-reviewers must be listed in agents_inactive for {profile_id}"


# ---------------------------------------------------------------------------
# Regression: pre-cycle-12 agents unchanged in lists
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", ALL_PROFILES)
def test_bibliography_curator_still_active_everywhere(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    assert "bibliography-curator" in active, \
        f"regression: bibliography-curator must still be ACTIVE in {profile_id}"
