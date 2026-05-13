"""Section→agent routing per spec section_to_agent_map."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sws_section_router import route_section, RouteError  # noqa: E402


@pytest.mark.parametrize("section_id, expected_agent", [
    ("intro", "drafter-flagship"),
    ("introduction", "drafter-flagship"),
    ("abstract", "drafter-flagship"),
    ("discussion", "drafter-flagship"),
    ("conclusion", "drafter-flagship"),
    ("conclusions", "drafter-flagship"),
    ("methods", "methods-writer"),
    ("experimental", "methods-writer"),
    ("experimental section", "methods-writer"),
    ("materials", "methods-writer"),
    ("statistical analysis", "methods-writer"),
    ("computational details", "methods-writer"),
    ("software", "methods-writer"),
    ("data availability", "methods-writer"),
    ("results", "drafter-fast"),
    ("results and discussion", "drafter-flagship"),
    ("figure_caption", "caption-writer"),
])
def test_publication_profile_routing(section_id, expected_agent):
    assert route_section(section_id, profile="full-article") == expected_agent


@pytest.mark.parametrize("section_id, expected_agent", [
    ("state of the art", "drafter-flagship"),
    ("state-of-the-art", "drafter-flagship"),
    ("vision", "drafter-flagship"),
    ("objectives", "drafter-flagship"),
    ("workplan", "drafter-flagship"),
    ("methodology", "drafter-flagship"),
    ("approach", "drafter-flagship"),
    ("impact", "drafter-flagship"),
    ("risk management", "drafter-flagship"),
    ("deliverables", "drafter-flagship"),
    ("timeline", "drafter-flagship"),
    ("budget", "proposal-budget-helper"),
    ("compliance", "proposal-compliance-helper"),
    ("figure_caption", "caption-writer"),
])
def test_funding_proposal_routing(section_id, expected_agent):
    assert route_section(section_id, profile="funding-proposal") == expected_agent


def test_publication_fallback_to_drafter_fast():
    assert route_section("limitations", profile="full-article") == "drafter-fast"


def test_funding_proposal_fallback_to_drafter_flagship():
    assert route_section("appendix", profile="funding-proposal") == "drafter-flagship"


def test_case_insensitive_routing():
    assert route_section("INTRO", profile="full-article") == "drafter-flagship"
    assert route_section("Methods", profile="full-article") == "methods-writer"


def test_methods_in_funding_proposal_does_not_route_to_methods_writer():
    # methods-writer is in funding-proposal's agents_inactive; the router
    # doesn't know that — that gating is the should_run check's job.
    # Router still maps the id using the funding-proposal map, which has
    # no "methods" entry → falls back to drafter-flagship (correct per D8).
    assert route_section("methods", profile="funding-proposal") == "drafter-flagship"


def test_empty_section_id_raises():
    with pytest.raises(RouteError):
        route_section("", profile="full-article")


def test_whitespace_section_id_normalized():
    assert route_section("  intro  ", profile="full-article") == "drafter-flagship"


def test_perspective_profile_uses_publication_map():
    # perspective is a publication profile; same map as full-article applies.
    assert route_section("intro", profile="perspective") == "drafter-flagship"
    assert route_section("results", profile="perspective") == "drafter-fast"
