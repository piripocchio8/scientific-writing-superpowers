"""Tests for sws_init_project.py — pure stdlib + unittest.

Tests grow incrementally per cycle-#2 task: slugify (Task 6),
validate_inputs (Task 7), scan_conflicts (Task 8), build_plan
(Task 9), apply_plan + rollback (Task 10).
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sws_init_project  # noqa: E402


class TestSlugify(unittest.TestCase):
    def test_simple_lowercase(self):
        self.assertEqual(sws_init_project.slugify("Smith"), "smith")

    def test_unicode_umlaut(self):
        self.assertEqual(sws_init_project.slugify("Müller"), "muller")

    def test_apostrophe(self):
        self.assertEqual(sws_init_project.slugify("O'Brien"), "obrien")

    def test_hyphen(self):
        self.assertEqual(sws_init_project.slugify("Smith-Jones"), "smithjones")

    def test_diacritics_combined(self):
        self.assertEqual(sws_init_project.slugify("Søren"), "soren")
        self.assertEqual(sws_init_project.slugify("Şefik"), "sefik")
        self.assertEqual(sws_init_project.slugify("García"), "garcia")

    def test_whitespace_stripped(self):
        self.assertEqual(sws_init_project.slugify("  Smith  "), "smith")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            sws_init_project.slugify("")
        with self.assertRaises(ValueError):
            sws_init_project.slugify("   ")


class TestValidateInputs(unittest.TestCase):
    def _base_inputs(self, **overrides):
        defaults = {
            "article_type": "communication",
            "language": "en",
            "format": "docx",
            "target_journal": "chembiochem",
            "target_call": None,
            "first_author": "smith",
            "year": 2026,
            "co_authors_present": True,
            "notebooklm_enabled": False,
        }
        defaults.update(overrides)
        return defaults

    def test_communication_with_journal_passes(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs())
        self.assertTrue(ok, msg)

    def test_funding_proposal_requires_call(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal=None,
            target_call="prin-2025",
        ))
        self.assertTrue(ok, msg)

    def test_communication_with_call_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            target_call="prin-2025",
        ))
        self.assertFalse(ok)
        self.assertIn("target_call", msg)

    def test_funding_proposal_with_journal_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal="chembiochem",
            target_call="prin-2025",
        ))
        self.assertFalse(ok)
        self.assertIn("target_journal", msg)

    def test_funding_proposal_missing_call_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal=None,
            target_call=None,
        ))
        self.assertFalse(ok)
        self.assertIn("target_call", msg)

    def test_non_funding_missing_journal_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            target_journal=None,
        ))
        self.assertFalse(ok)
        self.assertIn("target_journal", msg)

    def test_invalid_article_type_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="not-a-real-type",
        ))
        self.assertFalse(ok)
        self.assertIn("article_type", msg)

    def test_invalid_language_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            language="fr",
        ))
        self.assertFalse(ok)
        self.assertIn("language", msg)

    def test_invalid_format_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            format="rtf",
        ))
        self.assertFalse(ok)
        self.assertIn("format", msg)

    def test_co_authors_present_must_be_bool(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            co_authors_present="yes",
        ))
        self.assertFalse(ok)
        self.assertIn("co_authors_present", msg)


class TestScanConflicts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _classes(self, conflicts):
        return sorted(c.cls for c in conflicts)

    def test_empty_dir_no_conflicts(self):
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(conflicts, [])

    def test_root_docx_detected_as_C1(self):
        (self.root / "paper.docx").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].cls, "C1")
        self.assertEqual(conflicts[0].path, "paper.docx")

    def test_loose_figures_detected_as_C2(self):
        (self.root / "Figures").mkdir()
        (self.root / "Figures" / "fig1.png").write_bytes(b"x")
        (self.root / "Figures" / "fig2.pdf").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C2", self._classes(conflicts))

    def test_existing_main_subdir_suppresses_C2(self):
        (self.root / "Figures" / "main").mkdir(parents=True)
        (self.root / "Figures" / "main" / "fig1.png").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertNotIn("C2", self._classes(conflicts))

    def test_claude_material_detected_as_C3(self):
        (self.root / "claude_material").mkdir()
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C3", self._classes(conflicts))

    def test_root_claude_md_detected_as_C4(self):
        (self.root / "CLAUDE.md").write_text("# my notes")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C4", self._classes(conflicts))

    def test_existing_claude_memory_detected_as_C5(self):
        (self.root / "claude_memory").mkdir()
        (self.root / "claude_memory" / "MEMORY.md").write_text("- one")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C5", self._classes(conflicts))

    def test_existing_marker_detected_as_C6(self):
        (self.root / ".sws-project.local.md").write_text("---\nsws_version: 0.1\n---")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C6", self._classes(conflicts))

    def test_multiple_classes_detected_together(self):
        (self.root / "paper.docx").write_bytes(b"x")
        (self.root / "claude_material").mkdir()
        (self.root / "CLAUDE.md").write_text("notes")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(self._classes(conflicts), ["C1", "C3", "C4"])

    def test_conflict_has_suggested_action(self):
        (self.root / "paper.docx").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("Manuscript/", conflicts[0].suggested_action)


if __name__ == "__main__":
    unittest.main()
