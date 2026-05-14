---
name: ai-writing-tells
description: Catalog of stylistic and structural patterns that signal LLM-generated text in scientific writing. Used by all SWS drafting agents as a grep-pass before returning prose.
language: en
version: 0.1
total_tells: 50
---

# AI writing tells (English, v0.1)

Every drafting agent must grep its output against the patterns below before returning. Block-severity hits abort the response with a fix suggestion; warn-severity hits get flagged in the reply. The catalog seeds from the user's `claude_memory/feedback_ai_writing_tells.md` and expands by category.

## How to use this file

For each tell:

- `pattern`: a regex (Python `re` flavor, case-insensitive unless the regex specifies otherwise) the agent searches for in the draft
- `severity`: `block` (must fix before returning) or `warn` (flag in reply, do not block)
- `example_bad`: a sentence containing the tell
- `example_fix`: a rewrite that removes it
- `why`: short explanation of why this signals AI-generated text

The grep-pass is mechanical. If the source material genuinely needs the construction (a real triplet, a real em-dash for an aside that no comma can replace), the human reviser unblocks it on a per-instance basis. The goal is to bias first drafts toward human cadence, not to forbid the constructions outright.

## Categories

1. **Lexical** — word-level overuse: filler verbs, vogue adjectives, business jargon
2. **Syntactic** — sentence patterns: parallel-clause overload, em-dash abuse, "not X but Y" flips
3. **Structural** — paragraph-level: list-of-three padding, opener formulas, hedging avalanches
4. **Hedging** — softener phrases that delay or muffle the actual claim
5. **Transitions** — connective adverbs stacked across consecutive sentences or paragraphs

## Tells

### Category 1 — Lexical

- pattern: `\b[Dd]elve\b`
  severity: block
  example_bad: "We delve into the kinetics of the reaction."
  example_fix: "We examine the kinetics of the reaction."
  why: Strong LLM signature. Almost absent from scientific writing pre-2023; ubiquitous in ChatGPT output since.

- pattern: `\b[Ll]everage\b`
  severity: block
  example_bad: "We leverage the docking results to predict binding."
  example_fix: "We use the docking results to predict binding."
  why: Business jargon repurposed by LLMs as a high-prestige verb. "Use" is shorter and clearer.

- pattern: `\b[Hh]arness(ing|ed|es)?\b`
  severity: block
  example_bad: "The catalyst harnesses oxygen activation."
  example_fix: "The catalyst activates oxygen."
  why: Same family as "leverage" — heroic verb where a plain action verb fits.

- pattern: `\b[Uu]nlock(ing|ed|s)?\b`
  severity: block
  example_bad: "These results unlock new design principles."
  example_fix: "These results suggest new design principles."
  why: Marketing tell. Real findings don't unlock — they reveal, suggest, support, or refute.

- pattern: `\b[Nn]avigate\b`
  severity: warn
  example_bad: "This work navigates the complexity of multi-step catalysis."
  example_fix: "This work addresses multi-step catalysis."
  why: Metaphorical "navigate" is rare in scientific writing; literal navigation (a tool navigating a parameter space) is fine.

- pattern: `\b[Dd]ive(d|s)? into\b|\b[Dd]iving into\b`
  severity: block
  example_bad: "We dive into the mechanism."
  example_fix: "We analyze the mechanism."
  why: Same family as "delve". Conversational register, wrong for scientific writing.

- pattern: `\b[Ii]ntricate\b`
  severity: warn
  example_bad: "The intricate network of hydrogen bonds stabilizes the fold."
  example_fix: "The hydrogen-bond network stabilizes the fold."
  why: Vogue adjective. "Intricate" rarely adds information beyond "complex" or no qualifier at all.

- pattern: `\b[Rr]obust\b`
  severity: warn
  example_bad: "Robust catalytic activity was observed."
  example_fix: "Catalytic activity was reproducible across three independent runs."
  why: Empty intensifier in most contexts. Replace with the specific metric that justifies the claim.

- pattern: `\b[Cc]omprehensive\b`
  severity: warn
  example_bad: "We performed a comprehensive analysis of the data."
  example_fix: "We analyzed the data using methods A, B, and C."
  why: Self-praising adjective; reviewers read it as defensive. Specify the methods instead.

- pattern: `\b[Mm]eticulous(ly)?\b`
  severity: block
  example_bad: "The procedure was meticulously optimized."
  example_fix: "The procedure was optimized over 12 iterations."
  why: Self-congratulatory; LLMs deploy it as a generic intensifier.

