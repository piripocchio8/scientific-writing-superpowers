"""Fisher-weight fitting tests (D8a): recover a KNOWN separation, constraints,
regularization, and the w_h Haiku term fitted alongside feature weights."""
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
        self.assertGreaterEqual(res["w_h"], 0.0)

    def test_weights_plus_wh_sum_to_one(self):
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.1)]
        field = [_vec(hedge_density=9.0)]
        pos = [(author[0], author[1])]
        neg = [(author[0], field[0]), (author[1], field[0])]
        res = sm.fit_fisher_weights(pos, neg, lam=0.3)
        total = sum(res["weights"].values()) + res["w_h"]
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_lambda_one_gives_uniform_weights(self):
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.1)]
        field = [_vec(hedge_density=9.0)]
        pos = [(author[0], author[1])]
        neg = [(author[0], field[0]), (author[1], field[0])]
        res = sm.fit_fisher_weights(pos, neg, lam=1.0)
        vals = list(res["weights"].values()) + [res["w_h"]]
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

    def test_wh_high_when_haiku_separates(self):
        # Haiku similarity: positive pairs ~0.95 (close), negative ~0.2 (far).
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.0)]
        field = [_vec(hedge_density=1.0)]
        pos = [(author[0], author[1])]
        neg = [(author[0], field[0])]
        res = sm.fit_fisher_weights(
            pos, neg, lam=0.0,
            pos_haiku=[0.95], neg_haiku=[0.2],
        )
        # Features don't separate (all hedge=1), Haiku does -> w_h dominates.
        self.assertGreater(res["w_h"], max(res["weights"].values()))

    def test_distance_uses_weights_and_haiku_term(self):
        a = _vec(hedge_density=1.0)
        b = _vec(hedge_density=1.0)
        stats = sm.standardization_stats([a, b])
        # equal vectors, haiku_sim 0.5 -> distance = w_h * 0.5
        weights = {k: 0.0 for k in sm.FEATURE_ORDER}
        d = sm.weighted_distance(a, b, weights=weights, w_h=0.4,
                                 haiku_sim=0.5, stats=stats)
        self.assertAlmostEqual(d["distance"], 0.4 * 0.5, places=9)

    def test_per_feature_contrib_keys(self):
        a = _vec(hedge_density=2.0)
        b = _vec(hedge_density=0.0)
        stats = sm.standardization_stats([a, b])
        weights = {k: (1.0 if k == "hedge_density" else 0.0) for k in sm.FEATURE_ORDER}
        d = sm.weighted_distance(a, b, weights=weights, w_h=0.0,
                                 haiku_sim=1.0, stats=stats)
        self.assertIn("hedge_density", d["per_feature_contrib"])
        self.assertGreater(d["per_feature_contrib"]["hedge_density"], 0.0)


if __name__ == "__main__":
    unittest.main()
