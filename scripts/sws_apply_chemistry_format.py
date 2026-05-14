"""Apply chemistry-formatting patterns to an existing .docx — SWS style-enforcer helper.

Cycle #8 D11.  Reads the chemistry-formatting catalog from
references/chemistry-formatting.md (YAML frontmatter), then walks every
paragraph of the input .docx and applies run-level formatting (italic,
subscript, superscript, bold) per each pattern's ``apply`` and ``severity``
fields.

CLI:
  sws_apply_chemistry_format.py <input.docx>
  sws_apply_chemistry_format.py <input.docx> --out <output.docx>
  sws_apply_chemistry_format.py <input.docx> --dry-run
  sws_apply_chemistry_format.py <input.docx> --severity auto   # default: only auto
  sws_apply_chemistry_format.py <input.docx> --severity all    # also apply suggest

Exit codes:
  0  ok (also for format=latex no-op and --dry-run)
  2  input file not found
  3  python-docx / XML error
"""
from __future__ import annotations

import argparse
import copy
import os
import re
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent.parent
_CHEM_REF = _REPO / "references" / "chemistry-formatting.md"

# Namespace used by OOXML; python-docx uses lxml under the hood.
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# ---------------------------------------------------------------------------
# Catalog loader
# ---------------------------------------------------------------------------

def _load_catalog() -> dict[str, list[dict[str, Any]]]:
    """Parse YAML frontmatter of references/chemistry-formatting.md.

    Returns the ``categories`` dict mapping category name → list of pattern
    dicts, each with keys: id, pattern, apply, severity, etc.
    """
    try:
        import yaml
    except ImportError as exc:
        print(f"sws_apply_chemistry_format: PyYAML is required: {exc}", file=sys.stderr)
        sys.exit(3)

    text = _CHEM_REF.read_text(encoding="utf-8")
    parts = text.split("---")
    if len(parts) < 3:
        print("sws_apply_chemistry_format: chemistry-formatting.md has no YAML frontmatter",
              file=sys.stderr)
        sys.exit(3)
    try:
        meta = yaml.safe_load(parts[1])
    except Exception as exc:
        print(f"sws_apply_chemistry_format: YAML parse error: {exc}", file=sys.stderr)
        sys.exit(3)

    categories = meta.get("categories")
    if not categories:
        print("sws_apply_chemistry_format: 'categories' key missing in chemistry-formatting.md",
              file=sys.stderr)
        sys.exit(3)
    return categories


# ---------------------------------------------------------------------------
# Marker / format detection
# ---------------------------------------------------------------------------

def _is_latex_project(input_path: Path) -> bool:
    """Return True if the project marker says format: latex (D7)."""
    # Allow tests to inject a marker path via environment variable.
    env_marker = os.environ.get("SWS_MARKER")
    if env_marker:
        marker_path = Path(env_marker)
    else:
        marker_path = input_path.parent / ".sws-project.local.md"

    if not marker_path.is_file():
        return False

    text = marker_path.read_text(encoding="utf-8")
    # Simple scan: look for "format: latex" in marker text or YAML frontmatter.
    return bool(re.search(r"^\s*format\s*:\s*latex\s*$", text, re.MULTILINE | re.IGNORECASE))


# ---------------------------------------------------------------------------
# lxml / XML helpers
# ---------------------------------------------------------------------------

def _w(tag: str):
    """Return Clark-notation tag for the w: namespace."""
    return f"{{{_W_NS}}}{tag}"


def _get_or_add_rPr(r_elem):
    """Return the w:rPr child of a w:r element, creating it if absent."""
    rPr = r_elem.find(_w("rPr"))
    if rPr is None:
        from lxml import etree
        rPr = etree.SubElement(r_elem, _w("rPr"))
        r_elem.insert(0, rPr)  # rPr must be first child of w:r
    return rPr


def _set_vert_align(r_elem, value: str) -> None:
    """Set w:vertAlign w:val on a w:r element (subscript or superscript)."""
    from lxml import etree
    rPr = _get_or_add_rPr(r_elem)
    # Remove any existing vertAlign.
    for va in rPr.findall(_w("vertAlign")):
        rPr.remove(va)
    va_elem = etree.SubElement(rPr, _w("vertAlign"))
    va_elem.set(_w("val"), value)


def _set_bold(r_elem) -> None:
    """Set w:b on a w:r element."""
    from lxml import etree
    rPr = _get_or_add_rPr(r_elem)
    if rPr.find(_w("b")) is None:
        etree.SubElement(rPr, _w("b"))


def _set_italic(r_elem) -> None:
    """Set w:i on a w:r element."""
    from lxml import etree
    rPr = _get_or_add_rPr(r_elem)
    if rPr.find(_w("i")) is None:
        etree.SubElement(rPr, _w("i"))


