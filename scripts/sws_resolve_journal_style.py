#!/usr/bin/env python3
"""Helper for /sws:resolve-journal-style.

Orchestrates: validate profile is set; resolve slug to URL; load source HTML;
synthesize frontmatter (via env-var fixture in tests, via LLM subagent in prod —
the LLM dispatch lives in SKILL.md); archive existing overlay; write new overlay;
print diff summary.

Tests bypass the synthesizer subagent by setting:
    SWS_TEST_FIXTURE_SYNTH_OUTPUT=<path-to-yaml-file>

The fixture file is a YAML mapping that becomes the overlay frontmatter directly.

CLI:
    python sws_resolve_journal_style.py --paper <root> --slug <slug>
                                         [--url <url>]
                                         [--noninteractive]

Exit codes:
    0 - overlay written; diff printed (or "(no field changes)")
    1 - profile not set in marker
    2 - unknown slug and no --url provided
    3 - synthesizer fixture missing / malformed (test mode only)
    4 - marker not found
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sws_hook_utils import parse_marker  # noqa: E402
from sws_overlay_io import (  # noqa: E402
    archive_overlay, diff_summary, write_overlay,
)


def load_url_map(plugin_root: Path) -> dict:
    map_path = plugin_root / "references" / "journal-url-map.yaml"
    if not map_path.exists():
        return {}
    return yaml.safe_load(map_path.read_text()) or {}


def synthesize_via_fixture(fixture_path: Path) -> dict:
    if not fixture_path.exists():
        raise FileNotFoundError(f"synthesizer fixture missing: {fixture_path}")
    return yaml.safe_load(fixture_path.read_text()) or {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--url", default=None,
                    help="Override URL; required if slug is not in journal-url-map.yaml")
    ap.add_argument("--noninteractive", action="store_true",
                    help="Do not prompt for confirmation; test mode")
    args = ap.parse_args(argv)

    plugin_root = Path(__file__).absolute().parent.parent

    marker = args.paper / ".sws-project.local.md"
    if not marker.exists():
        print(
            "error: not an SWS project (no .sws-project.local.md found)",
            file=sys.stderr,
        )
        return 4
    marker_fm = parse_marker(marker)
    if not marker_fm.get("profile"):
        print(
            "error: no profile set — run /sws:set-profile <name> first",
            file=sys.stderr,
        )
        return 1

    url_map = load_url_map(plugin_root)
    url = args.url or url_map.get(args.slug)
    if not url:
        print(
            f"error: no URL on file for slug '{args.slug}' — pass --url <guide-for-authors-url>",
            file=sys.stderr,
        )
        return 2

    # Synthesizer: in production, the SKILL.md prose dispatches a subagent
    # against the URL contents (WebFetch). In tests we use a fixture YAML.
    fixture_env = os.environ.get("SWS_TEST_FIXTURE_SYNTH_OUTPUT")
    if fixture_env:
        try:
            new_fm = synthesize_via_fixture(Path(fixture_env))
        except (FileNotFoundError, yaml.YAMLError) as exc:
            print(f"error: synthesizer fixture problem: {exc}", file=sys.stderr)
            return 3
    else:
        # Production mode: the SKILL.md prose handles the subagent dispatch
        # and writes the resulting YAML to a temp path it passes via --url.
        # In v0.1 the wrapper itself does not call WebFetch — the model layer
        # supplies the synthesized frontmatter through the fixture env var or
        # by writing the overlay directly. If neither is set in noninteractive
        # mode we abort cleanly.
        if args.noninteractive:
            print(
                "error: this helper requires synthesized frontmatter input.\n"
                "End-users should run /sws:resolve-journal-style (the slash command),\n"
                "which dispatches the synthesizer subagent through SKILL.md.\n"
                "For tests: set SWS_TEST_FIXTURE_SYNTH_OUTPUT=<path-to-yaml-file>.",
                file=sys.stderr,
            )
            return 3
        # Interactive mode without a fixture: the SKILL.md prose is expected
        # to have populated SWS_TEST_FIXTURE_SYNTH_OUTPUT before invoking this
        # script. We surface an instruction rather than guessing.
        print(
            "info: this helper expects the SKILL.md prose layer (invoked by\n"
            "/sws:resolve-journal-style) to dispatch the synthesizer subagent and\n"
            "pass the result via SWS_TEST_FIXTURE_SYNTH_OUTPUT. URL for synthesis: "
            + url,
            file=sys.stderr,
        )
        return 3

    overlay_path = args.paper / "Manuscript" / "_journal-style" / f"{args.slug}.md"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)

    old_text = overlay_path.read_text() if overlay_path.exists() else ""
    archived = archive_overlay(overlay_path)

    # Render body — keep a one-line attribution.
    body = (
        f"# {args.slug} overlay (auto-synthesized {url})\n\n"
        "Generated by /sws:resolve-journal-style. Re-run the slash command to refresh."
    )
    write_overlay(overlay_path, new_fm, body=body)

    # Diff
    new_text = overlay_path.read_text()
    diff = diff_summary(old_text, new_text)

    msg = {
        "overlay_path": str(overlay_path),
        "archived_to": str(archived) if archived else None,
        "diff": diff,
    }
    print(json.dumps(msg, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
