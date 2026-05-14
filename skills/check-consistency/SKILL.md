---
name: check-consistency
description: "This skill should be used when the user invokes /sws:check-consistency, says 'check consistency', 'run a consistency check', 'find cross-section issues', 'check figure references' — and the cwd is an SWS project with drafts in _drafts/. Operates on _drafts/ (no args). Dispatches consistency-checker agent only for ambiguous findings; deterministic checks run via script. Not supported for funding-proposal profile in v0.1 (D19)."
version: 0.1.0
---

# /sws:check-consistency — Text-internal consistency check

Runs `scripts/sws_consistency_check.py` on `_drafts/` and writes `_review/consistency-report.md`. The `consistency-checker` agent is dispatched only when findings are ambiguous (e.g., possible abbreviation collisions that the script cannot resolve deterministically). Deterministic checks (figure-ref mismatches, citation duplication) run in the script alone.

## Checks performed (D9)

1. Figure and table references in prose (`Fig. N`, `Figure N`, `Figures N+M`) match the figures/tables declared in `_outline/outline.md`.
2. Section list in the assembled draft matches the profile's required sections.
3. Citation keys parse correctly and are uniquely formatted (no key written twice with different DOIs).
4. Abbreviations introduced on first use (`Full Name (ABBR)` pattern); subsequent occurrences must match an introduced abbreviation.
5. Terminology uniformity: mixed case for the same term in the same draft (e.g., `thrombin` / `Thrombin` / `THROMBIN`) flags as a finding.

All sections are read in profile order before scanning for abbreviation introductions — so an abbreviation defined in Methods and used in Results is not falsely flagged (D9, R3 mitigation).

## Funding-proposal profile — v0.1 limitation (D19)

When `RESOLVED_PROFILE_ID == funding-proposal`, the skill prints:

> Consistency check not supported for funding-proposal profile in v0.1 (WP/deliverable/milestone cross-reference checks ship in cycle #10). Manual review required.

and exits 0. Publication profiles are fully supported.

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check. If absent, print "not an SWS project (no .sws-project.local.md found)" and exit.
2. **Resolve profile.** If `profile_id == funding-proposal`, print the v0.1 unsupported message and exit 0 (D19).
3. **Run `scripts/sws_consistency_check.py`** on `_drafts/` (or on a stitched markdown file if drafts are not yet assembled). Pass the outline path for figure/table cross-reference.
4. **Dispatch `consistency-checker` agent** only if any findings are flagged as ambiguous by the script. The agent reviews ambiguous findings and adds `suggested_fix` annotations to the report.
5. **Write `_review/consistency-report.md`** (YAML frontmatter: `generated_at`, `profile`, `checked_files`, `findings_count`, `findings_by_severity`). Print summary: N block findings, M warn findings, report path.

## When to invoke

- Explicit `/sws:check-consistency`.
- User says "check consistency", "run a consistency check", "find figure reference mismatches".
- Also called as step 3 of `/sws:revise-paper`.

Do NOT invoke when the marker is missing, when no `_drafts/` files exist, or when profile is funding-proposal (exits 0 with explanation).
