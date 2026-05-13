"""Citation-key parsing for SWS drafted prose.

Format (cycle #7 D17):
    [<FirstAuthor><Year>; <prefix>:<id>]
where prefix in {"doi", "zotero"}.

Placeholder format:
    [CITATION_NEEDED: <free-text claim>]

Pure stdlib so it runs from any Python.
"""
from __future__ import annotations
import re
from typing import TypedDict


class ParseError(ValueError):
    pass


class CitationKey(TypedDict):
    first_author: str
    year: str
    id_kind: str
    id_value: str


_KEY_RE = re.compile(
    r"^\[(?P<author>[A-Za-z][A-Za-z\-]*)(?P<year>\d{4});\s*(?P<kind>doi|zotero):(?P<value>[^\]]+)\]$"
)

PLACEHOLDER_RE = re.compile(r"\[CITATION_NEEDED:\s*([^\]]+)\]")


def parse_citation_key(text: str) -> CitationKey:
    m = _KEY_RE.match(text.strip())
    if not m:
        raise ParseError(f"not a valid citation key: {text!r}")
    return {
        "first_author": m.group("author"),
        "year": m.group("year"),
        "id_kind": m.group("kind"),
        "id_value": m.group("value").strip(),
    }
