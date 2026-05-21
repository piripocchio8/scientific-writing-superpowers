#!/usr/bin/env python3
"""Harness for smoke_cycle_09.sh — drives sws_bibliography_fidelity.run_fidelity_check
with unittest.mock patches so each variant tests one specific code path (D9c, D9a, D9b, D9)
independently of what is actually installed on the host system.

Usage:
    python3 _harness.py variant_1 <paper_root>
    python3 _harness.py variant_2 <paper_root> <sqlite_path>
    python3 _harness.py variant_3 <paper_root>
    python3 _harness.py variant_4 <paper_root> <index_json>

Exit 0 on success (all assertions passed), non-zero on failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

# Ensure scripts/ is importable regardless of cwd.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import sws_bibliography_fidelity as bf


def run_variant_1(paper_root: Path) -> int:
    """D9c: neither zotero skill nor Zotero desktop detected.

    Asserts: ran=false, skip_reason=no-zotero-installation-detected,
    report.md contains the neutral 'No Zotero installation detected' message.
    """
    with (
        patch.object(bf, "_probe_claude_zotero_skill", return_value=False),
        patch.object(bf, "_probe_zotero_desktop", return_value=(False, None)),
    ):
        rc = bf.run_fidelity_check(paper_root)

    if rc != 0:
        print(f"FAIL: run_fidelity_check returned {rc}, expected 0", file=sys.stderr)
        return 1

    status_path = paper_root / "_review" / "bibliography-fidelity-checker" / "status.json"
    if not status_path.exists():
        print(f"FAIL: status.json not written at {status_path}", file=sys.stderr)
        return 1

    status = json.loads(status_path.read_text())
    if status.get("ran") is not False:
        print(f"FAIL: expected ran=false, got {status.get('ran')}", file=sys.stderr)
        return 1
    if status.get("skip_reason") != "no-zotero-installation-detected":
        print(f"FAIL: expected skip_reason=no-zotero-installation-detected, got {status.get('skip_reason')}", file=sys.stderr)
        return 1
    if status.get("zotero_skill_available") is not False:
        print(f"FAIL: expected zotero_skill_available=false, got {status.get('zotero_skill_available')}", file=sys.stderr)
        return 1
    if status.get("zotero_desktop_detected") is not False:
        print(f"FAIL: expected zotero_desktop_detected=false, got {status.get('zotero_desktop_detected')}", file=sys.stderr)
        return 1

    report_path = paper_root / "_review" / "bibliography-fidelity-checker" / "report.md"
    if not report_path.exists():
        print(f"FAIL: report.md not written at {report_path}", file=sys.stderr)
        return 1
    report_text = report_path.read_text()
    if "No Zotero installation detected" not in report_text:
        print("FAIL: report.md does not contain expected D9c neutral message", file=sys.stderr)
        return 1

    print("variant_1: PASS (D9c — no-zotero-installation-detected, neutral report)")
    return 0


def run_variant_2(paper_root: Path, sqlite_path: str) -> int:
    """D9a: Zotero desktop detected, but no Claude Code zotero skill.

    Asserts: ran=false, skip_reason=zotero-desktop-detected-but-claude-skill-missing,
    zotero_sqlite_path is set, report.md leads with the actionable recommendation
    including the verbatim string 'we recommend installing the zotero plugin in Claude Code'.
    """
    with (
        patch.object(bf, "_probe_claude_zotero_skill", return_value=False),
        patch.object(bf, "_probe_zotero_desktop", return_value=(True, sqlite_path)),
    ):
        rc = bf.run_fidelity_check(paper_root)

    if rc != 0:
        print(f"FAIL: run_fidelity_check returned {rc}, expected 0", file=sys.stderr)
        return 1

    status_path = paper_root / "_review" / "bibliography-fidelity-checker" / "status.json"
    if not status_path.exists():
        print(f"FAIL: status.json not written at {status_path}", file=sys.stderr)
        return 1

    status = json.loads(status_path.read_text())
    if status.get("ran") is not False:
        print(f"FAIL: expected ran=false, got {status.get('ran')}", file=sys.stderr)
        return 1
    if status.get("skip_reason") != "zotero-desktop-detected-but-claude-skill-missing":
        print(f"FAIL: expected skip_reason=zotero-desktop-detected-but-claude-skill-missing, got {status.get('skip_reason')}", file=sys.stderr)
        return 1
    if status.get("zotero_sqlite_path") != sqlite_path:
        print(f"FAIL: expected zotero_sqlite_path={sqlite_path!r}, got {status.get('zotero_sqlite_path')!r}", file=sys.stderr)
        return 1
    if status.get("zotero_desktop_detected") is not True:
        print(f"FAIL: expected zotero_desktop_detected=true, got {status.get('zotero_desktop_detected')}", file=sys.stderr)
        return 1

    report_path = paper_root / "_review" / "bibliography-fidelity-checker" / "report.md"
    if not report_path.exists():
        print(f"FAIL: report.md not written at {report_path}", file=sys.stderr)
        return 1
    report_text = report_path.read_text()
    if "We detected a Zotero installation at" not in report_text:
        print("FAIL: report.md does not contain 'We detected a Zotero installation at'", file=sys.stderr)
        return 1
    # Verbatim assertion — locked by spec D9a.
    if "we recommend installing the zotero plugin in Claude Code" not in report_text:
        print("FAIL: report.md does not contain the D9a verbatim recommendation string", file=sys.stderr)
        return 1

    print("variant_2: PASS (D9a — zotero-desktop-detected-but-claude-skill-missing, actionable recommendation)")
    return 0


def run_variant_3(paper_root: Path) -> int:
    """D9b: zotero skill mocked-available, library size 5 (below 10 threshold).

    Asserts: ran=false, skip_reason=zotero-library-too-small, library_item_count=5.
    """
    with (
        patch.object(bf, "_probe_claude_zotero_skill", return_value=True),
        patch.object(bf, "_probe_zotero_desktop", return_value=(True, "/mock/zotero.sqlite")),
        patch.object(bf, "_query_zotero_library_size", return_value=5),
    ):
        rc = bf.run_fidelity_check(paper_root)

    if rc != 0:
        print(f"FAIL: run_fidelity_check returned {rc}, expected 0", file=sys.stderr)
        return 1

    status_path = paper_root / "_review" / "bibliography-fidelity-checker" / "status.json"
    if not status_path.exists():
        print(f"FAIL: status.json not written at {status_path}", file=sys.stderr)
        return 1

    status = json.loads(status_path.read_text())
    if status.get("ran") is not False:
        print(f"FAIL: expected ran=false, got {status.get('ran')}", file=sys.stderr)
        return 1
    if status.get("skip_reason") != "zotero-library-too-small":
        print(f"FAIL: expected skip_reason=zotero-library-too-small, got {status.get('skip_reason')}", file=sys.stderr)
        return 1
    if status.get("library_item_count") != 5:
        print(f"FAIL: expected library_item_count=5, got {status.get('library_item_count')}", file=sys.stderr)
        return 1

    print("variant_3: PASS (D9b — zotero-library-too-small)")
    return 0


def run_variant_4(paper_root: Path, index_json: Path) -> int:
    """D9 happy path: zotero skill mocked-available, library>=10, seeded fidelity violation.

    Asserts: ran=true, flags.json contains >=1 flag, report.md has V0.1 LIMITATION header.
    """
    index = json.loads(index_json.read_text())
    seeded_item = index[0]  # THROMBIN2021 item

    # The seeded passage: first 15 words of the fulltext_excerpt
    seeded_passage_words = seeded_item["fulltext_excerpt"].split()
    trigger_phrase = " ".join(seeded_passage_words[:15])

    def _mock_search(passage: str) -> list:
        """Return the seeded item when the passage matches the trigger phrase."""
        if trigger_phrase in passage or passage in seeded_item["fulltext_excerpt"]:
            return [{
                "item_key": seeded_item["item_key"],
                "title": seeded_item["title"],
                "authors": seeded_item["authors"],
                "year": seeded_item["year"],
                "collection": seeded_item["collection"],
            }]
        return []

    # Build mock paragraphs from blank-line-separated blocks in the seeded draft.
    draft_file = paper_root / "_drafts" / "introduction-revised.md"
    if not draft_file.exists():
        print(f"FAIL: seeded draft not found at {draft_file}", file=sys.stderr)
        return 1

    draft_text = draft_file.read_text(encoding="utf-8")
    raw_blocks = draft_text.split("\n\n")
    mock_paragraphs = []
    pid = 0
    for block in raw_blocks:
        text = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if text.startswith("#"):
            continue
        if len(text.split()) >= 15:
            mock_paragraphs.append({
                "id": f"p{pid}",
                "section": "introduction",
                "text": text,
            })
            pid += 1

    if not mock_paragraphs:
        print("FAIL: no paragraphs with >=15 words found in seeded draft", file=sys.stderr)
        return 1

    with (
        patch.object(bf, "_probe_claude_zotero_skill", return_value=True),
        patch.object(bf, "_probe_zotero_desktop", return_value=(True, "/mock/zotero.sqlite")),
        patch.object(bf, "_query_zotero_library_size", return_value=42),
        patch.object(bf, "_extract_paragraphs_from_docx", return_value=mock_paragraphs),
        patch.object(bf, "_zotero_fulltext_search", side_effect=_mock_search),
    ):
        rc = bf.run_fidelity_check(paper_root)

    if rc != 0:
        print(f"FAIL: run_fidelity_check returned {rc}, expected 0", file=sys.stderr)
        return 1

    status_path = paper_root / "_review" / "bibliography-fidelity-checker" / "status.json"
    flags_path = paper_root / "_review" / "bibliography-fidelity-checker" / "flags.json"
    report_path = paper_root / "_review" / "bibliography-fidelity-checker" / "report.md"

    if not status_path.exists():
        print(f"FAIL: status.json not written at {status_path}", file=sys.stderr)
        return 1

    status = json.loads(status_path.read_text())
    if status.get("ran") is not True:
        print(f"FAIL: expected ran=true, got {status.get('ran')}", file=sys.stderr)
        return 1

    if not flags_path.exists():
        print(f"FAIL: flags.json not written at {flags_path}", file=sys.stderr)
        return 1

    flags = json.loads(flags_path.read_text())
    if len(flags) < 1:
        print(f"FAIL: expected >=1 flag, got {len(flags)}", file=sys.stderr)
        return 1

    if not report_path.exists():
        print(f"FAIL: report.md not written at {report_path}", file=sys.stderr)
        return 1

    report_text = report_path.read_text()
    if "V0.1 LIMITATION" not in report_text:
        print("FAIL: report.md does not contain V0.1 LIMITATION header", file=sys.stderr)
        return 1

    print(f"variant_4: PASS (D9 happy — {len(flags)} flag(s) in flags.json, V0.1 LIMITATION present)")
    return 0


def main() -> int:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <variant_1|variant_2|variant_3|variant_4> <paper_root> [extra_arg]", file=sys.stderr)
        return 2

    variant = sys.argv[1]
    paper_root = Path(sys.argv[2])

    if not paper_root.is_dir():
        print(f"FAIL: paper_root not found: {paper_root}", file=sys.stderr)
        return 1

    if variant == "variant_1":
        return run_variant_1(paper_root)
    elif variant == "variant_2":
        if len(sys.argv) < 4:
            print("FAIL: variant_2 requires <sqlite_path> as third argument", file=sys.stderr)
            return 2
        return run_variant_2(paper_root, sys.argv[3])
    elif variant == "variant_3":
        return run_variant_3(paper_root)
    elif variant == "variant_4":
        if len(sys.argv) < 4:
            print("FAIL: variant_4 requires <index_json> as third argument", file=sys.stderr)
            return 2
        return run_variant_4(paper_root, Path(sys.argv[3]))
    else:
        print(f"FAIL: unknown variant '{variant}'. Use variant_1, variant_2, variant_3, or variant_4.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
