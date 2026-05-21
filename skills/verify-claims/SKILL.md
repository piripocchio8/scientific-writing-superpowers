---
name: verify-claims
description: |
  Run the SWS claim-verifier agent to check every citation-bearing claim in _drafts/*-revised.md against the user's Zotero library, Semantic Scholar, and PubMed. Writes _review/claim-verifier/{report.md, claims.json}. Diagnoses only — never edits the manuscript. NLM-grounded RAG is deferred to cycle #11. Inactive in funding-proposal profile.
allowed-tools: Bash, Read, Write, Glob, WebFetch
---

# /sws:verify-claims

Verify every citation in the manuscript actually supports the claim attached to it.

## Usage

```
/sws:verify-claims                       # verify all claims in _drafts/*-revised.md
/sws:verify-claims --section <id>        # verify claims from a single section
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh claim-verifier`.
3. If `RESOLVED_PROFILE_ID == funding-proposal`, print the v0.1-unsupported message and exit 0.
4. Dispatch the `claim-verifier` agent. The agent runs `sws_claim_extract.py` to harvest claims, then verifies each per arch sketch §5 consumption order.
5. After the agent returns, print one-line summary: total claims / verified / unverified / contested / source-not-found.
6. Point the user at `${PAPER_ROOT}/_review/claim-verifier/report.md`.

## Spec source of truth

`docs/superpowers/specs/2026-05-17-cycle-09-review-design.md` — D1, D2, D8, D10.
