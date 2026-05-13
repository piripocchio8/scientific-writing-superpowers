"""Tests for profiles/*.md — verify the 9 v0.1 profile files are well-formed."""
from __future__ import annotations

import pathlib
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILES = ROOT / "profiles"

# Roster from claude_memory/project_roster_v0.1.md (24 agents).
ROSTER = {
    "brainstormer", "planner", "outline-architect", "style-calibrator",
    "literature-searcher", "drafter", "methods-writer", "caption-writer",
    "reviser", "humanizer", "style-enforcer", "consistency-checker",
    "peer-reviewer", "code-reviewer", "claim-verifier", "plagiarism-screener",
    "plot-maker", "data-curator", "bibliography-curator", "cover-letter-writer",
    "response-to-reviewers", "nlm-librarian", "proposal-budget-helper",
    "proposal-compliance-helper",
}

EXPECTED_PROFILES = {
    "full-article", "communication", "perspective", "review-paper",
    "mini-review", "editorial", "methodological-paper", "commentary-reply",
    "funding-proposal",
}

VALID_ABSTRACT_STYLES = {"structured", "unstructured", "graphical", "none"}
VALID_REFS_STYLES = {"numbered", "author-year", "footnote"}


def parse_frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        return {}
    return yaml.safe_load(rest[:end].lstrip("\n")) or {}


class TestProfilesShipped(unittest.TestCase):
    def test_all_9_profile_files_present(self):
        existing = {p.stem for p in PROFILES.glob("*.md")}
        self.assertEqual(existing, EXPECTED_PROFILES)


def _make_profile_test(name: str):
    def test(self):
        path = PROFILES / f"{name}.md"
        fm = parse_frontmatter(path)
        self.assertEqual(fm.get("profile"), name, "profile field must match filename")
        self.assertIn("sections", fm)
        self.assertIsInstance(fm["sections"], list)
        self.assertGreater(len(fm["sections"]), 0)
        for sec in fm["sections"]:
            self.assertIn("id", sec)
            self.assertIn("label", sec)
            self.assertIn("required", sec)
        self.assertIn(fm.get("abstract_style"), VALID_ABSTRACT_STYLES)
        self.assertIn(fm.get("refs_style"), VALID_REFS_STYLES)

        active = set(fm.get("agents_active") or [])
        inactive = set(fm.get("agents_inactive") or [])
        self.assertTrue(
            active.issubset(ROSTER),
            f"agents_active in {name} has unknown agent(s): {active - ROSTER}",
        )
        self.assertTrue(
            inactive.issubset(ROSTER),
            f"agents_inactive in {name} has unknown agent(s): {inactive - ROSTER}",
        )
        self.assertFalse(
            active & inactive,
            f"agents_active and agents_inactive overlap in {name}: {active & inactive}",
        )
    test.__name__ = f"test_{name.replace('-', '_')}_well_formed"
    return test


class TestProfiles(unittest.TestCase):
    pass


for _profile_name in sorted(EXPECTED_PROFILES):
    setattr(
        TestProfiles,
        f"test_{_profile_name.replace('-', '_')}_well_formed",
        _make_profile_test(_profile_name),
    )


class TestProfilesMatchMatrix(unittest.TestCase):
    """The 9 shipped profiles must match the agent_activation_matrix.yaml fixture
    (which mirrors the spec's agent_activation_matrix.per_profile_inactive)."""

    def test_inactive_lists_match_matrix(self):
        matrix = yaml.safe_load((ROOT / "tests" / "fixtures" / "agent_activation_matrix.yaml").read_text())
        per_profile_inactive = matrix["per_profile_inactive"]
        for name in EXPECTED_PROFILES:
            fm = parse_frontmatter(PROFILES / f"{name}.md")
            with self.subTest(profile=name):
                self.assertEqual(
                    set(fm.get("agents_inactive") or []),
                    set(per_profile_inactive[name]),
                    f"agents_inactive in {name}.md must match matrix fixture",
                )


if __name__ == "__main__":
    unittest.main()
