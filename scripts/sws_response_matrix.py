#!/usr/bin/env python3
"""Deterministic markdown -> R&R Traceability Matrix JSON parser.

Reads a reviewer-comments.md file and emits a structured JSON list of comment
objects. No LLM call (D5). Idempotent on re-parse: preserves user/agent-filled
`status`, `response_text`, `edits_made`, and `line_refs` fields when a comment
id stays the same; new comments append; deleted comments drop (R3).

Schema source of truth: references/submission-artifacts.md (response_matrix_schema).

Accepted shapes (auto-detected; D6):
  (a) "## Reviewer N" headings with numbered or bulleted comments under each.
  (b) Flat top-level numbered list — single implicit reviewer (id = 1).
  (c) "R<N>.<M>:" prefixed lines (Imbad0202 convention).

Severity inference (lowercased text):
  - keywords {must, critical, fatal, wrong, incorrect, should, important, missing} -> major
  - keywords {consider, suggest, might, could}                                     -> suggestion
  - else                                                                          -> minor

CLI:
    sws_response_matrix.py <reviewer-comments.md> [--out <matrix.json>]

Default --out: same directory as input, filename "response-matrix.json".

Exit codes:
    0 - success
    1 - input file not found
    2 - invalid markdown (cannot read)
    3 - shape detection failed
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Severity inference
# ---------------------------------------------------------------------------

_MAJOR_KEYWORDS = (
    "must", "critical", "fatal", "wrong", "incorrect",
    "should", "important", "missing",
)
_SUGGESTION_KEYWORDS = ("consider", "suggest", "might", "could")


def infer_severity(text: str) -> str:
    """Keyword-based severity inference. Lowercased substring match."""
    lo = text.lower()
    for kw in _MAJOR_KEYWORDS:
        if kw in lo:
            return "major"
    for kw in _SUGGESTION_KEYWORDS:
        if kw in lo:
            return "suggestion"
    return "minor"


# ---------------------------------------------------------------------------
# Shape detection
# ---------------------------------------------------------------------------

_REVIEWER_HEADING_RE = re.compile(r"^##\s+Reviewer\s+(\d+)\s*$", re.IGNORECASE)
_PREFIX_ID_RE = re.compile(r"^R(\d+)\.(\d+)\s*[:.]\s*(.+)$")
_NUMBERED_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+)$")


def detect_shape(lines):
    """Return one of 'a', 'b', 'c', or None.

    Detection precedence:
      - any line matches reviewer-heading pattern -> 'a'
      - any line matches "R<N>.<M>:" prefix -> 'c'
      - any line matches top-level numbered list -> 'b'
      - else None
    """
    has_reviewer_heading = False
    has_prefix_id = False
    has_numbered = False
    for ln in lines:
        s = ln.rstrip("\n")
        if _REVIEWER_HEADING_RE.match(s):
            has_reviewer_heading = True
        if _PREFIX_ID_RE.match(s):
            has_prefix_id = True
        if _NUMBERED_RE.match(s):
            has_numbered = True
    if has_reviewer_heading:
        return "a"
    if has_prefix_id:
        return "c"
    if has_numbered:
        return "b"
    return None


# ---------------------------------------------------------------------------
# Parsing per shape
# ---------------------------------------------------------------------------

def _comment_object(cid: str, reviewer: int, text: str) -> dict:
    return {
        "id": cid,
        "reviewer": reviewer,
        "text": text.strip(),
        "severity_inferred": infer_severity(text),
        "status": "pending",
        "response_text": "",
        "edits_made": [],
        "line_refs": [],
    }


def parse_shape_a(lines):
    """## Reviewer N headings with numbered/bulleted comments below."""
    out = []
    current_reviewer = None
    counter = 0
    for ln in lines:
        s = ln.rstrip("\n")
        m = _REVIEWER_HEADING_RE.match(s)
        if m:
            current_reviewer = int(m.group(1))
            counter = 0
            continue
        if current_reviewer is None:
            continue
        m_num = _NUMBERED_RE.match(s)
        m_bul = _BULLET_RE.match(s)
        text = None
        if m_num:
            text = m_num.group(2)
        elif m_bul:
            text = m_bul.group(1)
        if text:
            counter += 1
            cid = f"R{current_reviewer}.{counter}"
            out.append(_comment_object(cid, current_reviewer, text))
    return out


