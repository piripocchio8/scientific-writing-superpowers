---
profile: funding-proposal
inherits: null
sections:
  - { id: summary, label: Summary, word_limit: 500, required: true }
  - { id: state-of-the-art, label: State of the art, word_limit: null, required: true }
  - { id: objectives, label: Objectives, word_limit: null, required: true }
  - { id: methodology, label: Methodology, word_limit: null, required: true }
  - { id: workplan, label: Work plan, word_limit: null, required: true }
  - { id: impact, label: Impact, word_limit: null, required: true }
  - { id: references, label: References, word_limit: null, required: true }
ref_cap: null
word_total: null
figures_max: null
tables_max: null
abstract_style: structured
disclosure_required: true
cover_letter_required: false
supplementary_allowed: true
refs_style: numbered
agents_active: []
agents_inactive: [response-to-reviewers]
---

# Funding-proposal profile

**Audience:** non-specialist evaluators with strong opinions about impact and feasibility; specialist reviewers selected from the panel pool.
**Voice:** confident, concrete, slightly more forward-leaning than a paper. Evaluators reward clear claims of novelty and a credible plan.
**Structure discipline:** every section answers a different evaluator question — Summary = "what and why now", State-of-the-art = "why hasn't this been done", Objectives = "what specifically will you deliver", Methodology = "how (and why this method)", Work plan = "in what order, by when, with what risk mitigation", Impact = "what changes if you succeed".
**Banned patterns:** "innovative" / "cutting-edge" without specifying what is innovative; vague timelines ("years 1–3"); risk sections that list no actual risks; budget mentions in the science part of the proposal.

## Drafter notes

The call overlay (`/sws:resolve-call-rules`) sets the exact section list, page/word limits, language, and program-specific terminology. Profile defaults are placeholders; the overlay is authoritative once resolved. response-to-reviewers is inactive because this is a fresh submission, not a revision; if resubmitting after a previous round, the user should set article_type back to full-article or use a separate response section.

proposal-budget-helper and proposal-compliance-helper are the two profile-unique agents. They activate only here.
