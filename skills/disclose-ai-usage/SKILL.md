---
name: disclose-ai-usage
description: |
  Render a venue-specific AI-usage disclosure to _submission/ai-disclosure.md
  from one of four built-in templates (ICMJE / Wiley / RSC / ACS). Template
  selection follows the journal overlay's disclosure.template_id (ICMJE
  fallback on miss). Gated on RESOLVED_DISCLOSURE_REQUIRED. Accepts --venue
  override (D18) and --use-categories CSV. Deterministic — no agent dispatch,
  no LLM call.
allowed-tools: Bash, Read, Write, Glob
---

# /sws:disclose-ai-usage

Produce the journal's required AI-usage statement.

## Usage

```
/sws:disclose-ai-usage                                  # use marker target_journal
/sws:disclose-ai-usage --venue chembiochem              # override (D18)
/sws:disclose-ai-usage --use-categories "drafting prose, polishing language"
```

## Steps

1. Verify `${PAPER_ROOT}/.sws-project.local.md` exists.
2. Source `${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh disclose-ai-usage`
   to populate `RESOLVED_DISCLOSURE_REQUIRED`.
3. If `RESOLVED_DISCLOSURE_REQUIRED` is not `true`, exit cleanly with:
   "Disclosure not required for the active profile."
4. Parse optional flags: `--venue <slug>` and
   `--use-categories "a,b,c"`.
5. Invoke the deterministic renderer:
   ```
   ${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh "$PAPER_ROOT" \
       ${CLAUDE_PLUGIN_ROOT}/scripts/sws_disclosure_writer.py \
       --paper-root "$PAPER_ROOT" \
       [--venue <slug>] [--use-categories "<csv>"]
   ```
6. The script writes `${PAPER_ROOT}/_submission/ai-disclosure.md` atomically
   and prints the template's `last_verified` date to stderr (R6).
7. Point the user at the output path; remind them to re-check the policy URL
   if `last_verified` is more than 6 months old.

## V0.1 catalogue

Four templates ship with the plugin:

| template_id | publisher coverage           | last_verified |
|-------------|------------------------------|---------------|
| icmje       | clinical / biomedical (default) | 2026-05-30 |
| wiley       | Wiley journals               | 2026-05-30 |
| rsc         | Royal Society of Chemistry   | 2026-05-30 |
| acs         | American Chemical Society    | 2026-05-30 |

Other publishers can drop in via journal-overlay's `disclosure.template_id`
once a body is added to `references/submission-artifacts.md`.

## Spec source of truth

`docs/superpowers/specs/2026-05-30-cycle-12-submission-orchestration-design.md`
— D7, D18, R6.
