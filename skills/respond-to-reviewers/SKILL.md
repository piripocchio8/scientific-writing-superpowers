---
name: respond-to-reviewers
description: |
  Build the R&R Traceability Matrix and dispatch the response-to-reviewers
  agent (Opus 4.7) on _review/round-<N>/. Default round is the highest
  existing N; pass --round to target a specific round. Two-step pipeline:
  sws_response_matrix.py (deterministic parse, no LLM) -> response-to-reviewers
  agent (rebuttal prose + matrix fill). Output mirrored to _submission/ for
  journal upload. Cost-gated by R1 — runs Opus, so the prompt warns to use
  only after a finalized revision.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:respond-to-reviewers

Generate the Response-to-Reviewers document and fill the R&R matrix.

## Usage

```
/sws:respond-to-reviewers                       # latest round
/sws:respond-to-reviewers --round 2             # explicit round
```

## Pipeline

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh response-to-reviewers`.
3. Resolve `--round`:
   - If passed, use it.
   - Else run `${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT"
     ${CLAUDE_PLUGIN_ROOT}/scripts/sws_review_round.py find` and use the
     reported N. If `none`, instruct the user to run
     `/sws:respond-to-reviewers --round 1` after creating
     `_review/round-1/reviewer-comments.md` (or invoke
     `sws_review_round.py init`).
4. Verify `${PAPER_ROOT}/_review/round-<N>/reviewer-comments.md` exists. If
   not, exit with:
   "Paste reviewer comments into _review/round-<N>/reviewer-comments.md and
   re-run."
5. Build/refresh the matrix (deterministic, no LLM):
   ```
   ${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" \
       ${CLAUDE_PLUGIN_ROOT}/scripts/sws_response_matrix.py \
       ${PAPER_ROOT}/_review/round-<N>/reviewer-comments.md
   ```
   This is idempotent (R3): existing `status`, `response_text`, `edits_made`,
   and `line_refs` survive re-parse when a comment id is unchanged.
6. Dispatch the `response-to-reviewers` agent with `--round <N>`.
7. After the agent returns, print summary: rebuttal word count, concession
   counts (accepted / partial / rejected), grep-pass status.
8. Point the user at:
   - `${PAPER_ROOT}/_review/round-<N>/response-to-reviewers.md` (canonical)
   - `${PAPER_ROOT}/_submission/response-to-reviewers-round-<N>.md` (mirror
     for journal upload).

## V0.1 cost note (R1)

`response-to-reviewers` uses Opus 4.7. A full-paper rebuttal is the most
expensive submission-phase agent run. Use only after a finalized revision and
after receiving actual reviewer comments — speculative runs burn budget.

## Spec source of truth

`docs/superpowers/specs/2026-05-30-cycle-12-submission-orchestration-design.md`
— D5, D12, D16, R1, R3.
