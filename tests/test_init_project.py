"""Tests for sws_init_project.py — pure stdlib + unittest.

Tests grow incrementally per cycle-#2 task: slugify (Task 6),
validate_inputs (Task 7), scan_conflicts (Task 8), build_plan
(Task 9), apply_plan + rollback (Task 10).
"""
import sys
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


if __name__ == "__main__":
    unittest.main()
