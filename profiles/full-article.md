---
profile: full-article
inherits: null
sections:
  - { id: abstract, label: Abstract, word_limit: 250, required: true }
  - { id: introduction, label: Introduction, word_limit: null, required: true }
  - { id: results, label: Results and Discussion, word_limit: null, required: true }
  - { id: experimental, label: Experimental Section, word_limit: null, required: true }
  - { id: conclusion, label: Conclusions, word_limit: 300, required: true }
  - { id: references, label: References, word_limit: null, required: true }
ref_cap: 80
word_total: null
figures_max: null
tables_max: null
abstract_style: structured
disclosure_required: true
cover_letter_required: true
supplementary_allowed: true
refs_style: numbered
agents_active: [outline-architect, drafter-flagship, drafter-fast, methods-writer, caption-writer, proposal-budget-helper, proposal-compliance-helper, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker, data-curator, plot-maker, literature-searcher, bibliography-curator]
agents_inactive: []
---

# Full-article profile

**Audience:** specialist readers in the field; peer reviewers; editors.
**Voice:** measured, evidence-led. First-person plural only where the field convention allows it.
**Structure discipline:** every claim in Results must trace to a figure, a table, or cited prior work. No interpretation without an evidence anchor.
**Banned patterns:** none beyond the global AI-tells list (see `references/ai-writing-tells.md`).

## Drafter notes

Results-and-Discussion sections are tighter than Results-only because every interpretation must sit next to its evidence. Conclusion is short (target 300 words) — synthesis only, no new claims, no new citations.

Experimental Section is uncapped but should not duplicate the SI; cross-reference SI for protocol details, keep the main file readable end-to-end. The default Abstract style is structured (problem / approach / result / impact); journals that prefer unstructured will override via the journal-style overlay.
