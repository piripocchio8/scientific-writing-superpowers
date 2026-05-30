---
sws_artifact: submission-artifacts
artifact_version: 0.1
locked: 2026-05-30
used_by:
  - agents/cover-letter-writer.md
  - agents/response-to-reviewers.md
  - scripts/sws_disclosure_writer.py
  - scripts/sws_response_matrix.py
  - skills/write-cover-letter/SKILL.md
  - skills/respond-to-reviewers/SKILL.md
  - skills/disclose-ai-usage/SKILL.md

folder_schemas:
  _review/round-<N>/:
    reviewer-comments.md: USER-PROVIDED (or pasted from journal email/portal); markdown
    response-matrix.json: sws_response_matrix.py output; deterministic parse
    response-to-reviewers.md: response-to-reviewers agent output
    edits-summary.md: optional agent-generated edit log
  _submission/:
    cover-letter.md: cover-letter-writer agent output
    ai-disclosure.md: sws_disclosure_writer.py output
    response-to-reviewers-round-<N>.md: copy of _review/round-<N>/response-to-reviewers.md for journal upload

reviewer_comments_accepted_shapes:
  shape_a:
    description: "Per-reviewer headings with numbered/bulleted comments"
    example: |
      ## Reviewer 1
      1. The novelty claim in the abstract overreaches.
      2. Figure 3 lacks error bars.
      ## Reviewer 2
      - Methodology is sound but Section 4.2 needs clarification.
  shape_b:
    description: "Flat numbered list (single implicit reviewer)"
    example: |
      1. The introduction misses ref. X.
      2. Equation 3 needs derivation.
  shape_c:
    description: "Prefixed ID per Imbad0202 convention"
    example: |
      R1.1: The novelty claim overreaches.
      R1.2: Figure 3 lacks error bars.
      R2.1: Section 4.2 needs clarification.

response_matrix_schema:
  type: list of comment objects
  comment_fields:
    id: "R<reviewer>.<comment>; e.g. R1.2"
    reviewer: int
    text: string (verbatim reviewer comment)
    severity_inferred: enum [major, minor, suggestion]; inferred from keywords
    status: enum [pending, accepted, partial, rejected]; default pending
    response_text: string; agent fills
    edits_made: list of strings (each entry: section + edit description); agent fills
    line_refs: list of "file:line" pointers into _drafts/ or final .docx; agent fills

disclosure_templates:
  icmje:
    body_template: |
      The author(s) used generative AI tools (Anthropic Claude via the Scientific Writing Superpowers
      plugin) to assist with manuscript preparation. All scientific claims, data interpretations, and
      conclusions are the author's own, and the author takes full responsibility for the manuscript's
      content. AI-assisted writing was used for {USE_CATEGORIES}; all AI output was reviewed and revised
      by the author.
    use_categories_options: [drafting prose, copyediting, formatting references, generating figure captions, summarising prior work]
    policy_url: "https://www.icmje.org/recommendations/"
    last_verified: "2026-05-30"
  wiley:
    body_template: |
      Generative AI tools (Anthropic Claude via the Scientific Writing Superpowers plugin) were used to
      assist with {USE_CATEGORIES}. The author(s) reviewed and edited all AI-generated content and take
      full responsibility for the integrity of the manuscript. AI was not used to generate or interpret
      scientific data, nor is it listed as a co-author. This statement is provided in accordance with
      Wiley's Best Practice Guidelines on Research Integrity and Publishing Ethics.
    use_categories_options: [language polishing, structural drafting, reference formatting, caption generation]
    policy_url: "https://authorservices.wiley.com/author-resources/Journal-Authors/open-access/best-practice-guidelines-on-research-integrity-and-publishing-ethics.html"
    last_verified: "2026-05-30"
  rsc:
    body_template: |
      The author(s) declare the use of generative AI (Anthropic Claude via the Scientific Writing
      Superpowers plugin) in the preparation of this manuscript, limited to {USE_CATEGORIES}. The AI was
      not used for scientific reasoning, data analysis, or to make decisions about study design. All
      AI-assisted text was carefully reviewed, fact-checked, and revised by the author(s), who take full
      responsibility for the manuscript's content. This disclosure is provided per RSC's policy on
      generative AI in scholarly publishing.
    use_categories_options: [draft prose generation, language editing, reference formatting, figure caption drafting]
    policy_url: "https://www.rsc.org/journals-books-databases/journal-authors-reviewers/policies/"
    last_verified: "2026-05-30"
  acs:
    body_template: |
      The author(s) used generative AI (Anthropic Claude through the Scientific Writing Superpowers
      plugin) to assist with {USE_CATEGORIES} in this manuscript. All AI-assisted content was reviewed
      and edited by the author(s). The AI was not used to generate, analyse, or interpret experimental
      data, and is not listed as an author. The author(s) accept full responsibility for the manuscript
      in accordance with ACS Publishing Ethics.
    use_categories_options: [drafting prose, polishing language, formatting references, generating captions]
    policy_url: "https://pubs.acs.org/page/policy/authoring/index.html"
    last_verified: "2026-05-30"

cover_letter_canonical_structure:
  - opening_address: "Dear {EDITOR_NAME or 'Editor'}, (per D11 — never fabricate editor name)"
  - opening_paragraph: one-sentence submission statement + manuscript title + manuscript type
  - significance_paragraph: 3-5 sentences on the scientific significance and novelty (no superlatives, no AI-tells)
  - fit_paragraph: 2-3 sentences explaining fit with the journal's scope
  - conflict_disclosure: brief statement on no conflicts (or list)
  - suggested_editors: optional — only if the journal overlay lists suggested_handling_editors
  - signoff: "Sincerely, {AUTHOR_NAME or '[Author Name]'}"

cover_letter_constraints:
  - max_word_count: 400
  - never_fabricate: [editor_name, journal_editor_history, prior_paper_references]
  - tone: measured, evidence-led; no superlatives ("groundbreaking", "novel" etc.)
  - must_grep_pass: scripts/sws_lint_ai_tells.py
---

# Submission Artifacts (v0.1)

This body is orientation only; **the frontmatter dictionary above is the source of truth** for folder schemas, accepted reviewer-comment shapes, the response matrix schema, the 4 disclosure templates, and the cover-letter structure.

## What this doc anchors

Three submission outputs, produced by cycle-12 agents and scripts:

1. **Cover letter** (`_submission/cover-letter.md`) — venue-specific, generated by `cover-letter-writer` from the resolved journal-style overlay + the paper's abstract + the profile.
2. **AI-usage disclosure** (`_submission/ai-disclosure.md`) — venue-specific, generated by `sws_disclosure_writer.py` from a 4-template catalog (ICMJE / Wiley / RSC / ACS).
3. **Response-to-reviewers** (`_submission/response-to-reviewers-round-<N>.md`) — generated by `response-to-reviewers` agent from the user-provided `_review/round-<N>/reviewer-comments.md` + the R&R Traceability Matrix JSON (`_review/round-<N>/response-matrix.json`) that `sws_response_matrix.py` builds deterministically.

## Folder layout

`_review/round-<N>/` lives alongside the cycle-09 `_review/<agent>/` outputs and never collides (agent folders use known agent names, never starting with "round-").

`_submission/` is new in cycle-12 and is reserved for journal-upload-ready artifacts.

## Disclosure-template selection

The journal-style overlay's `disclosure.template_id` field selects the template. v0.1 ships 4 templates; missing template_id falls back to "icmje" with a TODO. v0.2 expands the catalog.
