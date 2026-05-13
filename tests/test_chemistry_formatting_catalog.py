"""Tests for references/chemistry-formatting.md — validate the YAML catalog.

Mirrors the pytest style of test_profiles.py and test_resolve_overlay.py.
"""
from __future__ import annotations

import pathlib
import re
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "references" / "chemistry-formatting.md"

REQUIRED_CATEGORIES = {
    "latin_abbreviations",
    "chemical_formulae",
    "species_names",
    "species_abbreviated",
    "gene_names",
    "figure_label_prefix",
}

VALID_APPLY = {"italic", "subscript", "superscript", "bold"}
VALID_SEVERITY = {"auto", "suggest"}

REQUIRED_ENTRY_FIELDS = {"pattern", "apply", "severity", "example_before", "example_after", "why"}


def _parse_frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} does not start with '---'")
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        raise ValueError(f"{path} has no closing '---'")
    return yaml.safe_load(rest[:end].lstrip("\n")) or {}


class TestCatalogExists(unittest.TestCase):
    def test_file_exists(self):
        self.assertTrue(CATALOG_PATH.exists(), f"Missing: {CATALOG_PATH}")

    def test_file_has_frontmatter(self):
        text = CATALOG_PATH.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---"), "File must open with '---'")


class TestCatalogTopLevel(unittest.TestCase):
    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)

    def test_sws_artifact_field(self):
        self.assertEqual(self.fm.get("sws_artifact"), "chemistry-formatting")

    def test_lang_field(self):
        self.assertEqual(self.fm.get("lang"), "en")

    def test_categories_key_present(self):
        self.assertIn("categories", self.fm)

    def test_all_required_categories_present(self):
        cats = set(self.fm["categories"].keys())
        missing = REQUIRED_CATEGORIES - cats
        self.assertFalse(missing, f"Missing categories: {missing}")


class TestCategoryNonEmpty(unittest.TestCase):
    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)
        self.categories = self.fm["categories"]

    def test_each_category_has_at_least_one_entry(self):
        for cat_name, entries in self.categories.items():
            with self.subTest(category=cat_name):
                self.assertIsInstance(entries, list, f"{cat_name} must be a list")
                self.assertGreater(len(entries), 0, f"{cat_name} is empty")


class TestEntryRequiredFields(unittest.TestCase):
    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)
        self.categories = self.fm["categories"]

    def _all_entries(self):
        for cat_name, entries in self.categories.items():
            for idx, entry in enumerate(entries):
                yield cat_name, idx, entry

    def test_every_entry_has_required_fields(self):
        for cat_name, idx, entry in self._all_entries():
            with self.subTest(category=cat_name, index=idx):
                missing = REQUIRED_ENTRY_FIELDS - set(entry.keys())
                self.assertFalse(
                    missing,
                    f"{cat_name}[{idx}] is missing fields: {missing}",
                )

    def test_apply_values_are_valid(self):
        for cat_name, idx, entry in self._all_entries():
            with self.subTest(category=cat_name, index=idx):
                self.assertIn(
                    entry.get("apply"),
                    VALID_APPLY,
                    f"{cat_name}[{idx}] has invalid apply={entry.get('apply')!r}",
                )

    def test_severity_values_are_valid(self):
        for cat_name, idx, entry in self._all_entries():
            with self.subTest(category=cat_name, index=idx):
                self.assertIn(
                    entry.get("severity"),
                    VALID_SEVERITY,
                    f"{cat_name}[{idx}] has invalid severity={entry.get('severity')!r}",
                )

    def test_why_is_nonempty_string(self):
        for cat_name, idx, entry in self._all_entries():
            with self.subTest(category=cat_name, index=idx):
                why = entry.get("why", "")
                self.assertIsInstance(why, str)
                self.assertGreater(len(why.strip()), 0, f"{cat_name}[{idx}] has empty 'why'")


class TestPatternCompiles(unittest.TestCase):
    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)
        self.categories = self.fm["categories"]

    def test_every_pattern_compiles(self):
        for cat_name, entries in self.categories.items():
            for idx, entry in enumerate(entries):
                pattern = entry.get("pattern", "")
                with self.subTest(category=cat_name, index=idx, pattern=pattern):
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        self.fail(
                            f"{cat_name}[{idx}] pattern={pattern!r} does not compile: {exc}"
                        )


class TestExampleBeforeMatches(unittest.TestCase):
    """example_before must match the compiled pattern (possibly with re.IGNORECASE)."""

    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)
        self.categories = self.fm["categories"]

    def test_example_before_matches_pattern(self):
        for cat_name, entries in self.categories.items():
            for idx, entry in enumerate(entries):
                pattern_str = entry.get("pattern", "")
                before = entry.get("example_before", "")
                with self.subTest(category=cat_name, index=idx):
                    try:
                        compiled = re.compile(pattern_str, re.MULTILINE)
                    except re.error:
                        self.skipTest(f"Pattern won't compile — covered by TestPatternCompiles")
                        return
                    match = compiled.search(before)
                    self.assertIsNotNone(
                        match,
                        f"{cat_name}[{idx}]: pattern={pattern_str!r} "
                        f"did not match example_before={before!r}",
                    )


