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
    """Best-effort extraction of files edited/written during the session.

    Preferred path: parse event['transcript_path'] (JSONL of session messages).
    Fallback: event['tool_uses'] or event['tool_calls'] (older / variant payloads).
    """
    cwd_resolved = cwd.resolve()
    files: list[str] = []

    # Primary path: transcript file (canonical Claude Code Stop hook field).
    transcript_path = event.get("transcript_path")
    if transcript_path:
        try:
            with open(transcript_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    files.extend(_extract_from_message(msg))
        except (OSError, ValueError):
            pass

    # Fallback: direct tool-use list in event payload.
    if not files:
        candidates = event.get("tool_uses") or event.get("tool_calls") or []
        for entry in candidates:
            files.extend(_extract_from_tool_call_dict(entry))

    # Canonicalize paths: resolve symlinks on both sides, then relativize.
    out = []
    for fp in files:
        if not fp:
            continue
        p = Path(fp)
        if p.is_absolute():
            try:
                p = p.resolve().relative_to(cwd_resolved)
            except (ValueError, OSError):
                pass
        out.append(str(p))
    return out


def _extract_from_message(msg: dict) -> list[str]:
    """Pull Edit/Write/MultiEdit file_path values from a single transcript message."""
    result = []
    # Transcript lines may wrap the message under a 'message' key or expose it directly.
    inner = msg.get("message") if isinstance(msg.get("message"), dict) else msg
    content = inner.get("content") if isinstance(inner, dict) else None
    if not isinstance(content, list):
        return result
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_use" and block.get("name") in ("Edit", "Write", "MultiEdit"):
            fp = (block.get("input") or {}).get("file_path")
            if fp:
                result.append(fp)
    return result


def _extract_from_tool_call_dict(entry: dict) -> list[str]:
    """Pull file_path from a single tool_uses/tool_calls entry (older payload shape)."""
    tool_name = entry.get("tool_name") or entry.get("name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return []
    tool_input = entry.get("tool_input") or entry.get("arguments", {})
    fp = tool_input.get("file_path")
    return [fp] if fp else []


if __name__ == "__main__":
    raise SystemExit(main())
