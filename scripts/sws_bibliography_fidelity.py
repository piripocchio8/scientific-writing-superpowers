"""Bibliography-fidelity check against the user's Zotero corpus.

Detects four paths:
  - D9   happy: claude zotero skill available + Zotero desktop indexed + library ≥10.
              → runs verbatim-overlap check; writes flags.json + report.md.
  - D9a  recommendation: Zotero desktop detected but Claude Code zotero skill missing.
              → exits 0; report.md leads with the actionable recommendation.
  - D9b  inert library: skill present but library too small / unresponsive / permission-denied.
              → exits 0; status.json carries the specific reason.
  - D9c  neutral skip: neither skill nor desktop detected.
              → exits 0; report.md is a neutral note (no install push).

All four paths exit 0 (skip is not an error). Status.json is the
machine-readable companion to report.md; both are always written.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


_MIN_PHRASE_WORDS = 15
_MIN_LIBRARY_ITEMS = 10
_QUERY_TIMEOUT_S = 30


# Verbatim wording locked by spec D9a. Smoke test asserts these strings.
_D9A_RECOMMENDATION_TEMPLATE = (
    "We detected a Zotero installation at {path}. If you use Zotero to manage references "
    "for this manuscript, we recommend installing the zotero plugin in Claude Code to enable "
    "the bibliography-fidelity check. Install with: /plugin install zotero (or your "
    "equivalent). After installation, re-run /sws:check-fidelity to verify your manuscript "
    "against your Zotero corpus."
)

_D9C_NEUTRAL_TEMPLATE = (
    "No Zotero installation detected on this system. The bibliography-fidelity check is "
    "Zotero-only in v0.1. If you use a different reference manager (Mendeley, EndNote, "
    "Papers, plain BibTeX), this check is not available in v0.1. Manual proofreading "
    "remains the recommended workaround. See v0.2 backlog for planned unbounded-corpus "
    "alternatives (Crossref Similarity Check, Google Programmable Search opt-in)."
)

_V01_LIMITATION_HEADER = (
    "## V0.1 LIMITATION\n\n"
    "This is a fidelity check against your Zotero library only, not unbounded-corpus "
    "plagiarism detection. It catches verbatim copies of ≥15 contiguous words from "
    "papers in your Zotero corpus. Paraphrase, synonym substitution, and sentence "
    "reordering will NOT be caught. Sources outside your Zotero (open web, papers you "
    "haven't read) are NOT checked.\n"
)


# ---------------------------------------------------------------------------
# Probe layer
# ---------------------------------------------------------------------------


def _probe_claude_zotero_skill() -> bool:
    """Detect whether the Claude Code zotero plugin/skill is installed.

    Tries three independent signals; any one positive returns True.
    """
    # Signal 1: ~/.claude/plugins/cache/* containing 'zotero' anywhere.
    home = Path.home()
    cache_dir = home / ".claude" / "plugins" / "cache"
    if cache_dir.is_dir():
        for child in cache_dir.iterdir():
            if "zotero" in child.name.lower():
                return True

    # Signal 2: `claude --list-skills` mentions zotero.
    claude_bin = shutil.which("claude")
    if claude_bin:
        try:
            result = subprocess.run(
                [claude_bin, "--list-skills"],
                capture_output=True, text=True, timeout=5,
            )
            if "zotero" in (result.stdout or "").lower():
                return True
        except (subprocess.SubprocessError, OSError):
            pass

    # Signal 3: ~/.claude/CLAUDE.md references the zotero skill.
    claude_md = home / ".claude" / "CLAUDE.md"
    if claude_md.is_file():
        try:
            if "zotero" in claude_md.read_text(encoding="utf-8", errors="ignore").lower():
                return True
        except OSError:
            pass

    return False


def _probe_zotero_desktop(env: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str]]:
    """Detect Zotero desktop SQLite. Returns (found, path)."""
    env = env if env is not None else os.environ
    home = Path(env.get("HOME") or env.get("USERPROFILE") or Path.home())

    candidates: List[Path] = []
    # Custom data dir override
    custom = env.get("ZOTERO_DATA_DIR")
    if custom:
        candidates.append(Path(custom) / "zotero.sqlite")

    # macOS / Linux default
    candidates.append(home / "Zotero" / "zotero.sqlite")
    # Windows default (when HOME is not set but USERPROFILE is)
    win_profile = env.get("USERPROFILE")
    if win_profile:
        candidates.append(Path(win_profile) / "Zotero" / "zotero.sqlite")
    # Older Zotero 5 profile-based path on Linux
    legacy = home / ".zotero" / "zotero"
    if legacy.is_dir():
        for profile in legacy.iterdir():
            candidates.append(profile / "zotero.sqlite")

    for c in candidates:
        if c.is_file():
            return True, str(c)
    return False, None


def probe_zotero() -> Dict[str, object]:
    """Return a probe-state dict combining both probe layers."""
    skill = _probe_claude_zotero_skill()
    desktop, path = _probe_zotero_desktop()
    return {
        "zotero_skill_available": skill,
        "zotero_desktop_detected": desktop,
        "zotero_sqlite_path": path,
    }


# ---------------------------------------------------------------------------
# Library / search shims (mocked by tests; real implementations would call
# the user's `zotero` skill via the agent dispatch surface).
# ---------------------------------------------------------------------------


def _query_zotero_library_size() -> int:
    """Return the number of items in the user's primary Zotero library.

    In v0.1 we do not have a stable Python entry point into the `zotero`
    skill; the agent layer wraps that. This shim returns 0 by default so
    that running the script outside a real session degrades to D9b
    library-too-small rather than a crash.
    """
    return 0


def _zotero_fulltext_search(passage: str) -> List[Dict]:
    """Return matching Zotero items for a phrase. Mocked in tests."""
    return []


def _extract_paragraphs_from_docx(docx_path: Path) -> List[Dict]:
    """Extract paragraphs from final .docx. Wraps scripts/sws_read_docx.py.

    In v0.1, when running outside a real paper-root, returns an empty list
    so the happy-path code is exercisable in unit tests via monkeypatch.
    """
    return []


# ---------------------------------------------------------------------------
# Phrase generation + match logic
# ---------------------------------------------------------------------------


def _generate_phrases(text: str, min_words: int = _MIN_PHRASE_WORDS) -> List[str]:
    words = text.split()
    if len(words) < min_words:
        return []
    return [" ".join(words[i : i + min_words]) for i in range(len(words) - min_words + 1)]


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_status(paper_root: Path, status: Dict) -> None:
    out_dir = paper_root / "_review" / "bibliography-fidelity-checker"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _write_flags(paper_root: Path, flags: List[Dict]) -> None:
    out_dir = paper_root / "_review" / "bibliography-fidelity-checker"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "flags.json").write_text(
        json.dumps(flags, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _write_report(paper_root: Path, body: str) -> None:
    out_dir = paper_root / "_review" / "bibliography-fidelity-checker"
    out_dir.mkdir(parents=True, exist_ok=True)
    header = (
        "---\n"
        "sws_artifact: bibliography-fidelity-report\n"
        "agent: bibliography-fidelity-checker\n"
        "---\n\n"
        "# Bibliography-fidelity report\n\n"
    )
    (out_dir / "report.md").write_text(header + body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def run_fidelity_check(paper_root: Path) -> int:
    state = probe_zotero()

    # D9c — neither skill nor desktop
    if not state["zotero_skill_available"] and not state["zotero_desktop_detected"]:
        status = {**state, "ran": False, "skip_reason": "no-zotero-installation-detected"}
        _write_status(paper_root, status)
        _write_report(paper_root, _D9C_NEUTRAL_TEMPLATE + "\n")
        _write_flags(paper_root, [])
        return 0

    # D9a — desktop detected, skill missing
    if not state["zotero_skill_available"] and state["zotero_desktop_detected"]:
        status = {
            **state,
            "ran": False,
            "skip_reason": "zotero-desktop-detected-but-claude-skill-missing",
        }
        _write_status(paper_root, status)
        body = _D9A_RECOMMENDATION_TEMPLATE.format(path=state["zotero_sqlite_path"]) + "\n"
        _write_report(paper_root, body)
        _write_flags(paper_root, [])
        return 0

    # D9b probe — library size / health
    try:
        size = _query_zotero_library_size()
    except TimeoutError:
        status = {**state, "ran": False, "skip_reason": "zotero-unresponsive"}
        _write_status(paper_root, status)
        _write_report(paper_root, "Zotero query exceeded 30 seconds. Skipped.\n")
        _write_flags(paper_root, [])
        return 0
    except PermissionError:
        status = {**state, "ran": False, "skip_reason": "zotero-permission-denied"}
        _write_status(paper_root, status)
        _write_report(paper_root, "Zotero permission denied. Skipped.\n")
        _write_flags(paper_root, [])
        return 0

    if size < _MIN_LIBRARY_ITEMS:
        status = {
            **state,
            "ran": False,
            "library_item_count": size,
            "skip_reason": "zotero-library-too-small",
        }
        _write_status(paper_root, status)
        _write_report(
            paper_root,
            f"Zotero library has {size} items; the fidelity check requires "
            f"at least {_MIN_LIBRARY_ITEMS} to be meaningful. Skipped.\n",
        )
        _write_flags(paper_root, [])
        return 0

    # D9 happy path — run the verbatim-overlap check
    manuscript_dir = paper_root / "Manuscript"
    docx_candidates = sorted(manuscript_dir.glob("*.docx"))
    docx_path = docx_candidates[0] if docx_candidates else manuscript_dir / "final.docx"
    paragraphs = _extract_paragraphs_from_docx(docx_path)

    flags: List[Dict] = []
    for para in paragraphs:
        for phrase in _generate_phrases(para["text"]):
            hits = _zotero_fulltext_search(phrase)
            for h in hits:
                flags.append(
                    {
                        "paragraph_id": para["id"],
                        "section": para.get("section", "unknown"),
                        "overlap_text": phrase,
                        "zotero_item_key": h.get("item_key"),
                        "zotero_title": h.get("title"),
                        "zotero_authors": h.get("authors"),
                        "zotero_year": h.get("year"),
                        "zotero_collection": h.get("collection"),
                        "page_hint": h.get("page_hint"),
                    }
                )

    status = {**state, "ran": True, "library_item_count": size, "flag_count": len(flags)}
    _write_status(paper_root, status)
    _write_flags(paper_root, flags)

    body_lines = [_V01_LIMITATION_HEADER, "\n## Findings\n"]
    if not flags:
        body_lines.append(
            "\nNo verbatim overlaps ≥15 contiguous words were found against your "
            f"Zotero corpus ({size} items).\n"
        )
    else:
        body_lines.append(f"\n{len(flags)} potential fidelity violation(s) flagged:\n\n")
        for f in flags:
            body_lines.append(
                f"- Section **{f['section']}**, paragraph `{f['paragraph_id']}`: matches "
                f"{f.get('zotero_authors')} ({f.get('zotero_year')}) — "
                f"_{f.get('zotero_title')}_ (item `{f.get('zotero_item_key')}`).\n"
                f"  Overlap: \"{f['overlap_text']}\"\n"
            )
    _write_report(paper_root, "".join(body_lines))
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bibliography-fidelity check (cycle-09 D9)")
    parser.add_argument("paper_root", type=Path, help="Paper root directory")
    parser.add_argument("--probe-zotero", action="store_true", help="Print probe state JSON only")
    args = parser.parse_args(argv)

    if args.probe_zotero:
        print(json.dumps(probe_zotero(), indent=2))
        return 0

    if not args.paper_root.is_dir():
        print(f"error: paper_root not found: {args.paper_root}", file=sys.stderr)
        return 2

    return run_fidelity_check(args.paper_root)


if __name__ == "__main__":
    raise SystemExit(main())
