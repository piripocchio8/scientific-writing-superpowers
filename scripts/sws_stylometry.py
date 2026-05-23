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
