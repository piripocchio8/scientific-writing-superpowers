---
profile: methodological-paper
inherits: null
sections:
  - { id: abstract, label: Abstract, word_limit: 250, required: true }
  - { id: introduction, label: Introduction, word_limit: null, required: true }
  - { id: results, label: Results, word_limit: null, required: true }
  - { id: experimental, label: Experimental Section, word_limit: null, required: true }
  - { id: validation, label: Validation, word_limit: null, required: true }
  - { id: conclusion, label: Conclusions, word_limit: 400, required: true }
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
agents_active: [outline-architect, drafter-flagship, drafter-fast, methods-writer, caption-writer, reviser-full, reviser-fast, humanizer, style-enforcer, consistency-checker, peer-reviewer, claim-verifier, bibliography-fidelity-checker, data-curator, plot-maker, literature-searcher, bibliography-curator]
agents_inactive: [proposal-budget-helper, proposal-compliance-helper]
---

# Methodological-paper profile

**Audience:** users of the method, not generic specialists. They will reimplement; clarity matters more than narrative.
**Voice:** procedural and explicit. Optimization choices stated, not justified post-hoc.
**Structure discipline:** Experimental Section is the centerpiece; Results show that it works; Validation shows that it works reliably. No proprietary black boxes — reproducibility is the deliverable.
**Banned patterns:** "we developed" without specifying what changed from prior methods; success-only Results sections; Validation that uses the same data the method was tuned on.

## Drafter notes

Conclusion (target 400 words) summarizes what the method does well, where it fails, and what the next iteration should change. methods-writer is fully active — depth here is the value proposition.
