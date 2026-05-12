---
sws_artifact: docx-style
artifact_version: 0.1
locked: 2026-05-08
sources:
  - claude_memory/feedback_docx_typography.md (canonical rationale + slot semantics)
  - docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md (custom_typography section)

styles:
  SWS-Body:        { font: Arial, size: 12, bold: false, italic: false }
  SWS-H1:          { font: Arial, size: 12, bold: true,  italic: false }   # top-level sections
  SWS-H2:          { font: Arial, size: 12, bold: true,  italic: true  }   # sub-sections within Results
  SWS-Caption:     { font: Arial, size: 10, bold: false, italic: false }   # figure + table captions
  SWS-References:  { font: Arial, size: 10, bold: false, italic: false }   # reference list

forbidden_word_styles: [Heading 1, Heading 2, Heading 3, Title, Subtitle]

slot_assignments_locked:
  top_level_sections: SWS-H1   # Intro, Results, Discussion, Experimental, Acknowledgments, References
  results_subsections: SWS-H2  # e.g. Synthesis, Spectroscopic characterization, Catalytic activity
  body_text: SWS-Body
  figure_captions: SWS-Caption
  table_captions: SWS-Caption
  reference_list_entries: SWS-References

slot_assignments_TBD:
  - Title
  - Author block
  - Abstract
  - Keyword block
  - Footnote
  - Equation numbering
  - Bullet/Numbered list items
  - Table-cell text

scope:
  applies_to: docx (format=docx in marker)
  exempt: latex (journal .cls owns typography; SWS does not override)

consumers:
  cycle_1: none
  cycle_2: this file ships; init-project does NOT apply styles to existing manuscripts (style normalization is style-enforcer's job in cycle #6)
  cycle_5_onward: drafter, style-enforcer, format-checker, table-formatter, equation-handler, figure-caption-writer
---

# SWS docx typography canon

Frontmatter is the source of truth. Rationale: `claude_memory/feedback_docx_typography.md`.

Custom named styles only. Word's built-in `Heading 1` / `Heading 2` / `Title` / `Subtitle` styles are visually ugly and trigger TOC-field generation the user doesn't want.

`slot_assignments_TBD` resolved as the drafter (cycle #5) needs each slot. Add new slots by extending `styles` and `slot_assignments_locked`; never embed style fields in agent prompts directly.
