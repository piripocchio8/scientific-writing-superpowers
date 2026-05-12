"""Shared helpers for SWS hooks. All hooks call check_marker() first.

Pure stdlib only — no pyyaml.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

MARKER_FILENAME = ".sws-project.local.md"


def find_marker(cwd) -> Optional[Path]:
    """Return Path to marker if it exists in cwd, else None."""
    marker = Path(cwd) / MARKER_FILENAME
    return marker if marker.is_file() else None


def parse_marker(marker_path) -> dict:
    """Parse top-level scalar YAML key-value pairs from the marker frontmatter.

    Handles only the limited subset SWS writes: scalars (string, bool, int, null)
    at the top level between the --- delimiters. Nested keys (e.g., notebooklm.enabled)
    are NOT parsed; hooks don't need them in v0.1.
    """
    text = Path(marker_path).read_text()
    m = re.search(r'^---\n(.*?)\n---', text, re.DOTALL | re.MULTILINE)
    if not m:
        return {}
    result = {}
    for line in m.group(1).split('\n'):
        line = line.rstrip()
        if not line or line.startswith((' ', '\t', '#')) or ':' not in line:
            continue
        key, _, value = line.partition(':')
        key, value = key.strip(), value.strip()
        if value == 'null' or value == '':
            value = None
        elif value in ('true', 'false'):
            value = (value == 'true')
        elif value.isdigit():
            value = int(value)
        elif (value.startswith('"') and value.endswith('"')) or \
             (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        result[key] = value
    return result


def check_marker(cwd) -> Optional[dict]:
    """Return parsed marker dict if SWS is active in cwd; None for silent no-op."""
    marker = find_marker(cwd)
    if marker is None:
        return None
    return parse_marker(marker)
