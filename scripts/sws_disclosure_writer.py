#!/usr/bin/env python3
"""Venue-specific AI-usage disclosure renderer.

Renders `_submission/ai-disclosure.md` from one of four templates shipped in
`references/submission-artifacts.md` (icmje | wiley | rsc | acs; D7).

Gating:
  - `RESOLVED_DISCLOSURE_REQUIRED` env var must be "true". If "false" (or
    unset), the script exits 0 with a "not required" message.
  - Template selection: reads `<paper>/Manuscript/_journal-style/<slug>.md`
    overlay frontmatter and looks for `disclosure.template_id` (one of the 4
    known ids). Missing -> fallback to "icmje" with stderr warning.
  - Unknown template_id -> exits 3.

CLI:
    sws_disclosure_writer.py [--paper-root <path>] [--venue <slug>]
                             [--use-categories a,b,c]

Defaults: --paper-root = cwd; --venue = `target_journal` from marker.

Use-categories default to `use_categories_options[:3]` from the chosen
template; --use-categories CSV overrides.

Side effects:
  - prints `last_verified` of the chosen template to stderr (R6).
  - atomic write to `_submission/ai-disclosure.md`.

Exit codes:
    0 - success (or disclosure not required)
    2 - missing reference doc / unreadable
    3 - unknown template_id requested
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    print(f"sws_disclosure_writer: PyYAML missing ({exc})", file=sys.stderr)
    raise SystemExit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent
REF_DOC = REPO_ROOT / "references" / "submission-artifacts.md"


# ---------------------------------------------------------------------------
# Reference doc loader
# ---------------------------------------------------------------------------

def load_templates(ref_path: Path = REF_DOC) -> dict:
    """Parse references/submission-artifacts.md frontmatter and return
    `disclosure_templates` mapping."""
    if not ref_path.exists():
        raise FileNotFoundError(f"reference doc missing: {ref_path}")
    text = ref_path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"reference doc missing YAML frontmatter: {ref_path}")
    end = text.index("\n---", 4)
    fm = yaml.safe_load(text[4:end])
    templates = fm.get("disclosure_templates") or {}
    if not isinstance(templates, dict):
        raise ValueError("disclosure_templates must be a mapping")
    return templates


# ---------------------------------------------------------------------------
# Marker + overlay helpers
# ---------------------------------------------------------------------------

def read_marker(paper_root: Path) -> dict:
    marker = paper_root / ".sws-project.local.md"
    if not marker.exists():
        return {}
    text = marker.read_text()
    if not text.startswith("---\n"):
        return {}
    try:
        end = text.index("\n---", 4)
        return yaml.safe_load(text[4:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}


def read_overlay_template_id(paper_root: Path, slug: str) -> str | None:
    """Return overlay's `disclosure.template_id` or None."""
    if not slug:
        return None
    overlay = paper_root / "Manuscript" / "_journal-style" / f"{slug}.md"
    if not overlay.exists():
        return None
    text = overlay.read_text()
    if not text.startswith("---\n"):
        return None
    try:
        end = text.index("\n---", 4)
        fm = yaml.safe_load(text[4:end]) or {}
    except (ValueError, yaml.YAMLError):
        return None
    disclosure = fm.get("disclosure")
    if isinstance(disclosure, dict):
        tid = disclosure.get("template_id")
        if isinstance(tid, str):
            return tid
    return None


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_disclosure(template: dict, use_categories: list[str]) -> str:
    """Substitute {USE_CATEGORIES} placeholder; return the rendered body."""
    body = template.get("body_template", "")
    joined = ", ".join(use_categories) if use_categories else "[USE_CATEGORIES]"
    return body.replace("{USE_CATEGORIES}", joined).rstrip() + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--paper-root", default=os.getcwd(), help="Paper root (default cwd)")
    ap.add_argument("--venue", default=None, help="Override target_journal slug")
    ap.add_argument(
        "--use-categories",
        default=None,
        help="CSV of use categories; default: top 3 of the chosen template's options",
    )
    args = ap.parse_args(argv)

    paper_root = Path(args.paper_root).resolve()

    # Gate on RESOLVED_DISCLOSURE_REQUIRED.
    required_env = os.environ.get("RESOLVED_DISCLOSURE_REQUIRED", "").strip().lower()
    if required_env != "true":
        print(
            "sws_disclosure_writer: disclosure not required for this profile "
            "(RESOLVED_DISCLOSURE_REQUIRED != 'true'). Nothing written.",
            file=sys.stderr,
        )
        return 0

    # Load templates.
    try:
        templates = load_templates()
    except (FileNotFoundError, ValueError) as exc:
        print(f"sws_disclosure_writer: {exc}", file=sys.stderr)
        return 2

    # Resolve venue + template id.
    marker = read_marker(paper_root)
    venue = args.venue or marker.get("target_journal")
    template_id = read_overlay_template_id(paper_root, venue) if venue else None

    if template_id is None:
        if venue:
            print(
                f"sws_disclosure_writer: no disclosure.template_id in overlay for "
                f"venue '{venue}'; falling back to 'icmje'. TODO: populate overlay.",
                file=sys.stderr,
            )
        else:
            print(
                "sws_disclosure_writer: no target_journal set; falling back to "
                "'icmje'. TODO: set target_journal or pass --venue.",
                file=sys.stderr,
            )
        template_id = "icmje"

    if template_id not in templates:
        print(
            f"sws_disclosure_writer: unknown template_id '{template_id}'. "
            f"Known: {sorted(templates.keys())}",
            file=sys.stderr,
        )
        return 3

    template = templates[template_id]

    # Use-categories.
    if args.use_categories:
        use_cats = [c.strip() for c in args.use_categories.split(",") if c.strip()]
    else:
        opts = template.get("use_categories_options") or []
        use_cats = list(opts[:3])

    rendered = render_disclosure(template, use_cats)

    # Last_verified to stderr (R6).
    last_v = template.get("last_verified")
    if last_v:
        print(
            f"sws_disclosure_writer: template '{template_id}' last_verified {last_v}",
            file=sys.stderr,
        )

    out_path = paper_root / "_submission" / "ai-disclosure.md"
    atomic_write(out_path, rendered)
    print(f"sws_disclosure_writer: wrote {out_path}", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