def parse_shape_b(lines):
    """Flat top-level numbered list; single implicit reviewer (id=1)."""
    out = []
    counter = 0
    for ln in lines:
        s = ln.rstrip("\n")
        m = _NUMBERED_RE.match(s)
        if m:
            counter += 1
            cid = f"R1.{counter}"
            out.append(_comment_object(cid, 1, m.group(2)))
    return out


def parse_shape_c(lines):
    """R<N>.<M>: prefixed lines."""
    out = []
    for ln in lines:
        s = ln.rstrip("\n")
        m = _PREFIX_ID_RE.match(s)
        if m:
            reviewer = int(m.group(1))
            comment_n = int(m.group(2))
            cid = f"R{reviewer}.{comment_n}"
            out.append(_comment_object(cid, reviewer, m.group(3)))
    return out


# ---------------------------------------------------------------------------
# Idempotency (R3)
# ---------------------------------------------------------------------------

_PRESERVE_FIELDS = ("status", "response_text", "edits_made", "line_refs")


def merge_with_existing(new_comments, existing_path: Path):
    """Preserve agent/user-filled fields from any existing matrix for unchanged ids.

    New comments append; deleted comments drop (already implicit: only ids in
    `new_comments` survive).
    """
    if not existing_path.exists():
        return new_comments
    try:
        prior = json.loads(existing_path.read_text())
    except (json.JSONDecodeError, OSError):
        return new_comments
    if not isinstance(prior, list):
        return new_comments
    prior_by_id = {c.get("id"): c for c in prior if isinstance(c, dict)}
    merged = []
    for c in new_comments:
        old = prior_by_id.get(c["id"])
        if old is not None:
            for field in _PRESERVE_FIELDS:
                if field in old and old[field] not in (None, "", []):
                    c[field] = old[field]
        merged.append(c)
    return merged


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_SHAPE_HELP = """\
Could not detect a recognised reviewer-comments shape. Accepted shapes:

  (a) Per-reviewer headings with numbered/bulleted comments:
        ## Reviewer 1
        1. ...
        2. ...
        ## Reviewer 2
        - ...

  (b) Flat numbered list (single implicit reviewer):
        1. ...
        2. ...

  (c) Prefixed ID per Imbad0202 convention:
        R1.1: ...
        R1.2: ...
        R2.1: ...

See references/submission-artifacts.md `reviewer_comments_accepted_shapes`.
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("input", help="Path to reviewer-comments.md")
    ap.add_argument(
        "--out",
        default=None,
        help="Output path for response-matrix.json (default: same dir as input)",
    )
    args = ap.parse_args(argv)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"sws_response_matrix: file not found: {in_path}", file=sys.stderr)
        return 1

    try:
        text = in_path.read_text()
    except OSError as exc:
        print(f"sws_response_matrix: cannot read {in_path}: {exc}", file=sys.stderr)
        return 2

    lines = text.splitlines()
    shape = detect_shape(lines)
    if shape is None:
        print(_SHAPE_HELP, file=sys.stderr)
        return 3

    if shape == "a":
        comments = parse_shape_a(lines)
    elif shape == "b":
        comments = parse_shape_b(lines)
    else:  # shape == "c"
        comments = parse_shape_c(lines)

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = in_path.parent / "response-matrix.json"

    merged = merge_with_existing(comments, out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(json.dumps(merged, indent=2, sort_keys=True))
    tmp.replace(out_path)

    print(
        f"sws_response_matrix: shape={shape} comments={len(merged)} -> {out_path}",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
