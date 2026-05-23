"""OpenAlex metadata client for SWS (D8).

Fallback for bibliography-curator and literature-searcher when Zotero/CrossRef
have no record. Broad coverage including OA full-text links. Abstract is
reconstructed from OpenAlex's inverted index representation.

Public API:
  resolve_doi(doi, cache_dir, max_retries) -> dict | None
  search(query, cache_dir, max_retries) -> list[dict]
  parse_work(raw) -> dict

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

BASE_URL = "https://api.openalex.org"


class RateLimitError(Exception):
    pass


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """Reconstruct abstract text from OpenAlex inverted index."""
    if not inverted_index:
        return ""
    max_pos = max(pos for positions in inverted_index.values() for pos in positions)
    tokens = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            tokens[pos] = word
    return " ".join(t for t in tokens if t)


def parse_work(raw: dict) -> dict:
    """Normalize an OpenAlex work object to a flat dict."""
    doi_raw = raw.get("doi") or ""
    doi = doi_raw.replace("https://doi.org/", "").replace("http://doi.org/", "") or None

    authors = []
    for a in raw.get("authorships") or []:
        name = (a.get("author") or {}).get("display_name") or ""
        if name:
            authors.append(name)

    primary = raw.get("primary_location") or {}
    source = primary.get("source") or {}
    journal = source.get("display_name") or ""
    is_oa = primary.get("is_oa") or False
    pdf_url = primary.get("pdf_url")

    abstract = _reconstruct_abstract(raw.get("abstract_inverted_index"))

    return {
        "openalex_id": raw.get("id"),
        "doi": doi,
        "title": raw.get("title") or "",
        "authors": authors,
        "year": raw.get("publication_year"),
        "journal": journal,
        "is_oa": is_oa,
        "pdf_url": pdf_url,
        "citation_count": raw.get("cited_by_count", 0),
        "abstract": abstract or None,
    }


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _fetch_json(url: str, cache_dir: Path | None = None) -> Any:
    if cache_dir is not None:
        key = _cache_key(url)
        cached = cache_dir / f"{key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    import os
    mailto = os.environ.get("OPENALEX_MAILTO", "")
    if mailto and "?" in url:
        url = f"{url}&mailto={mailto}"
    elif mailto:
        url = f"{url}?mailto={mailto}"

    req = urllib.request.Request(url)
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
    """Resolve a DOI to OpenAlex metadata."""
    import urllib.parse
    encoded = urllib.parse.quote(f"https://doi.org/{doi}", safe="")
    url = f"{BASE_URL}/works/{encoded}"
    for attempt in range(max_retries):
        try:
            raw = _fetch_json(url, cache_dir=cache_dir)
            return parse_work(raw)
        except RateLimitError:
            if attempt + 1 == max_retries:
                raise
            _backoff_sleep(attempt)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
    return None


def search(
    query: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
) -> list[dict]:
    """Search OpenAlex by free-text query."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"{BASE_URL}/works?search={encoded}&per-page=10"
    for attempt in range(max_retries):
        try:
            raw = _fetch_json(url, cache_dir=cache_dir)
            return [parse_work(w) for w in (raw.get("results") or [])]
        except RateLimitError:
            if attempt + 1 == max_retries:
                raise
            _backoff_sleep(attempt)
    return []