- pattern: `\b[Uu]nderscore(s|d)?\b`
  severity: warn
  example_bad: "These results underscore the importance of pH control."
  example_fix: "These results show that pH control matters."
  why: Common LLM-favored verb where "show", "demonstrate", or "indicate" is more direct.

- pattern: `\b[Pp]aramount\b`
  severity: warn
  example_bad: "Substrate purity is paramount."
  example_fix: "Substrate purity is critical."
  why: Archaic register; LLMs reach for it when a plainer adjective works.

- pattern: `\b[Mm]yriad\b`
  severity: warn
  example_bad: "A myriad of conformations was sampled."
  example_fix: "Hundreds of conformations were sampled."
  why: Quantitatively vague. Give a number or range.

- pattern: `\b[Pp]lethora\b`
  severity: block
  example_bad: "A plethora of factors influences the rate."
  example_fix: "Several factors influence the rate, including X, Y, and Z."
  why: Vogue noun, near-synonym for "many" but with prestige register.

- pattern: `\b[Tt]apestry\b`
  severity: block
  example_bad: "The tapestry of metabolic pathways."
  example_fix: "The network of metabolic pathways."
  why: Decorative metaphor. Strong LLM tell.

- pattern: `\b[Rr]ealm\b`
  severity: warn
  example_bad: "In the realm of homogeneous catalysis."
  example_fix: "In homogeneous catalysis."
  why: "Realm" rarely adds meaning; "field", "area", or no preface is cleaner.

- pattern: `\b[Ll]andscape\b(?! analysis)`
  severity: warn
  example_bad: "The landscape of peptide therapeutics."
  example_fix: "Peptide therapeutics."
  why: Metaphorical "landscape" is an LLM favorite. Literal use ("energy landscape", "fitness landscape") is fine — the negative-lookahead exempts "landscape analysis".

- pattern: `\b[Pp]ivotal\b`
  severity: warn
  example_bad: "The reaction plays a pivotal role."
  example_fix: "The reaction is the rate-limiting step."
  why: "Pivotal" is rarely the right word; LLMs use it when "central", "key", or a specific function fits better.

- pattern: `\b[Gg]ame[- ]?changer(s|ing)?\b`
  severity: block
  example_bad: "These catalysts are game-changers."
  example_fix: "These catalysts increase yield by 40 percent over the previous benchmark."
  why: Marketing register; reviewers reject on sight.

- pattern: `\b[Ss]eamless(ly)?\b`
  severity: warn
  example_bad: "The two methods integrate seamlessly."
  example_fix: "The two methods integrate without manual data conversion."
  why: Vague positive intensifier; specify what "seamless" means.

### Category 2 — Syntactic

- pattern: `[Nn]ot (just|only) [^,.;]{1,40},? but (also )?[^.]{1,80}`
  severity: block
  example_bad: "This is not just a synthetic improvement, but a conceptual shift."
  example_fix: "This synthetic improvement enables a conceptual shift: <explain>."
  why: Rhetorical flip pattern; LLMs use it to manufacture emphasis. Reviewers flag it as ChatGPT-style.

- pattern: `\b[Ii]t['s ]+not (just|only) [^,.;]{1,40} (—|--|that)`
  severity: block
  example_bad: "It's not only the yield — it's the selectivity."
  example_fix: "Both yield and selectivity improved (Table 1)."
  why: Same family as "not just X but Y"; conversational register.

- pattern: `(\w+(-\w+){2,}\s+){2,}`
  severity: warn
  linter_rule: { min_count_per_paragraph: 2 }
  example_bad: "A data-rich, well-characterized, multi-step pipeline."
  example_fix: "A pipeline characterized at every step (Methods §2)."
  why: Stacked compound adjectives are an LLM tell; the user explicitly flagged this.

- pattern: ` — [a-zA-Z]+ — `
  severity: warn
  linter_rule: { min_count_per_paragraph: 3 }
  example_bad: "The substrate — a chiral amine — binds in the active site."
  example_fix: "The substrate (a chiral amine) binds in the active site."
  why: Em-dash overuse for parenthetical asides; prefer parentheses or commas. One em-dash per page is plenty.

- pattern: `(?:[^—\n]*—){3,}`
  severity: block
  example_bad: "This finding — surprising at first — was confirmed by NMR — and by mass spec — and by HPLC."
  example_fix: "NMR, mass spectrometry, and HPLC confirmed this initially surprising finding."
  why: Three-or-more em-dashes in one passage signals decorative punctuation, not parsing aid.

- pattern: `\b[Aa]s such,?\s`
  severity: warn
  example_bad: "As such, we conclude that the mechanism is concerted."
  example_fix: "We conclude that the mechanism is concerted."
  why: "As such" is a legitimate connector but LLMs deploy it as filler before nearly every conclusion. Use sparingly.

