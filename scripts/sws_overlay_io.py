"""Shared overlay I/O — archive on re-resolve, diff summary, atomic write.

Used by sws_resolve_journal_style.py and sws_resolve_call_rules.py.
"""
from __future__ import annotations

import datetime
import shutil
from pathlib import Path
from typing import Optional

import yaml


def parse_frontmatter_text(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        return {}
    return yaml.safe_load(rest[:end].lstrip("\n")) or {}


def archive_overlay(overlay_path: Path) -> Optional[Path]:
    """Copy the existing overlay (if any) into the sibling _archive/ folder.

    Returns the archive path if archived, None if the overlay didn't exist.
    Archive filename: <slug>-YYYYMMDD-HHMMSS.md (UTC timestamp).
    """
    if not overlay_path.exists():
        return None
    archive_dir = overlay_path.parent / "_archive"
    archive_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    target = archive_dir / f"{overlay_path.stem}-{ts}.md"
    shutil.copy2(overlay_path, target)
    return target


def diff_summary(old_text: str, new_text: str) -> str:
    """Produce a human-readable diff of two overlay frontmatter blobs."""
    old_fm = parse_frontmatter_text(old_text)
    new_fm = parse_frontmatter_text(new_text)
    diff_lines = []
    for k in sorted(set(old_fm) | set(new_fm)):
        if old_fm.get(k) != new_fm.get(k):
            diff_lines.append(f"  {k}: {old_fm.get(k)} -> {new_fm.get(k)}")
    if not diff_lines:
        return "(no field changes)"
    return "diff:\n" + "\n".join(diff_lines)


def write_overlay(overlay_path: Path, frontmatter: dict, body: str = "") -> None:
    """Atomic write of an overlay file with sorted frontmatter."""
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    fm_yaml = yaml.safe_dump(frontmatter, sort_keys=True, default_flow_style=False)
    content = f"---\n{fm_yaml}---\n"
    if body:
        content += "\n" + body.lstrip("\n")
    tmp = overlay_path.with_suffix(overlay_path.suffix + ".tmp")
    tmp.write_text(content)
    tmp.replace(overlay_path)
