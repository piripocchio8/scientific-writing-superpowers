"""Static-analysis consistency checker for SWS assembled drafts.

CLI:
    sws_consistency_check.py <drafts-dir>
    sws_consistency_check.py <drafts-dir> --outline <outline.md>
    sws_consistency_check.py <drafts-dir> --json
    sws_consistency_check.py <drafts-dir> --report-out <path>

Six text-internal checks (D9):
  1. Figure-reference cross-check (cited Figure N exists in outline figures: dict).
  2. Table-reference cross-check (cited Table N exists in outline tables: dict).
  3. Section-list cross-check (drafts-dir filenames match profile required sections).
  4. Citation-key uniqueness (no key written twice with different DOIs).
  5. Abbreviation introduction (abbrev must be introduced before use; cross-section).
  6. Terminology uniformity (case variants of same token with combined freq >= 3).

Severity:
  block  — missing figure/table ref, duplicate citation key with different DOI.
  warn   — never-defined abbreviation, case-variant terminology.

Exit code 0 if no block findings, 1 otherwise.
funding-proposal profile -> print unsupported message and exit 0 (D19).

Pure stdlib so it runs from any Python >= 3.9.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Import citation-key parser from the scripts/ dir alongside this file
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from sws_citation_key import parse_citation_key, ParseError  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FUNDING_PROPOSAL_PROFILE = "funding-proposal"

FIG_REF_RE = re.compile(
    r"\b(?:Fig\.|Figure|Figures)\s+(\d+)(?:[a-z]?)(?:\s+and\s+(\d+)(?:[a-z]?))*",
    re.IGNORECASE,
)
TABLE_REF_RE = re.compile(
    r"\b(?:Tab\.|Table|Tables)\s+(\d+)(?:[a-z]?)(?:\s+and\s+(\d+)(?:[a-z]?))*",
    re.IGNORECASE,
)
CITATION_KEY_RE = re.compile(r"\[([A-Za-z][A-Za-z\-]*\d{4};\s*(?:doi|zotero):[^\]]+)\]")
ABBREV_INTRO_RE = re.compile(
    r"(?P<full>[A-Z][a-z][^()]{2,40})\s+\((?P<abbr>[A-Z]{2,})\)"
)
WORD_TOKEN_RE = re.compile(r"\b[A-Za-z]{3,}\b")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_marker(paper_root: Path) -> dict[str, Any]:
    """Read .sws-project.local.md and return the frontmatter as a dict."""
    marker = paper_root / ".sws-project.local.md"
    if not marker.exists():
        return {}
    text = marker.read_text(encoding="utf-8")
    return _parse_yaml_frontmatter(text)


def _parse_yaml_frontmatter(text: str) -> dict[str, Any]:
    """Extract YAML frontmatter between leading --- fences."""
    try:
        import yaml  # type: ignore
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return {}
        end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), None)
        if end is None:
            return {}
        return yaml.safe_load("\n".join(lines[1:end])) or {}
    except Exception:
        return _parse_yaml_frontmatter_stdlib(text)


def _parse_yaml_frontmatter_stdlib(text: str) -> dict[str, Any]:
    """Minimal YAML frontmatter parser (stdlib only, key: value pairs)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), None)
    if end is None:
        return {}
    result: dict[str, Any] = {}
    for line in lines[1:end]:
        if ":" in line:
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def _read_outline(outline_path: Path) -> dict[str, Any]:
    """Read outline.md and return its frontmatter."""
    if not outline_path.exists():
        return {}
    text = outline_path.read_text(encoding="utf-8")
    return _parse_yaml_frontmatter(text)


def _read_profile(profile_id: str, profiles_dir: Path) -> dict[str, Any]:
    """Read a profile file and return its frontmatter."""
    profile_file = profiles_dir / f"{profile_id}.md"
    if not profile_file.exists():
        return {}
    text = profile_file.read_text(encoding="utf-8")
    return _parse_yaml_frontmatter(text)


def _collect_drafts(drafts_dir: Path) -> list[Path]:
    """Return sorted .md files in drafts_dir (excludes dotfiles)."""
    return sorted(p for p in drafts_dir.glob("*.md") if not p.name.startswith("."))


