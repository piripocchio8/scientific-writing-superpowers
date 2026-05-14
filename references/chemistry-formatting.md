---
sws_artifact: chemistry-formatting
artifact_version: 0.1
locked: 2026-05-14
lang: en
description: >
  Machine-parseable catalog of chemistry-formatting patterns for SWS.
  Consumed by scripts/sws_apply_chemistry_format.py at style-enforcer time.
  Applies ONLY when format=docx; no-op for format=latex (D7).

categories:

  latin_abbreviations:
    - id: et_al
      pattern: "\\bet al\\.?"
      apply: italic
      severity: auto
      example_before: "Smith et al. reported"
      example_after: "Smith *et al.* reported"
      why: "Latin phrase; italic by scientific convention (Chicago, ACS, RSC)."

    - id: eg
      pattern: "\\be\\.g\\."
      apply: italic
      severity: auto
      example_before: "e.g. three trials"
      example_after: "*e.g.* three trials"
      why: "Latin exempli gratia; italic by convention."

    - id: ie
      pattern: "\\bi\\.e\\."
      apply: italic
      severity: auto
      example_before: "i.e. the rate constant"
      example_after: "*i.e.* the rate constant"
      why: "Latin id est; italic by convention."

    - id: in_vitro
      pattern: "\\bin vitro\\b"
      apply: italic
      severity: auto
      example_before: "the in vitro assay"
      example_after: "the *in vitro* assay"
      why: "Latin phrase used without italics only in informal contexts; journals require italic."

    - id: in_vivo
      pattern: "\\bin vivo\\b"
      apply: italic
      severity: auto
      example_before: "in vivo experiments"
      example_after: "*in vivo* experiments"
      why: "Latin phrase; italic by scientific convention."

    - id: ex_vivo
      pattern: "\\bex vivo\\b"
      apply: italic
      severity: auto
      example_before: "ex vivo tissue samples"
      example_after: "*ex vivo* tissue samples"
      why: "Latin phrase; same convention as in vivo / in vitro."

    - id: in_silico
      pattern: "\\bin silico\\b"
      apply: italic
      severity: auto
      example_before: "in silico docking"
      example_after: "*in silico* docking"
      why: "Quasi-Latin phrase coined by analogy; italic is now the journal standard."

    - id: versus
      pattern: "\\bvs?\\.(?=\\s|$)"
      apply: italic
      severity: auto
      example_before: "active vs. inactive"
      example_after: "active *vs.* inactive"
      why: "Latin versus abbreviation; italic in most chemistry style guides."

  chemical_formulae:
    - id: subscript_digits_in_formula
      pattern: "(?<=[A-Za-z])(\\d+)"
      apply: subscript
      severity: auto
      example_before: "H2O"
      example_after: "H₂O"
      why: "Digit following a letter in a chemical formula is a stoichiometric subscript."

    - id: cation_superscript
      pattern: "([A-Z][a-z]?)(\\d*)([+])"
      apply: superscript
      severity: auto
      example_before: "Na+"
      example_after: "Na⁺"
      why: "Charge on a cation is a superscript."

    - id: anion_superscript
      pattern: "([A-Z][a-z]?)(\\d*)([-])"
      apply: superscript
      severity: auto
      example_before: "Cl-"
      example_after: "Cl⁻"
      why: "Charge on an anion is a superscript."

    - id: multi_charge_cation
      pattern: "([A-Z][a-z]?)(\\d\\+)"
      apply: superscript
      severity: auto
      example_before: "Ca2+"
      example_after: "Ca²⁺"
      why: "Numeric charge on a polyvalent cation must be superscript."

    - id: multi_charge_anion
      pattern: "([A-Z][a-z]?\\d*)(\\d[-])"
      apply: superscript
      severity: auto
      example_before: "SO42-"
      example_after: "SO₄²⁻"
      why: "Numeric charge on a polyvalent anion must be superscript."

    - id: formula_subscript_complex
      pattern: "\\b([A-Z][A-Za-z]?)(\\d+)(?=[A-Z]|\\s|$)"
      apply: subscript
      severity: suggest
      example_before: "CO2 concentration"
      example_after: "CO₂ concentration"
      why: "Multi-atom formula subscript; suggest because 'CO2' could be a variable name in some contexts."

    - id: charge_superscript_combined
      pattern: "\\^(\\d+[+-]|[+-])"
      apply: superscript
      severity: auto
      example_before: "Fe^3+"
      example_after: "Fe³⁺"
      why: "Explicit caret notation for charge requires superscript formatting."

  species_names:
    - id: genus_species
      pattern: "\\b([A-Z][a-z]{2,})\\s([a-z]{4,})\\b"
      apply: italic
      severity: suggest
      example_before: "Staphylococcus aureus biofilm"
      example_after: "*Staphylococcus aureus* biofilm"
      why: "Genus + species epithet: suggest because pattern also matches proper-name phrases (e.g., 'John smith')."

    - id: genus_species_with_strain
      pattern: "\\b([A-Z][a-z]{2,})\\s([a-z]{4,})\\s([A-Z]{1,6}[0-9]*)\\b"
      apply: italic
      severity: suggest
      example_before: "Escherichia coli K12"
      example_after: "*Escherichia coli* K12"
      why: "Full genus-species with strain designation; suggest for same ambiguity reasons."

    - id: genus_only
      pattern: "\\b([A-Z][a-z]{4,}(aceae|ales|inae|idae|eae))\\b"
      apply: italic
      severity: suggest
      example_before: "Streptococcaceae family"
      example_after: "*Streptococcaceae* family"
      why: "Taxonomic family/order suffix patterns; suggest because not all -aceae words are taxa."

    - id: virus_species
      pattern: "\\b([A-Z][a-z]+virus|[A-Z][a-z]+phage|[A-Z][a-z]+viridae)\\b"
      apply: italic
      severity: suggest
      example_before: "Adenovirus vector"
      example_after: "*Adenovirus* vector"
      why: "Virus genus names are italicized per ICTV; suggest due to common-noun risk."

    - id: plant_cultivar
      pattern: "\\b([A-Z][a-z]{2,})\\s(sp|spp)\\."
      apply: italic
      severity: suggest
      example_before: "Arabidopsis sp. seedlings"
      example_after: "*Arabidopsis* sp. seedlings"
      why: "Genus sp./spp. abbreviation; suggest for ambiguity."

    - id: microorganism_trivial
      pattern: "\\b(yeast|fungi|bacteria|archaea|protozoa)\\b"
      apply: italic
      severity: suggest
      example_before: "the yeast cells"
      example_after: "the *yeast* cells"
      why: "Trivial taxon names sometimes italicized in mycology/microbiology; suggest because usage is inconsistent across journals."

  species_abbreviated:
    - id: abbreviated_genus_species
      pattern: "\\b([A-Z])\\. ([a-z]{4,})\\b"
      apply: italic
      severity: auto
      example_before: "E. coli"
      example_after: "*E. coli*"
      why: "Single-letter genus abbreviation + species epithet is unambiguous in scientific context; auto."

    - id: abbreviated_genus_long_epithet
      pattern: "([A-Z][a-z])\\. ([a-z]{4,})\\b"
      apply: italic
      severity: auto
      example_before: "St. aureus"
      example_after: "*St. aureus*"
      why: "Two-letter genus abbreviation (Staphylococcus = St., Streptococcus = Str.) + species; auto."

    - id: abbreviated_genus_with_strain
      pattern: "\\b([A-Z])\\. ([a-z]{4,}) (DSM|ATCC|NCTC|CCUG)\\s?\\d+"
      apply: italic
      severity: auto
      example_before: "E. coli ATCC 25922"
      example_after: "*E. coli* ATCC 25922"
      why: "Abbreviated genus + species + culture collection number; strain code stays roman."

    - id: abbreviated_species_subsp
      pattern: "\\b([A-Z])\\. ([a-z]{4,}) subsp\\. ([a-z]{3,})\\b"
      apply: italic
      severity: auto
      example_before: "B. subtilis subsp. subtilis"
      example_after: "*B. subtilis* subsp. *subtilis*"
      why: "Subspecies designation also requires italics per ICNP/ICBN."

    - id: common_lab_species
      pattern: "\\b(E\\. coli|S\\. cerevisiae|B\\. subtilis|C\\. elegans|D\\. melanogaster|A\\. thaliana|H\\. sapiens|M\\. musculus|R\\. norvegicus)\\b"
      apply: italic
      severity: auto
      example_before: "E. coli culture"
      example_after: "*E. coli* culture"
      why: "Most-common lab organisms listed as explicit auto-patterns for reliability."

    - id: abbreviated_genus_consonant_cluster
      pattern: "\\b([A-Z][a-z])\\. ([a-z]{4,})\\b"
      apply: italic
      severity: auto
      example_before: "Ps. aeruginosa"
      example_after: "*Ps. aeruginosa*"
      why: "Two-character genus abbreviation with period + species epithet; unambiguous."

  gene_names:
    - id: hugo_gene_symbol
      pattern: "\\b([A-Z][A-Z0-9]{1,4})\\b(?!\\s*[+-]?\\d)"
      apply: italic
      severity: suggest
      example_before: "TP53 mutation"
      example_after: "*TP53* mutation"
      why: "HUGO convention: human gene symbols are 2-6 uppercase letters/digits, italicized. Suggest because pattern also catches acronyms (NMR, PCR, HPLC)."

    - id: mouse_gene_symbol
      pattern: "\\b([A-Z][a-z][a-z0-9]{1,4})\\b"
      apply: italic
      severity: suggest
      example_before: "Trp53 knockout"
      example_after: "*Trp53* knockout"
      why: "Mouse gene symbols: initial cap + lowercase letters. Suggest due to overlap with normal capitalized words."

    - id: gene_number_suffix
      pattern: "\\b([A-Z]{2,5})(\\d+[A-Z]?)\\b(?!\\s*[+-])"
      apply: italic
      severity: suggest
      example_before: "BRCA1 carrier"
      example_after: "*BRCA1* carrier"
      why: "Gene symbol with numeric identifier (BRCA1, COX2, ATP7A); suggest because e.g. 'ACS2022' also matches."

    - id: gene_with_locus
      pattern: "\\b([A-Z]{2,5})-([0-9]+)\\b"
      apply: italic
      severity: suggest
      example_before: "SNCA-1 expression"
      example_after: "*SNCA-1* expression"
      why: "Gene locus designation; suggest because codes and identifiers share this format."

    - id: bacterial_gene_lowercase
      pattern: "\\b([a-z]{3}[A-Z])\\b"
      apply: italic
      severity: auto
      example_before: "lacZ reporter"
      example_after: "*lacZ* reporter"
      why: "Bacterial gene naming convention (three lowercase + one uppercase letter, e.g. lacZ, recA, rpoB); auto because pattern is highly specific to bacterial genetics."

    - id: bacterial_gene_recessive
      pattern: "\\b([a-z]{3}[A-Z][A-Z]?)\\b"
      apply: italic
      severity: auto
      example_before: "recA deletion"
      example_after: "*recA* deletion"
      why: "recA, katG, rpsA: three-lowercase + one-or-two uppercase bacterial gene names; auto."

  figure_label_prefix:
    - id: figure_number_prefix
      pattern: "^(Figure|Fig\\.)(\\s)(\\d+|S\\d+)([.:])"
      apply: bold
      severity: auto
      example_before: "Figure 1. Reaction scheme."
      example_after: "**Figure 1.** Reaction scheme."
      why: "Figure label prefix is bold non-italic by SWS style canon (references/docx-style.md SWS-Caption)."

    - id: table_number_prefix
      pattern: "^(Table|Tab\\.)(\\s)(\\d+|S\\d+)([.:])"
      apply: bold
      severity: auto
      example_before: "Table 2. Kinetic parameters."
      example_after: "**Table 2.** Kinetic parameters."
      why: "Table label prefix is bold non-italic by SWS style canon."

    - id: scheme_number_prefix
      pattern: "^(Scheme)(\\s)(\\d+|S\\d+)([.:])"
      apply: bold
      severity: auto
      example_before: "Scheme 1. Synthetic route."
      example_after: "**Scheme 1.** Synthetic route."
      why: "Scheme captions follow same convention as Figure captions in chemistry journals (ACS, RSC, Wiley)."

    - id: chart_number_prefix
      pattern: "^(Chart)(\\s)(\\d+|S\\d+)([.:])"
      apply: bold
      severity: auto
      example_before: "Chart 1. Compound structures."
      example_after: "**Chart 1.** Compound structures."
      why: "Chart captions follow same convention in chemical communication formats."

    - id: supporting_figure_prefix
      pattern: "^(Figure|Fig\\.)(\\s)(S\\d+)([.:])"
      apply: bold
      severity: auto
      example_before: "Figure S1. NMR spectrum."
      example_after: "**Figure S1.** NMR spectrum."
      why: "Supporting-information figure labels follow the same bolding rule as main-text figures."

    - id: figure_abbreviated_prefix
      pattern: "^(Figures|Tables|Schemes)(\\s)(\\d+)([-–])(\\d+)([.:]?)"
      apply: bold
      severity: auto
      example_before: "Figures 1-3. Spectral data."
      example_after: "**Figures 1-3.** Spectral data."
      why: "Plural figure-range label prefix is also bolded; plural form used in combined captions."
