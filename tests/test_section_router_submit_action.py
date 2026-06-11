"""Unit test for the section-router 'submit' axis (cycle-12 D17)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from sws_section_router import route_section, RouteError, _VALID_ACTIONS  # noqa: E402


def test_submit_in_valid_actions():
    assert "submit" in _VALID_ACTIONS


def test_submit_cover_letter_routes_to_write_cover_letter_skill():
    assert route_section("cover-letter", "full-article", action="submit") == "skill:/sws:write-cover-letter"
    # underscore alias
    assert route_section("cover_letter", "full-article", action="submit") == "skill:/sws:write-cover-letter"


def test_submit_response_routes_to_respond_to_reviewers_skill():
    assert route_section("response", "full-article", action="submit") == "skill:/sws:respond-to-reviewers"


def test_submit_disclosure_routes_to_disclose_skill():
    assert route_section("disclosure", "full-article", action="submit") == "skill:/sws:disclose-ai-usage"
    # alias
    assert route_section("ai-disclosure", "full-article", action="submit") == "skill:/sws:disclose-ai-usage"


def test_submit_unknown_id_raises():
    with pytest.raises(RouteError):
        route_section("budget", "full-article", action="submit")


def test_submit_is_profile_independent():
    # Same routes regardless of profile.
    assert route_section("cover-letter", "funding-proposal", action="submit") == "skill:/sws:write-cover-letter"
    assert route_section("disclosure", "editorial", action="submit") == "skill:/sws:disclose-ai-usage"


def test_existing_actions_regression_unchanged():
    # cycle-07 / cycle-08 / cycle-09 actions still route as before.
    assert route_section("intro", "full-article", action="draft") == "drafter-flagship"
    assert route_section("intro", "full-article", action="revise") == "reviser-fast"
    assert route_section("intro", "full-article", action="consistency") == "consistency-checker"
    assert route_section("intro", "full-article", action="style") == "style-enforcer"
    assert route_section("intro", "full-article", action="lint") == "script:sws_lint_ai_tells.py"
    assert route_section("intro", "full-article", action="review") == "peer-reviewer"