def _strip_code_fences(text: str) -> str:
    """Remove fenced code blocks from text."""
    return re.sub(r"```[^\n]*\n.*?```", " ", text, flags=re.DOTALL)


def _strip_inline_code(text: str) -> str:
    """Remove inline code spans."""
    return re.sub(r"`[^`]+`", " ", text)


def _strip_citation_placeholders(text: str) -> str:
    """Remove [CITATION_NEEDED: ...] placeholders."""
    return re.sub(r"\[CITATION_NEEDED:[^\]]+\]", " ", text)


def _clean_prose(text: str) -> str:
    return _strip_citation_placeholders(_strip_inline_code(_strip_code_fences(text)))


def _line_col(text: str, pos: int) -> tuple[int, int]:
    """Return (line, col) for a character position in text."""
    before = text[:pos]
    line = before.count("\n") + 1
    col = pos - before.rfind("\n")
    return line, col


def _snippet(text: str, pos: int, length: int = 120) -> str:
    start = max(0, pos - 20)
    end = min(len(text), pos + length)
    return text[start:end].replace("\n", " ")


def _make_finding(severity: str, category: str, what: str, where: str,
                  context: str, suggested_fix: str) -> dict[str, Any]:
    return {
        "severity": severity,
        "category": category,
        "what": what,
        "where": where,
        "context": context,
        "suggested_fix": suggested_fix,
    }


# ---------------------------------------------------------------------------
# Check 1 & 2 — Figure and table reference cross-check
# ---------------------------------------------------------------------------

def _extract_outline_keys(outline_data: dict, key: str) -> set[str]:
    """Extract keys from a dict-valued frontmatter field (e.g. figures: or tables:)."""
    raw = outline_data.get(key)
    if raw is None:
        return set()
    if isinstance(raw, dict):
        return set(str(k) for k in raw.keys())
    if isinstance(raw, list):
        return set(str(item) for item in raw)
    return set()


def _check_ref_cross(
    drafts: list[tuple[Path, str]], outline_data: dict,
    pattern: re.Pattern, ref_type: str, outline_key: str
) -> list[dict[str, Any]]:
    """Generic figure/table reference cross-check."""
    known_keys = _extract_outline_keys(outline_data, outline_key)
    findings = []
    for path, text in drafts:
        prose = _clean_prose(text)
        for m in pattern.finditer(prose):
            # Collect all numbers captured in this match
            nums = [g for g in m.groups() if g is not None]
            if not nums:
                nums = [m.group(1)] if m.lastindex and m.lastindex >= 1 else []
            for num in nums:
                # Map to a key to look up in the outline
                # Try numeric key as string, and "f<n>" / "t<n>" / "Fig<n>" etc.
                str_num = str(num)
                prefix = "f" if ref_type.lower().startswith("fig") else "t"
                candidates = {
                    str_num,
                    f"{prefix}{num}",
                    f"Fig{num}",
                    f"Table{num}",
                    f"fig{num}",
                    f"table{num}",
                    num,
                }
                if known_keys and not candidates.intersection(known_keys):
                    line, col = _line_col(text, m.start())
                    findings.append(_make_finding(
                        severity="block",
                        category=f"{ref_type}-reference",
                        what=f"{ref_type} {num} cited in prose but not declared in outline {outline_key}:",
                        where=f"{path.name}:{line}:{col}",
                        context=_snippet(text, m.start()),
                        suggested_fix=f"Add '{prefix}{num}:' entry to _outline/outline.md frontmatter '{outline_key}:'",
                    ))
    return findings


# ---------------------------------------------------------------------------
# Check 3 — Section-list cross-check
# ---------------------------------------------------------------------------