- pattern: `\b[Tt]o this end,?\s`
  severity: warn
  example_bad: "To this end, we synthesized analogue 5."
  example_fix: "We synthesized analogue 5 to test this hypothesis."
  why: Formulaic transition; usually addable to almost any sentence without information change.

- pattern: `\b[Bb]y the same token,?\s`
  severity: warn
  example_bad: "By the same token, the inhibitor binds the open conformation."
  example_fix: "The inhibitor binds the open conformation by the same mechanism."
  why: Cliché transition; rephrase to specify what the token actually is.

- pattern: `\bin a (manner|fashion) (that|which) `
  severity: warn
  example_bad: "The data behave in a manner that suggests cooperativity."
  example_fix: "The data suggest cooperativity."
  why: Padding construction; the verb usually fits without the "in a manner that" wrapper.

- pattern: `\b(plays?|playing|played) a (key|crucial|critical|vital|pivotal|central|major|important|significant) role\b`
  severity: block
  example_bad: "Mg²⁺ plays a crucial role in catalysis."
  example_fix: "Mg²⁺ coordinates the transition-state phosphate."
  why: "Plays a [adjective] role" is the most-flagged LLM phrase in scientific abstracts. Replace with the specific function.

### Category 3 — Structural

- pattern: `\b(clarity, precision,? and (depth|insight|rigor))\b`
  severity: block
  example_bad: "We aim for clarity, precision, and depth."
  example_fix: "We aim for measurements at sub-millimolar resolution."
  why: Generic noun-triplet. Reviewers see this and assume LLM padding.

- pattern: `\b\w+, \w+,? and \w+(-\w+)*\b\s*(are|provide|enable|offer|underscore|highlight|illustrate|demonstrate)\b`
  severity: warn
  example_bad: "Yield, selectivity, and reproducibility are improved."
  example_fix: "Yield rose to 92 percent and ee to 98 percent (Table 2)."
  why: Triplet-of-nouns followed by a generic verb. Often a lazy summary of three things that should each get a sentence.

- pattern: `(?im)^\s*[-*]\s.+\n^\s*[-*]\s.+\n^\s*[-*]\s.+\n^\s*[-*]\s.+`
  severity: warn
  example_bad: "(four-or-more bullet list inside narrative prose)"
  example_fix: Convert to a sentence or a numbered list with explicit ranking.
  why: Long bullet lists inside narrative sections (Intro, Discussion) signal LLM template-fill rather than human composition.

- pattern: `\b[Ii]n conclusion,?\s`
  severity: warn
  example_bad: "In conclusion, the catalyst is selective."
  example_fix: (delete the phrase; let the conclusion stand on its own)
  why: Acceptable in a Conclusions section. Inside Intro/Discussion mid-paper, "In conclusion" reads as LLM scaffolding.

- pattern: `\b[Ii]n summary,?\s`
  severity: warn
  example_bad: "In summary, the data support a concerted mechanism."
  example_fix: "The data support a concerted mechanism."
  why: Same family as "In conclusion"; usually deletable.

- pattern: `\b[Tt]aken together,?\s`
  severity: warn
  example_bad: "Taken together, these results indicate cooperativity."
  example_fix: "These results indicate cooperativity."
  why: Soft scaffolding; the reader has already taken the results together.

- pattern: `\b[Cc]ollectively,?\s`
  severity: warn
  example_bad: "Collectively, the data argue for a stepwise mechanism."
  example_fix: "The data argue for a stepwise mechanism."
  why: Same family; deletable.

- pattern: `\b(?:may|might|could) potentially\b`
  severity: block
  example_bad: "The intermediate may potentially form a hydrogen bond."
  example_fix: "The intermediate may form a hydrogen bond."
  why: Hedging avalanche; "may", "might", or "could" already encodes potentiality.

- pattern: `\bcan potentially\b`
  severity: block
  example_bad: "The reaction can potentially proceed via two pathways."
  example_fix: "The reaction can proceed via two pathways."
  why: Same as above; "can" is the modal, "potentially" is redundant.

- pattern: `\b[Ii]n recent years,?\s`
  severity: block
  example_bad: "In recent years, peptide therapeutics have grown rapidly."
  example_fix: "Since 2018, peptide therapeutics have grown 40 percent annually."
  why: Sweeping opener with no time anchor. Always replaceable with a real date or range.

- pattern: `\b[Ii]n the modern era,?\s`
  severity: block
  example_bad: "In the modern era, drug discovery is data-driven."
  example_fix: (anchor to a year, technology, or paradigm shift)
  why: Same family as "In recent years"; even more decorative.

