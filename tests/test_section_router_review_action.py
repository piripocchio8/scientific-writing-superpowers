"""Unit test for the section-router review action (cycle-09 D14)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from sws_section_router import route_section, RouteError, _VALID_ACTIONS  # noqa: E402


def test_review_action_routes_to_peer_reviewer_for_any_section():
    for section in ("introduction", "methods", "results", "discussion", "abstract", "any-name"):
        assert route_section(section, "full-article", action="review") == "peer-reviewer"


def test_review_action_routes_to_peer_reviewer_for_funding_proposal():
    assert route_section("vision", "funding-proposal", action="review") == "peer-reviewer"
    assert route_section("budget", "funding-proposal", action="review") == "peer-reviewer"


def test_review_is_in_valid_actions():
    assert "review" in _VALID_ACTIONS


def test_unknown_action_raises():
    with pytest.raises(RouteError):
        route_section("intro", "full-article", action="autopilot")


def test_existing_actions_still_work():
    # Regression: cycle-08 actions unchanged
    assert route_section("intro", "full-article", action="revise") == "reviser-fast"
    assert route_section("intro", "full-article", action="consistency") == "consistency-checker"
    assert route_section("intro", "full-article", action="style") == "style-enforcer"
    assert route_section("intro", "full-article", action="lint") == "script:sws_lint_ai_tells.py"
    assert route_section("intro", "full-article", action="draft") == "drafter-flagship"
