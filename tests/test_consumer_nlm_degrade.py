"""For each of the 6 NLM-consumer agents (cycle #13), assert:

- Frontmatter `notebooklm_enabled: dynamic` (D10).
- Body mentions the `notebooklm.enabled` gate or RESOLVED_NOTEBOOKLM_ENABLED.
- Body explicitly mentions degrade-gracefully behavior (D6).
- Body does NOT contain "DEFERRED" or "cycle #11" leftover language.
- Body references the `nlm-librarian` agent and NOT `sws_nlm.sh` directly (D5).
"""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "agents"

CONSUMERS = [
    "drafter-flagship.md",
    "drafter-fast.md",
    "literature-searcher.md",
    "claim-verifier.md",
    "bibliography-curator.md",
    "proposal-compliance-helper.md",
]


def _frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}


def _body(path: Path) -> str:
    text = path.read_text()
    end = text.index("\n---", 3)
    return text[end + 4:]


class ConsumerDegrade(unittest.TestCase):

    def _for(self, name: str):
        path = AGENTS_DIR / name
        return path, _frontmatter(path), _body(path)


def _make_consumer_test(consumer_filename: str):
    """Return a TestCase class parameterized for one consumer agent."""

    class Test(unittest.TestCase):
        maxDiff = None

        def setUp(self):
            self.path = AGENTS_DIR / consumer_filename
            self.fm = _frontmatter(self.path)
            self.body = _body(self.path)

        def test_frontmatter_notebooklm_enabled_dynamic(self):
            self.assertEqual(
                self.fm.get("notebooklm_enabled"),
                "dynamic",
                msg=f"{consumer_filename}: frontmatter notebooklm_enabled must be 'dynamic' (D10)",
            )

        def test_body_mentions_gate(self):
            body_low = self.body.lower()
            mentions_gate = (
                "resolved_notebooklm_enabled" in body_low
                or "notebooklm.enabled" in body_low
                or "notebooklm enabled" in body_low
            )
            self.assertTrue(
                mentions_gate,
                msg=f"{consumer_filename}: body must mention the notebooklm.enabled gate",
            )

        def test_body_mentions_degrade(self):
            body_low = self.body.lower()
            self.assertTrue(
                "degrade" in body_low or "without nlm" in body_low,
                msg=f"{consumer_filename}: body must explicitly mention degrade-gracefully behavior",
            )

        def test_body_no_deferred_leftover(self):
            body_low = self.body.lower()
            self.assertNotIn(
                "deferred",
                body_low,
                msg=f"{consumer_filename}: 'DEFERRED' leftover from cycle-11 framing (D10 says active now)",
            )
            self.assertNotIn(
                "cycle #11",
                body_low,
                msg=f"{consumer_filename}: 'cycle #11' leftover (should be cycle #13 or removed)",
            )

        def test_body_references_nlm_librarian(self):
            self.assertIn(
                "nlm-librarian",
                self.body,
                msg=f"{consumer_filename}: body must reference the nlm-librarian agent",
            )

        def test_body_does_not_call_wrapper_directly(self):
            # D5: only nlm-librarian invokes sws_nlm.sh
            self.assertNotIn(
                "sws_nlm.sh",
                self.body,
                msg=f"{consumer_filename}: D5 violation — consumer must NOT call sws_nlm.sh directly",
            )

    Test.__name__ = f"Consumer_{consumer_filename.replace('-', '_').replace('.md', '')}"
    return Test


# Generate one TestCase per consumer file in the module namespace so unittest
# discovery picks them all up.
for _name in CONSUMERS:
    _cls = _make_consumer_test(_name)
    globals()[_cls.__name__] = _cls


if __name__ == "__main__":
    unittest.main()
