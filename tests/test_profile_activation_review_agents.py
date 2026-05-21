"""Verify cycle-09 D10 activation matrix across all 9 profiles."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

PUBLICATION_PROFILES = [
    "full-article",
    "communication",
    "perspective",
    "review-paper",
    "mini-review",
    "editorial",
    "methodological-paper",
    "commentary-reply",
]

ALL_PROFILES = PUBLICATION_PROFILES + ["funding-proposal"]


def _load_frontmatter(profile_id: str) -> dict:
    text = (PROFILES_DIR / f"{profile_id}.md").read_text()
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    yaml_block = text[4:end]
    return yaml.safe_load(yaml_block)


@pytest.mark.parametrize("profile_id", ALL_PROFILES)
def test_peer_reviewer_active_in_all_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "peer-reviewer" in active, f"peer-reviewer must be ACTIVE in {profile_id}"
    assert "peer-reviewer" not in inactive


@pytest.mark.parametrize("profile_id", PUBLICATION_PROFILES)
def test_claim_verifier_active_in_publication_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "claim-verifier" in active, f"claim-verifier must be ACTIVE in {profile_id}"
    assert "claim-verifier" not in inactive


@pytest.mark.parametrize("profile_id", PUBLICATION_PROFILES)
def test_bibliography_fidelity_active_in_publication_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "bibliography-fidelity-checker" in active, f"bibliography-fidelity-checker must be ACTIVE in {profile_id}"
    assert "bibliography-fidelity-checker" not in inactive


def test_claim_verifier_inactive_in_funding_proposal():
    fm = _load_frontmatter("funding-proposal")
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "claim-verifier" in inactive
    assert "claim-verifier" not in active


def test_bibliography_fidelity_inactive_in_funding_proposal():
    fm = _load_frontmatter("funding-proposal")
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "bibliography-fidelity-checker" in inactive
    assert "bibliography-fidelity-checker" not in active
