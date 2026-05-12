#!/usr/bin/env python3
"""Pre-edit backup hook (PreToolUse Edit|Write).

Creates <filename>.backup_pre_<event>.<ext> before docx (always) or
*.{tex,bib,cls} (when format: latex). Blocks the tool call on failure.
Silent no-op outside SWS projects.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sws_hook_utils

DOCX_EXTS = (".docx",)
LATEX_EXTS = (".tex", ".bib", ".cls")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    cwd = Path.cwd()
    marker = sws_hook_utils.check_marker(cwd)
    if marker is None:
        return 0

    tool_name = event.get("tool_name") or event.get("hook_event_name", "")
    tool_input = event.get("tool_input") or event.get("arguments", {})
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return 0

    fp = tool_input.get("file_path", "")
    if not fp:
        return 0
    target = Path(fp)
    if not target.is_absolute():
        target = cwd / target

    ext = target.suffix.lower()
    is_docx = ext in DOCX_EXTS
    is_latex = (marker.get("format") == "latex" and ext in LATEX_EXTS)
    if not (is_docx or is_latex):
        return 0

    if not target.exists():
        return 0

    event_name = tool_name.lower()
    backup = target.with_suffix(f".backup_pre_{event_name}{ext}")
    try:
        shutil.copy2(target, backup)
    except OSError as e:
        print(f"SWS backup failed: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
