"""Channel-mix + combined-score tests (voice-metric correction).

These cover the fix for the anti-correlation bug: the Haiku term is combined at
the SIMILARITY level via a fitted mix S = alpha*k_stylo + beta*haiku_sim, rather
than folded as a linear term inside a squared distance. The ORDERING test is the
key regression: when the Haiku channel separates better (beta > alpha), a
candidate with higher Haiku voice must win even if its stylometric kernel is
slightly worse.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
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


def _author_field_fixture():
    """Synthetic same-author (tight) vs different-author (spread) pairs."""
    author = [
        _vec(hedge_density=1.0, connective_density=2.0),
        _vec(hedge_density=1.1, connective_density=2.1),
        _vec(hedge_density=0.9, connective_density=1.9),
    ]
    field = [
        _vec(hedge_density=7.0, connective_density=8.0),
        _vec(hedge_density=8.0, connective_density=1.0),
    ]
    pos = [(author[0], author[1]), (author[1], author[2]), (author[0], author[2])]
    neg = [(a, f) for a in author for f in field]
    return author, field, pos, neg


class TestChannelMix(unittest.TestCase):
    def test_alpha_beta_sum_to_one_and_gamma_positive(self):
        _, _, pos, neg = _author_field_fixture()
        fit = sm.fit_fisher_weights(pos, neg)
        mix = sm.fit_channel_mix(
            pos, neg,
            pos_haiku=[0.9, 0.88, 0.91],
            neg_haiku=[0.3] * len(neg),
            weights=fit["weights"], stats=fit["stats"],
        )
        self.assertAlmostEqual(mix["alpha"] + mix["beta"], 1.0, places=9)
        self.assertGreater(mix["gamma"], 0.0)

    def test_haiku_channel_wins_weight_when_it_separates_better(self):
        # Make the stylometric channel barely separate (author and field nearly
        # identical on features) while the Haiku channel separates strongly.
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.0), _vec(hedge_density=1.0)]
        field = [_vec(hedge_density=1.02), _vec(hedge_density=0.98)]
        pos = [(author[0], author[1]), (author[1], author[2]), (author[0], author[2])]
        neg = [(a, f) for a in author for f in field]
        fit = sm.fit_fisher_weights(pos, neg)
        mix = sm.fit_channel_mix(
            pos, neg,
            pos_haiku=[0.95, 0.95, 0.95],
            neg_haiku=[0.10] * len(neg),
            weights=fit["weights"], stats=fit["stats"],
        )
        self.assertGreater(mix["beta"], mix["alpha"])

    def test_stylo_channel_wins_weight_when_it_separates_better(self):
        _, _, pos, neg = _author_field_fixture()
        fit = sm.fit_fisher_weights(pos, neg)
        # Haiku barely separates here -> stylo should dominate.
        mix = sm.fit_channel_mix(
            pos, neg,
            pos_haiku=[0.55, 0.55, 0.55],
            neg_haiku=[0.50] * len(neg),
            weights=fit["weights"], stats=fit["stats"],
        )
        self.assertGreater(mix["alpha"], mix["beta"])


class TestCombinedScore(unittest.TestCase):
    def test_increases_with_haiku_sim(self):
        a = _vec(hedge_density=1.0)
        b = _vec(hedge_density=1.5)
        stats = sm.standardization_stats([a, b])
        weights = {k: 1.0 / len(sm.FEATURE_ORDER) for k in sm.FEATURE_ORDER}
        kw = dict(weights=weights, stats=stats, gamma=0.5, alpha=0.5, beta=0.5)
        low = sm.combined_score(a, b, 0.2, **kw)
        mid = sm.combined_score(a, b, 0.5, **kw)
        high = sm.combined_score(a, b, 0.9, **kw)
        self.assertLess(low, mid)
        self.assertLess(mid, high)

    def test_in_unit_interval(self):
        a = _vec(hedge_density=1.0)
        b = _vec(hedge_density=4.0)
        stats = sm.standardization_stats([a, b])
        weights = {k: 1.0 / len(sm.FEATURE_ORDER) for k in sm.FEATURE_ORDER}
        s = sm.combined_score(a, b, 0.7, weights, stats, gamma=0.5, alpha=0.4, beta=0.6)
        self.assertGreaterEqual(s, 0.0)
        self.assertLessEqual(s, 1.0)

    def test_ordering_regression_haiku_dominant_mix(self):
        """THE regression: on a Haiku-dominant mix (beta > alpha), a candidate
        with BETTER k_stylo but LOWER Haiku must lose to one with WORSE k_stylo
        but HIGHER Haiku. The old in-distance w_h made the blend anti-correlate
        with voice; the similarity-level mix fixes it."""
        ho = _vec(hedge_density=1.0, connective_density=2.0)
        # Candidate A: closer in features (better k_stylo) but low Haiku voice.
        cand_a = _vec(hedge_density=1.1, connective_density=2.1)
        # Candidate B: farther in features (worse k_stylo) but high Haiku voice.
        cand_b = _vec(hedge_density=2.2, connective_density=3.5)
        stats = sm.standardization_stats([ho, cand_a, cand_b])
        weights = {k: 1.0 / len(sm.FEATURE_ORDER) for k in sm.FEATURE_ORDER}
        gamma = 0.5
        # Sanity: A really does have the better stylometric kernel.
        k_a = sm.rbf(sm.weighted_distance(cand_a, ho, weights, stats)["distance"], gamma)
        k_b = sm.rbf(sm.weighted_distance(cand_b, ho, weights, stats)["distance"], gamma)
        self.assertGreater(k_a, k_b)
        # Haiku-dominant mix.
        alpha, beta = 0.2, 0.8
        s_a = sm.combined_score(cand_a, ho, 0.40, weights, stats, gamma, alpha, beta)
        s_b = sm.combined_score(cand_b, ho, 0.85, weights, stats, gamma, alpha, beta)
        self.assertGreater(s_b, s_a)


class TestChannelCLI(unittest.TestCase):
    def _write(self, td, name, obj):
        p = Path(td) / name
        p.write_text(json.dumps(obj))
        return str(p)

    def test_cli_fit_mix_emits_alpha_beta_gamma(self):
        _, _, pos, neg = _author_field_fixture()
        fit = sm.fit_fisher_weights(pos, neg)
        wjson = {"weights": fit["weights"],
                 "stats": {k: list(v) for k, v in fit["stats"].items()}}
        with tempfile.TemporaryDirectory() as td:
            pp = self._write(td, "pos.json", [[a, b] for a, b in pos])
            np = self._write(td, "neg.json", [[a, b] for a, b in neg])
            wp = self._write(td, "w.json", wjson)
            out = subprocess.check_output(
                [sys.executable, str(SCRIPT), "--fit-mix", pp, np,
                 "--weights", wp,
                 "--pos-haiku", "0.9,0.88,0.91",
                 "--neg-haiku", ",".join(["0.3"] * len(neg))],
                text=True,
            )
        res = json.loads(out)
        self.assertAlmostEqual(res["alpha"] + res["beta"], 1.0, places=9)
        self.assertGreater(res["gamma"], 0.0)

    def test_cli_score_emits_score(self):
        a = _vec(hedge_density=1.0)
        b = _vec(hedge_density=1.5)
        weights = {k: 1.0 / len(sm.FEATURE_ORDER) for k in sm.FEATURE_ORDER}
        stats = sm.standardization_stats([a, b])
        wjson = {"weights": weights, "stats": {k: list(v) for k, v in stats.items()}}
        with tempfile.TemporaryDirectory() as td:
            ap = self._write(td, "a.json", a)
            bp = self._write(td, "b.json", b)
            wp = self._write(td, "w.json", wjson)
            out = subprocess.check_output(
                [sys.executable, str(SCRIPT), "--score", ap, bp,
                 "--weights", wp, "--haiku-sim", "0.7",
                 "--alpha", "0.5", "--beta", "0.5", "--gamma", "0.5"],
                text=True,
            )
        res = json.loads(out)
        self.assertIn("score", res)
        self.assertGreaterEqual(res["score"], 0.0)
        self.assertLessEqual(res["score"], 1.0)

    def test_cli_self_band_with_mix_params(self):
        author = [_vec(hedge_density=1.0), _vec(hedge_density=1.2), _vec(hedge_density=0.9)]
        weights = {k: 1.0 / len(sm.FEATURE_ORDER) for k in sm.FEATURE_ORDER}
        stats = sm.standardization_stats(author)
        wjson = {"weights": weights, "stats": {k: list(v) for k, v in stats.items()}}
        with tempfile.TemporaryDirectory() as td:
            vp = self._write(td, "vecs.json", author)
            wp = self._write(td, "w.json", wjson)
            out = subprocess.check_output(
                [sys.executable, str(SCRIPT), "--self-band", vp,
                 "--weights", wp, "--alpha", "0.6", "--beta", "0.4",
                 "--gamma", "0.5", "--haiku-sims", "0.88,0.82,0.90"],
                text=True,
            )
        band = json.loads(out)
        self.assertLessEqual(band["band_lo"], band["band_mean"])
        self.assertLessEqual(band["band_mean"], band["band_hi"])


if __name__ == "__main__":
    unittest.main()
