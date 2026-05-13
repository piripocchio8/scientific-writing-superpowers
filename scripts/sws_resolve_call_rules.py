#!/usr/bin/env python3
"""Helper for /sws:resolve-call-rules.

Scans <paper>/Manuscript/call/ for non-underscore source files (PDF/DOCX/MD/TXT/HTML);
applies a hybrid regex+LLM extractor (regex/heuristic for deadline / page-limit /
budget patterns; LLM fills gaps); user-confirm pass on uncertain fields; or, with
no source, a 5-field Q&A wizard. Archives + writes overlay; prints diff.

The LLM step is dispatched by the SKILL.md prose. In tests, the synthesized
frontmatter comes from SWS_TEST_FIXTURE_SYNTH_OUTPUT (a YAML file path).

CLI:
    python sws_resolve_call_rules.py --paper <root> [--slug <slug>] [--noninteractive]

Exit codes:
    0 - overlay written; diff printed
    1 - profile is not funding-proposal
    3 - synthesizer fixture missing / malformed (test mode)
    4 - marker not found
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sws_hook_utils import parse_marker  # noqa: E402
from sws_overlay_io import archive_overlay, diff_summary, write_overlay  # noqa: E402


SOURCE_EXTENSIONS = (".pdf", ".docx", ".md", ".txt", ".html")


def scan_call_dir(call_dir: Path) -> list[Path]:
    """Return non-underscore source files in call_dir.

    Underscore-prefixed files and any _archive/ subdir are ignored.
    """
    if not call_dir.is_dir():
        return []
    matches: list[Path] = []
    for p in sorted(call_dir.iterdir()):
        if p.is_dir():
            continue
        if p.name.startswith("_"):
            continue
        if p.suffix.lower() in SOURCE_EXTENSIONS:
            matches.append(p)
    return matches


# Deadline pattern: dates like "31 January 2026", "2026-01-31", "January 31, 2026".
DEADLINE_RE = re.compile(
    r"(?P<deadline>(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"
    r"|(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4})"
    r"|(?:\d{4}-\d{2}-\d{2}))",
    re.IGNORECASE,
)

PAGE_LIMIT_RE = re.compile(
    r"(?:max(?:imum)?\.?\s*)?(?P<pages>\d{1,3})\s*pages?",
    re.IGNORECASE,
)

BUDGET_RE = re.compile(
    r"(?:€|EUR\s*|USD\s*)\s*(?P<amount>[\d,.]+\s*(?:k|K|m|M|million|thousand)?)",
)


def heuristic_extract(text: str) -> dict:
    """Regex-extract deadline, page limit, budget. Per D13 (hybrid B+C)."""
    out: dict[str, object] = {}
    m = DEADLINE_RE.search(text)
    if m:
        out["deadline"] = m.group("deadline").strip()
    m = PAGE_LIMIT_RE.search(text)
    if m:
        out["page_limit"] = int(m.group("pages"))
    m = BUDGET_RE.search(text)
    if m:
        out["budget"] = m.group(0).strip()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--slug", default=None,
                    help="Overlay slug. If absent, derived from the source filename.")
    ap.add_argument("--noninteractive", action="store_true")
    args = ap.parse_args(argv)

    marker = args.paper / ".sws-project.local.md"
    if not marker.exists():
        print(
            "error: not an SWS project (no .sws-project.local.md found)",
            file=sys.stderr,
        )
        return 4
    marker_fm = parse_marker(marker)
    profile = marker_fm.get("profile")
    if profile != "funding-proposal":
        print(
            f"error: /sws:resolve-call-rules requires profile=funding-proposal "
            f"(current: {profile!r}). Run /sws:set-profile funding-proposal first.",
            file=sys.stderr,
        )
        return 1

    call_dir = args.paper / "Manuscript" / "call"
    call_dir.mkdir(parents=True, exist_ok=True)
    sources = scan_call_dir(call_dir)

    if sources:
        primary = sources[0]
        slug = args.slug or primary.stem
        # Extraction text — for v0.1 the SKILL.md prose runs Read on the file
        # (handles DOCX/PDF/HTML/MD/TXT) and writes the plain text to a tempfile,
        # then sets SWS_TEST_FIXTURE_SOURCE_TEXT to that path. Tests use it too.
        text_path = os.environ.get("SWS_TEST_FIXTURE_SOURCE_TEXT")
        if text_path and Path(text_path).exists():
            text = Path(text_path).read_text(errors="ignore")
        elif primary.suffix.lower() in (".md", ".txt", ".html"):
            text = primary.read_text(errors="ignore")
        else:
            text = ""
        heuristics = heuristic_extract(text)
    else:
        primary = None
        slug = args.slug or "qa-wizard"
        heuristics = {}

    fixture_env = os.environ.get("SWS_TEST_FIXTURE_SYNTH_OUTPUT")
    if fixture_env:
        try:
            new_fm = yaml.safe_load(Path(fixture_env).read_text()) or {}
        except (FileNotFoundError, yaml.YAMLError) as exc:
            print(f"error: synthesizer fixture problem: {exc}", file=sys.stderr)
            return 3
        # Merge in heuristics for fields the fixture didn't override.
        for k, v in heuristics.items():
            new_fm.setdefault(k, v)
    else:
        if args.noninteractive:
            print(
                "error: this helper requires synthesized frontmatter input.\n"
                "End-users should run /sws:resolve-call-rules (the slash command),\n"
                "which dispatches the LLM extractor + Q&A wizard through SKILL.md.\n"
                "For tests: set SWS_TEST_FIXTURE_SYNTH_OUTPUT=<path-to-yaml-file>.",
                file=sys.stderr,
            )
            return 3
        # The SKILL.md prose handles the interactive LLM + Q&A wizard in prod.
        print(
            "info: this helper expects the SKILL.md prose layer (invoked by\n"
            "/sws:resolve-call-rules) to dispatch the LLM extractor + Q&A wizard\n"
            "and pass the result via SWS_TEST_FIXTURE_SYNTH_OUTPUT.",
            file=sys.stderr,
        )
        return 3

    overlay_path = args.paper / "Manuscript" / "_call" / f"{slug}.md"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)

    old_text = overlay_path.read_text() if overlay_path.exists() else ""
    archived = archive_overlay(overlay_path)

    src_note = f" (source: {primary.name})" if primary else " (Q&A wizard)"
    body = (
        f"# {slug} call overlay{src_note}\n\n"
        "Generated by /sws:resolve-call-rules. Re-run the slash command to refresh."
    )
    write_overlay(overlay_path, new_fm, body=body)
    new_text = overlay_path.read_text()
    diff = diff_summary(old_text, new_text)

    msg = {
        "overlay_path": str(overlay_path),
        "archived_to": str(archived) if archived else None,
        "source": str(primary) if primary else None,
        "heuristics": heuristics,
        "diff": diff,
    }
    print(json.dumps(msg, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
