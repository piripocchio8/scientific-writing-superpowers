#!/usr/bin/env python3
"""Stop hook — append a passport.json history entry when files were modified.

Marker-scoped. Idempotent on empty turns (no entry written).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sws_hook_utils


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    cwd = Path.cwd()
    marker = sws_hook_utils.check_marker(cwd)
    if marker is None:
        return 0

    modified = _extract_modified_files(event, cwd)
    if not modified:
        return 0

    passport_path = cwd / "claude_memory" / "passport.json"
    if not passport_path.exists():
        return 0

    try:
        data = json.loads(passport_path.read_text())
    except (json.JSONDecodeError, OSError):
        return 0

    history = data.setdefault("history", [])
    # Compute next cycle: max existing history cycle + 1.
    # Fall back to data["cycle"] + 1 when history is empty (stub has cycle: 0).
    if history:
        next_cycle = max(e.get("cycle", 0) for e in history) + 1
    else:
        next_cycle = data.get("cycle", 0) + 1

    entry = {
        "cycle": next_cycle,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agent": None,
        "file": sorted(set(modified)),
        "change_summary": None,
        "next_step": None,
    }
    history.append(entry)
    try:
        passport_path.write_text(json.dumps(data, indent=2, sort_keys=True))
    except OSError:
        return 0  # don't block session on write failure
    return 0


def _extract_modified_files(event: dict, cwd: Path) -> list:
    """Extract relative paths of files edited/written during this session.

    Probes multiple likely fields across Claude Code versions; falls back to
    empty list if none found (E5 edge case).
    """
    files = []
    # Probe multiple candidate fields for portability across CC versions.
    candidates = (
        event.get("tool_uses")
        or event.get("tool_calls")
        or event.get("transcript")
        or []
    )
    for entry in candidates:
        tool_name = entry.get("tool_name") or entry.get("name", "")
        if tool_name not in ("Edit", "Write", "MultiEdit"):
            continue
        tool_input = entry.get("tool_input") or entry.get("arguments", {})
        fp = tool_input.get("file_path")
        if not fp:
            continue
        p = Path(fp)
        if p.is_absolute():
            try:
                p = p.relative_to(cwd)
            except ValueError:
                pass
        files.append(str(p))
    return files


if __name__ == "__main__":
    raise SystemExit(main())