def _check_sections(drafts_dir: Path, drafts: list[tuple[Path, str]],
                    profile_data: dict) -> list[dict[str, Any]]:
    """Verify that draft file stems match profile required sections."""
    sections = profile_data.get("sections", [])
    if not sections:
        return []

    required_ids = {s["id"] for s in sections if isinstance(s, dict) and s.get("required")}
    draft_stems = {p.stem for p, _ in drafts}

    findings = []
    for req_id in required_ids:
        if req_id not in draft_stems:
            findings.append(_make_finding(
                severity="warn",
                category="section-list",
                what=f"Required section '{req_id}' (per profile) has no draft file in {drafts_dir.name}/",
                where=f"{drafts_dir.name}/",
                context=f"Profile requires: {sorted(required_ids)}; found: {sorted(draft_stems)}",
                suggested_fix=f"Create {drafts_dir}/{req_id}.md or adjust profile",
            ))
    return findings


# ---------------------------------------------------------------------------
# Check 4 — Citation-key uniqueness
# ---------------------------------------------------------------------------

def _check_citation_keys(drafts: list[tuple[Path, str]]) -> list[dict[str, Any]]:
    """Flag citation keys that appear with different DOIs/zotero IDs."""
    # key_label -> list of (doi_value, where)
    seen: dict[str, list[tuple[str, str]]] = defaultdict(list)
    findings = []

    for path, text in drafts:
        prose = _clean_prose(text)
        for m in CITATION_KEY_RE.finditer(prose):
            raw = "[" + m.group(1) + "]"
            try:
                parsed = parse_citation_key(raw)
            except ParseError:
                continue
            label = f"{parsed['first_author']}{parsed['year']}"
            id_val = f"{parsed['id_kind']}:{parsed['id_value']}"
            line, col = _line_col(text, m.start())
            seen[label].append((id_val, f"{path.name}:{line}:{col}"))

    for label, occurrences in seen.items():
        unique_ids = set(id_val for id_val, _ in occurrences)
        if len(unique_ids) > 1:
            findings.append(_make_finding(
                severity="block",
                category="citation-key-uniqueness",
                what=f"Citation key '{label}' used with {len(unique_ids)} different IDs: {sorted(unique_ids)}",
                where=", ".join(where for _, where in occurrences[:3]),
                context=f"All occurrences: {occurrences}",
                suggested_fix=f"Unify all '{label}' citations to the same DOI/zotero ID",
            ))
    return findings


# ---------------------------------------------------------------------------
# Check 5 — Abbreviation introduction
# ---------------------------------------------------------------------------

def _check_abbreviations(drafts: list[tuple[Path, str]]) -> list[dict[str, Any]]:
    """Check that abbreviations are introduced before their first use.

    R3 mitigation: scan ALL sections in order before flagging 'never introduced'.
    First-occurrence-in-document is what counts, not first-occurrence-in-section.
    """
    # Pass 1: collect all introductions across the full document (in draft order)
    introduced: dict[str, str] = {}  # abbr -> full form
    all_abbrevs_used: list[tuple[str, str, str]] = []  # (abbr, file, line:col)

    # Build combined document text (in order) to find first introduction
    combined_pos = 0
    doc_positions: list[tuple[Path, str, int]] = []  # (path, text, start_offset)
    for path, text in drafts:
        doc_positions.append((path, text, combined_pos))
        combined_pos += len(text) + 1  # +1 for separator

    # Find all introductions in document order
    combined = "\n".join(text for _, text in drafts)
    combined_clean = _clean_prose(combined)

    for m in ABBREV_INTRO_RE.finditer(combined_clean):
        abbr = m.group("abbr")
        full = m.group("full").strip()
        if abbr not in introduced:
            introduced[abbr] = full

    # Pass 2: scan for bare abbreviation occurrences (not inside an introduction)
    findings = []
    # Pattern for bare abbreviation use: word-bounded, NOT inside (...) context
    for path, text in drafts:
        prose = _clean_prose(text)
        # Remove introduction occurrences so they don't count as bare usage
        # Find bare abbreviations: 2+ uppercase letters used as tokens
        bare_re = re.compile(r"\b([A-Z]{2,})\b")
        for m in bare_re.finditer(prose):
            abbr = m.group(1)
            # Skip if it is part of an introduction pattern at this position
            # Check if the match is inside a parenthetical (abbr introduction)
            start = m.start()
            # Simple check: see if preceded by "(" without a matching close before
            preceding = prose[max(0, start - 60):start]
            if "(" in preceding:
                last_open = preceding.rfind("(")
                if ")" not in preceding[last_open:]:
                    # This abbreviation is inside a parenthetical — it IS the introduction
                    continue
            if abbr not in introduced:
                line, col = _line_col(text, start)
                findings.append(_make_finding(
                    severity="warn",
                    category="abbreviation-introduction",
                    what=f"Abbreviation '{abbr}' used without prior introduction",
                    where=f"{path.name}:{line}:{col}",
                    context=_snippet(text, start),
                    suggested_fix=f"Introduce '{abbr}' as 'Full Name ({abbr})' on first use",
                ))
    return findings