def _has_vert_align(r_elem, value: str) -> bool:
    """Return True if this run already has w:vertAlign set to *value*."""
    rPr = r_elem.find(_w("rPr"))
    if rPr is None:
        return False
    va = rPr.find(_w("vertAlign"))
    if va is None:
        return False
    return va.get(_w("val")) == value


def _has_bold(r_elem) -> bool:
    rPr = r_elem.find(_w("rPr"))
    return rPr is not None and rPr.find(_w("b")) is not None


def _has_italic(r_elem) -> bool:
    rPr = r_elem.find(_w("rPr"))
    return rPr is not None and rPr.find(_w("i")) is not None


# ---------------------------------------------------------------------------
# Run-splitting
# ---------------------------------------------------------------------------

def _get_run_text(r_elem) -> str:
    """Concatenate all w:t children text from a w:r element."""
    parts = []
    for t in r_elem.findall(_w("t")):
        parts.append(t.text or "")
    return "".join(parts)


def _make_run_with_text(text: str, rPr_source=None):
    """Create a new w:r element with the given text, copying rPr from source."""
    from lxml import etree
    r = etree.Element(_w("r"))
    if rPr_source is not None:
        rPr = rPr_source.find(_w("rPr"))
        if rPr is not None:
            r.insert(0, copy.deepcopy(rPr))
    t = etree.SubElement(r, _w("t"))
    t.text = text
    # Preserve whitespace on the w:t element when text starts/ends with spaces.
    if text and (text[0] == " " or text[-1] == " "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r


def _split_run(p_elem, r_elem, start: int, end: int):
    """Split *r_elem* at [start:end], returning the middle w:r element.

    Produces up to three runs in the paragraph:
      - before: text[:start]  (may be empty → not inserted)
      - matched: text[start:end]
      - after: text[end:]     (may be empty → not inserted)

    The original *r_elem* is replaced in-place. Returns the new middle run.
    """
    text = _get_run_text(r_elem)
    parent = r_elem.getparent()
    idx = list(parent).index(r_elem)

    before_text = text[:start]
    match_text = text[start:end]
    after_text = text[end:]

    # Build the three candidate runs.
    runs_to_insert = []
    if before_text:
        runs_to_insert.append(_make_run_with_text(before_text, r_elem))
    middle_run = _make_run_with_text(match_text, r_elem)
    runs_to_insert.append(middle_run)
    if after_text:
        runs_to_insert.append(_make_run_with_text(after_text, r_elem))

    # Replace the original run.
    parent.remove(r_elem)
    for i, r in enumerate(runs_to_insert):
        parent.insert(idx + i, r)

    return middle_run


# ---------------------------------------------------------------------------
# Paragraph-level formatting
# ---------------------------------------------------------------------------

def _collect_runs(p_elem) -> list:
    """Return all w:r children of a w:p (direct children only, not nested)."""
    return p_elem.findall(_w("r"))


def _apply_format_to_run(r_elem, apply: str) -> None:
    """Apply the formatting named by *apply* to a single run element."""
    if apply == "italic":
        _set_italic(r_elem)
    elif apply == "bold":
        _set_bold(r_elem)
    elif apply == "subscript":
        _set_vert_align(r_elem, "subscript")
    elif apply == "superscript":
        _set_vert_align(r_elem, "superscript")


def _run_already_has(r_elem, apply: str) -> bool:
    """Return True if the run already has the requested formatting."""
    if apply == "italic":
        return _has_italic(r_elem)
    if apply == "bold":
        return _has_bold(r_elem)
    if apply == "subscript":
        return _has_vert_align(r_elem, "subscript")
    if apply == "superscript":
        return _has_vert_align(r_elem, "superscript")
    return False


def _apply_pattern_to_paragraph(p_elem, regex: re.Pattern, apply: str) -> int:
    """Apply a single compiled pattern to a paragraph element.

    Returns the number of runs modified (new formatting applied).
    """
    modified = 0

    # Collect runs and re-collect after each split (since we mutate the tree).
    runs = _collect_runs(p_elem)
    run_idx = 0
    while run_idx < len(runs):
        r = runs[run_idx]
        text = _get_run_text(r)
        m = regex.search(text)
        if m is None:
            run_idx += 1
            continue

        # Which group carries the actual span to format?
        # For patterns with groups, the relevant span is the full match.
        start, end = m.start(), m.end()

        # If the whole run matches and already has the formatting, skip.
        if start == 0 and end == len(text) and _run_already_has(r, apply):
            run_idx += 1
            continue

        # Split the run into before/match/after.
        middle = _split_run(p_elem, r, start, end)
        # Re-collect after mutation.
        runs = _collect_runs(p_elem)
        # Find the index of middle in the new run list.
        try:
            run_idx = runs.index(middle)
        except ValueError:
            run_idx += 1
            continue

        if not _run_already_has(middle, apply):
            _apply_format_to_run(middle, apply)
            modified += 1

        # Advance past the middle run so we don't re-process it.
        run_idx += 1

    return modified


# ---------------------------------------------------------------------------
# Suggestion reporting
# ---------------------------------------------------------------------------

def _collect_suggestions(p_elem, regex: re.Pattern, pattern_id: str, para_text: str) -> list[str]:
    """Return suggestion strings for suggest-severity matches in a paragraph."""
    suggestions = []
    for m in regex.finditer(para_text):
        snippet = para_text[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")
        suggestions.append(f"  [suggest:{pattern_id}] ...{snippet}...")
    return suggestions


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------

def apply_chemistry_format(
    input_path: Path,
    output_path: Path,
    dry_run: bool,
    severity: str,
) -> int:
    """Core logic. Returns exit code (0/2/3)."""
    if not input_path.is_file():
        print(f"sws_apply_chemistry_format: file not found: {input_path}", file=sys.stderr)
        return 2

    # Load catalog.
    try:
        categories = _load_catalog()
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 3

    # Marker check: no-op for format=latex (D7).
    if _is_latex_project(input_path):
        print("skipped (format=latex)")
        return 0

    # Open the docx.
    try:
        from docx import Document
        doc = Document(str(input_path))
    except Exception as exc:
        print(f"sws_apply_chemistry_format: parse error: {exc}", file=sys.stderr)
        return 3

    try:
        # Compile patterns and bucket by severity.
        compiled: list[tuple[str, str, re.Pattern, str, str]] = []
        # (category, pattern_id, regex, apply, severity_str)
        for cat_name, patterns in categories.items():
            for pat in patterns:
                try:
                    rgx = re.compile(pat["pattern"])
                except re.error as exc:
                    print(
                        f"sws_apply_chemistry_format: bad regex '{pat['pattern']}': {exc}",
                        file=sys.stderr,
                    )
                    return 3
                compiled.append((cat_name, pat["id"], rgx, pat["apply"], pat["severity"]))

        # Stats.
        applied_by_cat: dict[str, int] = {}
        suggestions: list[str] = []
        total_modified = 0

        for para in doc.paragraphs:
            p_elem = para._element
            para_text = para.text  # used for suggestion scanning only

            for cat_name, pat_id, rgx, apply, sev in compiled:
                if sev == "auto":
                    if not dry_run:
                        n = _apply_pattern_to_paragraph(p_elem, rgx, apply)
                        applied_by_cat[cat_name] = applied_by_cat.get(cat_name, 0) + n
                        total_modified += n
                    else:
                        # Dry-run: count matches without writing.
                        for m in rgx.finditer(para_text):
                            applied_by_cat[cat_name] = applied_by_cat.get(cat_name, 0) + 1
                            total_modified += 1

                elif sev == "suggest":
                    if severity == "all" and not dry_run:
                        n = _apply_pattern_to_paragraph(p_elem, rgx, apply)
                        applied_by_cat[cat_name] = applied_by_cat.get(cat_name, 0) + n
                        total_modified += n
                    else:
                        # Report only.
                        new_sug = _collect_suggestions(p_elem, rgx, pat_id, para_text)
                        suggestions.extend(new_sug)

        # Write output (unless dry-run).
        if not dry_run:
            doc.save(str(output_path))

        # Print summary.
        mode = "dry-run" if dry_run else "applied"
        print(f"sws_apply_chemistry_format: {mode} — {total_modified} runs modified")
        for cat, n in sorted(applied_by_cat.items()):
            if n:
                print(f"  {cat}: {n}")
        if suggestions:
            print(f"  suggestions ({len(suggestions)}) — rerun with --severity all to apply:")
            for s in suggestions[:20]:   # cap output at 20 lines
                print(s)
            if len(suggestions) > 20:
                print(f"  ... and {len(suggestions) - 20} more")

        return 0

    except Exception as exc:
        print(f"sws_apply_chemistry_format: error: {exc}", file=sys.stderr)
        return 3


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Apply chemistry-formatting patterns from references/chemistry-formatting.md\n"
            "to a .docx file (italic species names, sub/superscripts, bold figure labels).\n\n"
            "Reads the SWS chemistry catalog at start-up; no-op when format=latex in\n"
            "the project marker (.sws-project.local.md or SWS_MARKER env var)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("input", help="Path to the input .docx file")
    ap.add_argument(
        "--out",
        metavar="OUTPUT",
        help="Write result to OUTPUT instead of modifying input in place",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be changed without writing any file",
    )
    ap.add_argument(
        "--severity",
        choices=["auto", "all"],
        default="auto",
        help=(
            "auto (default): apply only severity=auto patterns. "
            "all: also apply severity=suggest patterns."
        ),
    )
    args = ap.parse_args(argv)

    input_path = Path(args.input)
    if args.out:
        output_path = Path(args.out)
    else:
        output_path = input_path

    return apply_chemistry_format(
        input_path=input_path,
        output_path=output_path,
        dry_run=args.dry_run,
        severity=args.severity,
    )


if __name__ == "__main__":
    sys.exit(main())
