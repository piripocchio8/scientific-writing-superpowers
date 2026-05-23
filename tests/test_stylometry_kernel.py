"""RBF kernel, gamma median heuristic, self-band math, keep-best monotonicity."""
from __future__ import annotations

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
SCRIPT = SCRIPT_DIR / "sws_stylometry.py"
sys.path.insert(0, str(SCRIPT_DIR))

import sws_stylometry as sm  # noqa: E402


def _vec(**kw):
    v = {k: 0.0 for k in sm.FEATURE_ORDER}
    v.update(kw)
    return v


class TestKernel(unittest.TestCase):
    def test_rbf_in_unit_interval(self):
        for d in [0.0, 0.1, 1.0, 10.0, 1e6]:
            k = sm.rbf(d, gamma=0.5)
            self.assertGreaterEqual(k, 0.0)
            self.assertLessEqual(k, 1.0)

    def test_rbf_zero_distance_is_one(self):
        self.assertAlmostEqual(sm.rbf(0.0, gamma=2.0), 1.0, places=12)

    def test_rbf_monotone_decreasing(self):
        self.assertGreater(sm.rbf(0.1, 1.0), sm.rbf(1.0, 1.0))

    def test_median_gamma_from_intra_distances(self):
        g = sm.median_gamma([1.0, 2.0, 3.0])  # median 2.0 -> gamma 0.5
        self.assertAlmostEqual(g, 0.5, places=12)

    def test_median_gamma_guards_zero_median(self):
        g = sm.median_gamma([0.0, 0.0, 0.0])
        self.assertGreater(g, 0.0)
        self.assertTrue(math.isfinite(g))

    def test_self_band_returns_band_keys(self):
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.2), _vec(hedge_density=0.9)]
        stats = sm.standardization_stats(author)
        weights = {k: (1.0 if k == "hedge_density" else 0.0) for k in sm.FEATURE_ORDER}
        band = sm.self_band(author, weights=weights, w_h=0.0, stats=stats)
        for key in ["band_mean", "band_sd", "band_lo", "band_hi"]:
            self.assertIn(key, band)
        self.assertLessEqual(band["band_lo"], band["band_mean"])
        self.assertGreaterEqual(band["band_hi"], band["band_mean"])

    def test_self_band_similarity_in_unit_interval(self):
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.2)]
        stats = sm.standardization_stats(author)
        weights = {k: (1.0 if k == "hedge_density" else 0.0) for k in sm.FEATURE_ORDER}
        band = sm.self_band(author, weights=weights, w_h=0.0, stats=stats)
        self.assertGreaterEqual(band["band_mean"], 0.0)
        self.assertLessEqual(band["band_mean"], 1.0)

    def test_keep_best_is_monotone(self):
        hist = [(1, 0.40), (2, 0.55), (3, 0.50), (4, 0.60)]
        self.assertEqual(sm.keep_best(hist), [0.40, 0.55, 0.55, 0.60])

    # --- CLI contract (smoke + agent depend on these flags/keys) ----------
    def test_cli_vector_emits_feature_json(self):
        out = subprocess.check_output(
            [sys.executable, str(SCRIPT), "--vector", "We saw a clear effect. We conclude."],
            text=True,
        )
        data = json.loads(out)
        self.assertEqual(list(data.keys()), sm.FEATURE_ORDER)

    def test_cli_rbf_emits_similarity(self):
        out = subprocess.check_output(
            [sys.executable, str(SCRIPT), "--rbf", "0", "--gamma", "1"], text=True
        )
        self.assertAlmostEqual(json.loads(out)["similarity"], 1.0, places=12)

    def test_cli_fit_weights_round_trip(self):
        a = _vec(hedge_density=1.0)
        b = _vec(hedge_density=1.1)
        f = _vec(hedge_density=9.0)
        pos = [[a, b]]
        neg = [[a, f], [b, f]]
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            pp = Path(td) / "pos.json"
            np = Path(td) / "neg.json"
            pp.write_text(json.dumps(pos))
            np.write_text(json.dumps(neg))
            out = subprocess.check_output(
                [sys.executable, str(SCRIPT), "--fit-weights", str(pp), str(np), "--lam", "0.3"],
                text=True,
            )
        res = json.loads(out)
        self.assertIn("weights", res)
        self.assertIn("w_h", res)
        total = sum(res["weights"].values()) + res["w_h"]
        self.assertAlmostEqual(total, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
