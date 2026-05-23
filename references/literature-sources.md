---
sws_artifact: literature-sources
artifact_version: 0.1
locked: 2026-05-22
used_by: [agents/literature-searcher.md, agents/bibliography-curator.md, agents/claim-verifier.md]
---

# Literature sources — fallback chain + policy (v0.1)

This document specifies which source each agent calls, in which order, and the rate-limit / caching policy for each. MCP-aversion is honored throughout: only PubMed retains an MCP path (no first-class CLI exists for it); all others use WebFetch/curl + parsing scripts.

## Source registry

| ID | Script / MCP | Primary use | Free tier limit |
|----|--------------|-------------|-----------------|
| Zotero | `zotero` skill (existing) | All agents — first in chain | Local library, no rate limit |
| PubMed | `claude_ai_PubMed` MCP | Biomedical search + PMID resolve | 3 req/s (NCBI E-utilities) |
| Semantic Scholar | `scripts/sws_semantic_scholar.py` | Discovery + citation graph | 100 req/5 min unauthenticated |
| CrossRef | `scripts/sws_crossref.py` | DOI resolution + metadata | ~50 req/s polite pool |
| OpenAlex | `scripts/sws_openalex.py` | Broad metadata + OA full-text | 10 req/s polite pool |
| NLM | DEFERRED (D9) | Grounded RAG — cycle #13 | n/a |

## Per-agent fallback chains

### literature-searcher (DISCOVERY — Plan phase)

1. **Zotero** (local library via `zotero` skill) — search by keyword + topic. Most lookups stay local.
2. **PubMed** (MCP) — biomedical topics, PMID → abstract.
3. **Semantic Scholar** (`sws_semantic_scholar.py`) — title-fuzzy match, citation-graph expansion, abstract fetch.
4. **OpenAlex** (`sws_openalex.py`) — when Semantic Scholar returns no result or rate-limits.
5. **NLM grounded-RAG** — DEFERRED (D9). Agent degrades gracefully; never fails on absence.

Output: `refs/_lit-search/<slug>.md` — ranked candidates (title / authors / year / DOI / abstract + why-relevant).

### bibliography-curator (AUDIT — Submit phase)

1. **Zotero** (local library via `zotero` skill) — resolve citation key → bibliographic record.
2. **CrossRef** (`sws_crossref.py`) — DOI → authoritative metadata; used for format validation.
3. **OpenAlex** (`sws_openalex.py`) — fallback when CrossRef has no record (e.g., non-DOI items).
4. **NLM grounded-RAG** — DEFERRED (D9). Agent degrades gracefully.

Output: `_review/bibliography-audit/report.md` + `_review/bibliography-audit/fixes.json`.

### claim-verifier (reference, cycle #9)

Uses Zotero → Semantic Scholar → PubMed. Documented in cycle-#9 spec. Repeated here for completeness only.

## Caching policy (all WebFetch/curl scripts)

Each script maintains a per-paper cache at `$PAPER_ROOT/.sws_cache/<source_id>/`. Cache entries are keyed by the normalized query (DOI, title hash, or search string SHA-256). TTL: 7 days for metadata; 30 days for full-text snippets. The cache directory is gitignored.

## 429 backoff (all WebFetch/curl scripts)

On HTTP 429, each script waits `min(2^n * 1s, 64s)` where `n` is the retry attempt index, up to 5 retries. After 5 failures the script exits non-zero with a human-readable message naming the source and the recommended action (reduce request frequency or add an API key via env var).

## Authentication opt-in

Set `SEMANTIC_SCHOLAR_API_KEY` in the paper-root `.env` (gitignored) to raise the Semantic Scholar rate limit to 1 req/s (official key) or higher (institutional). The scripts read this env var if present and add the `x-api-key` header. Not required in v0.1.
