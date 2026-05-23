# Cycle #10 — Style calibration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 1 agent (`style-calibrator`, Sonnet 4.6 high), 1 skill (`/sws:calibrate-style`), 1 stylometry script (`scripts/sws_stylometry.py`, stdlib + venv only — NO numpy/NLTK/spaCy), 2 references (`stylometry-features.md`, `voice-profile-schema.md`), 5 consumer-agent edits, a `VOICE_PROFILE` export in `agent_prelude.sh`, the agent-contract R3 I/O update, the per-profile activation matrix across all 9 profiles (D14), ~5 unit-test modules, and a fixture-driven smoke. No banner flip this cycle (version stays `0.1.0-alpha`).

**Architecture:** `style-calibrator` runs the whole 5-phase loop (D1/D2). It pulls the OBJECTIVE numbers from `sws_stylometry.py` (feature vectors, Fisher-fitted weights, weighted distance, RBF similarity, self-similarity band) and never invents a score. The Haiku 4.5 voice-similarity judge (D9) is an INTERNAL dispatched step, not a rostered agent — roster stays at 24. The voice profile is a NEW axis SEPARATE from the journal-style/constraints overlay: `_voice/profile.md` does NOT pass through `resolve_overlay.py` (D13). The 5 consumer agents (`drafter-flagship`, `drafter-fast`, `reviser-full`, `reviser-fast`, `humanizer`) read `_voice/profile.md` via a prelude-exported `VOICE_PROFILE` path when present, else degrade exactly as today.

