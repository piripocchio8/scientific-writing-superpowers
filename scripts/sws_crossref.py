"""CrossRef DOI resolver + metadata for SWS bibliography-curator (D8).

WebFetch/curl + JSON parsing. Caching + 429 backoff (cycle-#9 R1 discipline).
Used by bibliography-curator as the primary DOI fallback chain (after Zotero).

Public API:
  resolve_doi(doi, cache_dir, max_retries) -> dict | None
  parse_work(message) -> dict
  format_reference(record, style) -> str

Exceptions:
  RateLimitError  — raised after max_retries exhausted on HTTP 429
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

BASE_URL = "https://api.crossref.org/works"
POLITE_MAILTO = ""  # set via CROSSREF_MAILTO env var for polite pool


class RateLimitError(Exception):
    pass


def parse_work(message: dict) -> dict:
    """Normalize a CrossRef work message to a flat dict."""
    authors = []
    for a in message.get("author") or []:
        given = a.get("given", "")
        family = a.get("family", "")
        name = f"{family} {given}".strip() if family else given
        if name:
            authors.append(name)

    date_parts = (message.get("published") or {}).get("date-parts") or [[None]]
    year = date_parts[0][0] if date_parts[0] else None

    titles = message.get("title") or []
    title = titles[0] if titles else ""

    container = message.get("container-title") or []
    journal = container[0] if container else ""

    return {
        "doi": message.get("DOI"),
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "volume": message.get("volume"),
        "issue": message.get("issue"),
        "pages": message.get("page"),
        "type": message.get("type"),
    }


def format_reference(record: dict, style: str = "numbered") -> str:
    """Format a parsed CrossRef record to a citation string.

    style: 'numbered' (Vancouver-like) or 'apa'.
    """
    authors = "; ".join(record.get("authors") or []) or "Unknown Author"
    year = record.get("year") or "n.d."
    title = record.get("title") or ""
    journal = record.get("journal") or ""
    volume = record.get("volume") or ""
    issue = record.get("issue") or ""
    pages = record.get("pages") or ""
    doi = record.get("doi") or ""

    if style == "apa":
        vol_issue = f"{volume}({issue})" if issue else volume
        page_part = f", {pages}" if pages else ""
        doi_part = f" https://doi.org/{doi}" if doi else ""
        return f"{authors} ({year}). {title}. {journal}, {vol_issue}{page_part}.{doi_part}"
    else:
        vol_part = f"{volume}" + (f"({issue})" if issue else "")
        page_part = f":{pages}" if pages else ""
        doi_part = f" DOI: {doi}" if doi else ""
        return f"{authors}. {title}. {journal}. {year};{vol_part}{page_part}.{doi_part}"


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _fetch_json(url: str, cache_dir: Path | None = None) -> Any:
    if cache_dir is not None:
        key = _cache_key(url)
        cached = cache_dir / f"{key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    import os
    mailto = os.environ.get("CROSSREF_MAILTO", POLITE_MAILTO)
    headers = {}
    if mailto:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}mailto={mailto}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimitError(f"HTTP 429 from {url}") from exc
        raise

    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(data), encoding="utf-8")

    return data


def _backoff_sleep(attempt: int) -> None:
    time.sleep(min(2 ** attempt, 64))


def resolve_doi(
    doi: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
) -> dict | None:
    """Resolve a DOI to bibliographic metadata via CrossRef."""
    import urllib.parse
    encoded = urllib.parse.quote(doi, safe="")
    url = f"{BASE_URL}/{encoded}"
    for attempt in range(max_retries):
        try:
            raw = _fetch_json(url, cache_dir=cache_dir)
            return parse_work(raw.get("message", {}))
        except RateLimitError:
            if attempt + 1 == max_retries:
                raise
            _backoff_sleep(attempt)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
    return None
