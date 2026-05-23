"""Unit tests for sws_stylometry.py feature extraction (D8 vector half)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sws_stylometry as sm  # noqa: E402

# Synthetic invented prose — no real author, no real content.
AUTHOR_A = (
    "We observed a clear trend in the data. The effect was robust across runs. "
    "We therefore conclude that the mechanism holds. Moreover, the signal was strong."
)
SHORT = "We saw it."
EMPTY = ""


class TestFeatureVector(unittest.TestCase):
    def test_vector_keys_match_feature_order(self):
        vec = sm.feature_vector(AUTHOR_A)
        self.assertEqual(list(vec.keys()), sm.FEATURE_ORDER)

    def test_vector_is_deterministic(self):
        self.assertEqual(sm.feature_vector(AUTHOR_A), sm.feature_vector(AUTHOR_A))

    def test_sentence_len_mean_positive(self):
        vec = sm.feature_vector(AUTHOR_A)
        self.assertGreater(vec["sentence_len_mean"], 0.0)

    def test_fp_plural_rate_detects_we(self):
        vec = sm.feature_vector(AUTHOR_A)
        self.assertGreater(vec["fp_plural_rate"], 0.0)

    def test_hedge_density_detects_hedge(self):
        hedged = "The result may indicate an effect. It is possibly relevant."
        vec = sm.feature_vector(hedged)
        self.assertGreater(vec["hedge_density"], 0.0)

    def test_connective_density_detects_connective(self):
        vec = sm.feature_vector(AUTHOR_A)  # contains "Moreover" and "therefore"
        self.assertGreater(vec["connective_density"], 0.0)

    def test_lexical_diversity_in_unit_range(self):
        vec = sm.feature_vector(AUTHOR_A)
        self.assertGreaterEqual(vec["lexical_diversity"], 0.0)
        self.assertLessEqual(vec["lexical_diversity"], 1.0)

    def test_empty_text_returns_zero_vector_not_crash(self):
        vec = sm.feature_vector(EMPTY)
        self.assertEqual(list(vec.keys()), sm.FEATURE_ORDER)
        for v in vec.values():
            self.assertEqual(v, 0.0)

    def test_short_text_does_not_crash(self):
        vec = sm.feature_vector(SHORT)
        self.assertEqual(list(vec.keys()), sm.FEATURE_ORDER)

    def test_section_pool_concatenates_then_vectorises(self):
        pooled = sm.pool_section_texts([AUTHOR_A, SHORT])
        # pooled vector equals vector of the joined text
        joined = sm.feature_vector(AUTHOR_A + " " + SHORT)
        self.assertEqual(pooled, joined)

    def test_pool_empty_list_is_zero_vector(self):
        self.assertEqual(sm.pool_section_texts([]), sm.feature_vector(""))


if __name__ == "__main__":
    unittest.main()
