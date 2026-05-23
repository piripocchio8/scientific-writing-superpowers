---
name: search-literature
description: |
  Discover new relevant sources for a topic or section. Zotero-first fallback chain
  (Zotero -> PubMed -> Semantic Scholar -> OpenAlex). Writes refs/_lit-search/<slug>.md.
  DISCOVERY only — does not audit existing citations (that is /sws:audit-bibliography).
  NLM deferred (D9). Dispatches the literature-searcher agent.
allowed-tools: Bash, Read, Write, Glob, WebFetch
---

# /sws:search-literature

Find new relevant sources for a topic or manuscript section.

## Usage

```
/sws:search-literature "<query>"              # search by topic string
/sws:search-literature --section <id>         # search for a specific manuscript section
/sws:search-literature "<query>" --limit 10   # limit to N candidates (default 20)
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Parse the query or section id from the invocation arguments.
3. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh literature-searcher`.
4. Check `RESOLVED_OK`; if 0, print the prelude's message and exit 0.
5. Dispatch the `literature-searcher` agent with the query.
6. After the agent returns, print one-line summary: N candidates found, sources used.
7. Point the user at `${PAPER_ROOT}/refs/_lit-search/`.

## Spec source of truth

`docs/superpowers/specs/2026-05-22-cycle-11-data-and-literature-wave-design.md` — D3, D8, D9.
