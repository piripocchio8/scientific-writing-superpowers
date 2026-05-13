---
name: prepare-lit-context
description: "This skill should be used when the user invokes /sws:prepare-lit-context, says 'prepare the literature manifest', 'export Zotero for this paper', 'make the citation manifest', 'load my Zotero collection', or similar — and the cwd is an SWS project. Wraps the user's zotero skill (if installed) to write _lit/zotero-manifest.md. Degrades to PubMed MCP fallback or to a no-op if neither is available."
version: 0.1.0
---

# /sws:prepare-lit-context — Build the citation manifest for drafting

This skill exports the user's Zotero collection (scoped to the paper, if the user keyed it) into a manifest file at `<paper>/_lit/zotero-manifest.md`. Drafter agents read the manifest to ground in-text citations using the format `[<FirstAuthor><Year>; doi:<doi>]` or `[<FirstAuthor><Year>; zotero:<key>]`.

## Degradation chain (D16)

1. **Zotero skill installed (preferred):** invoke the user's `zotero` skill to export a JSON of the collection associated with this paper, then convert via `scripts/sws_extract_zotero_manifest.py`.
2. **Zotero skill not installed:** print a one-line recommendation to install it (`/plugin install zotero`), then proceed to step 3.
3. **PubMed MCP fallback:** if `mcp__claude_ai_PubMed__*` tools are available and the user has provided a search query, run a small search (< 50 results) and synthesize a manifest from the returns. Less rich than Zotero (no `key_claims` digest) but enough for drafter to cite.
4. **Neither available:** write an empty manifest with `item_count: 0` and a comment explaining drafter will produce `[CITATION_NEEDED: ...]` placeholders. Do NOT fail the skill.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check (same as outline-paper). If absent, print "not an SWS project (no .sws-project.local.md found)" and exit.
2. **Detect zotero skill availability.** Check the available-skills list in the conversation context.
3. **Branch on availability** per the chain above.
4. **Token-budget cap.** If the export exceeds 15k tokens (approximate; see `sws_extract_zotero_manifest.py --cap-tokens`), truncate to most-recent-by-date-added and set `truncated: true` in the manifest frontmatter. The user can re-run with a tighter collection scope or adjust `cap_token_budget` in the manifest frontmatter for next time.
5. **Write the manifest** at `${PAPER_ROOT}/_lit/zotero-manifest.md` via:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sws_extract_zotero_manifest.py" \
       --input <zotero-export.json> --paper "$PAPER_ROOT"
   ```
   Print the path and item count.

## When to invoke

- Explicit `/sws:prepare-lit-context`.
- User says any of the description triggers — and the cwd has a valid marker.

Do NOT invoke when the cwd has no marker; print the not-an-SWS-project line and exit.

## What lives downstream

Drafter-flagship and drafter-fast read this manifest before drafting. Items missing from the manifest become `[CITATION_NEEDED: <claim>]` placeholders that the cycle-#11 literature-searcher agent will resolve later.
