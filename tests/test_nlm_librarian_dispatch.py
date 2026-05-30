"""Contract tests for agents/nlm-librarian.md (cycle #13).

The agent file is a markdown prompt with YAML frontmatter; these tests assert
its structure rather than its runtime behavior (we don't dispatch the agent
in the test loop).

Locked-decision references:
    D5  — sole owner of sws_nlm.sh dispatch
    D8  — return JSON schema
    D10 — frontmatter notebooklm_enabled: dynamic
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT = REPO_ROOT / "agents" / "nlm-librarian.md"


def _frontmatter(path: Path) -> dict:
    text = path.read_text()
    assert text.startswith("---"), f"{path} missing frontmatter"
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end])


def _body(path: Path) -> str:
    text = path.read_text()
    end = text.index("\n---", 3)
    return text[end + 4:]


class FrontmatterContract(unittest.TestCase):
    def setUp(self):
        self.fm = _frontmatter(AGENT)

    def test_name_is_nlm_librarian(self):
        self.assertEqual(self.fm["name"], "nlm-librarian")

    def test_model_is_sonnet(self):
        # Roster #22: Sonnet 4.6 high.
        self.assertIn("sonnet", self.fm["model"].lower())

    def test_notebooklm_enabled_is_dynamic(self):
        self.assertEqual(self.fm.get("notebooklm_enabled"), "dynamic")

    def test_description_mentions_single_owner_role(self):
        desc = (self.fm["description"] or "").lower()
        # D5 — sole owner of sws_nlm.sh dispatch
        self.assertIn("sws_nlm.sh", desc)
        self.assertTrue("sole" in desc or "single" in desc or "only" in desc,
                        msg=f"description missing single-owner language: {desc!r}")


class BodyStructure(unittest.TestCase):
    def setUp(self):
        self.body = _body(AGENT)

    def test_body_references_sws_nlm_sh(self):
        self.assertIn("sws_nlm.sh", self.body)

    def test_body_never_invokes_notebooklm_mcp_cli_directly(self):
        # D5: only sws_nlm.sh invokes the binary; nlm-librarian goes through the wrapper.
        # "notebooklm-mcp-cli" appears in pointer/install text but not as a direct CLI call.
        lines_with_binary = [
            line for line in self.body.splitlines()
            if "notebooklm-mcp-cli" in line
            and "sws_nlm.sh" not in line
            and not line.lstrip().startswith("#")
        ]
        # Only allowed mentions: hard-rule notice + pattern docstring pointer
        for line in lines_with_binary:
            self.assertTrue(
                "NEVER" in line or "directly" in line.lower(),
                msg=f"suspicious direct-binary reference: {line!r}",
            )

    def test_body_has_seven_step_structure(self):
        for marker in (
            "Step 1",
            "Step 2",
            "Step 3",
            "Step 4",
            "Step 5",
            "Step 6",
            "Step 7",
        ):
            self.assertIn(marker, self.body, msg=f"missing {marker}")

    def test_body_includes_probe_dispatch_and_degrade_language(self):
        body_low = self.body.lower()
        self.assertIn("probe", body_low)
        self.assertIn("dispatch", body_low)
        self.assertIn("degrade", body_low)

    def test_body_mentions_empty_notebook_check(self):
        # R6 mitigation
        self.assertIn("empty", self.body.lower())

    def test_body_references_return_json_schema(self):
        # The agent must return D8 normalized JSON.
        self.assertIn("nlm-librarian-pattern.md", self.body)

    def test_body_honors_r5_no_gender_default(self):
        # R5 — no gender-default in user address
        body_low = self.body.lower()
        self.assertTrue("r5" in body_low or "gender" in body_low or "first name" in body_low,
                        msg="R5 user-address language missing")

    def test_body_invokes_agent_prelude(self):
        self.assertIn("agent_prelude.sh", self.body)
        self.assertIn("agent_should_run.sh", self.body)


class SingleOwnerEnforcement(unittest.TestCase):
    """D5 enforced across the roster: only nlm-librarian.md may invoke sws_nlm.sh."""

    def test_no_other_agent_calls_sws_nlm_sh(self):
        agents_dir = REPO_ROOT / "agents"
        offenders = []
        for agent_md in agents_dir.glob("*.md"):
            if agent_md.name == "nlm-librarian.md":
                continue
            text = agent_md.read_text()
            if "sws_nlm.sh" in text:
                offenders.append(agent_md.name)
        self.assertEqual(
            offenders, [],
            msg=f"D5 violation: agents calling sws_nlm.sh directly: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
