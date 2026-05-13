#!/usr/bin/env python3
"""Helper for /sws:set-profile — validate name + rewrite marker profile field.

CLI:
    python sws_set_profile.py --paper <root> --name <profile-name>

Exit codes:
    0 - profile set; one-line confirmation printed
    1 - invalid profile name (lists valid names on stderr)
    2 - not an SWS project (no marker found)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sws_hook_utils import parse_marker, write_marker_field  # noqa: E402


def valid_profile_names(profiles_dir: Path) -> list[str]:
    return sorted(p.stem for p in profiles_dir.glob("*.md"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path,
                    help="Paper root (contains .sws-project.local.md)")
    ap.add_argument("--name", required=True,
                    help="Profile id (one of 9 v0.1 locked ids)")
    ap.add_argument("--profiles-dir", default=None, type=Path,
                    help="Override profile directory (test use only)")
    args = ap.parse_args(argv)

    plugin_root = Path(__file__).absolute().parent.parent
    profiles_dir = args.profiles_dir or (plugin_root / "profiles")

    valid = valid_profile_names(profiles_dir)
    if args.name not in valid:
        print(
            f"error: '{args.name}' is not a valid profile. "
            f"Valid: {', '.join(valid)}",
            file=sys.stderr,
        )
        return 1

    marker = args.paper / ".sws-project.local.md"
    if not marker.exists():
        print(
            "error: not an SWS project (no .sws-project.local.md found)",
            file=sys.stderr,
        )
        return 2

    old = parse_marker(marker).get("profile")
    write_marker_field(marker, "profile", args.name)
    print(f"profile: {args.name} (was: {old})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
