#!/usr/bin/env python3
"""SWS init-project orchestration utility.

Functions exposed (built incrementally across cycle-#2 tasks 6-10):
    slugify(name)                  — normalize first_author family name
    validate_inputs(inputs)        — Q5b conditional rules (target_journal/call)
    scan_conflicts(root)           — 6-class smart-merge detection scan
    build_plan(inputs, resolutions)— assemble ordered op list
    apply_plan(plan)               — atomic apply with rollback

CLI subcommands wrap these for skill invocation:
    python sws_init_project.py scan --root <dir>
    python sws_init_project.py plan --inputs <vars.json> --resolutions <res.json>
    python sws_init_project.py apply --plan <plan.json>
"""
from __future__ import annotations
import unicodedata


def slugify(name: str) -> str:
    """Normalize first_author family name: NFD-decompose → drop non-ASCII →
    lowercase → strip apostrophes/hyphens.

    Examples:
        Smith → smith
        Müller → muller
        O'Brien → obrien
        Smith-Jones → smithjones

    Raises ValueError on empty/whitespace input.
    """
    s = name.strip()
    if not s:
        raise ValueError("first_author cannot be empty")

    # Step 1: NFD decompose to separate base from combining marks
    decomposed = unicodedata.normalize("NFD", s)

    # Step 2: Remove combining characters (diacritics)
    no_combining = "".join(c for c in decomposed if not unicodedata.combining(c))

    # Step 3: Map precomposed non-ASCII chars that don't decompose to ASCII equivalents
    # (e.g., ø → o, æ → ae)
    mapping = {
        'ø': 'o', 'Ø': 'o',
        'ð': 'd', 'Ð': 'd',
        'þ': 'th', 'Þ': 'th',
        'ß': 'ss',
        'æ': 'ae', 'Æ': 'ae',
        'œ': 'oe', 'Œ': 'oe',
    }

    result = ""
    for c in no_combining:
        if ord(c) > 127:  # Non-ASCII
            result += mapping.get(c, '')
        else:
            result += c

    # Step 4: Keep only alphanumeric (strips apostrophes, hyphens, spaces, etc.)
    cleaned = "".join(c for c in result if c.isalnum())
    return cleaned.lower()


ARTICLE_TYPES = (
    "full-article", "communication", "perspective", "review-paper",
    "mini-review", "editorial", "methodological-paper",
    "commentary-reply", "funding-proposal",
)
LANGUAGES = ("en", "it")
FORMATS = ("docx", "latex")


def validate_inputs(inputs: dict) -> tuple[bool, str]:
    """Enforce Q5b conditional rules + enum validation.

    Returns (True, "ok") if inputs pass; (False, error_msg) otherwise.
    """
    article_type = inputs.get("article_type")
    if article_type not in ARTICLE_TYPES:
        return False, (
            f"article_type must be one of {ARTICLE_TYPES}; got {article_type!r}"
        )

    language = inputs.get("language")
    if language not in LANGUAGES:
        return False, f"language must be one of {LANGUAGES}; got {language!r}"

    fmt = inputs.get("format")
    if fmt not in FORMATS:
        return False, f"format must be one of {FORMATS}; got {fmt!r}"

    co_authors = inputs.get("co_authors_present")
    if not isinstance(co_authors, bool):
        return False, (
            f"co_authors_present must be bool; got {type(co_authors).__name__}"
        )

    target_journal = inputs.get("target_journal")
    target_call = inputs.get("target_call")

    if article_type == "funding-proposal":
        if not target_call:
            return False, (
                "article_type=funding-proposal requires target_call"
            )
        if target_journal:
            return False, (
                "article_type=funding-proposal must have target_journal=null; "
                f"got {target_journal!r}"
            )
    else:
        if not target_journal:
            return False, (
                f"article_type={article_type} requires target_journal"
            )
        if target_call:
            return False, (
                f"article_type={article_type} must have target_call=null; "
                f"got {target_call!r}"
            )

    return True, "ok"
