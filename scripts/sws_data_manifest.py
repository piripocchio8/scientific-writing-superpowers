"""Build and update Zenodo_db/manifest.json atomically (D5).

Each manifest entry links: dataset -> script -> figure(s).
Atomic write uses a .tmp rename to prevent corruption on crash.

CLI:
  sws_data_manifest.py <zenodo_db_dir> --add
        --dataset <rel-path> --sheet <name>
        --script <rel-path>
        --figures <rel-path> [<rel-path> ...]
        --journal-style <id-or-empty>
        [--width-in <float>] [--min-font-pt <float>]

  sws_data_manifest.py <zenodo_db_dir> --check
        (flags figures/ files absent from manifest.json)

Exit codes:
  0  ok
  1  orphaned figures found (--check mode)
  2  zenodo_db_dir not found or required argument missing
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_NAME = "manifest.json"
MANIFEST_TMP = ".manifest.json.tmp"


def _load_manifest(db: Path) -> list:
    manifest_path = db / MANIFEST_NAME
    if not manifest_path.exists():
        return []
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_manifest_atomic(db: Path, entries: list) -> None:
    tmp = db / MANIFEST_TMP
    content = json.dumps(entries, indent=2, ensure_ascii=False)
    tmp.write_text(content, encoding="utf-8")
    tmp.rename(db / MANIFEST_NAME)


def cmd_add(db: Path, args) -> int:
    entries = _load_manifest(db)
    entry = {
        "dataset": args.dataset,
        "sheet": args.sheet,
        "script": args.script,
        "figures": args.figures,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "journal_style": args.journal_style or "",
        "notes": "",
    }
    # D6a figure-readability metrics from sws_plot_runner.py — recorded only when
    # the plot-maker passes them through; omitted otherwise so non-figure entries
    # stay clean.
    if args.width_in is not None:
        entry["width_in"] = args.width_in
    if args.min_font_pt is not None:
        entry["min_font_pt"] = args.min_font_pt
    entries.append(entry)
    _save_manifest_atomic(db, entries)
    print(f"sws_data_manifest: added entry for {args.dataset} -> {args.figures}")
    return 0


def cmd_check(db: Path) -> int:
    manifest_path = db / MANIFEST_NAME
    entries = _load_manifest(db)
    registered_figures: set[str] = set()
    for entry in entries:
        for fig in entry.get("figures", []):
            registered_figures.add(fig)

    figures_dir = db / "figures"
    all_figures_on_disk: list[str] = []
    if figures_dir.is_dir():
        for f in figures_dir.iterdir():
            if f.is_file():
                all_figures_on_disk.append(f"figures/{f.name}")

    orphans = [fig for fig in all_figures_on_disk if fig not in registered_figures]
    if orphans:
        print("sws_data_manifest: orphaned figures (in figures/ but absent from manifest.json):")
        for o in sorted(orphans):
            print(f"  {o}")
        return 1
    print("sws_data_manifest: all figures registered in manifest.json")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build/update Zenodo_db/manifest.json (D5)."
    )
    ap.add_argument("zenodo_db", help="Path to Zenodo_db/ directory")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--add", action="store_true", help="Add a new manifest entry")
    mode.add_argument("--check", action="store_true", help="Check for orphaned figures")
    ap.add_argument("--dataset", help="Relative path to the source .xlsx inside Zenodo_db/")
    ap.add_argument("--sheet", help="Worksheet name within the dataset")
    ap.add_argument("--script", help="Relative path to the plot/fit script inside Zenodo_db/")
    ap.add_argument("--figures", nargs="+", help="Relative paths to output figures inside Zenodo_db/")
    ap.add_argument("--journal-style", default="", help="Resolved journal-style overlay id")
    ap.add_argument("--width-in", type=float, default=None,
                    help="D6a figure width in inches (from sws_plot_runner.py)")
    ap.add_argument("--min-font-pt", type=float, default=None,
                    help="D6a measured minimum font size in pt (from sws_plot_runner.py)")
    args = ap.parse_args(argv)

    db = Path(args.zenodo_db)
    if not db.is_dir():
        print(f"sws_data_manifest: directory not found: {db}", file=sys.stderr)
        return 2

    if args.add:
        for required in ("dataset", "sheet", "script", "figures"):
            if not getattr(args, required.replace("-", "_"), None):
                print(
                    f"sws_data_manifest: --add requires --{required}", file=sys.stderr
                )
                return 2
        return cmd_add(db, args)

    return cmd_check(db)


if __name__ == "__main__":
    sys.exit(main())