**Tech Stack:** Python 3.9+ via per-paper `.venv/`, stdlib-only for `sws_stylometry.py` (pure-Python stats: mean/variance over lists, no heavy deps); bash for prelude + smoke; markdown + YAML frontmatter for the agent, skill, references, and profiles; Python stdlib `unittest` for unit tests (the repo's existing test files import `pytest`, but the new stylometry math tests are written with `unittest` and run under either `pytest` or `python -m unittest`); shell smoke for e2e with the Haiku call STUBBED via a test-mode env var.

**Spec source of truth:** `docs/superpowers/specs/2026-05-22-cycle-10-style-calibration-design.md`. The frontmatter `locked_decisions:` block (D1–D17, D8a) is canonical; this plan implements every locked decision.

**Privacy:** This plan is committed to a PUBLIC repo. It contains NO personal identity, NO `/Users/...` absolute paths, NO real names/institutions/manuscripts. The local test interpreter is referenced as `$DEV_PY` (set it once per shell, e.g. `export DEV_PY=python3` if your interpreter has PyYAML, or point it at your venv). Paths use `$REPO_ROOT`, `$PAPER_ROOT`, `${CLAUDE_PLUGIN_ROOT}`. All test fixtures are synthetic invented prose.

**Execution mode:** Maximize parallelism per phase. Open PR in DRAFT for next-day review.

---

## File Structure

**CREATE (new files):**

Scripts:
- `scripts/sws_stylometry.py` — pure-Python stylometry engine: feature vector, weighted distance, diagonal-Fisher weight fit, RBF kernel, self-similarity band. One file, five CLI modes.

References:
- `references/stylometry-features.md` — canonical feature list + the function-word / hedge / connective word-lists the script reads, plus the Fisher + RBF + self-band math, documented for reproducibility.
- `references/voice-profile-schema.md` — frontmatter schema for `_voice/profile.md` (machine-readable feature targets) + the global-block / per-section-delta body contract.

Agent:
- `agents/style-calibrator.md` — Sonnet 4.6 high (roster #4). Orchestrates the 5 phases + the loop; dispatches the Haiku scoring step; reads `sws_stylometry.py` JSON; writes `_voice/` artifacts.

Skill:
- `skills/calibrate-style/SKILL.md` — `/sws:calibrate-style`. Phase driver; holds loop defaults (epsilon, max-rounds, lambda).

Tests:
- `tests/test_stylometry_vector.py` — feature-extraction determinism, edge cases, section pooling.
- `tests/test_stylometry_fisher.py` — Fisher weights recover a KNOWN separation; constraints w≥0 / Σ=1; regularization shrink + within-var floor; w_h fitted alongside.
- `tests/test_stylometry_kernel.py` — RBF bounds in [0,1]; gamma median heuristic; self-band math; keep-best monotonicity helper.
- `tests/test_voice_profile_schema.py` — `profile.md` frontmatter + global/per-section-delta block validation.
- `tests/test_profile_activation_calibrator.py` — style-calibrator active in 7 profiles / inactive in editorial + commentary-reply (D14).
- `tests/fixtures/cycle_10/` — synthetic corpus: 3 author snippets, 2 field snippets, 1 held-out snippet, plus a tiny manual marker.
- `tests/smoke_cycle_10.sh` — full `/sws:calibrate-style` flow against the fixture; Haiku stubbed via test-mode env var.

**MODIFY (existing files):**
- `scripts/agent_prelude.sh` — export `VOICE_PROFILE` (path to `_voice/profile.md` if present, else empty).
- `agents/drafter-flagship.md`, `agents/drafter-fast.md`, `agents/reviser-full.md`, `agents/reviser-fast.md`, `agents/humanizer.md` — upgrade the existing one-line `_voice/profile.md` mention into a real consumption contract (global block always; per-section delta for the section being written; graceful degrade when absent; humanizer humanizes TOWARD the voice).
- `references/agent-contract.md` — R3 I/O inventory: add `_voice/*` shapes (calibrator WRITES; 5 consumers READ `profile.md`).
- `profiles/full-article.md`, `communication.md`, `perspective.md`, `review-paper.md`, `mini-review.md`, `methodological-paper.md`, `funding-proposal.md` — add `style-calibrator` to `agents_active`.
- `profiles/editorial.md`, `commentary-reply.md` — add `style-calibrator` to `agents_inactive` (D14).
- `claude_memory/project_v02_backlog.md` — MKL/learned-kernel, conditional detrending, drafter-in-loop realism test (D16; not committed to public repo — claude_memory/ is gitignored).
- `claude_memory/project_cycle_execution_status.md` — cycle #10 merged at end of PR (gitignored).

---

## Phase Map (sequential phases; parallelizable within a phase)

**Phase 1 — Foundations (3 tasks):** `sws_stylometry.py` (TDD across 3 test modules) + `references/stylometry-features.md` + `references/voice-profile-schema.md`. The two references are parallel with the script once the feature contract (Task 1.1 Step 3) is fixed.

**Phase 2 — Agent (1 task; depends on Phase 1):** `agents/style-calibrator.md`.

**Phase 3 — Skill (1 task; depends on Phase 2):** `skills/calibrate-style/SKILL.md`.

**Phase 4 — Consumer wiring (6 tasks, parallel; depends on Phase 1 contract):** 5 consumer-agent edits + the `VOICE_PROFILE` prelude export + agent-contract R3 update.

**Phase 5 — Profile activation (10 tasks, parallel; depends on Phase 2 agent name being final):** 9 profile edits + `test_profile_activation_calibrator.py`.

**Phase 6 — Schema test (1 task; depends on Phase 1 references):** `test_voice_profile_schema.py`.

**Phase 7 — Smoke + PR (sequential):** fixture corpus + `smoke_cycle_10.sh` + draft PR.

---

# PHASE 1 — Foundations

## Task 1.1: Script — `sws_stylometry.py` feature vector (TDD)

**Files:**
- Create: `scripts/sws_stylometry.py`
- Test: `tests/test_stylometry_vector.py`

**Feature contract (FIXED here; every later task matches it).** The vector is a flat ordered dict. `FEATURE_ORDER` (the keys, in order):
```
sentence_len_mean, sentence_len_sd, hedge_density, connective_density,
passive_ratio, lexical_diversity, fp_plural_rate,
fw_the, fw_of, fw_and, fw_to, fw_in, fw_that, fw_we, fw_is, fw_for, fw_as
```
(7 stylometric features + 10 function-word relative frequencies = a 17-dim vector.) The Haiku term is NOT in the vector — it enters the distance separately as `w_h·(1 − haiku_sim)` (D8). All densities are per-100-tokens; `lexical_diversity` is type/token ratio; `fp_plural_rate` is first-person-plural pronoun count per 100 tokens; function-word freqs are count/total-tokens.

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_stylometry_vector.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they FAIL**

```bash
cd "$REPO_ROOT"
$DEV_PY -m pytest tests/test_stylometry_vector.py -q
```

Expected: collection error / `ModuleNotFoundError: No module named 'sws_stylometry'` (11 errors).

- [ ] **Step 3: Implement the vector half of `scripts/sws_stylometry.py`**

Create `scripts/sws_stylometry.py` with this content (the distance/Fisher/kernel/CLI parts are added in later steps of this task and Tasks 1.2–1.3; write the whole file now through the vector + word-lists, then extend):

```python
#!/usr/bin/env python3
"""SWS stylometry engine (cycle #10, D8/D8a/D10).

Pure stdlib — NO numpy / NLTK / spaCy. Implements:
  * feature_vector(text)            -> ordered dict of 17 stylometric features
  * weighted_distance(a, b, ...)     -> D = SUM_i w_i (a_i-b_i)^2 + w_h (1-haiku)
  * fit_fisher_weights(pos, neg, ..) -> diagonal-Fisher weights (regularized)
  * rbf(D, gamma)                    -> exp(-gamma*D) in [0,1]
  * median_gamma(intra_distances)    -> gamma from the median heuristic
  * self_band(author_vectors, ...)   -> intra-author self-similarity band

The Haiku voice-similarity term is supplied by the caller (style-calibrator
dispatches Haiku); this script never calls a model. Word-lists below mirror
references/stylometry-features.md.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# --- word lists (mirror references/stylometry-features.md) -----------------
HEDGES = {
    "may", "might", "could", "possibly", "perhaps", "likely", "suggest",
    "suggests", "appear", "appears", "seem", "seems", "indicate", "indicates",
    "probably", "presumably", "arguably", "relatively",
}
CONNECTIVES = {
    "however", "moreover", "therefore", "thus", "furthermore", "nevertheless",
    "consequently", "hence", "accordingly", "additionally", "whereas", "although",
}
FP_PLURAL = {"we", "us", "our", "ours", "ourselves"}
PASSIVE_AUX = {"was", "were", "is", "are", "been", "be", "being"}
# 10 function words tracked individually (relative frequency features)
FUNC_WORDS = ["the", "of", "and", "to", "in", "that", "we", "is", "for", "as"]

FEATURE_ORDER = [
    "sentence_len_mean",
    "sentence_len_sd",
    "hedge_density",
    "connective_density",
    "passive_ratio",
    "lexical_diversity",
    "fp_plural_rate",
] + [f"fw_{w}" for w in FUNC_WORDS]

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_ED_RE = re.compile(r"[A-Za-z]+ed$")


def _zero_vector() -> Dict[str, float]:
    return {k: 0.0 for k in FEATURE_ORDER}


def _sentences(text: str) -> List[str]:
    text = text.replace("\n", " ").strip()
    if not text:
        return []
    return [s for s in _SENT_SPLIT.split(text) if s.strip()]


def _tokens(text: str) -> List[str]:
    return [w.lower() for w in _WORD.findall(text)]


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _pop_sd(xs: Sequence[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def feature_vector(text: str) -> Dict[str, float]:
    """Return the ordered 17-feature vector for one text. Empty -> zero vector."""
    toks = _tokens(text)
    if not toks:
        return _zero_vector()
    n = len(toks)
    sents = _sentences(text)
    sent_lens = [len(_tokens(s)) for s in sents] or [n]

    hedge = sum(1 for t in toks if t in HEDGES)
    conn = sum(1 for t in toks if t in CONNECTIVES)
    fp = sum(1 for t in toks if t in FP_PLURAL)
    # passive proxy: an auxiliary be-verb followed within 2 tokens by an -ed word
    passive = 0
    for i, t in enumerate(toks):
        if t in PASSIVE_AUX:
            window = toks[i + 1 : i + 3]
            if any(_ED_RE.match(w) for w in window):
                passive += 1
    vec = _zero_vector()
    vec["sentence_len_mean"] = _mean(sent_lens)
    vec["sentence_len_sd"] = _pop_sd(sent_lens)
    vec["hedge_density"] = 100.0 * hedge / n
    vec["connective_density"] = 100.0 * conn / n
    vec["passive_ratio"] = passive / len(sents) if sents else 0.0
    vec["lexical_diversity"] = len(set(toks)) / n
    vec["fp_plural_rate"] = 100.0 * fp / n
    for w in FUNC_WORDS:
        vec[f"fw_{w}"] = toks.count(w) / n
    return vec


def pool_section_texts(texts: Sequence[str]) -> Dict[str, float]:
    """Pool (concatenate) several texts of one section type, then vectorise."""
    return feature_vector(" ".join(t for t in texts if t))
```

- [ ] **Step 4: Run tests to verify PASS**

```bash
$DEV_PY -m pytest tests/test_stylometry_vector.py -q
```

Expected: `11 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_stylometry.py tests/test_stylometry_vector.py
git commit -m "feat(cycle-10): sws_stylometry.py feature vector — 17-dim stylometric extraction (D8)"
```

---

## Task 1.2: Script — Fisher-weighted distance + weight fit (TDD)

**Files:**
- Modify: `scripts/sws_stylometry.py`
- Test: `tests/test_stylometry_fisher.py`

**Math contract (D8/D8a).**
- Standardize each feature across the pooled anchor set to mean 0 / sd 1 BEFORE weighting, so squared differences are comparable. Standardization stats are computed once over all anchor vectors and returned so distance/fit share them.
- Distance: `D(a,b) = Σ_i w_i (â_i − b̂_i)² + w_h (1 − haiku_sim)` where `â` is the standardized vector.
- Fisher per feature: `fisher_i = between_var_i / max(within_var_i, FLOOR)`. `within_var_i` = mean of within-author (positive-pair) squared standardized differences. `between_var_i` = mean of author-vs-field (negative-pair) squared standardized differences.
- `w_h` is fitted identically from a Haiku sample: `fisher_h = between_h / max(within_h, FLOOR)` where within/between are computed from `(1 − haiku_sim)` values on positive/negative pairs.
- Normalize: append `fisher_h` to the feature Fisher list, shrink toward uniform `raw = (1−λ)·fisher + λ·uniform`, clip to ≥0, renormalize so `Σ w_i + w_h = 1`.

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_stylometry_fisher.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they FAIL**

```bash
$DEV_PY -m pytest tests/test_stylometry_fisher.py -q
```

Expected: 8 failures — `AttributeError: module 'sws_stylometry' has no attribute 'fit_fisher_weights'` (and `standardization_stats`, `weighted_distance`).

- [ ] **Step 3: Append the distance + Fisher functions to `scripts/sws_stylometry.py`**

Insert this block immediately after `pool_section_texts` (before any CLI code):

```python
# --- standardization + distance + Fisher fit (D8/D8a) ----------------------
WITHIN_VAR_FLOOR = 1e-6


def standardization_stats(vectors: Sequence[Dict[str, float]]) -> Dict[str, Tuple[float, float]]:
    """Per-feature (mean, sd) across the anchor set; sd floored to 1.0 when ~0."""
    stats: Dict[str, Tuple[float, float]] = {}
    for k in FEATURE_ORDER:
        col = [v[k] for v in vectors]
        m = _mean(col)
        sd = _pop_sd(col)
        stats[k] = (m, sd if sd > 1e-12 else 1.0)
    return stats


def _standardize(vec: Dict[str, float], stats: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    return {k: (vec[k] - stats[k][0]) / stats[k][1] for k in FEATURE_ORDER}


def weighted_distance(
    a: Dict[str, float],
    b: Dict[str, float],
    weights: Dict[str, float],
    w_h: float,
    haiku_sim: float,
    stats: Dict[str, Tuple[float, float]],
) -> Dict[str, object]:
    """D = SUM_i w_i (a_i-b_i)^2 + w_h (1 - haiku_sim), on standardized features."""
    sa = _standardize(a, stats)
    sb = _standardize(b, stats)
    contrib: Dict[str, float] = {}
    total = 0.0
    for k in FEATURE_ORDER:
        c = weights.get(k, 0.0) * (sa[k] - sb[k]) ** 2
        contrib[k] = c
        total += c
    haiku_term = w_h * (1.0 - haiku_sim)
    contrib["_haiku"] = haiku_term
    total += haiku_term
    return {"distance": total, "per_feature_contrib": contrib}


def _sq_diffs_per_feature(
    pairs: Sequence[Tuple[Dict[str, float], Dict[str, float]]],
    stats: Dict[str, Tuple[float, float]],
) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {k: [] for k in FEATURE_ORDER}
    for a, b in pairs:
        sa = _standardize(a, stats)
        sb = _standardize(b, stats)
        for k in FEATURE_ORDER:
            out[k].append((sa[k] - sb[k]) ** 2)
    return out


def fit_fisher_weights(
    pos_pairs: Sequence[Tuple[Dict[str, float], Dict[str, float]]],
    neg_pairs: Sequence[Tuple[Dict[str, float], Dict[str, float]]],
    lam: float = 0.3,
    pos_haiku: Optional[Sequence[float]] = None,
    neg_haiku: Optional[Sequence[float]] = None,
) -> Dict[str, object]:
    """Diagonal-Fisher weights from boundary conditions, shrunk toward uniform.

    POSITIVE pairs (author,author) -> small distance; NEGATIVE pairs
    (author,field) -> large distance. fisher_i = between_i / max(within_i, FLOOR).
    """
    all_vecs = [v for pr in list(pos_pairs) + list(neg_pairs) for v in pr]
    stats = standardization_stats(all_vecs)
    within = _sq_diffs_per_feature(pos_pairs, stats)
    between = _sq_diffs_per_feature(neg_pairs, stats)

    fisher: Dict[str, float] = {}
    for k in FEATURE_ORDER:
        w_var = max(_mean(within[k]), WITHIN_VAR_FLOOR)
        b_var = _mean(between[k])
        fisher[k] = b_var / w_var

    # w_h fitted from the Haiku sample exactly like any other term.
    if pos_haiku and neg_haiku:
        pos_d = [(1.0 - s) ** 2 for s in pos_haiku]
        neg_d = [(1.0 - s) ** 2 for s in neg_haiku]
        fisher_h = _mean(neg_d) / max(_mean(pos_d), WITHIN_VAR_FLOOR)
    else:
        fisher_h = 0.0

    keys = FEATURE_ORDER + ["_h"]
    raw = [fisher[k] for k in FEATURE_ORDER] + [fisher_h]
    n = len(keys)
    uniform = 1.0 / n
    shrunk = [max((1.0 - lam) * r + lam * uniform, 0.0) for r in raw]
    s = sum(shrunk) or 1.0
    norm = [x / s for x in shrunk]

    weights = {k: norm[i] for i, k in enumerate(FEATURE_ORDER)}
    w_h = norm[-1]
    return {"weights": weights, "w_h": w_h, "stats": stats}
```

- [ ] **Step 4: Run tests to verify PASS**

```bash
$DEV_PY -m pytest tests/test_stylometry_fisher.py -q
```

Expected: `8 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_stylometry.py tests/test_stylometry_fisher.py
git commit -m "feat(cycle-10): Fisher-weighted distance + diagonal-Fisher weight fit incl. w_h (D8/D8a)"
```

---

## Task 1.3: Script — RBF kernel, gamma heuristic, self-band, keep-best, CLI (TDD)

**Files:**
- Modify: `scripts/sws_stylometry.py`
- Test: `tests/test_stylometry_kernel.py`

**Math contract (D8/D10).**
- `rbf(D, gamma) = exp(-gamma·D)`, always in (0, 1]; D≥0 so it never exceeds 1.
- `median_gamma(intra_distances)`: `gamma = 1 / median(d)` over the positive (intra-author) weighted distances, with a guard when the median is ~0 (return a large default gamma).
- `self_band(author_vectors, weights, w_h, stats, haiku_fn=None)`: compute the weighted distance for every distinct intra-author pair, convert each to RBF similarity, and return `{band_mean, band_sd, band_lo, band_hi}` where `band_lo = mean − sd`, `band_hi = mean + sd`. (Haiku sim defaults to 1.0 in the band when no `haiku_fn` is given — the band is computed on the deterministic part for testability; the calibrator passes real Haiku medians at runtime.)
- `keep_best(history)`: given a list of `(round, score)` returns the running max — an edit that worsens a section's score is reverted (monotone non-decreasing).

CLI modes (string contract the smoke + agent depend on):
```
sws_stylometry.py --vector "<text>"
sws_stylometry.py --distance A.json B.json [--weights W.json] [--haiku-sim X]
sws_stylometry.py --fit-weights POS.json NEG.json [--lam L] [--pos-haiku p1,p2] [--neg-haiku n1,n2]
sws_stylometry.py --rbf D --gamma G
sws_stylometry.py --self-band VECS.json [--weights W.json]
```
`A.json`/`B.json` = a single vector object. `POS.json`/`NEG.json` = a list of `[vecA, vecB]` pairs. `W.json` = `{"weights": {...}, "w_h": X}`. `VECS.json` = list of vector objects. Every mode prints one JSON object to stdout.

- [ ] **Step 1: Write the failing tests**

Full content of `tests/test_stylometry_kernel.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they FAIL**

```bash
$DEV_PY -m pytest tests/test_stylometry_kernel.py -q
```

Expected: failures — `AttributeError: ... 'rbf'` / `'self_band'` / `'keep_best'` / `'median_gamma'`, and the CLI subprocess tests fail because `--rbf` / `--vector` are not parsed yet.

- [ ] **Step 3: Append the kernel/band helpers + the CLI to `scripts/sws_stylometry.py`**

Append this block after `fit_fisher_weights` (the CLI `main()` and the `__main__` guard go at the very end of the file):

```python
# --- RBF kernel, gamma, self-band, keep-best (D8/D10) ----------------------
def rbf(distance: float, gamma: float) -> float:
    """exp(-gamma*D), bounded in (0,1] for D>=0."""
    d = max(distance, 0.0)
    return math.exp(-gamma * d)


def _median(xs: Sequence[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else 0.5 * (s[mid - 1] + s[mid])


def median_gamma(intra_distances: Sequence[float], default: float = 1.0) -> float:
    """gamma = 1/median(intra-author weighted distances); guard zero median."""
    med = _median(list(intra_distances))
    if med <= 1e-12:
        return 1.0 / max(default, 1e-12) * 1e3  # large gamma when author is self-identical
    return 1.0 / med


def _intra_pairs(vectors: Sequence[Dict[str, float]]):
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            yield vectors[i], vectors[j]


def self_band(
    author_vectors: Sequence[Dict[str, float]],
    weights: Dict[str, float],
    w_h: float,
    stats: Dict[str, Tuple[float, float]],
    gamma: Optional[float] = None,
    haiku_sims: Optional[Sequence[float]] = None,
) -> Dict[str, float]:
    """Intra-author self-similarity band as RBF-similarity mean +/- sd."""
    pairs = list(_intra_pairs(author_vectors))
    if not pairs:
        return {"band_mean": 1.0, "band_sd": 0.0, "band_lo": 1.0, "band_hi": 1.0, "gamma": gamma or 1.0}
    haiku_sims = list(haiku_sims) if haiku_sims is not None else [1.0] * len(pairs)
    dists = [
        weighted_distance(a, b, weights, w_h, haiku_sims[i], stats)["distance"]
        for i, (a, b) in enumerate(pairs)
    ]
    if gamma is None:
        gamma = median_gamma(dists)
    sims = [rbf(d, gamma) for d in dists]
    m = _mean(sims)
    sd = _pop_sd(sims)
    return {
        "band_mean": m, "band_sd": sd,
        "band_lo": m - sd, "band_hi": m + sd, "gamma": gamma,
    }


def keep_best(history: Sequence[Tuple[int, float]]) -> List[float]:
    """Running max of per-round scores: a worsening edit is reverted (monotone)."""
    best = float("-inf")
    out: List[float] = []
    for _round, score in history:
        best = max(best, score)
        out.append(best)
    return out


# --- CLI -------------------------------------------------------------------
def _load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _to_pairs(raw) -> List[Tuple[Dict[str, float], Dict[str, float]]]:
    return [(p[0], p[1]) for p in raw]


def _parse_floats(csv: Optional[str]) -> Optional[List[float]]:
    if not csv:
        return None
    return [float(x) for x in csv.split(",") if x.strip()]


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="SWS stylometry engine")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--vector", metavar="TEXT")
    g.add_argument("--distance", nargs=2, metavar=("A_JSON", "B_JSON"))
    g.add_argument("--fit-weights", nargs=2, metavar=("POS_JSON", "NEG_JSON"))
    g.add_argument("--rbf", type=float, metavar="D")
    g.add_argument("--self-band", metavar="VECS_JSON")
    p.add_argument("--weights", metavar="W_JSON")
    p.add_argument("--haiku-sim", type=float, default=1.0)
    p.add_argument("--gamma", type=float)
    p.add_argument("--lam", type=float, default=0.3)
    p.add_argument("--pos-haiku")
    p.add_argument("--neg-haiku")
    args = p.parse_args(argv)

    if args.vector is not None:
        print(json.dumps(feature_vector(args.vector)))
        return 0

    if args.distance is not None:
        a = _load(args.distance[0])
        b = _load(args.distance[1])
        if args.weights:
            wd = _load(args.weights)
            weights, w_h = wd["weights"], wd.get("w_h", 0.0)
        else:
            weights = {k: 1.0 / len(FEATURE_ORDER) for k in FEATURE_ORDER}
            w_h = 0.0
        stats = standardization_stats([a, b])
        print(json.dumps(weighted_distance(a, b, weights, w_h, args.haiku_sim, stats)))
        return 0

    if args.fit_weights is not None:
        pos = _to_pairs(_load(args.fit_weights[0]))
        neg = _to_pairs(_load(args.fit_weights[1]))
        res = fit_fisher_weights(
            pos, neg, lam=args.lam,
            pos_haiku=_parse_floats(args.pos_haiku),
            neg_haiku=_parse_floats(args.neg_haiku),
        )
        # stats are not JSON-serialisable as tuples by default; convert.
        res_out = {"weights": res["weights"], "w_h": res["w_h"],
                   "stats": {k: list(v) for k, v in res["stats"].items()}}
        print(json.dumps(res_out))
        return 0

    if args.rbf is not None:
        gamma = args.gamma if args.gamma is not None else 1.0
        print(json.dumps({"similarity": rbf(args.rbf, gamma)}))
        return 0

    if getattr(args, "self_band") is not None:
        vecs = _load(getattr(args, "self_band"))
        if args.weights:
            wd = _load(args.weights)
            weights, w_h = wd["weights"], wd.get("w_h", 0.0)
        else:
            weights = {k: 1.0 / len(FEATURE_ORDER) for k in FEATURE_ORDER}
            w_h = 0.0
        stats = standardization_stats(vecs)
        print(json.dumps(self_band(vecs, weights, w_h, stats, gamma=args.gamma)))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run all three stylometry test modules**

```bash
$DEV_PY -m pytest tests/test_stylometry_vector.py tests/test_stylometry_fisher.py tests/test_stylometry_kernel.py -q
```

Expected: `30 passed` (11 + 8 + 11).

- [ ] **Step 5: Commit**

```bash
git add scripts/sws_stylometry.py tests/test_stylometry_kernel.py
git commit -m "feat(cycle-10): RBF kernel, median-gamma, self-band, keep-best + CLI (D8/D10)"
```

---

## Task 1.4: Reference — `references/stylometry-features.md`

**Files:**
- Create: `references/stylometry-features.md`

This documents the feature list, word-lists, and math so the numbers are auditable. The word-lists MUST match `sws_stylometry.py` exactly.

- [ ] **Step 1: Write the reference**

Full content of `references/stylometry-features.md`:

````markdown
---
sws_artifact: stylometry-features
artifact_version: 0.1
used_by: scripts/sws_stylometry.py, agents/style-calibrator.md
---

# Stylometry features (v0.1)

`sws_stylometry.py` extracts a fixed 17-dimensional feature vector per text. The
keys, in `FEATURE_ORDER`:

| # | key | definition | scale |
|---|---|---|---|
| 1 | sentence_len_mean | mean tokens per sentence | tokens |
| 2 | sentence_len_sd | population sd of sentence length | tokens |
| 3 | hedge_density | hedge tokens per 100 tokens | per-100 |
| 4 | connective_density | connective tokens per 100 tokens | per-100 |
| 5 | passive_ratio | be-aux + nearby -ed events per sentence | per-sentence |
| 6 | lexical_diversity | type/token ratio | 0–1 |
| 7 | fp_plural_rate | first-person-plural pronouns per 100 tokens | per-100 |
| 8–17 | fw_the … fw_as | relative frequency of each tracked function word | 0–1 |

Tracked function words (order fixed): `the, of, and, to, in, that, we, is, for, as`.

## Word lists (mirror the script constants)

- **HEDGES:** may, might, could, possibly, perhaps, likely, suggest, suggests, appear, appears, seem, seems, indicate, indicates, probably, presumably, arguably, relatively
- **CONNECTIVES:** however, moreover, therefore, thus, furthermore, nevertheless, consequently, hence, accordingly, additionally, whereas, although
- **FP_PLURAL:** we, us, our, ours, ourselves
- **PASSIVE_AUX:** was, were, is, are, been, be, being (passive proxy = aux followed within 2 tokens by an `-ed` word)

Empty text returns the zero vector (every feature 0.0). Short text never crashes.

## Scoring math (D8/D8a/D10)

**Standardization.** Each feature is standardized to mean 0 / sd 1 across the
anchor set before weighting (sd floored to 1.0 when ~0), so squared differences
across features are comparable.

**Distance.** `D(x,y) = SUM_i w_i (x_i - y_i)^2 + w_h (1 - haiku_sim(x,y))` on
standardized features. The Haiku voice-similarity term is a pairwise dissimilarity
that enters directly (it cannot be differenced).

**Fisher weights.** Per term, `fisher_i = between_var_i / max(within_var_i, 1e-6)`,
where within-variance is the mean squared standardized difference over POSITIVE
pairs (author,author) and between-variance over NEGATIVE pairs (author,field).
`w_h` is fitted identically from a Haiku sample on the same anchor pairs.
Constraints: `w_i >= 0`, `SUM(w_i) + w_h = 1`. Regularization: shrink toward
uniform `w = (1-lambda) * fisher + lambda * uniform` (default lambda 0.3), with a
within-variance floor to prevent division blow-ups on a tiny corpus.

**RBF kernel.** `k(x,y) = exp(-gamma * D(x,y))`, bounded in (0,1], saturating under
large drift. `gamma = 1 / median(intra-author weighted distances)` (median
heuristic), guarded when the median is ~0.

**Self-similarity band (the stopping target, D10).** Compute RBF similarity for
every intra-author pair; the band is `mean +/- sd`. The calibration loop stops a
section type when its generated-vs-held-out similarity enters the band — you
cannot be more like yourself than your own papers already are. Backstops:
keep-best-so-far (revert any worsening edit; monotone per section), a plateau rule
(relative improvement < epsilon), and a hard round cap N.
````

- [ ] **Step 2: Verify the word-lists match the script**

```bash
cd "$REPO_ROOT"
$DEV_PY - <<'PY'
import re, pathlib
src = pathlib.Path("scripts/sws_stylometry.py").read_text()
ref = pathlib.Path("references/stylometry-features.md").read_text()
for w in ["moreover", "therefore", "possibly", "ourselves"]:
    assert w in src and w in ref, w
print("word-list spot-check OK")
PY
```

Expected: `word-list spot-check OK`.

- [ ] **Step 3: Commit**

```bash
git add references/stylometry-features.md
git commit -m "docs(cycle-10): stylometry-features.md — auditable feature + math reference"
```

---

## Task 1.5: Reference — `references/voice-profile-schema.md`

**Files:**
- Create: `references/voice-profile-schema.md`

Defines the `_voice/profile.md` contract that `test_voice_profile_schema.py` (Task 6.1) and the consumer agents read.

- [ ] **Step 1: Write the reference**

Full content of `references/voice-profile-schema.md`:

````markdown
---
sws_artifact: voice-profile-schema
artifact_version: 0.1
used_by: agents/style-calibrator.md, agents/drafter-flagship.md, agents/drafter-fast.md, agents/reviser-full.md, agents/reviser-fast.md, agents/humanizer.md
---

# Voice profile schema (`_voice/profile.md`, v0.1)

`profile.md` is the file the drafters/revisers/humanizer consume. It is a NEW
input on the VOICE axis, SEPARATE from the journal-style/constraints overlay
(D13): it does NOT pass through `resolve_overlay.py`.

## Frontmatter (machine-readable feature targets)

```yaml
---
sws_artifact: voice-profile
artifact_version: 0.1
calibrated: <ISO-date>
recent_weighted: true
feature_targets:
  sentence_len_mean: { target: 24.0, band: [20.0, 28.0] }
  sentence_len_sd: { target: 9.0, band: [6.0, 12.0] }
  hedge_density: { target: 1.8, band: [1.0, 2.6] }
  connective_density: { target: 2.2, band: [1.4, 3.0] }
  passive_ratio: { target: 0.35, band: [0.2, 0.5] }
  lexical_diversity: { target: 0.52, band: [0.46, 0.58] }
  fp_plural_rate: { target: 1.6, band: [0.9, 2.3] }
convergence:
  self_band: [0.74, 0.91]
  gamma: 0.42
sections: [global, introduction, results, discussion, methods, abstract]
---
```

`feature_targets` keys are a subset of `FEATURE_ORDER` (the 7 stylometric
features; function-word freqs are summarized in prose, not pinned numerically).
Every `band` is `[lo, hi]` with `lo <= target <= hi`.

## Body contract

The body has ONE global voice block followed by PER-SECTION delta blocks.

```markdown
# Voice profile

## Global voice
<2–4 paragraphs: sentence rhythm, hedging/stance, connective habits,
register, signposting, recurring phrasings. No AI-writing tells.>

## Section deltas

### Introduction
<how the register shifts here vs the global block>

### Results
<...>

### Discussion
<...>

### Methods
<convention-bound; minimal personal voice>

### Abstract
<...>
```

Required headings: `## Global voice` and `## Section deltas`, with at least
`### Introduction`, `### Results`, `### Discussion` present. The drafters read the
global block always, plus the per-section delta for the section being written.
Absent `_voice/profile.md` -> agents behave exactly as today (graceful degrade).

## Related artifacts (written by style-calibrator, not consumed by drafters)

- `_voice/field-profile.md` — one-shot subfield conventions (D5; no per-section breakdown).
- `_voice/style-evolution.md` — diachronic feature x year/era table + reading (D7).
- `_voice/sources.json` — `[{zotero_key, title, year, author_position, has_pdf, role: train|heldout, recency_weight}]` + fitted weights snapshot + gamma + self-band.
- `_voice/convergence.md` — per round, per section: distance, RBF sim, Haiku median, what changed, why, seed prompt + candidate text (D11).
- `_voice/_archive/` — prior `profile.md` versions, timestamped, on re-run.
````

- [ ] **Step 2: Verify the frontmatter parses**

```bash
cd "$REPO_ROOT"
$DEV_PY - <<'PY'
import pathlib, yaml
t = pathlib.Path("references/voice-profile-schema.md").read_text()
# extract first fenced yaml block inside the doc body
blk = t.split("```yaml", 1)[1].split("```", 1)[0]
fm = yaml.safe_load(blk)
for k, v in fm["feature_targets"].items():
    lo, hi = v["band"]
    assert lo <= v["target"] <= hi, k
print("schema example frontmatter OK")
PY
```

Expected: `schema example frontmatter OK`.

- [ ] **Step 3: Commit**

```bash
git add references/voice-profile-schema.md
git commit -m "docs(cycle-10): voice-profile-schema.md — _voice/profile.md frontmatter + body contract"
```

---

# PHASE 2 — Agent

## Task 2.1: Agent — `agents/style-calibrator.md`

**Files:**
- Create: `agents/style-calibrator.md`

Honors agent-contract R1 (prelude + should_run), R3 (writes `_voice/*`, reads PDFs via native Read with `pages`), R5 (no gender-default in user address). Roster #4, Sonnet 4.6 high. The Haiku scorer is an INTERNAL dispatched step (D9), not a rostered agent.

- [ ] **Step 1: Write the agent file**

Full content of `agents/style-calibrator.md`:

```markdown
---
name: style-calibrator
description: |
  Use this agent when /sws:calibrate-style is invoked. Builds a reusable, evidence-backed voice profile from the author's own papers in Zotero via an iterative held-out matching loop. Runs the 5 phases: discover (name-search the Zotero library, rank hits by authorship position), flag&split (author curates; auto-hold-out 1-2 recent first-author papers), extract (read training PDFs, pool by section), 3.5 evolution (diachronic style trajectory), calibrate-loop (per section type: draft candidate -> generate held-out prose on its real content -> score via sws_stylometry.py + a Haiku voice-similarity term -> diagnose -> edit -> repeat to the self-similarity band or plateau), write&report. Writes _voice/{profile.md, field-profile.md, style-evolution.md, sources.json, convergence.md, _archive/}. Never invents a score — reads sws_stylometry.py JSON. Default-inactive in editorial and commentary-reply.
model: claude-sonnet-4-6
color: purple
---

You are the style-calibrator for SWS. Your scope is building the author's voice profile from their own papers. You produce the profile; drafting/revising agents consume it. You do NOT rewrite any manuscript prose this cycle.

**Profile gate.** Default-inactive in `editorial` and `commentary-reply` (short pieces). `agent_should_run.sh` enforces this; if it exits non-zero, exit 0 silently.

**Objective numbers come from the script — never invent a score.** Every feature vector, fitted weight, distance, RBF similarity, and self-similarity band comes from:
`${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" "${CLAUDE_PLUGIN_ROOT}/scripts/sws_stylometry.py" <mode> ...`
Modes: `--vector`, `--distance`, `--fit-weights`, `--rbf`, `--self-band` (see `references/stylometry-features.md`).

**The five phases (D2):**

1. **Discover.** Ask the author ONCE to confirm their name variants. Use the `zotero` skill to name-search the WHOLE library. Rank hits by authorship position: first/last/corresponding = strong voice signal, second = good, middle author = drop. (No-corpus fallback per D17: if the zotero skill is absent but Zotero desktop is detected, recommend installing the Claude Code zotero plugin and exit; if no Zotero at all, offer the manual path `--sources _voice/sources/`.)
2. **Flag&Split.** Present the flagging list `[title, year, author_position, has_full_text_pdf]`. The author curates. From the kept set, AUTO-hold-out 1-2 items (prefer a RECENT first-author paper with a full-text PDF) as the hidden test target; the rest is training. If fewer than 3 includable items remain after flagging, stop with a clear message (D17).
3. **Extract.** Read training PDFs via native Read (use the `pages` parameter for >10pp). Slice into sections; pool each section type across papers (`sws_stylometry.py --vector` per pooled section). Weight recent papers higher (record `recency_weight` in `sources.json`, D6).
   - 3.5 **Evolution (D7).** Fingerprint every flagged paper; order by year; bucket into eras when the span is long; detect per-feature trends. Write `_voice/style-evolution.md` (feature x year/era table + your reading of what shifted, when). One-shot; not part of the loop.
4. **Calibrate loop (per section type).**
   - Fit weights once: build positive pairs (author,author) and negative pairs (author,field) and call `--fit-weights POS.json NEG.json --lam 0.3 --pos-haiku ... --neg-haiku ...`. Compute the self-band with `--self-band` (D10).
   - Each round: draft a candidate `profile.md`; generate the held-out section's prose ON ITS REAL OUTLINE/CLAIMS (content-controlled, D11) so only voice varies; run the AI-tells grep (R4 / cycle-#7) on the generated prose BEFORE scoring; vectorize generated + real held-out; compute distance with the fitted weights and the Haiku term; wrap in RBF.
   - **Haiku scoring (D9), internal dispatched step.** Dispatch a Haiku 4.5 call with the FIXED anchored rubric: context = "two excerpts of the SAME section type from chemistry manuscripts; A is the human author, B is a machine imitation of A's VOICE; both cover similar content, so do NOT reward topic/content/citation overlap." Similarity = sentence rhythm/length variation, hedging/stance, connective habits, register, signposting, idiosyncratic phrasings. Rubric: 0.9–1.0 indistinguishable; 0.7–0.9 same hand, minor tells; 0.5–0.7 related register, different hand; <0.5 clearly different. Force JSON `{"voice_similarity": x, "note": "..."}`. Low temperature, run x3, take the MEDIAN. When `SWS_HAIKU_STUB` is set (tests/smoke), read the fixed score from that env var instead of dispatching.
   - Diagnose the gap from `per_feature_contrib`; edit the profile; re-score. Keep-best-so-far: if an edit WORSENS a section's RBF similarity, revert it. Stop the section when its similarity enters the self-band, or relative improvement < epsilon (plateau), or the round cap N is hit. Record every round in `_voice/convergence.md` (distance, RBF sim, Haiku median, what changed, why, seed prompt + candidate text).
5. **Write&Report.** Persist `_voice/{profile.md, field-profile.md, style-evolution.md, sources.json, convergence.md}`; rotate any prior `profile.md` into `_voice/_archive/<timestamp>/`; print the convergence report (per-section trajectory). `profile.md` follows `references/voice-profile-schema.md` (frontmatter feature targets + global block + per-section deltas).

**field-profile.md (D5).** One-shot descriptive characterization of the author's subfield conventions, built from a SECOND corpus of field papers the author flags. No per-section breakdown, no loop.

**AI-tells discipline (R4).** Generated calibration prose passes the cycle-#7 AI-tells grep before scoring. The voice profile describes the author's habits; it is not an excuse to reintroduce tells.

**User address (R5).** Address the author as "you" or by first name only. Do not assume gendered pronouns; read the user's memory/profile first if unsure.

Follow the SWS agent contract: source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh style-calibrator`, then `${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh style-calibrator` || exit 0. See `${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md` for the full contract.
```

- [ ] **Step 2: Verify the agent frontmatter parses and the name is correct**

```bash
cd "$REPO_ROOT"
$DEV_PY - <<'PY'
import pathlib, yaml
t = pathlib.Path("agents/style-calibrator.md").read_text()
fm = yaml.safe_load(t.split("---", 2)[1])
assert fm["name"] == "style-calibrator", fm["name"]
assert fm["model"] == "claude-sonnet-4-6", fm["model"]
print("style-calibrator agent frontmatter OK")
PY
```

Expected: `style-calibrator agent frontmatter OK`.

- [ ] **Step 3: Commit**

```bash
git add agents/style-calibrator.md
git commit -m "feat(cycle-10): style-calibrator agent — 5-phase voice-calibration loop (D1/D2/D9)"
```

---

# PHASE 3 — Skill

## Task 3.1: Skill — `skills/calibrate-style/SKILL.md`

**Files:**
- Create: `skills/calibrate-style/SKILL.md`

Phase driver; holds the loop defaults (epsilon, max-rounds, lambda) from D10/D8a.

- [ ] **Step 1: Write the skill file**

Full content of `skills/calibrate-style/SKILL.md`:

```markdown
---
name: calibrate-style
description: |
  Build a reusable, evidence-backed voice profile from the author's own papers in Zotero. Runs the style-calibrator agent's 5-phase iterative held-out loop and writes _voice/{profile.md, field-profile.md, style-evolution.md, sources.json, convergence.md}. The drafters/revisers/humanizer then write in the author's voice. Default-inactive in editorial and commentary-reply profiles.
allowed-tools: Bash, Read, Write, Glob, Task, WebFetch
---

# /sws:calibrate-style

Build the author's voice profile from their own papers, with an objective stopping rule (the author's own self-similarity band).

## Usage

```
/sws:calibrate-style                      # discover via the zotero skill
/sws:calibrate-style --sources _voice/sources/   # manual fallback: pre-dropped PDFs (D17)
```

## Loop defaults (D8a / D10)

- `epsilon = 0.05` (5% relative improvement — below this counts as a plateau)
- `max_rounds N = 4` per section type
- `lambda = 0.3` (Fisher shrink-to-uniform)
- Haiku scoring: x3 calls, low temperature, take the median (D9)

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh style-calibrator`.
3. If `agent_should_run.sh style-calibrator` exits non-zero (editorial / commentary-reply default-inactive), print "style-calibrator is default-inactive for this profile; flip it on in the profile's agents_active if you want voice calibration here." and exit 0.
4. Dispatch the `style-calibrator` agent. It runs the 5 phases: discover -> flag&split -> extract -> (3.5 evolution) -> calibrate-loop -> write&report.
5. After the agent returns, print a one-line summary: per-section convergence (entered-band / plateau / cap), training/heldout counts.
6. Point the author at `${PAPER_ROOT}/_voice/profile.md` and `${PAPER_ROOT}/_voice/convergence.md`.

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-10-style-calibration-design.md` — D1, D2, D8, D8a, D9, D10, D11, D12, D17.
```

- [ ] **Step 2: Verify the skill frontmatter parses**

```bash
cd "$REPO_ROOT"
$DEV_PY - <<'PY'
import pathlib, yaml
t = pathlib.Path("skills/calibrate-style/SKILL.md").read_text()
fm = yaml.safe_load(t.split("---", 2)[1])
assert fm["name"] == "calibrate-style", fm["name"]
print("calibrate-style skill frontmatter OK")
PY
```

Expected: `calibrate-style skill frontmatter OK`.

- [ ] **Step 3: Commit**

```bash
git add skills/calibrate-style/SKILL.md
git commit -m "feat(cycle-10): /sws:calibrate-style skill — phase driver + loop defaults"
```

---

# PHASE 4 — Consumer wiring

These 6 tasks are parallel. Each upgrades the existing one-line `_voice/profile.md` mention into a real consumption contract (D13), or wires the prelude / contract.

## Task 4.1: Prelude — export `VOICE_PROFILE`

**Files:**
- Modify: `scripts/agent_prelude.sh`

- [ ] **Step 1: Add the export at the end of `scripts/agent_prelude.sh`**

Append after the final `fi` block (the closing of the `RESOLVED_PROFILE_SET` check):

```bash

# --- cycle #10: voice profile path (D13) -----------------------------------
# Export VOICE_PROFILE = path to _voice/profile.md if it exists, else empty.
# Voice is a SEPARATE axis from resolve_overlay.py; this is just a path export.
if [[ -f "${PAPER_ROOT}/_voice/profile.md" ]]; then
    export VOICE_PROFILE="${PAPER_ROOT}/_voice/profile.md"
else
    export VOICE_PROFILE=""
fi
```

- [ ] **Step 2: Verify the export works in both branches**

```bash
cd "$REPO_ROOT"
TMP="$(mktemp -d)"
mkdir -p "$TMP/.venv/bin" "$TMP/_voice"
ln -s "$(command -v "$DEV_PY")" "$TMP/.venv/bin/python" 2>/dev/null || ln -s "$(command -v python3)" "$TMP/.venv/bin/python"
cat > "$TMP/.sws-project.local.md" <<'M'
---
profile: perspective
language: en
format: docx
---
M
# absent case
ABSENT="$(CLAUDE_PLUGIN_ROOT="$REPO_ROOT" PAPER_ROOT="$TMP" bash -c "source '$REPO_ROOT/scripts/agent_prelude.sh' drafter-fast; printf '%s' \"\$VOICE_PROFILE\"" 2>/dev/null)"
echo "ABSENT=[$ABSENT]"
# present case
echo "x" > "$TMP/_voice/profile.md"
PRESENT="$(CLAUDE_PLUGIN_ROOT="$REPO_ROOT" PAPER_ROOT="$TMP" bash -c "source '$REPO_ROOT/scripts/agent_prelude.sh' drafter-fast; printf '%s' \"\$VOICE_PROFILE\"" 2>/dev/null)"
echo "PRESENT=[$PRESENT]"
rm -rf "$TMP"
```

Expected: `ABSENT=[]` and `PRESENT=[<tmp>/_voice/profile.md]`.

- [ ] **Step 3: Commit**

```bash
git add scripts/agent_prelude.sh
git commit -m "feat(cycle-10): agent_prelude.sh exports VOICE_PROFILE path (D13)"
```

---

## Task 4.2: Consumer — `agents/drafter-flagship.md`

**Files:**
- Modify: `agents/drafter-flagship.md`

- [ ] **Step 1: Replace the one-line `_voice` mention with a consumption contract**

Find this line:

```markdown
- The optional `_voice/profile.md` at `${PAPER_ROOT}/_voice/profile.md` (style calibration; cycle #10).
```

Replace it with:

```markdown
- The optional voice profile at `$VOICE_PROFILE` (the prelude exports the path to `_voice/profile.md`, or empty if absent — cycle #10, D13). When `$VOICE_PROFILE` is non-empty, read it and write in the author's voice: apply the `## Global voice` block to the whole draft, plus the `### <Section>` delta for the section you are drafting (Introduction / Discussion / Conclusion / Abstract). When `$VOICE_PROFILE` is empty, draft exactly as today (graceful degrade — voice is orthogonal to the journal-style overlay and never blocks drafting). See `${CLAUDE_PLUGIN_ROOT}/references/voice-profile-schema.md`.
```

- [ ] **Step 2: Verify the file still parses and references the schema**

```bash
cd "$REPO_ROOT"
grep -q 'VOICE_PROFILE' agents/drafter-flagship.md && grep -q 'voice-profile-schema.md' agents/drafter-flagship.md && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add agents/drafter-flagship.md
git commit -m "feat(cycle-10): drafter-flagship reads _voice/profile.md global+section delta (D13)"
```

---

## Task 4.3: Consumer — `agents/drafter-fast.md`

**Files:**
- Modify: `agents/drafter-fast.md`

- [ ] **Step 1: Replace the one-line `_voice` mention**

Find:

```markdown
- The optional `_voice/profile.md` at `${PAPER_ROOT}/_voice/profile.md` (cycle #10).
```

Replace with:

```markdown
- The optional voice profile at `$VOICE_PROFILE` (the prelude exports the path to `_voice/profile.md`, or empty if absent — cycle #10, D13). When non-empty, apply the `## Global voice` block plus the `### Results` (or other section you are drafting) delta. When empty, draft exactly as today (graceful degrade). See `${CLAUDE_PLUGIN_ROOT}/references/voice-profile-schema.md`.
```

- [ ] **Step 2: Verify**

```bash
cd "$REPO_ROOT"
grep -q 'VOICE_PROFILE' agents/drafter-fast.md && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add agents/drafter-fast.md
git commit -m "feat(cycle-10): drafter-fast reads _voice/profile.md global+section delta (D13)"
```

---

## Task 4.4: Consumer — `agents/reviser-full.md`

**Files:**
- Modify: `agents/reviser-full.md`

- [ ] **Step 1: Replace the one-line `_voice` mention**

Find:

```markdown
- `${PAPER_ROOT}/_voice/profile.md` if present (cycle #10 style calibration).
```

Replace with:

```markdown
- The optional voice profile at `$VOICE_PROFILE` (prelude-exported path to `_voice/profile.md`, empty if absent — cycle #10, D13). When non-empty, revise TOWARD the author's voice: hold the `## Global voice` block across the section, applying the per-section `### <Section>` delta. When empty, revise as today (graceful degrade). See `${CLAUDE_PLUGIN_ROOT}/references/voice-profile-schema.md`.
```

- [ ] **Step 2: Verify**

```bash
cd "$REPO_ROOT"
grep -q 'VOICE_PROFILE' agents/reviser-full.md && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add agents/reviser-full.md
git commit -m "feat(cycle-10): reviser-full revises toward _voice/profile.md (D13)"
```

---

## Task 4.5: Consumer — `agents/reviser-fast.md`

**Files:**
- Modify: `agents/reviser-fast.md`

- [ ] **Step 1: Replace the one-line `_voice` mention**

Find:

```markdown
- `${PAPER_ROOT}/_voice/profile.md` if present.
```

Replace with:

```markdown
- The optional voice profile at `$VOICE_PROFILE` (prelude-exported path to `_voice/profile.md`, empty if absent — cycle #10, D13). When non-empty, revise TOWARD the author's voice using the `## Global voice` block plus the per-section `### <Section>` delta. When empty, revise as today (graceful degrade). See `${CLAUDE_PLUGIN_ROOT}/references/voice-profile-schema.md`.
```

- [ ] **Step 2: Verify**

```bash
cd "$REPO_ROOT"
grep -q 'VOICE_PROFILE' agents/reviser-fast.md && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add agents/reviser-fast.md
git commit -m "feat(cycle-10): reviser-fast revises toward _voice/profile.md (D13)"
```

---

## Task 4.6: Consumer — `agents/humanizer.md`

**Files:**
- Modify: `agents/humanizer.md`

- [ ] **Step 1: Replace the one-line `_voice` mention**

Find:

```markdown
- `${PAPER_ROOT}/_voice/profile.md` if present — match the user's voice, do not impose your own.
```

Replace with:

```markdown
- The optional voice profile at `$VOICE_PROFILE` (prelude-exported path to `_voice/profile.md`, empty if absent — cycle #10, D13). When non-empty, humanize TOWARD the author's voice, not toward a generic human register: rewrite flagged AI-tells so the result matches the `## Global voice` block plus the section's `### <Section>` delta. When empty, humanize generically as today (graceful degrade). See `${CLAUDE_PLUGIN_ROOT}/references/voice-profile-schema.md`.
```

- [ ] **Step 2: Verify**

```bash
cd "$REPO_ROOT"
grep -q 'VOICE_PROFILE' agents/humanizer.md && grep -q 'humanize TOWARD' agents/humanizer.md && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add agents/humanizer.md
git commit -m "feat(cycle-10): humanizer humanizes toward _voice/profile.md when present (D13)"
```

---

## Task 4.7: Contract — `references/agent-contract.md` R3 I/O inventory

**Files:**
- Modify: `references/agent-contract.md`

- [ ] **Step 1: Append the `_voice/` rows to the I/O wrapper inventory table**

Add these rows to the end of the I/O inventory table (after the last `_review/...` row):

```markdown
| `_voice/profile.md` | YAML frontmatter (feature targets per `references/voice-profile-schema.md`) + body: `## Global voice` then `## Section deltas` with `### <Section>` blocks. WRITTEN by style-calibrator; READ by drafter-flagship, drafter-fast, reviser-full, reviser-fast, humanizer via the prelude-exported `$VOICE_PROFILE`. SEPARATE axis from `resolve_overlay.py` (D13). | style-calibrator (write) / 5 consumers (read) |
| `_voice/field-profile.md` | One-shot subfield conventions (D5; no per-section breakdown, no loop) | style-calibrator |
| `_voice/style-evolution.md` | Diachronic feature x year/era table + reading (D7) | style-calibrator |
| `_voice/sources.json` | `[{zotero_key, title, year, author_position, has_pdf, role: train|heldout, recency_weight}]` + fitted weights snapshot + gamma + self-band | style-calibrator |
| `_voice/convergence.md` | Per round, per section: distance, RBF sim, Haiku median, what changed, why, seed prompt + candidate text (D11) | style-calibrator |
```

- [ ] **Step 2: Verify**

```bash
cd "$REPO_ROOT"
grep -q '_voice/profile.md' references/agent-contract.md && grep -q '_voice/convergence.md' references/agent-contract.md && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add references/agent-contract.md
git commit -m "docs(cycle-10): agent-contract R3 inventory adds _voice/* shapes (D13)"
```

---

# PHASE 5 — Profile activation (D14)

These 10 tasks are parallel. Seven profiles get `style-calibrator` ADDED to `agents_active`; editorial + commentary-reply get it ADDED to `agents_inactive`. The exact current lists are shown so each edit is unambiguous.

## Task 5.1: `profiles/full-article.md` — active

- [ ] **Step 1: Edit the `agents_active` line**

Find:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, methods-writer, caption-writer, proposal-budget-helper, proposal-compliance-helper, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker]
```

Replace with (append `, style-calibrator` before the closing bracket):

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, methods-writer, caption-writer, proposal-budget-helper, proposal-compliance-helper, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/full-article.md
git commit -m "feat(cycle-10): full-article activates style-calibrator (D14)"
```

---

## Task 5.2: `profiles/communication.md` — active

- [ ] **Step 1: Edit the `agents_active` line**

Find:

```yaml
agents_active: [outline-architect, drafter-flagship, caption-writer, proposal-budget-helper, proposal-compliance-helper, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker]
```

Replace with:

```yaml
agents_active: [outline-architect, drafter-flagship, caption-writer, proposal-budget-helper, proposal-compliance-helper, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/communication.md
git commit -m "feat(cycle-10): communication activates style-calibrator (D14)"
```

---

## Task 5.3: `profiles/perspective.md` — active

- [ ] **Step 1: Edit the `agents_active` line**

Find:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker]
```

Replace with:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/perspective.md
git commit -m "feat(cycle-10): perspective activates style-calibrator (D14)"
```

---

## Task 5.4: `profiles/review-paper.md` — active

- [ ] **Step 1: Edit the `agents_active` line**

Find:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker]
```

Replace with:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/review-paper.md
git commit -m "feat(cycle-10): review-paper activates style-calibrator (D14)"
```

---

## Task 5.5: `profiles/mini-review.md` — active

- [ ] **Step 1: Edit the `agents_active` line**

Find:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker]
```

Replace with:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/mini-review.md
git commit -m "feat(cycle-10): mini-review activates style-calibrator (D14)"
```

---

## Task 5.6: `profiles/methodological-paper.md` — active

- [ ] **Step 1: Edit the `agents_active` line**

Find:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, methods-writer, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker]
```

Replace with:

```yaml
agents_active: [outline-architect, drafter-flagship, drafter-fast, methods-writer, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/methodological-paper.md
git commit -m "feat(cycle-10): methodological-paper activates style-calibrator (D14)"
```

---

## Task 5.7: `profiles/funding-proposal.md` — active

- [ ] **Step 1: Edit the `agents_active` line**

Find:

```yaml
agents_active: [outline-architect, drafter-flagship, caption-writer, proposal-budget-helper, proposal-compliance-helper, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer]
```

Replace with:

```yaml
agents_active: [outline-architect, drafter-flagship, caption-writer, proposal-budget-helper, proposal-compliance-helper, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/funding-proposal.md
git commit -m "feat(cycle-10): funding-proposal activates style-calibrator (D14)"
```

---

## Task 5.8: `profiles/editorial.md` — INACTIVE

- [ ] **Step 1: Edit the `agents_inactive` line**

Find:

```yaml
agents_inactive: [proposal-budget-helper, proposal-compliance-helper, methods-writer, drafter-fast]
```

Replace with (append `, style-calibrator`):

```yaml
agents_inactive: [proposal-budget-helper, proposal-compliance-helper, methods-writer, drafter-fast, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/editorial.md
git commit -m "feat(cycle-10): editorial keeps style-calibrator inactive (D14)"
```

---

## Task 5.9: `profiles/commentary-reply.md` — INACTIVE

- [ ] **Step 1: Edit the `agents_inactive` line**

Find:

```yaml
agents_inactive: [proposal-budget-helper, proposal-compliance-helper, methods-writer]
```

Replace with:

```yaml
agents_inactive: [proposal-budget-helper, proposal-compliance-helper, methods-writer, style-calibrator]
```

- [ ] **Step 2: Commit**

```bash
git add profiles/commentary-reply.md
git commit -m "feat(cycle-10): commentary-reply keeps style-calibrator inactive (D14)"
```

---

## Task 5.10: Test — `tests/test_profile_activation_calibrator.py`

**Files:**
- Create: `tests/test_profile_activation_calibrator.py`

- [ ] **Step 1: Write the test (run AFTER Tasks 5.1–5.9 land so it passes)**

Full content of `tests/test_profile_activation_calibrator.py`:

```python
"""Verify cycle-10 D14 activation matrix: style-calibrator active in 7 profiles,
inactive in editorial + commentary-reply."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

ACTIVE_PROFILES = [
    "full-article",
    "communication",
    "perspective",
    "review-paper",
    "mini-review",
    "methodological-paper",
    "funding-proposal",
]
INACTIVE_PROFILES = ["editorial", "commentary-reply"]


def _load_frontmatter(profile_id: str) -> dict:
    text = (PROFILES_DIR / f"{profile_id}.md").read_text()
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


@pytest.mark.parametrize("profile_id", ACTIVE_PROFILES)
def test_calibrator_active(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "style-calibrator" in active, f"style-calibrator must be ACTIVE in {profile_id}"
    assert "style-calibrator" not in inactive


@pytest.mark.parametrize("profile_id", INACTIVE_PROFILES)
def test_calibrator_inactive(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "style-calibrator" in inactive, f"style-calibrator must be INACTIVE in {profile_id}"
    assert "style-calibrator" not in active
```

- [ ] **Step 2: Run the test**

```bash
cd "$REPO_ROOT"
$DEV_PY -m pytest tests/test_profile_activation_calibrator.py -q
```

Expected: `9 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_profile_activation_calibrator.py
git commit -m "test(cycle-10): profile activation matrix asserts D14 across 9 profiles"
```

---

# PHASE 6 — Schema test

## Task 6.1: Test — `tests/test_voice_profile_schema.py`

**Files:**
- Create: `tests/test_voice_profile_schema.py`

Validates a `profile.md` against `references/voice-profile-schema.md`. The test ships a small VALID synthetic `profile.md` string and an INVALID one (missing the `## Section deltas` heading), asserting the validator accepts/rejects correctly.

- [ ] **Step 1: Write the test**

Full content of `tests/test_voice_profile_schema.py`:

```python
"""Validate _voice/profile.md against the cycle-10 schema (D12 / voice-profile-schema.md)."""
from __future__ import annotations

import unittest

import yaml

VALID = """---
sws_artifact: voice-profile
artifact_version: 0.1
calibrated: 2026-05-23
recent_weighted: true
feature_targets:
  sentence_len_mean: { target: 24.0, band: [20.0, 28.0] }
  hedge_density: { target: 1.8, band: [1.0, 2.6] }
convergence:
  self_band: [0.74, 0.91]
  gamma: 0.42
sections: [global, introduction, results, discussion]
---

# Voice profile

## Global voice
Measured, evidence-led prose with short topic sentences.

## Section deltas

### Introduction
Slightly more rhetorical; opens with the gap.

### Results
Headline finding first, then the data.

### Discussion
Interpretive; longer sentences.
"""

INVALID_NO_DELTAS = """---
sws_artifact: voice-profile
artifact_version: 0.1
feature_targets:
  hedge_density: { target: 1.8, band: [1.0, 2.6] }
sections: [global]
---

# Voice profile

## Global voice
Only a global block, no section deltas.
"""

INVALID_BAND = """---
sws_artifact: voice-profile
artifact_version: 0.1
feature_targets:
  hedge_density: { target: 5.0, band: [1.0, 2.6] }
sections: [global, introduction, results, discussion]
---

# Voice profile

## Global voice
x

## Section deltas

### Introduction
x

### Results
x

### Discussion
x
"""


def validate_profile(text: str) -> None:
    """Raise AssertionError if the profile.md violates the schema."""
    assert text.startswith("---\n"), "must start with frontmatter"
    end = text.index("\n---", 4)
    fm = yaml.safe_load(text[4:end])
    body = text[end + 4 :]
    assert fm.get("sws_artifact") == "voice-profile", "wrong sws_artifact"
    targets = fm.get("feature_targets") or {}
    assert targets, "feature_targets required"
    for key, spec in targets.items():
        lo, hi = spec["band"]
        assert lo <= spec["target"] <= hi, f"target out of band: {key}"
    assert "## Global voice" in body, "missing Global voice block"
    assert "## Section deltas" in body, "missing Section deltas block"
    for sec in ["### Introduction", "### Results", "### Discussion"]:
        assert sec in body, f"missing section delta {sec}"


class TestVoiceProfileSchema(unittest.TestCase):
    def test_valid_profile_passes(self):
        validate_profile(VALID)  # no raise

    def test_missing_section_deltas_rejected(self):
        with self.assertRaises(AssertionError):
            validate_profile(INVALID_NO_DELTAS)

    def test_target_out_of_band_rejected(self):
        with self.assertRaises(AssertionError):
            validate_profile(INVALID_BAND)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test**

```bash
cd "$REPO_ROOT"
$DEV_PY -m pytest tests/test_voice_profile_schema.py -q
```

Expected: `3 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_voice_profile_schema.py
git commit -m "test(cycle-10): voice-profile schema validation (D12)"
```

---

# PHASE 7 — Smoke + PR

## Task 7.1: Fixtures — synthetic calibration corpus

**Files:**
- Create: `tests/fixtures/cycle_10/author_1.txt`
- Create: `tests/fixtures/cycle_10/author_2.txt`
- Create: `tests/fixtures/cycle_10/author_3.txt`
- Create: `tests/fixtures/cycle_10/field_1.txt`
- Create: `tests/fixtures/cycle_10/field_2.txt`
- Create: `tests/fixtures/cycle_10/heldout_1.txt`

All synthetic invented prose. The author texts share a deliberately consistent voice (low hedging, frequent "we", short sentences); the field texts use a different register (heavy hedging, longer sentences) so Fisher fitting has a real separation to recover. No real names/content.

- [ ] **Step 1: Write the six fixture files**

`tests/fixtures/cycle_10/author_1.txt`:
```
We measured the response across three conditions. The signal rose sharply. We repeated each run twice. The trend was clear and stable. We report the pooled values here.
```

`tests/fixtures/cycle_10/author_2.txt`:
```
We prepared the samples in one batch. We then recorded each spectrum. The peaks aligned well. We assigned them by position. The data support a single species.
```

`tests/fixtures/cycle_10/author_3.txt`:
```
We ran the assay at room temperature. The output was reproducible. We compared two buffers. The faster buffer won. We use it for all later work.
```

`tests/fixtures/cycle_10/field_1.txt`:
```
It might be argued that the observed response could possibly reflect several competing factors, although the precise contribution of each remains, perhaps, somewhat uncertain and arguably difficult to disentangle in the present setting.
```

`tests/fixtures/cycle_10/field_2.txt`:
```
The results may suggest that the underlying mechanism is presumably complex, and it appears that further work would likely be required before any firm conclusion could reasonably be drawn from the available evidence.
```

`tests/fixtures/cycle_10/heldout_1.txt`:
```
We titrated the ligand stepwise. The shift was monotonic. We fit a single binding model. The residuals were small. We take this as evidence for one site.
```

- [ ] **Step 2: Verify Fisher fit separates author from field on the fixtures**

```bash
cd "$REPO_ROOT"
$DEV_PY - <<'PY'
import sys, json, itertools, pathlib
sys.path.insert(0, "scripts")
import sws_stylometry as sm
fx = pathlib.Path("tests/fixtures/cycle_10")
author = [sm.feature_vector((fx / f"author_{i}.txt").read_text()) for i in (1, 2, 3)]
field = [sm.feature_vector((fx / f"field_{i}.txt").read_text()) for i in (1, 2)]
pos = list(itertools.combinations(author, 2))
neg = [(a, f) for a in author for f in field]
res = sm.fit_fisher_weights(pos, neg, lam=0.3)
# hedge_density should carry real weight: field hedges, author does not.
print("hedge weight:", round(res["weights"]["hedge_density"], 4))
assert res["weights"]["hedge_density"] > 0.0
band = sm.self_band(author, res["weights"], res["w_h"], res["stats"])
print("self-band:", round(band["band_lo"], 3), round(band["band_hi"], 3))
print("fixture separation OK")
PY
```

Expected: prints a positive hedge weight, a self-band, and `fixture separation OK`.

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/cycle_10/
git commit -m "test(cycle-10): synthetic calibration fixtures — 3 author + 2 field + 1 heldout"
```

---

## Task 7.2: Smoke — `tests/smoke_cycle_10.sh`

**Files:**
- Create: `tests/smoke_cycle_10.sh`

Exercises every code path of `sws_stylometry.py` against the fixture corpus and asserts the calibrator's wiring (agent file, skill, prelude export, schema). The Haiku call is STUBBED via `SWS_HAIKU_STUB` — the smoke never dispatches a model. It validates the deterministic stylometry pipeline end-to-end and that a written `profile.md` passes the schema.

- [ ] **Step 1: Write the smoke script**

Full content of `tests/smoke_cycle_10.sh`:

```bash
#!/usr/bin/env bash
# smoke_cycle_10.sh — e2e for cycle #10 (style calibration).
#
# Deterministic: the Haiku voice-similarity call is STUBBED via SWS_HAIKU_STUB.
# Exercises the full sws_stylometry.py pipeline against the synthetic fixture
# corpus (3 author + 2 field + 1 heldout) and asserts the calibrator wiring.
#
# Step  1: fixtures present
# Step  2: --vector emits the 17-key feature vector
# Step  3: --fit-weights emits weights + w_h summing to 1
# Step  4: --self-band emits a band on the author vectors
# Step  5: --distance heldout-vs-author + --rbf similarity in [0,1]
# Step  6: keep-best monotonicity (held-out improves toward the band)
# Step  7: a written profile.md passes the schema validator
# Step  8: prelude exports VOICE_PROFILE when _voice/profile.md present
# Step  9: style-calibrator agent + calibrate-style skill files exist + parse
# Step 10: D14 — calibrator inactive in editorial via agent_should_run
#
# Expected summary: 10 passed, 0 failed
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
FX="$REPO/tests/fixtures/cycle_10"
PYBIN="${SWS_SMOKE_PYTHON:-python3}"

TMP="$(mktemp -d)"
trap "rm -rf '$TMP'" EXIT

PASS=0
FAIL=0
step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  OK\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

# ---------------------------------------------------------------------------
# Step 1: fixtures present
# ---------------------------------------------------------------------------
step 1 "synthetic fixture corpus present (3 author + 2 field + 1 heldout)"
ALL=1
for f in author_1 author_2 author_3 field_1 field_2 heldout_1; do
    [[ -f "$FX/$f.txt" ]] || ALL=0
done
if [[ "$ALL" -eq 1 ]]; then ok; else ko "missing fixture file"; fi

# ---------------------------------------------------------------------------
# Step 2: --vector emits the 17-key feature vector
# ---------------------------------------------------------------------------
step 2 "--vector emits 17-key feature JSON"
VEC="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --vector "$(cat "$FX/author_1.txt")")"
NKEYS="$(printf '%s' "$VEC" | "$PYBIN" -c 'import json,sys; print(len(json.load(sys.stdin)))')"
if [[ "$NKEYS" -eq 17 ]]; then ok; else ko "expected 17 keys, got $NKEYS"; fi

# ---------------------------------------------------------------------------
# Step 3: --fit-weights -> weights + w_h sum to 1
# ---------------------------------------------------------------------------
step 3 "--fit-weights emits normalized weights (sum + w_h == 1)"
"$PYBIN" - "$FX" "$TMP" <<'PY'
import sys, json, itertools, pathlib
sys.path.insert(0, "scripts")
import sws_stylometry as sm  # noqa
fx, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
author = [sm.feature_vector((fx / f"author_{i}.txt").read_text()) for i in (1,2,3)]
field = [sm.feature_vector((fx / f"field_{i}.txt").read_text()) for i in (1,2)]
pos = list(itertools.combinations(author, 2))
neg = [[a, f] for a in author for f in field]
(tmp / "pos.json").write_text(json.dumps([[a,b] for a,b in pos]))
(tmp / "neg.json").write_text(json.dumps(neg))
PY
WJSON="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --fit-weights "$TMP/pos.json" "$TMP/neg.json" --lam 0.3 --pos-haiku 0.9,0.9,0.9 --neg-haiku 0.2,0.2,0.2,0.2,0.2,0.2)"
printf '%s' "$WJSON" > "$TMP/weights.json"
SUM_OK="$(printf '%s' "$WJSON" | "$PYBIN" -c 'import json,sys; d=json.load(sys.stdin); print("1" if abs(sum(d["weights"].values())+d["w_h"]-1.0)<1e-6 else "0")')"
if [[ "$SUM_OK" == "1" ]]; then ok; else ko "weights+w_h do not sum to 1"; fi

# ---------------------------------------------------------------------------
# Step 4: --self-band on author vectors
# ---------------------------------------------------------------------------
step 4 "--self-band emits band_lo<=band_mean<=band_hi in [0,1]"
"$PYBIN" - "$FX" "$TMP" <<'PY'
import sys, json, pathlib
sys.path.insert(0, "scripts")
import sws_stylometry as sm  # noqa
fx, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
author = [sm.feature_vector((fx / f"author_{i}.txt").read_text()) for i in (1,2,3)]
(tmp / "author_vecs.json").write_text(json.dumps(author))
PY
BAND="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --self-band "$TMP/author_vecs.json" --weights "$TMP/weights.json")"
BAND_OK="$(printf '%s' "$BAND" | "$PYBIN" -c 'import json,sys; b=json.load(sys.stdin); print("1" if 0.0<=b["band_lo"]<=b["band_mean"]<=b["band_hi"]<=1.0001 else "0")')"
if [[ "$BAND_OK" == "1" ]]; then ok; else ko "band invariants violated: $BAND"; fi

# ---------------------------------------------------------------------------
# Step 5: --distance heldout-vs-author then --rbf similarity in [0,1]
# ---------------------------------------------------------------------------
step 5 "--distance + --rbf produce a similarity in [0,1] (Haiku stubbed)"
HAIKU_SIM="${SWS_HAIKU_STUB:-0.8}"
"$PYBIN" "$REPO/scripts/sws_stylometry.py" --vector "$(cat "$FX/heldout_1.txt")" > "$TMP/heldout.json"
"$PYBIN" "$REPO/scripts/sws_stylometry.py" --vector "$(cat "$FX/author_1.txt")" > "$TMP/a1.json"
DJSON="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --distance "$TMP/heldout.json" "$TMP/a1.json" --weights "$TMP/weights.json" --haiku-sim "$HAIKU_SIM")"
DVAL="$(printf '%s' "$DJSON" | "$PYBIN" -c 'import json,sys; print(json.load(sys.stdin)["distance"])')"
SIM="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --rbf "$DVAL" --gamma 0.5)"
SIM_OK="$(printf '%s' "$SIM" | "$PYBIN" -c 'import json,sys; s=json.load(sys.stdin)["similarity"]; print("1" if 0.0<=s<=1.0 else "0")')"
if [[ "$SIM_OK" == "1" ]]; then ok; else ko "rbf similarity out of [0,1]: $SIM"; fi

# ---------------------------------------------------------------------------
# Step 6: keep-best monotonicity
# ---------------------------------------------------------------------------
step 6 "keep_best produces a monotone non-decreasing trajectory"
MONO="$("$PYBIN" -c '
import sys; sys.path.insert(0, "scripts")
import sws_stylometry as sm
seq = sm.keep_best([(1,0.40),(2,0.55),(3,0.50),(4,0.62)])
print("1" if seq == sorted(seq) and seq[-1]==0.62 else "0")
')"
if [[ "$MONO" == "1" ]]; then ok; else ko "keep_best not monotone"; fi

# ---------------------------------------------------------------------------
# Step 7: a written profile.md passes the schema validator
# ---------------------------------------------------------------------------
step 7 "synthetic profile.md passes the voice-profile schema validator"
mkdir -p "$TMP/_voice"
cat > "$TMP/_voice/profile.md" <<'PROF'
---
sws_artifact: voice-profile
artifact_version: 0.1
calibrated: 2026-05-23
recent_weighted: true
feature_targets:
  sentence_len_mean: { target: 8.0, band: [6.0, 11.0] }
  hedge_density: { target: 0.0, band: [0.0, 1.5] }
convergence:
  self_band: [0.74, 0.91]
  gamma: 0.42
sections: [global, introduction, results, discussion]
---

# Voice profile

## Global voice
Short declarative sentences, frequent first-person plural, minimal hedging.

## Section deltas

### Introduction
Opens with the gap, then the aim.

### Results
Headline finding first, then the data.

### Discussion
Interpretive, slightly longer sentences.
PROF
SCHEMA_OK="$("$PYBIN" - "$TMP/_voice/profile.md" <<'PY'
import sys, yaml, pathlib
sys.path.insert(0, "tests")
from test_voice_profile_schema import validate_profile
try:
    validate_profile(pathlib.Path(sys.argv[1]).read_text())
    print("1")
except Exception as e:
    print("0", e)
PY
)"
if [[ "$SCHEMA_OK" == "1" ]]; then ok; else ko "profile.md schema fail: $SCHEMA_OK"; fi

# ---------------------------------------------------------------------------
# Step 8: prelude exports VOICE_PROFILE when _voice/profile.md present
# ---------------------------------------------------------------------------
step 8 "agent_prelude.sh exports VOICE_PROFILE path when profile.md present"
mkdir -p "$TMP/.venv/bin"
if "$PYBIN" -c "import yaml, docx, openpyxl" 2>/dev/null; then
    ln -sf "$(command -v "$PYBIN")" "$TMP/.venv/bin/python"
elif [[ -n "${SWS_SMOKE_PYTHON:-}" && -x "${SWS_SMOKE_PYTHON}" ]]; then
    ln -sf "${SWS_SMOKE_PYTHON}" "$TMP/.venv/bin/python"
else
    echo "FAIL: no python with PyYAML found (set SWS_SMOKE_PYTHON)" >&2
    exit 1
fi
cat > "$TMP/.sws-project.local.md" <<'M'
---
profile: perspective
language: en
format: docx
---
M
VP="$(CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$TMP" bash -c "source '$REPO/scripts/agent_prelude.sh' drafter-fast; printf '%s' \"\$VOICE_PROFILE\"" 2>/dev/null)"
if [[ "$VP" == "$TMP/_voice/profile.md" ]]; then ok; else ko "VOICE_PROFILE=[$VP]"; fi

# ---------------------------------------------------------------------------
# Step 9: agent + skill files exist and parse
# ---------------------------------------------------------------------------
step 9 "style-calibrator agent + calibrate-style skill exist with valid frontmatter"
GOOD="$("$PYBIN" - "$REPO" <<'PY'
import sys, yaml, pathlib
repo = pathlib.Path(sys.argv[1])
ag = (repo / "agents/style-calibrator.md").read_text()
sk = (repo / "skills/calibrate-style/SKILL.md").read_text()
agfm = yaml.safe_load(ag.split("---", 2)[1])
skfm = yaml.safe_load(sk.split("---", 2)[1])
print("1" if agfm["name"]=="style-calibrator" and skfm["name"]=="calibrate-style" else "0")
PY
)"
if [[ "$GOOD" == "1" ]]; then ok; else ko "agent/skill frontmatter mismatch"; fi

# ---------------------------------------------------------------------------
# Step 10: D14 — calibrator inactive in editorial
# ---------------------------------------------------------------------------
step 10 "agent_should_run: style-calibrator inactive for editorial, active for perspective"
ED="$(mktemp -d)"
trap "rm -rf '$TMP' '$ED'" EXIT
mkdir -p "$ED/.venv/bin"
ln -sf "$(readlink -f "$TMP/.venv/bin/python" 2>/dev/null || echo "$TMP/.venv/bin/python")" "$ED/.venv/bin/python"
cat > "$ED/.sws-project.local.md" <<'M'
---
profile: editorial
language: en
format: docx
---
M
ED_RC=0
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$ED" \
    bash "$REPO/scripts/agent_should_run.sh" style-calibrator 2>/dev/null || ED_RC=$?
PE_RC=0
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$TMP" \
    bash "$REPO/scripts/agent_should_run.sh" style-calibrator 2>/dev/null || PE_RC=$?
if [[ "$ED_RC" -ne 0 && "$PE_RC" -eq 0 ]]; then ok
else ko "editorial_rc=$ED_RC perspective_rc=$PE_RC (expected non-0, 0)"; fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf "\nsmoke_cycle_10: %d passed, %d failed\n" "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]] || exit 1
```

- [ ] **Step 2: Make executable and run**

```bash
cd "$REPO_ROOT"
chmod +x tests/smoke_cycle_10.sh
SWS_SMOKE_PYTHON="$(command -v "$DEV_PY")" bash tests/smoke_cycle_10.sh
```

Expected: `smoke_cycle_10: 10 passed, 0 failed`.

- [ ] **Step 3: Run the full cycle-10 unit suite once more**

```bash
$DEV_PY -m pytest tests/test_stylometry_vector.py tests/test_stylometry_fisher.py tests/test_stylometry_kernel.py tests/test_voice_profile_schema.py tests/test_profile_activation_calibrator.py -q
```

Expected: `41 passed` (11 + 8 + 11 + 3 + 9 — minus the 1 activation count if pytest collects 8 parametrized + 1; confirm the printed total, all green).

- [ ] **Step 4: Commit**

```bash
git add tests/smoke_cycle_10.sh
git commit -m "test(cycle-10): smoke_cycle_10.sh — 10-step e2e against synthetic fixtures, Haiku stubbed (D15)"
```

---

## Task 7.3: Memory updates + draft PR

**Files:**
- Modify: `claude_memory/project_v02_backlog.md` (gitignored — local only)
- Modify: `claude_memory/project_cycle_execution_status.md` (gitignored — local only)

- [ ] **Step 1: Append the v0.2 backlog entries (D16 + rejected approaches)**

Add to `claude_memory/project_v02_backlog.md`:

```markdown
## Cycle #10 deferrals
- **MKL / learned non-diagonal Mahalanobis metric / string-kernel on syntactic shape** — v0.1 uses a diagonal Fisher metric wrapped in a single RBF (D8 scope).
- **Year-trend detrending of within-author variance before the kernel (D16)** — CONDITIONAL: revisit ONLY IF `style-evolution.md` on real corpora shows drift large enough to inflate within-author variance. Not pre-built (YAGNI).
- **Drafter-in-the-loop realism test** (production drafter as in-loop generator) — Approach B, rejected; production-consumer validation is a post-calibration concern.
- **Author personal-skill lookup** (pre-existing hand-written voice SKILL.md) — v0.1 always calibrates fresh.
- **HTML rendering of voice files / _archive comparison viewer** — voice files stay md + YAML frontmatter.
```

- [ ] **Step 2: Mark cycle #10 status**

In `claude_memory/project_cycle_execution_status.md`, set cycle #10 to "PR open (draft)"; flip to "merged" after the user merges.

- [ ] **Step 3: Open the draft PR**

```bash
cd "$REPO_ROOT"
git push -u origin cycle/10-style-calibration
gh pr create --draft --title "Cycle #10 — Style calibration (style-calibrator + /sws:calibrate-style + _voice/)" --body "$(cat <<'EOF'
## Summary
- Adds the `style-calibrator` agent (Sonnet 4.6 high, roster #4) and `/sws:calibrate-style`, building a recent-weighted voice profile from the author's own Zotero papers via an iterative held-out loop (D1/D2).
- New `scripts/sws_stylometry.py` (stdlib-only): 17-dim feature vector, Fisher-weighted distance with a fitted Haiku term `w_h` (D8/D8a), RBF kernel + median-gamma + self-similarity-band stopping rule (D10).
- Wires `_voice/profile.md` as a NEW voice axis (separate from `resolve_overlay.py`, D13) consumed by the 5 drafter/reviser/humanizer agents via the prelude-exported `VOICE_PROFILE`.
- D14 activation matrix: calibrator active in 7 profiles, inactive in editorial + commentary-reply.

## Test plan
- [ ] `pytest tests/test_stylometry_vector.py tests/test_stylometry_fisher.py tests/test_stylometry_kernel.py tests/test_voice_profile_schema.py tests/test_profile_activation_calibrator.py` — all green
- [ ] `bash tests/smoke_cycle_10.sh` — 10 passed, 0 failed (Haiku stubbed)
- [ ] No banner/version change this cycle (stays 0.1.0-alpha)
- [ ] Optional local dogfood against real Zotero (user-approved; nothing from that run committed)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Return the PR URL.

---

## Self-review checklist (run before opening the PR)

- [ ] **Spec coverage.** Every locked decision maps to a task: D1 (Task 2.1), D2 (2.1/3.1), D3 (2.1 discover), D4 (2.1 per-section deltas + 1.5 schema), D5 (2.1 field-profile), D6 (2.1 recency_weight), D7 (2.1 evolution), D8 (1.2/1.3/1.4), D8a (1.2), D9 (2.1 Haiku rubric + stub), D10 (1.3 self-band/keep-best + 3.1 defaults), D11 (2.1 content-control + convergence.md), D12 (1.5 + 4.7 inventory), D13 (4.1–4.7), D14 (5.1–5.10), D15 (Phase 6/7), D16 (7.3 backlog), D17 (2.1/3.1 fallbacks).
- [ ] **No placeholders.** Every code step shows complete code; every command shows expected output; no "TBD" / "similar to Task N" / "add error handling".
- [ ] **Type/signature consistency.** CLI flags (`--vector`, `--distance`, `--fit-weights`, `--rbf`, `--self-band`, `--weights`, `--haiku-sim`, `--gamma`, `--lam`, `--pos-haiku`, `--neg-haiku`) and JSON keys (`weights`, `w_h`, `distance`, `per_feature_contrib`, `similarity`, `band_mean/sd/lo/hi`, `gamma`) match across the script task (1.3), the unit tests (1.2/1.3), and the smoke (7.2). `FEATURE_ORDER` (17 keys) is identical in `sws_stylometry.py`, `references/stylometry-features.md`, and every test.
- [ ] **Privacy.** No real names/paths/institutions; `$DEV_PY`, `$REPO_ROOT`, `$PAPER_ROOT`, `${CLAUDE_PLUGIN_ROOT}` throughout; fixtures synthetic; Haiku stubbed via `SWS_HAIKU_STUB`.
```
