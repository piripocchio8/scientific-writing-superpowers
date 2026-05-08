#!/usr/bin/env python3
"""SWS filesystem-index utility.

Walk a project directory, write a JSON manifest of file metadata so later
tool calls read the manifest instead of repeatedly running ls/find.
Designed for the pymol25 mamba env (Python 3.9+, stdlib only).

Usage:
    python sws_fs_index.py [--root <dir>] [--out <path>]
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import sys
from pathlib import Path

VERSION = "0.1.0"

DEFAULT_EXCLUDES = (
    ".git",
    ".venv",
    "__pycache__",
    "_archive",
    "node_modules",
    ".DS_Store",
    "*.backup_pre_*.docx",
    "*.backup_pre_*.tex",
    "*.backup_pre_*.bib",
    "*.backup_pre_*.cls",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
)


def _is_excluded(path: Path, root: Path, patterns) -> bool:
    rel = path.relative_to(root)
    for part in rel.parts:
        for pattern in patterns:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False


def build_index(root, excludes=DEFAULT_EXCLUDES) -> dict:
    root = Path(root).resolve()
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _is_excluded(path, root, excludes):
            continue
        stat = path.stat()
        files.append({
            "path": str(path.relative_to(root)),
            "size_bytes": stat.st_size,
            "mtime": dt.datetime.fromtimestamp(
                stat.st_mtime, tz=dt.timezone.utc
            ).isoformat(),
            "ext": path.suffix.lower(),
        })
    return {
        "version": VERSION,
        "generated": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "root": str(root),
        "files": files,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root (default: cwd)")
    parser.add_argument(
        "--out",
        default="./claude_memory/fs_index.json",
        help="output JSON path (default: ./claude_memory/fs_index.json)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_index(root)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"Wrote {len(manifest['files'])} entries to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
