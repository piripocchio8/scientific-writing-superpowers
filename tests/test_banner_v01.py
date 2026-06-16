"""Banner-flip gate (cycle #13, D11).

This test asserts the README banner reads `v0.1` (not `v0.1 alpha`) and the
plugin version is `0.1.0` (no `-alpha` suffix). It is deliberately introduced
in Phase 5 of cycle-13 — it will FAIL until Phase 6 lands the banner-flip
commit. That is by design: the failing test is the gate that prevents the PR
from being opened before the flip.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"


def _banner_block(text: str) -> str:
    # The banner is the leading block-quote (lines 1-10 per spec D11).
    return "\n".join(text.splitlines()[:10])


class ReadmeBanner(unittest.TestCase):
    def setUp(self):
        self.text = README.read_text()
        self.banner = _banner_block(self.text)

    def test_banner_contains_v01_literal(self):
        self.assertIn(
            "**v0.1**",
            self.banner,
            msg="README banner must contain the literal **v0.1** (D11)",
        )

    def test_banner_does_not_contain_alpha(self):
        self.assertNotIn(
            "v0.1 alpha",
            self.banner.lower(),
            msg="README banner must not contain 'v0.1 alpha' after the flip (D11)",
        )

    def test_banner_does_not_contain_test_tube(self):
        # The 🧪 emoji is the alpha-state visual marker (D11). After the flip
        # the banner must drop it.
        self.assertNotIn(
            "🧪",
            self.banner,
            msg="README banner must not contain the 🧪 alpha-state marker (D11)",
        )


class PluginVersion(unittest.TestCase):
    def test_plugin_version_is_010_no_alpha_suffix(self):
        data = json.loads(PLUGIN_JSON.read_text())
        self.assertEqual(
            data["version"],
            "0.1.0",
            msg="plugin.json version must be '0.1.0' (D11)",
        )


if __name__ == "__main__":
    unittest.main()
