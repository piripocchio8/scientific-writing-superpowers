#!/usr/bin/env python3
"""Helper for managing `_review/round-<N>/` folders.

Subcommands:
  init [N]      Create `_review/round-<N>/` plus a template `reviewer-comments.md`.
                Default N = highest existing + 1 (1 if none exist). Idempotent:
                does not overwrite an existing reviewer-comments.md.
  find          Print highest existing N, or `none`.
  inventory N   Print which artifacts exist in `_review/round-<N>/`:
                  comments  (reviewer-comments.md)
                  matrix    (response-matrix.json)
                  response  (response-to-reviewers.md)
                  edits     (edits-summary.md)
                Each on its own line as "<artifact>: present | absent".

CLI:
    sws_review_round.py {init [N] | find | inventory N} [--paper-root <path>]

Exit codes:
    0 - success
    2 - usage / argument error
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


ROUND_RE = re.compile(r"^round-(\d+)$")

TEMPLATE_COMMENTS = """\
# Reviewer comments

Paste reviewer comments here in one of the accepted shapes:

## Reviewer 1
1. <comment text>
2. <comment text>

## Reviewer 2
1. <comment text>

See `references/submission-artifacts.md` for accepted shapes a/b/c.
"""


def _review_dir(paper_root: Path) -> Path:
    return paper_root / "_review"


def existing_rounds(paper_root: Path) -> list[int]:
    rev = _review_dir(paper_root)
    if not rev.exists():
        return []
    rounds = []
    for child in rev.iterdir():
        if not child.is_dir():
            continue
        m = ROUND_RE.match(child.name)
        if m:
            rounds.append(int(m.group(1)))
    return sorted(rounds)


def cmd_find(paper_root: Path) -> int:
    rounds = existing_rounds(paper_root)
    if rounds:
        print(rounds[-1])
    else:
        print("none")
    return 0


def cmd_init(paper_root: Path, n: int | None) -> int:
    if n is None:
        rounds = existing_rounds(paper_root)
        n = (rounds[-1] + 1) if rounds else 1
    if n < 1:
        print(f"sws_review_round: round number must be >= 1, got {n}", file=sys.stderr)
        return 2
    round_dir = _review_dir(paper_root) / f"round-{n}"
    round_dir.mkdir(parents=True, exist_ok=True)
    comments_path = round_dir / "reviewer-comments.md"
    if not comments_path.exists():
        comments_path.write_text(TEMPLATE_COMMENTS)
        print(f"sws_review_round: created {round_dir}/ with template reviewer-comments.md")
    else:
        print(f"sws_review_round: {round_dir}/ already initialised (no overwrite)")
    return 0


_ARTIFACT_FILES = (
    ("comments", "reviewer-comments.md"),
    ("matrix", "response-matrix.json"),
    ("response", "response-to-reviewers.md"),
    ("edits", "edits-summary.md"),
)


def cmd_inventory(paper_root: Path, n: int) -> int:
    round_dir = _review_dir(paper_root) / f"round-{n}"
    if not round_dir.exists():
        print(f"sws_review_round: round-{n} does not exist", file=sys.stderr)
        return 2
    for label, fname in _ARTIFACT_FILES:
        status = "present" if (round_dir / fname).exists() else "absent"
        print(f"{label}: {status}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--paper-root", default=os.getcwd())
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp_init = sub.add_parser("init")
    sp_init.add_argument("n", nargs="?", type=int, default=None)
    sub.add_parser("find")
    sp_inv = sub.add_parser("inventory")
    sp_inv.add_argument("n", type=int)
    args = ap.parse_args(argv)

    paper_root = Path(args.paper_root).resolve()
    if args.cmd == "init":
        return cmd_init(paper_root, args.n)
    if args.cmd == "find":
        return cmd_find(paper_root)
    if args.cmd == "inventory":
        return cmd_inventory(paper_root, args.n)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