class TestExampleAfterTransformed(unittest.TestCase):
    """example_after must NOT match the same raw regex on the format-marker substring.

    The underlying logic: after the chemistry-format script applies a
    transformation (italic, subscript, superscript, bold), the ASCII source
    pattern should no longer match the transformed text.  We approximate this by
    verifying that the example_after string is *different* from example_before —
    signalling that a transformation actually occurred — and that the pattern
    does not trivially match example_after unless it is correct to re-match (e.g.
    the label prefix pattern applied to already-bolded markdown).

    For patterns whose example_after legitimately still contains the same ASCII
    substring (e.g. the markdown bold wrapper '**Figure 1.**' still contains
    'Figure 1.'), we assert at minimum that example_after != example_before.
    """

    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)
        self.categories = self.fm["categories"]

    def test_example_after_differs_from_example_before(self):
        for cat_name, entries in self.categories.items():
            for idx, entry in enumerate(entries):
                before = entry.get("example_before", "")
                after = entry.get("example_after", "")
                with self.subTest(category=cat_name, index=idx):
                    self.assertNotEqual(
                        before,
                        after,
                        f"{cat_name}[{idx}]: example_after must differ from example_before "
                        f"(no transformation recorded)",
                    )

    def test_example_after_shows_formatting_marker(self):
        """example_after should contain a recognisable formatting marker."""
        ITALIC_MARKERS = {"*", "_"}
        BOLD_MARKERS = {"**"}

        for cat_name, entries in self.categories.items():
            for idx, entry in enumerate(entries):
                apply = entry.get("apply", "")
                after = entry.get("example_after", "")
                with self.subTest(category=cat_name, index=idx):
                    if apply == "italic":
                        has_marker = any(m in after for m in ITALIC_MARKERS)
                        self.assertTrue(
                            has_marker,
                            f"{cat_name}[{idx}]: apply=italic but example_after lacks * or _ marker",
                        )
                    elif apply == "bold":
                        self.assertIn(
                            "**",
                            after,
                            f"{cat_name}[{idx}]: apply=bold but example_after lacks ** marker",
                        )
                    # subscript/superscript: unicode chars or special notation acceptable
                    # (no enforced ASCII marker)


class TestCategoryMinimumCoverage(unittest.TestCase):
    """Each category should have >= 6 entries per spec (~6-8 per category)."""

    MIN_ENTRIES = 6

    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)
        self.categories = self.fm["categories"]

    def test_each_required_category_has_minimum_entries(self):
        for cat_name in REQUIRED_CATEGORIES:
            entries = self.categories.get(cat_name, [])
            with self.subTest(category=cat_name):
                self.assertGreaterEqual(
                    len(entries),
                    self.MIN_ENTRIES,
                    f"{cat_name} has only {len(entries)} entries; need >= {self.MIN_ENTRIES}",
                )


class TestSeverityDistribution(unittest.TestCase):
    """Spot-check that known-ambiguous categories use suggest severity."""

    SUGGEST_ONLY_CATEGORIES = {"species_names"}

    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)
        self.categories = self.fm["categories"]

    def test_species_names_all_suggest(self):
        entries = self.categories.get("species_names", [])
        for idx, entry in enumerate(entries):
            with self.subTest(index=idx):
                self.assertEqual(
                    entry.get("severity"),
                    "suggest",
                    f"species_names[{idx}] should be suggest (high false-positive risk from spec D6 R1)",
                )

    def test_species_abbreviated_all_auto(self):
        """Abbreviated genus patterns (E. coli) are unambiguous — must be auto."""
        entries = self.categories.get("species_abbreviated", [])
        for idx, entry in enumerate(entries):
            with self.subTest(index=idx):
                self.assertEqual(
                    entry.get("severity"),
                    "auto",
                    f"species_abbreviated[{idx}] should be auto per spec D6",
                )

    def test_latin_abbreviations_all_auto(self):
        """Latin abbreviations are unambiguous in scientific prose."""
        entries = self.categories.get("latin_abbreviations", [])
        for idx, entry in enumerate(entries):
            with self.subTest(index=idx):
                self.assertEqual(
                    entry.get("severity"),
                    "auto",
                    f"latin_abbreviations[{idx}] should be auto",
                )

    def test_figure_label_prefix_all_auto(self):
        """Figure/Table/Scheme label prefixes are structurally unambiguous."""
        entries = self.categories.get("figure_label_prefix", [])
        for idx, entry in enumerate(entries):
            with self.subTest(index=idx):
                self.assertEqual(
                    entry.get("severity"),
                    "auto",
                    f"figure_label_prefix[{idx}] should be auto",
                )


class TestPatternIdsUnique(unittest.TestCase):
    """Each entry id (if present) must be unique across the whole catalog."""

    def setUp(self):
        self.fm = _parse_frontmatter(CATALOG_PATH)
        self.categories = self.fm["categories"]

    def test_entry_ids_unique(self):
        seen: dict[str, str] = {}
        for cat_name, entries in self.categories.items():
            for idx, entry in enumerate(entries):
                entry_id = entry.get("id")
                if entry_id is None:
                    continue
                location = f"{cat_name}[{idx}]"
                self.assertNotIn(
                    entry_id,
                    seen,
                    f"Duplicate id={entry_id!r} at {location} (first seen at {seen.get(entry_id)})",
                )
                seen[entry_id] = location


if __name__ == "__main__":
    unittest.main()
