---
name: peer-review
description: |
  Run the SWS peer-reviewer agent (Opus 4.7 max) on the active manuscript or a single section. Encodes EIC + 3-reviewer + Decision Authority structure from the rubric at references/peer-review-rubric.md. Writes _review/peer-reviewer/report.md. Diagnoses only — never writes to the manuscript. Optional --claim-report and --fidelity-report args fold prior review outputs into the synthesis (used by /sws:review-paper). Active in all 9 profiles.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:peer-review

Trigger a peer-review pass on the active manuscript (or a single section).

## Usage

```
/sws:peer-review                           # full paper review
/sws:peer-review --section introduction    # single-section review
/sws:peer-review --claim-report <path>     # fold a prior claim-verifier report in
/sws:peer-review --fidelity-report <path>  # fold a prior fidelity report in
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists. If not, exit with the standard "not an SWS project" message.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh peer-reviewer` to load `RESOLVED_*` env vars.
3. Dispatch the `peer-reviewer` agent. Pass `--manuscript ${PAPER_ROOT}/Manuscript/<active-docx>` plus any `--claim-report` / `--fidelity-report` args the user supplied. If `SWS_FIDELITY_STATUS` is in the environment, propagate it.
4. After the agent returns, print the one-line summary the agent already produced (decision, overall score, flag counts).
5. Point the user at `${PAPER_ROOT}/_review/peer-reviewer/report.md` for the full report.

## V0.1 cost note

`peer-reviewer` uses Opus 4.7 at `max` effort. A full-paper run is the most expensive single agent invocation in SWS. Users wanting cheaper diagnostics can run `/sws:verify-claims` and `/sws:check-fidelity` standalone.

## Spec source of truth

`docs/superpowers/specs/2026-05-17-cycle-09-review-design.md` — D1, D2, D5, D6, D7, D11 (cost note), D14 (single-section routing), D16 (rubric).