---

# Chemistry formatting catalog

Frontmatter is source of truth. Rationale for individual decisions lives in
`docs/superpowers/specs/2026-05-14-cycle-08-revising-design.md` (D6, D7, D11)
and `claude_memory/feedback_docx_typography.md`.

## How to use this file

`scripts/sws_apply_chemistry_format.py` reads the `categories` block from the
YAML frontmatter. For each paragraph in a `.docx` file it scans runs against
each `pattern`; when a pattern matches it applies the formatting named in
`apply` (italic, subscript, superscript, or bold).

`severity: auto` patterns are applied unconditionally. `severity: suggest`
patterns are only reported unless the caller passes `--severity all`.

This catalog applies **only** when `format: docx` is set in the project marker.
When `format: latex` the script exits 0 with a no-op message (D7).

## Categories

| Category | n patterns | Severity mix |
|---|---|---|
| `latin_abbreviations` | 8 | all auto |
| `chemical_formulae` | 7 | 6 auto, 1 suggest |
| `species_names` | 6 | all suggest |
| `species_abbreviated` | 6 | all auto |
| `gene_names` | 6 | 4 suggest, 2 auto |
| `figure_label_prefix` | 6 | all auto |

Totals: 39 patterns. `species_names` and `gene_names` are suggest-only because
of high false-positive risk (person names, acronyms). All other categories are
auto where the pattern is unambiguous in scientific prose.
