---
sws_artifact: peer-review-rubric
artifact_version: 0.1
attribution: "Outer narrative shape adapted from Imbad0202/academic-research-skills (MIT). Section-weight matrix is SWS-specific."
used_by: agents/peer-reviewer.md
---

# Peer-review rubric (v0.1)

The peer-reviewer agent reads this file at runtime, selects the section matching the user's resolved profile, and applies the listed weights when structuring its report.

## Narrative shape (all profiles)

The peer-reviewer encodes four personas in a single prompt:

1. **EIC (Editor-in-Chief):** assesses fit-for-journal/venue, novelty bar, ethical concerns.
2. **Reviewer 1 — methods focus:** assesses rigor, reproducibility, statistical correctness, claims-vs-evidence alignment.
3. **Reviewer 2 — domain focus:** assesses positioning vs prior art, novelty of contribution, citation completeness.
4. **Reviewer 3 — clarity focus:** assesses presentation, figure quality, logical flow, prose clarity.
5. **DA (Decision Authority):** synthesizes into one of {Accept, Minor Revision, Major Revision, Reject}.

The four reviewer personas share the report. The EIC frame opens; the DA frame closes.

## Section-weight matrix

When a section is missing from the manuscript, redistribute its weight proportionally across the remaining sections.

### full-article
- introduction: 15%
- methods: 25%
- results: 30%
- discussion: 20%
- references: 10%

### communication
- intro: 30%
- methods: 20%
- results: 40%
- references: 10%

### review-paper
- coverage: 35%
- synthesis: 30%
- critical evaluation: 25%
- references: 10%

### mini-review
- coverage: 35%
- synthesis: 30%
- critical evaluation: 25%
- references: 10%

### perspective
- framing: 30%
- argumentation: 40%
- novelty: 20%
- references: 10%

### editorial
- argument: 50%
- voice: 30%
- brevity: 20%

### methodological-paper
- novelty: 20%
- methods: 40%
- validation: 30%
- references: 10%

### commentary-reply
- fidelity-to-original: 30%
- argument: 40%
- civility: 20%
- references: 10%

### funding-proposal
- feasibility: 25%
- novelty: 25%
- impact: 25%
- team: 15%
- budget: 10%

## Report-file shape

The peer-reviewer writes `_review/peer-reviewer/report.md` with this YAML frontmatter dictionary:

```yaml
---
sws_artifact: peer-review-report
profile: <resolved profile>
manuscript_file: <relative path>
decision: Accept | Minor Revision | Major Revision | Reject
overall_score: 1-5
section_scores:
  <section_id>: { weight: 0.XX, score: 1-5, comments_count: N }
flags:
  ethical: N
  reproducibility: N
  novelty: N
  citations: N
fidelity_status: ran | skipped:<reason>
claim_verification_status: ran | skipped:<reason>
---
```

Body: EIC opening, four reviewer sections with per-section scores and comments, DA closing.

## V0.1 limitations (must appear in every report)

- No sprint-contracts paper-blind Phase 1 in v0.1 (deferred to cycle #9.1). The reviewer reads the paper directly.
- No concession-threshold scoring (dormant until response-to-reviewers ships in cycle #10).
- Single-agent multi-persona; not five separate dispatched agents (v0.2+ option).
