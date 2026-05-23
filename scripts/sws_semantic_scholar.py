"""Semantic Scholar API client for SWS (D8).

WebFetch/curl + JSON parsing. Caching + 429 backoff (cycle-#9 R1 discipline).
Title-fuzzy-match uses difflib SequenceMatcher (stdlib); threshold >= 0.70.
No live network calls in tests — all tests use captured fixture JSON.

Public API:
  search(query, cache_dir, max_retries) -> list[dict]
  resolve_doi(doi, cache_dir, max_retries) -> dict | None
  parse_search_results(raw) -> list[dict]
  parse_paper_detail(raw) -> dict
  title_similarity(a, b) -> float
  filter_by_title_similarity(items, query, threshold) -> list[dict]

Exceptions:
  RateLimitError  — raised after max_retries exhausted on HTTP 429
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import urllib.error
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,authors,year,externalIds,abstract,citationCount,references"


class RateLimitError(Exception):
    pass


def title_similarity(a: str, b: str) -> float:
    """Return SequenceMatcher ratio between two title strings (case-insensitive)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def filter_by_title_similarity(
    items: list[dict], query: str, threshold: float = 0.70
) -> list[dict]:
    """Return items whose title similarity to query is >= threshold, sorted descending."""
    scored = []
    for item in items:
        t = item.get("title") or ""
        score = title_similarity(query, t)
        if score >= threshold:
            scored.append((score, item))
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored]


def parse_search_results(raw: dict) -> list[dict]:
    """Normalize a Semantic Scholar search response to a flat list of dicts."""
    results = []
    for item in raw.get("data", []):
        results.append({
            "paper_id": item.get("paperId"),
            "title": item.get("title"),
            "authors": [a.get("name") for a in (item.get("authors") or [])],
            "year": item.get("year"),
            "doi": (item.get("externalIds") or {}).get("DOI"),
            "abstract": item.get("abstract") or "",
            "citation_count": item.get("citationCount", 0),
        })
    return results


def parse_paper_detail(raw: dict) -> dict:
    """Normalize a Semantic Scholar paper-detail response."""
    return {
        "paper_id": raw.get("paperId"),
        "title": raw.get("title"),
        "authors": [a.get("name") for a in (raw.get("authors") or [])],
        "year": raw.get("year"),
        "doi": (raw.get("externalIds") or {}).get("DOI"),
        "abstract": raw.get("abstract") or "",
        "citation_count": raw.get("citationCount", 0),
        "references": [
            {"paper_id": r.get("paperId"), "title": r.get("title"), "year": r.get("year")}
            for r in (raw.get("references") or [])
        ],
    }


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _fetch_json(
    url: str,
    headers: dict | None = None,
    cache_dir: Path | None = None,
) -> Any:
    """Make a live network request and return parsed JSON.

    Cache read/write is handled by _fetch_with_backoff so that the cache layer
    remains testable independently of the network layer (tests monkeypatch
    _fetch_json to avoid any live calls while still exercising cache logic).
    """
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimitError(f"HTTP 429 from {url}") from exc
        raise
    return data


def _backoff_sleep(attempt: int) -> None:
    delay = min(2 ** attempt, 64)
    time.sleep(delay)


def _fetch_with_backoff(
    url: str,
    headers: dict | None = None,
    cache_dir: Path | None = None,
    max_retries: int = 5,
) -> Any:
    """Fetch with cache + exponential backoff on 429.

    Cache is checked and written here so tests can monkeypatch _fetch_json
    (network only) while still exercising the cache-hit path.
    """
    if cache_dir is not None:
        key = _cache_key(url)
        cached = cache_dir / f"{key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    for attempt in range(max_retries):
        try:
            data = _fetch_json(url, headers=headers, cache_dir=None)
            if cache_dir is not None:
                cache_dir.mkdir(parents=True, exist_ok=True)
                cached.write_text(json.dumps(data), encoding="utf-8")
            return data
        except RateLimitError:
            if attempt + 1 == max_retries:
                raise
            _backoff_sleep(attempt)
    raise RateLimitError("max retries exhausted")


def search(
    query: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
    api_key: str | None = None,
) -> list[dict]:
    """Search Semantic Scholar by title/keyword query."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"{BASE_URL}/paper/search?query={encoded}&fields={FIELDS}&limit=10"
    headers = {"x-api-key": api_key} if api_key else {}
    raw = _fetch_with_backoff(url, headers=headers, cache_dir=cache_dir, max_retries=max_retries)
    return parse_search_results(raw)


def resolve_doi(
    doi: str,
    cache_dir: Path | None = None,
    max_retries: int = 5,
    api_key: str | None = None,
) -> dict | None:
    """Fetch a Semantic Scholar paper record by DOI."""
    import urllib.parse
    encoded = urllib.parse.quote(f"DOI:{doi}")
    url = f"{BASE_URL}/paper/{encoded}?fields={FIELDS}"
    headers = {"x-api-key": api_key} if api_key else {}
    try:
        raw = _fetch_with_backoff(url, headers=headers, cache_dir=cache_dir, max_retries=max_retries)
    except Exception:
        return None
    return parse_paper_detail(raw)
