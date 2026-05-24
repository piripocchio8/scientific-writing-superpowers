"""Fisher-weight fitting tests (D8a + voice-metric correction): recover a KNOWN
separation, constraints, regularization, and per-term CLIPPING of the now
stylometric-only weights. The Haiku term is no longer fitted in this function;
it is handled at the similarity level by fit_channel_mix (see
test_stylometry_channel.py)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sws_stylometry as sm  # noqa: E402


def _vec(**kw):
    """Build a full vector with given keys set; others 0."""
    v = {k: 0.0 for k in sm.FEATURE_ORDER}
    v.update(kw)
    return v


class TestFisherFit(unittest.TestCase):
    def test_recovers_known_separating_feature(self):
        # hedge_density separates author (low, stable) from field (high);
        # connective_density is pure noise (varies within author as much as between).
        author = [
            _vec(hedge_density=1.0, connective_density=1.0),
            _vec(hedge_density=1.1, connective_density=9.0),
            _vec(hedge_density=0.9, connective_density=2.0),
        ]
        field = [
            _vec(hedge_density=8.0, connective_density=8.0),
            _vec(hedge_density=8.2, connective_density=1.0),
        ]
        pos = [(author[0], author[1]), (author[1], author[2]), (author[0], author[2])]
        neg = [(a, f) for a in author for f in field]
        res = sm.fit_fisher_weights(pos, neg, lam=0.0)
        w = res["weights"]
        # The separating feature must outweigh the noise feature.
        self.assertGreater(w["hedge_density"], w["connective_density"])

    def test_weights_are_nonnegative(self):
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.1)]
        field = [_vec(hedge_density=9.0)]
        pos = [(author[0], author[1])]
        neg = [(author[0], field[0]), (author[1], field[0])]
        res = sm.fit_fisher_weights(pos, neg, lam=0.3)
        for v in res["weights"].values():
            self.assertGreaterEqual(v, 0.0)

    def test_weights_sum_to_one(self):
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.1)]
        field = [_vec(hedge_density=9.0)]
        pos = [(author[0], author[1])]
        neg = [(author[0], field[0]), (author[1], field[0])]
        res = sm.fit_fisher_weights(pos, neg, lam=0.3)
        self.assertAlmostEqual(sum(res["weights"].values()), 1.0, places=6)

    def test_weights_respect_clip_band(self):
        # Without clipping, fw_and-style features can run away; assert every
        # normalized weight stays inside [clip_lo*u, clip_hi*u].
        author = [
            _vec(hedge_density=1.0, fw_and=0.10),
            _vec(hedge_density=1.05, fw_and=0.101),
            _vec(hedge_density=0.95, fw_and=0.099),
        ]
        field = [_vec(hedge_density=9.0, fw_and=0.01), _vec(hedge_density=8.5, fw_and=0.02)]
        pos = [(author[0], author[1]), (author[1], author[2]), (author[0], author[2])]
        neg = [(a, f) for a in author for f in field]
        clip_lo, clip_hi = 0.4, 2.5
        res = sm.fit_fisher_weights(pos, neg, lam=0.3, clip_lo=clip_lo, clip_hi=clip_hi)
        u = 1.0 / len(sm.FEATURE_ORDER)
        # The clip+renormalize loop ends on a renormalize, so the converged
        # fixed point sits within a tiny floating-point tolerance of the band.
        tol = 1e-3
        for k, v in res["weights"].items():
            self.assertGreaterEqual(v, clip_lo * u - tol, f"{k} below floor")
            self.assertLessEqual(v, clip_hi * u + tol, f"{k} above ceiling")
        self.assertAlmostEqual(sum(res["weights"].values()), 1.0, places=9)

    def test_clip_prevents_runaway_dominance(self):
        # A feature that separates perfectly would otherwise grab almost all the
        # mass; the ceiling caps it at clip_hi*u.
        author = [_vec(fw_and=0.10), _vec(fw_and=0.10), _vec(fw_and=0.10)]
        field = [_vec(fw_and=0.50), _vec(fw_and=0.50)]
        pos = [(author[0], author[1]), (author[1], author[2]), (author[0], author[2])]
        neg = [(a, f) for a in author for f in field]
        res = sm.fit_fisher_weights(pos, neg, lam=0.0, clip_hi=2.5)
        u = 1.0 / len(sm.FEATURE_ORDER)
        self.assertLessEqual(res["weights"]["fw_and"], 2.5 * u + 1e-3)

    def test_lambda_one_gives_uniform_weights(self):
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.1)]
        field = [_vec(hedge_density=9.0)]
        pos = [(author[0], author[1])]
        neg = [(author[0], field[0]), (author[1], field[0])]
        res = sm.fit_fisher_weights(pos, neg, lam=1.0)
        vals = list(res["weights"].values())
        for v in vals:
            self.assertAlmostEqual(v, vals[0], places=9)

    def test_within_variance_floor_prevents_blowup(self):
        # Identical positive pairs -> within-var 0; floor must keep fisher finite.
        author = [_vec(hedge_density=2.0), _vec(hedge_density=2.0)]
        field = [_vec(hedge_density=9.0)]
        pos = [(author[0], author[1])]
        neg = [(author[0], field[0])]
        res = sm.fit_fisher_weights(pos, neg, lam=0.3)
        for v in res["weights"].values():
            self.assertTrue(v == v and abs(v) != float("inf"))  # not nan/inf

    def test_no_w_h_in_fit_output(self):
        # The Haiku channel is intentionally removed from fit_fisher_weights.
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.1)]
        field = [_vec(hedge_density=9.0)]
        pos = [(author[0], author[1])]
        neg = [(author[0], field[0])]
        res = sm.fit_fisher_weights(pos, neg)
        self.assertNotIn("w_h", res)
        self.assertIn("weights", res)
        self.assertIn("stats", res)

    def test_distance_is_stylometric_only(self):
        # weighted_distance no longer takes w_h / haiku_sim: equal vectors -> 0.
        a = _vec(hedge_density=1.0)
        b = _vec(hedge_density=1.0)
        stats = sm.standardization_stats([a, b])
        weights = {k: 1.0 / len(sm.FEATURE_ORDER) for k in sm.FEATURE_ORDER}
        d = sm.weighted_distance(a, b, weights=weights, stats=stats)
        self.assertAlmostEqual(d["distance"], 0.0, places=9)

    def test_per_feature_contrib_keys(self):
        a = _vec(hedge_density=2.0)
        b = _vec(hedge_density=0.0)
        stats = sm.standardization_stats([a, b])
        weights = {k: (1.0 if k == "hedge_density" else 0.0) for k in sm.FEATURE_ORDER}
        d = sm.weighted_distance(a, b, weights=weights, stats=stats)
        self.assertIn("hedge_density", d["per_feature_contrib"])
        self.assertGreater(d["per_feature_contrib"]["hedge_density"], 0.0)
        # No Haiku term leaks into the per-feature contributions anymore.
        self.assertNotIn("_haiku", d["per_feature_contrib"])


if __name__ == "__main__":
    unittest.main()