- pattern: `\b[Oo]ver the past (few |several )?(years|decade|decades),?\s`
  severity: warn
  example_bad: "Over the past decade, machine learning has reshaped the field."
  example_fix: "Since 2014, machine learning has reshaped the field."
  why: Vague time anchor; specify the year or the triggering paper.

### Category 4 — Hedging

- pattern: `\b[Ii]t is worth noting that\b`
  severity: block
  example_bad: "It is worth noting that yield depends on temperature."
  example_fix: "Yield depends on temperature (Figure 3)."
  why: If the claim is worth making, make it. The hedge wastes tokens and reads as LLM padding.

- pattern: `\b[Ii]t should be (emphasized|noted|highlighted|stressed|mentioned|pointed out) that\b`
  severity: block
  example_bad: "It should be emphasized that the reaction is exothermic."
  example_fix: "The reaction is exothermic (ΔH = −12 kJ/mol)."
  why: Same family. Drop the meta-comment; state the fact.

- pattern: `\b[Ii]t is important to (note|consider|recognize|emphasize|mention|highlight)\b`
  severity: block
  example_bad: "It is important to consider the kinetic barrier."
  example_fix: "The kinetic barrier (24 kcal/mol) limits turnover."
  why: Same family; nearly always deletable.

- pattern: `\b[Ii]t is interesting to (note|observe|see)\b`
  severity: warn
  example_bad: "It is interesting to note that the yield drops at pH > 8."
  example_fix: "The yield drops at pH > 8 (Figure 4)."
  why: Trust the reader to find a specific finding interesting; the hedge undercuts the claim.

- pattern: `\b[Nn]otably,?\s`
  severity: warn
  example_bad: "Notably, the reaction proceeds without a catalyst."
  example_fix: "The reaction proceeds without a catalyst — a result not previously reported (refs)."
  why: "Notably" tells the reader to pay attention without explaining why. Specify the contrast.

- pattern: `\b[Ii]nterestingly,?\s`
  severity: warn
  example_bad: "Interestingly, the rate is independent of substrate concentration."
  example_fix: "The rate is independent of substrate concentration, indicating saturation."
  why: Same family as "Notably". Replace with the actual implication.

- pattern: `\b[Ii]ndeed,?\s`
  severity: warn
  example_bad: "Indeed, X-ray diffraction confirms the structure."
  example_fix: "X-ray diffraction confirms the structure."
  why: Acceptable once or twice per paper as a real reinforcement; LLMs deploy it as filler before nearly every confirmatory sentence.

### Category 5 — Transitions

- pattern: `\b[Ff]urthermore,?\s.{0,300}\b[Mm]oreover,?\s`
  severity: block
  example_bad: "Furthermore, X. ... Moreover, Y."
  example_fix: "X. Y." (or rewrite without either transition)
  why: "Furthermore" + "Moreover" within ~300 characters is the canonical LLM-paragraph signature.

- pattern: `\b[Mm]oreover,?\s.{0,300}\b[Ff]urthermore,?\s`
  severity: block
  example_bad: "Moreover, X. ... Furthermore, Y."
  example_fix: "X. Y."
  why: Mirror of the previous tell.

- pattern: `\b[Ff]urthermore,?\s.{0,300}\b[Aa]dditionally,?\s`
  severity: block
  example_bad: "Furthermore, X. ... Additionally, Y."
  example_fix: "X. Y."
  why: Same family; three connective adverbs in close proximity is LLM-paragraph cadence.

- pattern: `\b[Ww]hile [^,.]{1,80}, on the other hand,\b`
  severity: warn
  example_bad: "While the yield improved, on the other hand, the selectivity dropped."
  example_fix: "Yield improved, but selectivity dropped."
  why: "While X, on the other hand, Y" double-marks the contrast. Pick one connector.

- pattern: `(?<!on one hand[,.; ])\bOn the other hand,?\s`
  severity: warn
  example_bad: "On the other hand, the inhibitor binds tighter."
  example_fix: "The inhibitor, in contrast, binds tighter." (or "By contrast, the inhibitor binds tighter.")
  why: "On the other hand" without a prior "On one hand" is unbalanced rhetoric; usually replaceable with "in contrast".

- pattern: `(?im)^\s*(Furthermore|Moreover|Additionally|However|Nevertheless|Nonetheless),`
  severity: warn
  linter_rule: { min_count_per_paragraph: 2 }
  example_bad: "Furthermore, the data show..."
  example_fix: Restructure the sentence so the substantive subject comes first.
  why: Sentence-initial connective adverb is fine in moderation; flag for review when it appears at the start of three-or-more consecutive paragraphs.
