#!/usr/bin/env python3
"""Context-aware AI-tells linter for SWS markdown drafts.

Reads references/ai-writing-tells.md, extracts tells, and checks a markdown
file for AI-writing patterns with three context rules (D8 of cycle-#8 spec):
  1. PARAGRAPH-COUNT — tells with `linter_rule: { min_count_per_paragraph: N }`
     are only flagged when the pattern fires ≥N times in the same paragraph.
  2. CODE-FENCE SKIP — text inside ``` fences and inline `code` is excluded.
  3. CITATION-PLACEHOLDER SKIP — text inside [CITATION_NEEDED: ...] is excluded.

CLI:
    sws_lint_ai_tells.py <file.md> [--severity block|warn|all] [--json]

Exit codes:
    0 — no block-severity hits
    1 — one or more block-severity hits
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Tell parsing
# ---------------------------------------------------------------------------

def _parse_tells(ref_path: Path) -> list[dict]:
    """Parse tells from references/ai-writing-tells.md.

    Each tell is a markdown dash-led bullet with indented key: value lines.
    Returns list of dicts with keys: pattern, severity, why,
    linter_rule (optional dict).
    """
    text = ref_path.read_text(encoding="utf-8")

    tells = []
    # Split on bullet entries that start with "- pattern:"
    chunks = re.split(r'\n(?=- pattern:)', text)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("- pattern:"):
            continue
        tell: dict = {}

        # pattern — strip outer backticks
        m = re.match(r"- pattern:\s*`(.+?)`", chunk)
        if not m:
            continue
        tell["pattern"] = m.group(1)

        # severity
        m2 = re.search(r"^\s*severity:\s*(block|warn)", chunk, re.MULTILINE)
        if not m2:
            continue
        tell["severity"] = m2.group(1)

        # why
        m3 = re.search(r"^\s*why:\s*(.+)", chunk, re.MULTILINE)
        tell["why"] = m3.group(1).strip() if m3 else ""

        # linter_rule (optional): { min_count_per_paragraph: N }
        m4 = re.search(
            r"^\s*linter_rule:\s*\{\s*min_count_per_paragraph:\s*(\d+)\s*\}",
            chunk,
            re.MULTILINE,
        )
        if m4:
            tell["linter_rule"] = {"min_count_per_paragraph": int(m4.group(1))}

        tells.append(tell)

    return tells


# ---------------------------------------------------------------------------
# Text masking
# ---------------------------------------------------------------------------

def _mask_text(text: str) -> str:
    """Replace code fences, inline code, and citation placeholders with spaces.

    Masking preserves newlines so line numbers stay accurate.
    """
    def _blank(match: re.Match) -> str:
        s = match.group(0)
        # Keep newlines; blank everything else.
        return re.sub(r"[^\n]", " ", s)

    # Fenced code blocks (``` ... ```)
    text = re.sub(r"```[\s\S]*?```", _blank, text)
    # Inline code (`...`) — non-greedy, single line
    text = re.sub(r"`[^`\n]+`", _blank, text)
    # Citation placeholders: [CITATION_NEEDED: ...]
    text = re.sub(r"\[CITATION_NEEDED:[^\]]*\]", _blank, text)
    return text


# ---------------------------------------------------------------------------
# Paragraph splitting
# ---------------------------------------------------------------------------

def _split_paragraphs(text: str) -> list[tuple[int, str]]:
    """Return list of (start_line_1indexed, paragraph_text)."""
    paragraphs = []
    current_lines: list[str] = []
    start_line = 1
    current_start = 1

    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        stripped = line.rstrip("\n\r")
        if stripped == "":
            if current_lines:
                paragraphs.append((current_start, "".join(current_lines)))
                current_lines = []
                current_start = lineno + 1
            else:
                current_start = lineno + 1
        else:
            if not current_lines:
                current_start = lineno
            current_lines.append(line)

    if current_lines:
        paragraphs.append((current_start, "".join(current_lines)))

    return paragraphs


# ---------------------------------------------------------------------------
# Finding builder
# ---------------------------------------------------------------------------

def _make_finding(
    line: int,
    col: int,
    match_text: str,
    tell: dict,
    full_text_lines: list[str],
) -> dict:
    # Build ~80-char snippet centred on match
    raw_line = full_text_lines[line - 1] if 0 < line <= len(full_text_lines) else ""
    start = max(0, col - 20)
    snippet = raw_line[start : start + 80].rstrip()
    return {
        "line": line,
        "col": col + 1,  # 1-indexed column
        "snippet": snippet,
        "pattern_name": tell["pattern"][:60],
        "severity": tell["severity"],
        "why": tell["why"],
    }


# ---------------------------------------------------------------------------
# Core lint logic
# ---------------------------------------------------------------------------

def _lint(
    target_text: str,
    masked_text: str,
    tells: list[dict],
    severity_filter: str,
) -> list[dict]:
    """Run all tells against the masked text; return list of findings."""
    findings: list[dict] = []
    full_lines = target_text.splitlines()
    paragraphs = _split_paragraphs(masked_text)

    for tell in tells:
        sev = tell["severity"]
        if severity_filter == "block" and sev != "block":
            continue
        if severity_filter == "warn" and sev != "warn":
            continue

        flags = re.IGNORECASE if "(?i" not in tell["pattern"] else 0
        try:
            rx = re.compile(tell["pattern"], flags)
        except re.error:
            continue

        min_per_para = tell.get("linter_rule", {}).get("min_count_per_paragraph")

        if min_per_para is not None:
            # Paragraph-count rule: only flag if pattern fires ≥ min_per_para
            # times within one paragraph.
            for para_start_line, para_text in paragraphs:
                matches = list(rx.finditer(para_text))
                if len(matches) < min_per_para:
                    continue
                # Report each match (but only because threshold crossed)
                para_lines = para_text.splitlines(keepends=True)
                for m in matches:
                    # Compute line/col within paragraph text
                    before = para_text[: m.start()]
                    para_line_offset = before.count("\n")
                    abs_line = para_start_line + para_line_offset
                    col = m.start() - before.rfind("\n") - 1
                    findings.append(
                        _make_finding(abs_line, col, m.group(0), tell, full_lines)
                    )
        else:
            # Simple: flag every match anywhere in the masked text
            for m in rx.finditer(masked_text):
                before = masked_text[: m.start()]
                abs_line = before.count("\n") + 1
                col = m.start() - before.rfind("\n") - 1
                findings.append(
                    _make_finding(abs_line, col, m.group(0), tell, full_lines)
                )

    return findings


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _human_output(findings: list[dict]) -> str:
    if not findings:
        return "sws-lint: no AI-tells found.\n"
    lines = ["sws-lint AI-tells report", "=" * 40]
    for f in findings:
        lines.append(
            f"  [{f['severity'].upper()}] line {f['line']} col {f['col']}"
        )
        lines.append(f"    pattern : {f['pattern_name']}")
        lines.append(f"    snippet : {f['snippet']!r}")
        lines.append(f"    why     : {f['why']}")
        lines.append("")
    lines.append(f"Total findings: {len(findings)}")
    block_count = sum(1 for f in findings if f["severity"] == "block")
    warn_count = sum(1 for f in findings if f["severity"] == "warn")
    lines.append(f"  block: {block_count}  warn: {warn_count}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Context-aware AI-tells linter for SWS markdown files."
    )
    ap.add_argument("file", type=Path, help="Markdown file to lint")
    ap.add_argument(
        "--severity",
        choices=["block", "warn", "all"],
        default="all",
        help="Filter findings by severity (default: all)",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit findings as JSON list instead of human-readable text",
    )
    args = ap.parse_args(argv)

    if not args.file.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    plugin_root = Path(__file__).resolve().parent.parent
    ref_path = plugin_root / "references" / "ai-writing-tells.md"
    if not ref_path.exists():
        print(f"error: reference not found: {ref_path}", file=sys.stderr)
        return 3

    tells = _parse_tells(ref_path)
    target_text = args.file.read_text(encoding="utf-8")
    masked_text = _mask_text(target_text)

    findings = _lint(target_text, masked_text, tells, args.severity)

    if args.json_output:
        print(json.dumps(findings, indent=2))
    else:
        print(_human_output(findings), end="")

    block_hits = any(f["severity"] == "block" for f in findings)
    return 1 if block_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
