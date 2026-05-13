#!/usr/bin/env python3
"""SessionStart hook — passport summary + journal-style nudge.

Marker-scoped. Output goes to stdout (Claude Code injects into session context).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sws_hook_utils


def main() -> int:
    cwd = Path.cwd()
    marker = sws_hook_utils.check_marker(cwd)
    if marker is None:
        return 0

    # Missing-profile nudge takes priority (cycle #6, D7).
    # When the marker's profile field is null or absent, surface only the
    # one-line nudge and skip the passport summary and journal-style hint —
    # agents are paused until the user sets a profile.
    profile = marker.get("profile")
    if profile in (None, "", "null"):
        print(
            "No profile set — run /sws:set-profile <name> "
            "(e.g. communication, full-article, funding-proposal). "
            "Agents are paused until set."
        )
        return 0

    lines = []

    passport_path = cwd / "claude_memory" / "passport.json"
    if passport_path.exists():
        try:
            data = json.loads(passport_path.read_text())
            history = data.get("history", [])
            if history:
                last = history[-1]
                cycle = last.get("cycle", "?")
                files = last.get("file", [])
                if files:
                    head = ", ".join(files[:3])
                    extra = f", +{len(files) - 3} more" if len(files) > 3 else ""
                    file_summary = f"{len(files)} file(s): {head}{extra}"
                else:
                    file_summary = "no files"
                lines.append(f"\U0001f4cb SWS: last cycle #{cycle}, touched {file_summary}")
        except (json.JSONDecodeError, OSError):
            pass

    article_type = marker.get("article_type") or ""
    if article_type and article_type != "funding-proposal":
        overlay_dir = cwd / "Manuscript" / "_journal-style"
        has_overlay = False
        if overlay_dir.is_dir():
            has_overlay = any(
                p.suffix == ".md" and not p.name.startswith("_")
                for p in overlay_dir.iterdir()
            )
        if not has_overlay:
            lines.append(
                "\U0001f4a1 No journal style cached. Run `/sws:resolve-journal-style <slug>` when ready."
            )

    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
