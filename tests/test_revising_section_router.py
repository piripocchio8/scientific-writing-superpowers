"""Tests for the cycle-#8 action axis of sws_section_router.

Covers: action=draft (default/omitted), action=revise, action=consistency,
action=style, action=lint, unknown-action error, and backwards-compat
smoke checks against the cycle-#7 routes tested in test_section_to_agent_map.py.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sws_section_router import route_section, RouteError  # noqa: E402


# ---------------------------------------------------------------------------
# action=draft (explicit)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section_id, profile, expected_agent", [
    ("intro", "full-article", "drafter-flagship"),
    ("methods", "full-article", "methods-writer"),
    ("results", "full-article", "drafter-fast"),
    ("figure_caption", "full-article", "caption-writer"),
    ("budget", "funding-proposal", "proposal-budget-helper"),
    ("vision", "funding-proposal", "drafter-flagship"),
])
def test_draft_action_explicit_returns_cycle7_routes(section_id, profile, expected_agent):
    assert route_section(section_id, profile=profile, action="draft") == expected_agent


# ---------------------------------------------------------------------------
# action=draft omitted (default) — backwards-compat smoke
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section_id, profile, expected_agent", [
    ("intro", "full-article", "drafter-flagship"),
    ("experimental", "full-article", "methods-writer"),
    ("results and discussion", "full-article", "drafter-flagship"),
])
def test_draft_action_omitted_default_matches_cycle7(section_id, profile, expected_agent):
    """Omitting action= must give the same result as action='draft'."""
    assert route_section(section_id, profile=profile) == expected_agent


# ---------------------------------------------------------------------------
# action=revise
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section_id", [
    "intro", "introduction", "abstract", "discussion",
    "conclusion", "conclusions", "methods", "experimental",
    "experimental section", "results", "results and discussion",
    "figure_caption",
])
def test_revise_known_sections_return_reviser_fast(section_id):
    assert route_section(section_id, profile="full-article", action="revise") == "reviser-fast"


def test_revise_full_returns_reviser_full():
    assert route_section("full", profile="full-article", action="revise") == "reviser-full"


def test_revise_full_is_profile_agnostic():
    # revise action doesn't use profile; both give the same answer
    assert route_section("full", profile="funding-proposal", action="revise") == "reviser-full"


def test_revise_unknown_section_falls_back_to_reviser_fast():
    assert route_section("supplementary", profile="full-article", action="revise") == "reviser-fast"
    assert route_section("acknowledgements", profile="full-article", action="revise") == "reviser-fast"


def test_revise_case_insensitive():
    assert route_section("INTRO", profile="full-article", action="revise") == "reviser-fast"
    assert route_section("Full", profile="full-article", action="revise") == "reviser-full"


# ---------------------------------------------------------------------------
# action=consistency
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section_id", [
    "intro", "results", "full", "figure_caption", "anything-at-all",
])
def test_consistency_any_section_returns_consistency_checker(section_id):
    assert route_section(section_id, profile="full-article", action="consistency") == "consistency-checker"


def test_consistency_profile_agnostic():
    assert route_section("methods", profile="funding-proposal", action="consistency") == "consistency-checker"


# ---------------------------------------------------------------------------
# action=style
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section_id", [
    "intro", "results", "full", "figure_caption", "any-section",
])
def test_style_any_section_returns_style_enforcer(section_id):
    assert route_section(section_id, profile="full-article", action="style") == "style-enforcer"


def test_style_profile_agnostic():
    assert route_section("vision", profile="funding-proposal", action="style") == "style-enforcer"


# ---------------------------------------------------------------------------
# action=lint
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section_id", [
    "intro", "results", "full", "figure_caption", "any-file.md",
])
def test_lint_any_section_returns_script_sentinel(section_id):
    result = route_section(section_id, profile="full-article", action="lint")
    assert result == "script:sws_lint_ai_tells.py"


def test_lint_sentinel_is_not_an_agent_id():
    """The sentinel must start with 'script:' so callers can distinguish it from agents."""
    result = route_section("intro", profile="full-article", action="lint")
    assert result.startswith("script:")


def test_lint_profile_agnostic():
    assert route_section("methods", profile="funding-proposal", action="lint") == "script:sws_lint_ai_tells.py"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_empty_section_id_still_raises_regardless_of_action():
    for action in ("draft", "revise", "consistency", "style", "lint"):
        with pytest.raises(RouteError):
            route_section("", profile="full-article", action=action)


def test_unknown_action_raises_route_error():
    with pytest.raises(RouteError, match="unknown action"):
        route_section("intro", profile="full-article", action="summarize")


# ---------------------------------------------------------------------------
# Backwards-compat: cycle-#7 test_section_to_agent_map.py representative cases
# Omitting action must reproduce the same answers as the cycle-#7 test file.
# DO NOT modify test_section_to_agent_map.py — these are independent smoke checks.
# ---------------------------------------------------------------------------

def test_backcompat_publication_profile_intro():
    assert route_section("intro", profile="full-article") == "drafter-flagship"


def test_backcompat_publication_profile_methods():
    assert route_section("methods", profile="full-article") == "methods-writer"


def test_backcompat_publication_profile_results():
    assert route_section("results", profile="full-article") == "drafter-fast"


def test_backcompat_funding_proposal_budget():
    assert route_section("budget", profile="funding-proposal") == "proposal-budget-helper"


def test_backcompat_unknown_publication_fallback():
    assert route_section("limitations", profile="full-article") == "drafter-fast"


def test_backcompat_unknown_funding_fallback():
    assert route_section("appendix", profile="funding-proposal") == "drafter-flagship"
