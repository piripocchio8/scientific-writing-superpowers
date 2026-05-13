"""Tests for sws_hook_utils.py — pure stdlib + unittest."""
import os
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


class TestWriteMarkerField(unittest.TestCase):
    def _make_marker(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        tmp.write(content)
        tmp.close()
        path = Path(tmp.name)
        self.addCleanup(lambda: path.unlink() if path.exists() else None)
        return path

    def test_writes_new_field_to_frontmatter(self):
        marker = self._make_marker(SAMPLE_MARKER)
        sws_hook_utils.write_marker_field(marker, "profile", "communication")
        parsed = sws_hook_utils.parse_marker(marker)
        self.assertEqual(parsed["profile"], "communication")

    def test_overwrites_existing_field(self):
        marker = self._make_marker(SAMPLE_MARKER)
        sws_hook_utils.write_marker_field(marker, "language", "it")
        parsed = sws_hook_utils.parse_marker(marker)
        self.assertEqual(parsed["language"], "it")

    def test_preserves_other_fields_and_body(self):
        marker = self._make_marker(SAMPLE_MARKER)
        sws_hook_utils.write_marker_field(marker, "profile", "full-article")
        text = marker.read_text()
        # Body preserved
        self.assertIn("# smith_et_al_2026 — SWS marker", text)
        # Other fields preserved
        parsed = sws_hook_utils.parse_marker(marker)
        self.assertEqual(parsed["article_type"], "communication")
        self.assertEqual(parsed["format"], "docx")
        self.assertEqual(parsed["target_journal"], "chembiochem")

    def test_creates_frontmatter_block_if_absent(self):
        marker = self._make_marker("# No frontmatter here\nJust body.\n")
        sws_hook_utils.write_marker_field(marker, "profile", "communication")
        parsed = sws_hook_utils.parse_marker(marker)
        self.assertEqual(parsed["profile"], "communication")
        text = marker.read_text()
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("# No frontmatter here", text)

    def test_serializes_null_for_None(self):
        marker = self._make_marker(SAMPLE_MARKER)
        sws_hook_utils.write_marker_field(marker, "profile", None)
        text = marker.read_text()
        self.assertIn("profile: null", text)
        parsed = sws_hook_utils.parse_marker(marker)
        self.assertIsNone(parsed.get("profile"))

    def test_serializes_bool(self):
        marker = self._make_marker(SAMPLE_MARKER)
        sws_hook_utils.write_marker_field(marker, "ready", True)
        text = marker.read_text()
        self.assertIn("ready: true", text)
        parsed = sws_hook_utils.parse_marker(marker)
        self.assertIs(parsed["ready"], True)


if __name__ == "__main__":
    unittest.main()