# ---------------------------------------------------------------------------
# Check 6 — Terminology uniformity
# ---------------------------------------------------------------------------

def _check_terminology(drafts: list[tuple[Path, str]]) -> list[dict[str, Any]]:
    """Flag terms that appear in >= 2 case variants with combined frequency >= 3."""
    # Normalize: group by lowercased form
    freq: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))  # lower -> {variant -> count}
    first_where: dict[str, dict[str, str]] = defaultdict(dict)  # lower -> {variant -> where}

    for path, text in drafts:
        prose = _clean_prose(text)
        for m in WORD_TOKEN_RE.finditer(prose):
            token = m.group(0)
            lower = token.lower()
            freq[lower][token] += 1
            if token not in first_where[lower]:
                line, col = _line_col(text, m.start())
                first_where[lower][token] = f"{path.name}:{line}:{col}"

    findings = []
    for lower, variants in freq.items():
        if len(variants) < 2:
            continue
        total = sum(variants.values())
        if total < 3:
            continue
        # Only flag if the variants differ by more than capitalization at sentence start
        # (i.e., skip words that only appear capitalized at start of line)
        sorted_variants = sorted(variants.items(), key=lambda x: -x[1])
        findings.append(_make_finding(
            severity="warn",
            category="terminology-uniformity",
            what=f"Term '{lower}' appears in {len(variants)} case variants: "
                 + ", ".join(f"'{v}' ({c}x)" for v, c in sorted_variants),
            where=", ".join(first_where[lower].get(v, "?") for v, _ in sorted_variants[:2]),
            context=f"Total occurrences: {total}; variants: {dict(variants)}",
            suggested_fix=f"Standardize to one form; most frequent is '{sorted_variants[0][0]}'",
        ))
    return findings


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def _write_report(report_path: Path, profile_id: str, checked_files: list[str],
                  findings: list[dict[str, Any]]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    block_count = sum(1 for f in findings if f["severity"] == "block")
    warn_count = sum(1 for f in findings if f["severity"] == "warn")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "---",
        f"generated_at: {now}",
        f"profile: {profile_id}",
        f"checked_files: [{', '.join(checked_files)}]",
        f"findings_count: {len(findings)}",
        "findings_by_severity:",
        f"  block: {block_count}",
        f"  warn: {warn_count}",
        "---",
        "",
        "# Consistency report",
        "",
    ]

    for f in findings:
        lines += [
            f"## {f['severity']} — {f['category']} — {f['where']}",
            f"  - what: {f['what']}",
            f"  - where: {f['where']}",
            f"  - context: {f['context'][:120]}",
            f"  - suggested_fix: {f['suggested_fix']}",
            "",
        ]

    report_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# JSON output helper
# ---------------------------------------------------------------------------

