"""Shared helpers for SWS hooks. All hooks call check_marker() first.

Pure stdlib only — no pyyaml.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Union

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


def _serialize_value(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    return str(value)


def write_marker_field(path, key: str, value: Union[str, bool, int, None]) -> None:
    """Set a top-level scalar field in the marker frontmatter.

    Behavior:
    - If the leading `---` … `---` block exists, parse line-by-line preserving
      order and update the matching key in place (or append if new).
    - If the frontmatter block is absent, prepend a new block at the top of
      the file containing this one key, keeping any existing body below.
    - Writes atomically via tempfile + os.replace.

    Value serialization: None → null, True → true, False → false, ints → bare,
    strings → bare (marker is line-scoped; quoting is unnecessary for the
    limited values SWS writes).
    """
    path = Path(path)
    rendered_value = _serialize_value(value)
    line_for_key = f"{key}: {rendered_value}\n"

    if path.exists():
        text = path.read_text()
    else:
        text = ""

    m = re.search(r"^---\n(.*?)\n---", text, re.DOTALL | re.MULTILINE)
    if not m:
        # No frontmatter block — prepend one.
        new_block = f"---\n{key}: {rendered_value}\n---\n"
        if text:
            new_text = new_block + ("\n" if not text.startswith("\n") else "") + text
        else:
            new_text = new_block
    else:
        block_body = m.group(1)
        new_lines = []
        found = False
        for raw_line in block_body.split("\n"):
            stripped = raw_line.rstrip()
            # Top-level key match: not indented, not a comment, contains a colon,
            # and the key prefix matches exactly.
            if (
                not stripped.startswith((" ", "\t", "#"))
                and ":" in stripped
                and stripped.split(":", 1)[0].strip() == key
            ):
                new_lines.append(f"{key}: {rendered_value}")
                found = True
            else:
                new_lines.append(raw_line)
        if not found:
            new_lines.append(f"{key}: {rendered_value}")
        new_block_body = "\n".join(new_lines)
        new_text = (
            text[: m.start(1)] + new_block_body + text[m.end(1):]
        )

    # Atomic write.
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", dir=str(path.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(new_text)
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
