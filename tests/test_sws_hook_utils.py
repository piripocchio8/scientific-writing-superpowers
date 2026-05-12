"""Tests for sws_hook_utils.py — pure stdlib + unittest."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sws_hook_utils

SAMPLE_MARKER = """\
---
sws_version: 0.1
article_type: communication
language: en
format: docx
target_journal: chembiochem
target_call: null
notebooklm:
  enabled: false
created: 2026-05-12T12:00:00Z
---

# smith_et_al_2026 — SWS marker
"""


class TestCheckMarker(unittest.TestCase):
    def test_check_marker_returns_none_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = sws_hook_utils.check_marker(tmp)
            self.assertIsNone(result)

    def test_check_marker_returns_dict_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / ".sws-project.local.md"
            marker.write_text(SAMPLE_MARKER)
            result = sws_hook_utils.check_marker(tmp)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("article_type"), "communication")


class TestParseMarker(unittest.TestCase):
    def test_parse_marker_extracts_top_level_scalars(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(SAMPLE_MARKER)
            path = f.name
        result = sws_hook_utils.parse_marker(path)
        self.assertEqual(result["article_type"], "communication")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["format"], "docx")
        self.assertEqual(result["target_journal"], "chembiochem")

    def test_parse_marker_handles_null_values(self):
        content = "---\nfoo: null\nbar: \n---\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            path = f.name
        result = sws_hook_utils.parse_marker(path)
        self.assertIsNone(result.get("foo"))
        self.assertIsNone(result.get("bar"))

    def test_parse_marker_handles_booleans(self):
        content = "---\nenabled: true\ndisabled: false\n---\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            path = f.name
        result = sws_hook_utils.parse_marker(path)
        self.assertIs(result["enabled"], True)
        self.assertIs(result["disabled"], False)

    def test_parse_marker_returns_empty_dict_on_no_frontmatter(self):
        content = "# No frontmatter here\nJust body text.\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            path = f.name
        result = sws_hook_utils.parse_marker(path)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
