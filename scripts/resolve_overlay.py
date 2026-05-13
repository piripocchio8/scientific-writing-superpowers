#!/usr/bin/env python3
"""Resolve the 3-layer profile/overlay contract for SWS agents.

Layers (low → high precedence): schema_defaults < profile < overlay (journal then call).
List-typed fields are REPLACE (overlay wins entirely if it sets them).
Scalar fields: explicit null in overlay drops the profile value (D17).

Output is JSON on stdout. See spec frontmatter resolve_overlay_contract for
the full schema. Exit codes:
    0 - OK (profile may or may not be set)
    2 - profile file not found
    3 - malformed YAML in any layer
    4 - marker not found (not an SWS project)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency missing at runtime
    print(
        json.dumps({"error": "PyYAML not installed in resolver env", "details": str(exc)}),
        file=sys.stderr,
    )
    sys.exit(3)


SCHEMA_DEFAULTS = {
    "inherits": None,
    "sections": [],
    "ref_cap": None,
    "word_total": None,
    "figures_max": None,
    "tables_max": None,
    "abstract_style": "unstructured",
    "disclosure_required": False,
    "cover_letter_required": False,
    "supplementary_allowed": True,
    "refs_style": "numbered",
    "agents_active": [],
    "agents_inactive": [],
}


def parse_frontmatter(path: Path) -> dict:
    """Read a markdown file's YAML frontmatter into a dict.

    Returns {} when the file has no leading --- block.
    Raises yaml.YAMLError if the block is present but malformed.
    """
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    # Find the closing --- after the opening.
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        return {}
    block = rest[:end].lstrip("\n")
    return yaml.safe_load(block) or {}


def merge(base: dict, overlay: dict) -> dict:
    """Apply overlay on top of base.

    Semantics:
        - overlay key present (including explicit null) wins (D17).
        - overlay key absent: base value kept.
        - List fields (D14): overlay value replaces base value entirely.

    Both branches reduce to the same operation: any key present in overlay
    replaces the corresponding base key. Distinguishing list vs scalar is
    important for documentation/future patch semantics but produces the same
    output here.
    """
    result = dict(base)
    for k, v in (overlay or {}).items():
        result[k] = v
    return result


def _ok(payload: dict) -> int:
    print(json.dumps(payload))
    return 0


def _err(message: str, code: int, **extra) -> int:
    blob = {"error": message}
    blob.update(extra)
    print(json.dumps(blob), file=sys.stderr)
    return code


def resolve(
    paper_root: Path,
    agent: str | None,
    profiles_dir: Path,
) -> tuple[int, dict]:
    """Core resolver. Returns (exit_code, payload_dict).

    Payload is always JSON-serializable. Errors return non-zero exit
    and payload-as-error dict; main() routes that to stderr.
    """
    marker = paper_root / ".sws-project.local.md"
    if not marker.exists():
        return 4, {"error": "marker not found", "path": str(marker)}

    try:
        marker_fm = parse_frontmatter(marker)
    except yaml.YAMLError as exc:
        return 3, {"error": "malformed marker YAML", "details": str(exc)}

    profile_id = marker_fm.get("profile")

    empty_payload = {
        "profile_set": False,
        "profile_id": None,
        "profile_path": None,
        "journal_overlay_path": None,
        "call_overlay_path": None,
        "resolved_frontmatter": None,
        "should_run": None,
        "diagnostics": {
            "warnings": ["no profile set"],
            "missing_journal_overlay": False,
            "missing_call_overlay": False,
        },
    }

    if profile_id in (None, "", "null"):
        return 0, empty_payload

    profile_path = profiles_dir / f"{profile_id}.md"
    if not profile_path.exists():
        return 2, {
            "error": f"unknown profile: {profile_id}",
            "looked_in": str(profiles_dir),
        }

    try:
        profile_fm = parse_frontmatter(profile_path)
    except yaml.YAMLError as exc:
        return 3, {
            "error": "malformed profile YAML",
            "path": str(profile_path),
            "details": str(exc),
        }

    journal_slug = marker_fm.get("target_journal") or marker_fm.get("journal")
    journal_overlay_path: Path | None = None
    journal_fm: dict = {}
    if journal_slug:
        candidate = paper_root / "Manuscript" / "_journal-style" / f"{journal_slug}.md"
        if candidate.exists():
            journal_overlay_path = candidate
            try:
                journal_fm = parse_frontmatter(candidate)
            except yaml.YAMLError as exc:
                return 3, {
                    "error": "malformed journal overlay YAML",
                    "path": str(candidate),
                    "details": str(exc),
                }

    call_slug = marker_fm.get("target_call") or marker_fm.get("call")
    call_overlay_path: Path | None = None
    call_fm: dict = {}
    if call_slug:
        candidate = paper_root / "Manuscript" / "_call" / f"{call_slug}.md"
        if candidate.exists():
            call_overlay_path = candidate
            try:
                call_fm = parse_frontmatter(candidate)
            except yaml.YAMLError as exc:
                return 3, {
                    "error": "malformed call overlay YAML",
                    "path": str(candidate),
                    "details": str(exc),
                }

    resolved = merge(merge(merge(SCHEMA_DEFAULTS, profile_fm), journal_fm), call_fm)

    should_run: bool | None = None
    if agent:
        active = resolved.get("agents_active") or []
        inactive = resolved.get("agents_inactive") or []
        if agent in inactive:
            should_run = False
        elif not active:
            should_run = True
        else:
            should_run = agent in active

    diagnostics = {
        "warnings": [],
        "missing_journal_overlay": bool(journal_slug) and journal_overlay_path is None,
        "missing_call_overlay": bool(call_slug) and call_overlay_path is None,
    }
    if diagnostics["missing_journal_overlay"]:
        diagnostics["warnings"].append(
            f"target_journal '{journal_slug}' is set but no overlay at "
            f"Manuscript/_journal-style/{journal_slug}.md"
        )
    if diagnostics["missing_call_overlay"]:
        diagnostics["warnings"].append(
            f"target_call '{call_slug}' is set but no overlay at "
            f"Manuscript/_call/{call_slug}.md"
        )

    return 0, {
        "profile_set": True,
        "profile_id": profile_id,
        "profile_path": str(profile_path),
        "journal_overlay_path": str(journal_overlay_path) if journal_overlay_path else None,
        "call_overlay_path": str(call_overlay_path) if call_overlay_path else None,
        "resolved_frontmatter": resolved,
        "should_run": should_run,
        "diagnostics": diagnostics,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path,
                    help="Path to paper root (contains .sws-project.local.md)")
    ap.add_argument("--agent", default=None,
                    help="Optional: agent id to check should_run for")
    ap.add_argument("--profiles-dir", default=None, type=Path,
                    help="Override profile directory (test use only)")
    args = ap.parse_args(argv)

    # Resolve plugin root from __file__ without following the symlink — when
    # tests stage a fake plugin directory, the scripts are symlinked into it
    # and we need profiles/ to come from the staged dir, not the real repo.
    plugin_root = Path(__file__).absolute().parent.parent
    profiles_dir = args.profiles_dir or (plugin_root / "profiles")

    code, payload = resolve(args.paper, args.agent, profiles_dir)
    if code == 0:
        print(json.dumps(payload))
    else:
        print(json.dumps(payload), file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
