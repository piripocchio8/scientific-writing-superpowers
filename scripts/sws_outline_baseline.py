"""Sidecar baseline checksum for outline-architect overwrite policy (D3).

The outline-architect writes <paper>/_outline/.outline-baseline.sha256 after
generating outline.md. On re-run, it compares the current outline hash to the
sidecar — if they differ, the user has hand-edited the outline and the
architect must surface the would-be-lost content before overwriting.

CLI surface (used by outline-architect):
    sws_outline_baseline.py write   <outline.md path>
    sws_outline_baseline.py matches <outline.md path>
"""
from __future__ import annotations
import hashlib
from pathlib import Path


SIDECAR_NAME = ".outline-baseline.sha256"


class BaselineMissing(FileNotFoundError):
    pass


def sidecar_path(outline_md: Path) -> Path:
    return outline_md.parent / SIDECAR_NAME


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_baseline(outline_md: Path) -> None:
    sc = sidecar_path(outline_md)
    sc.write_text(_hash_file(outline_md) + "\n")


def baseline_matches(outline_md: Path) -> bool:
    sc = sidecar_path(outline_md)
    if not sc.exists():
        raise BaselineMissing(f"no baseline sidecar at {sc}")
    return sc.read_text().strip() == _hash_file(outline_md)


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    p_write = sub.add_parser("write")
    p_write.add_argument("outline")
    p_match = sub.add_parser("matches")
    p_match.add_argument("outline")
    args = p.parse_args(argv)

    outline = Path(args.outline)
    if args.cmd == "write":
        write_baseline(outline)
        print(f"sws: wrote baseline for {outline}")
        return 0
    if args.cmd == "matches":
        try:
            ok = baseline_matches(outline)
        except BaselineMissing:
            print("missing")
            return 2
        print("yes" if ok else "no")
        return 0 if ok else 1
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
