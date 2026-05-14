"""Re-apply SWS styles to an existing .docx — style-enforcer's restyle hammer.

Cycle #8 (D5 / D22 deferral from cycle #7): converts a Word-default-styled
.docx (Heading 1/2, Normal, etc.) to the SWS style canon defined in
references/docx-style.md. Preserves ALL direct character formatting (bold,
italic, underline) and highlight colours — only paragraph-style assignments
are rewritten.

CLI:
  sws_restyle_docx.py <input.docx>                     # restyle in place
  sws_restyle_docx.py <input.docx> --out <output.docx> # write to new path

Exit codes:
  0  ok
  2  input file not found
  3  python-docx error
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# SWS style definitions (mirrors references/docx-style.md)
# ---------------------------------------------------------------------------

_SWS_STYLES: dict[str, dict] = {
    "SWS-H1": {
        "font_name": "Arial",
        "font_size_pt": 12,
        "bold": True,
        "italic": False,
    },
    "SWS-H2": {
        "font_name": "Arial",
        "font_size_pt": 12,
        "bold": True,
        "italic": True,
    },
    "SWS-Body": {
        "font_name": "Arial",
        "font_size_pt": 12,
        "bold": False,
        "italic": False,
    },
    "SWS-Caption": {
        "font_name": "Arial",
        "font_size_pt": 10,
        "bold": False,
        "italic": False,
    },
    "SWS-References": {
        "font_name": "Arial",
        "font_size_pt": 10,
        "bold": False,
        "italic": False,
    },
}

# Mapping from Word built-in style names → target SWS style
_H1_NAMES = {"Heading 1", "Title"}
_H2_NAMES = {"Heading 2", "Heading 3", "Heading 4", "Subtitle"}
_BODY_NAMES = {"Normal", "Body Text", ""}

# Paragraph text prefixes that indicate captions (case-insensitive)
_CAPTION_RE = re.compile(r"^(Figure\s+\d+|Fig\.\s*\d+|Table\s+\d+)", re.IGNORECASE)

# Heading text that marks the start of a references section
_REFERENCES_HEADING_RE = re.compile(r"^\s*references?\s*$", re.IGNORECASE)


def _is_sws_style(name: str) -> bool:
    return name in _SWS_STYLES


def _ensure_sws_styles(doc) -> None:
    """Add SWS styles to the document if they are not already present (idempotent)."""
    from docx.shared import Pt
    from docx.enum.style import WD_STYLE_TYPE

    existing = {s.name for s in doc.styles}
    for style_name, props in _SWS_STYLES.items():
        if style_name in existing:
            continue
        style = doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
        font = style.font
        font.name = props["font_name"]
        font.size = Pt(props["font_size_pt"])
        font.bold = props["bold"]
        font.italic = props["italic"]


def _target_style(para, in_references: bool) -> str:
    """Return the SWS style name that should be applied to this paragraph."""
    if in_references:
        return "SWS-References"

    text = (para.text or "").strip()

    # Caption detection overrides style name
    if _CAPTION_RE.match(text):
        return "SWS-Caption"

    style_name = getattr(para.style, "name", "") or ""

    if style_name in _H1_NAMES:
        return "SWS-H1"
    if style_name in _H2_NAMES:
        return "SWS-H2"
    if style_name in _BODY_NAMES:
        return "SWS-Body"
    # Already an SWS style — keep it
    if _is_sws_style(style_name):
        return style_name
    # Unknown/custom style — fall back to SWS-Body
    return "SWS-Body"


def restyle(input_path: Path, output_path: Path) -> int:
    """Core restyle logic. Returns 0 on success, 2/3 on error."""
    if not input_path.is_file():
        print(f"sws_restyle_docx: file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        from docx import Document
        doc = Document(str(input_path))
    except Exception as exc:
        print(f"sws_restyle_docx: parse error: {exc}", file=sys.stderr)
        return 3

    try:
        _ensure_sws_styles(doc)

        in_references = False
        for para in doc.paragraphs:
            text = (para.text or "").strip()

            # Detect the References heading to flip the in_references flag
            style_name = getattr(para.style, "name", "") or ""
            is_heading = style_name in _H1_NAMES | _H2_NAMES | {
                s for s in _SWS_STYLES if "H" in s
            }
            if is_heading and _REFERENCES_HEADING_RE.match(text):
                in_references = True
                # The heading itself becomes SWS-H1
                para.style = doc.styles["SWS-H1"]
                continue

            target = _target_style(para, in_references)
            para.style = doc.styles[target]
            # NOTE: run-level formatting (bold, italic, underline, highlight)
            # is untouched — python-docx only stores direct character
            # formatting at the run/XML level, which we never clear here.

        doc.save(str(output_path))
        return 0

    except Exception as exc:
        print(f"sws_restyle_docx: error during restyle: {exc}", file=sys.stderr)
        return 3


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Re-apply SWS styles to an existing .docx.\n\n"
            "Converts Word-default styles (Heading 1/2, Normal, etc.) to the\n"
            "SWS style canon (SWS-H1, SWS-H2, SWS-Body, SWS-Caption,\n"
            "SWS-References). Direct character formatting (bold, italic,\n"
            "underline) and highlight colours are PRESERVED — only paragraph-\n"
            "style assignments are rewritten."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("input", help="Path to the input .docx file")
    ap.add_argument(
        "--out",
        metavar="OUTPUT",
        help="Write result to OUTPUT instead of modifying input in place",
    )
    args = ap.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.out) if args.out else input_path

    return restyle(input_path, output_path)


if __name__ == "__main__":
    sys.exit(main())
