---
name: Journal-style overlay
about: Submit an overlay for a journal SWS doesn't yet support
title: "[overlay] <Journal Name>"
labels: journal-style-overlay
---

**Journal**

**Publisher**

**Author guidelines URL**

**Date guidelines were checked** (YYYY-MM-DD)

**Overlay frontmatter**

Fill in the values from the journal's current author guidelines:

```yaml
---
journal_slug:                       # lowercase, no spaces (e.g. chembiochem)
inherits:                           # one of the 9 v0.1 profiles (see profiles/ — full-article, communication, perspective, review-paper, mini-review, editorial, methodological-paper, commentary-reply, funding-proposal)
word_total:                         # integer or null
ref_cap:                            # integer or null
abstract_style:                     # structured | unstructured | graphical | null
figures_max:                        # integer or null
tables_max:                         # integer or null
sections:                           # ordered list of expected section names
disclosure_required:                # true | false
latex_class: null                   # path to journal .cls if applicable, else null
---
```

**Overlay body**

Tone, citation style, special conventions (compound numbering, figure aspect ratios, supporting-information policy, etc.).

**Verification**

- [ ] Values pulled directly from the journal's current author guidelines (URL above).
- [ ] No additional fields needed beyond the schema. (List any below — useful signal for v0.2+ schema extensions.)

**Additional fields the schema might be missing** (optional)
