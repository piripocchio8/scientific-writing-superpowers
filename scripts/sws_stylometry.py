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