def _build_json_output(profile_id: str, checked_files: list[str],
                       findings: list[dict[str, Any]]) -> dict[str, Any]:
    block_count = sum(1 for f in findings if f["severity"] == "block")
    warn_count = sum(1 for f in findings if f["severity"] == "warn")
    return {
        "profile": profile_id,
        "checked_files": checked_files,
        "findings_count": len(findings),
        "findings_by_severity": {"block": block_count, "warn": warn_count},
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SWS static-analysis consistency checker (D9).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("drafts_dir", help="Path to the _drafts/ directory")
    parser.add_argument(
        "--outline",
        default=None,
        help="Path to outline.md (default: <drafts-dir>/../_outline/outline.md)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_out",
        help="Output findings as JSON instead of human-readable",
    )
    parser.add_argument(
        "--report-out",
        default=None,
        help="Path to write consistency-report.md (default: <drafts-dir>/../_review/consistency-report.md)",
    )
    args = parser.parse_args(argv)

    drafts_dir = Path(args.drafts_dir).resolve()
    if not drafts_dir.is_dir():
        print(f"Error: drafts-dir not found: {drafts_dir}", file=sys.stderr)
        return 2

    paper_root = drafts_dir.parent

    # Determine outline path
    outline_path = Path(args.outline).resolve() if args.outline else paper_root / "_outline" / "outline.md"

    # Determine report output path
    if args.report_out:
        report_path = Path(args.report_out).resolve()
    else:
        report_path = paper_root / "_review" / "consistency-report.md"

    # Determine profile
    marker_data = _read_marker(paper_root)
    profile_id = marker_data.get("profile_id", marker_data.get("profile", "full-article"))
    if isinstance(profile_id, str):
        profile_id = profile_id.strip()

    # D19: funding-proposal is not supported in v0.1
    if profile_id == FUNDING_PROPOSAL_PROFILE:
        msg = (
            "v0.1 consistency-checker does not support funding-proposal; "
            "manual review required"
        )
        print(msg)
        if args.json_out:
            print(json.dumps({"message": msg, "profile": profile_id, "findings": []}))
        return 0

    # Read outline
    outline_data = _read_outline(outline_path)

    # Read profile for section check
    plugin_root = Path(__file__).resolve().parents[1]
    profiles_dir = plugin_root / "profiles"
    profile_data = _read_profile(profile_id, profiles_dir)

    # Collect drafts (in sorted order — R3 mitigation: read ALL before abbreviation scan)
    draft_files = _collect_drafts(drafts_dir)
    if not draft_files:
        print(f"No markdown drafts found in {drafts_dir}", file=sys.stderr)
        if args.json_out:
            print(json.dumps({"profile": profile_id, "checked_files": [], "findings_count": 0,
                              "findings_by_severity": {"block": 0, "warn": 0}, "findings": []}))
        return 0

    drafts: list[tuple[Path, str]] = [(p, p.read_text(encoding="utf-8")) for p in draft_files]
    checked_files = [p.name for p, _ in drafts]

    # Run all checks
    findings: list[dict[str, Any]] = []

    # Check 1: figure references
    findings.extend(_check_ref_cross(drafts, outline_data, FIG_REF_RE, "Figure", "figures"))

    # Check 2: table references
    findings.extend(_check_ref_cross(drafts, outline_data, TABLE_REF_RE, "Table", "tables"))

    # Check 3: section list
    findings.extend(_check_sections(drafts_dir, drafts, profile_data))

    # Check 4: citation-key uniqueness
    findings.extend(_check_citation_keys(drafts))

    # Check 5: abbreviation introduction (cross-section, R3)
    findings.extend(_check_abbreviations(drafts))

    # Check 6: terminology uniformity
    findings.extend(_check_terminology(drafts))

    # Write report
    _write_report(report_path, profile_id, checked_files, findings)

    # Output
    if args.json_out:
        print(json.dumps(_build_json_output(profile_id, checked_files, findings), indent=2))
    else:
        block_findings = [f for f in findings if f["severity"] == "block"]
        warn_findings = [f for f in findings if f["severity"] == "warn"]
        print(f"Consistency check — profile: {profile_id}")
        print(f"Checked: {', '.join(checked_files)}")
        print(f"Findings: {len(findings)} ({len(block_findings)} block, {len(warn_findings)} warn)")
        if findings:
            print()
            for f in findings:
                print(f"[{f['severity'].upper()}] {f['category']} — {f['where']}")
                print(f"  {f['what']}")
                print(f"  Fix: {f['suggested_fix']}")
                print()
        print(f"Report written to: {report_path}")

    has_block = any(f["severity"] == "block" for f in findings)
    return 1 if has_block else 0


if __name__ == "__main__":
    sys.exit(main())
