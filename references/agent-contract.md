# SWS agent contract

All SWS agents (cycle #7 onward) follow this contract. Agent files reference this document instead of duplicating the rules. Future agents (cycles #8 through #11) inherit the same rules; this is the single source of truth.

## Required first action

Every agent's prompt opens with:

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh" <agent-id>
"${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh" <agent-id> || exit 0
```

`agent_prelude.sh` exports `RESOLVED_OK`, `RESOLVED_PROFILE_SET`, `RESOLVED_PROFILE_ID`, plus per-field `RESOLVED_*` variables (e.g. `RESOLVED_WORD_TOTAL`, `RESOLVED_REF_CAP`, `RESOLVED_FIGURES_MAX`, `RESOLVED_ABSTRACT_STYLE`).

`agent_should_run.sh` exits 0 if the agent is allowed to run for the resolved profile, non-zero otherwise. Agents silently exit on the non-zero case (no banner, no chatter — the dispatching skill handles the user-facing message).

## Five cross-cutting rules

### R1 — Python frugality

Reuse `<paper>/.venv/`. Do NOT install new pip packages unless the task genuinely requires them. The default deps in `requirements/sws-deps.txt` cover YAML (PyYAML), DOCX (python-docx), PDF (pypdf), XML (lxml), Excel (openpyxl), and pytest. If a new dependency is unavoidable, raise it in the user-facing reply rather than silently `pip install`ing.

### R2 — Filesystem frugality

Prefer `scripts/sws_fs_index.py` (the project manifest) and the `Explore` tool over `Bash`/`ls`/`find`. Reach for shell only when no alternative exists. Long sessions burn tokens on repeated directory walks; the fs-index utility (cycle #1) was built specifically to avoid that. When you need a single file path you already know, use `Read` directly — do not list its parent first.

### R3 — Built-in skill preference

Use Claude's native PDF reading, DOCX reading, and image viewing for: paper figures, manuscript PNG/TIF/JPEG/SVG files, PDF figures, and full PDF/DOCX documents. Do NOT spawn external Python parsers (python-docx, pdfplumber, PIL) when a built-in skill suffices. The built-ins are token-efficient and require no per-paper dependency installation. R1 reinforces this — fewer parsers = fewer pip installs.

### R4 — Token discipline

Concise thinking. Concise user-facing chatter. Avoid restating the request, narrating which file you are about to read, or summarizing what you just did when the file path itself is the deliverable.

**DRAFTED PROSE IS EXEMPT.** The user controls voice and length via `_voice/` profiles and the resolved profile/overlay word targets. Drafted Intro/Discussion/Conclusion/Methods/Results prose, AI-tells reference content, and source-snapshot extracts are written at the length the spec demands — token discipline applies to the agent's *narration around* the work, not to the work itself.

### R5 — No gender-default in user address

Before adopting any pronoun, honorific, or gendered descriptor when addressing or referring to the user, read the user's memory/profile (e.g. `$HOME/.claude/projects/<project>/memory/user_*.md`). If pronouns are unknown, use the user's first name or neutral phrasing ("you", "the user"). Do NOT guess.

This applies recursively: any prose your agent generates that is shown to the user inherits the same rule. Drafted manuscript prose typically has no occasion to address the user; user-facing reply text and budget Q&A prompts do.

## AI-writing-tells avoidance

Before returning drafted prose, every drafting agent greps the output against `references/ai-writing-tells.md` patterns. Block-severity hits abort the response with a fix suggestion; warn-severity hits get flagged in the agent's reply ("warn: pattern X matched, consider rephrasing").

The reference doc is structured by category (lexical, syntactic, structural, hedging, transitions). Each tell ships with a regex pattern, severity, an example_bad sentence, an example_fix, and a one-line `why`. The grep-pass is mechanical — no LLM judgment in the loop. Cycle #8's reviser will gain a smarter linter once we have false-positive data.

## Attribution pattern (for adapted prompts)

Agent files whose prompts are adapted from MIT-licensed prior art carry a one-line header above the YAML frontmatter:

```
# Adapted from <plugin-url> (MIT)
```

Survey targets: `andrehuang/academic-writing-agents`, `Imbad0202/academic-research-skills`. The roster (agent names, scopes, models) is original to SWS; only prompt content adapts. If adaptation is below ~30% of the prompt body, the header is not added — the agent counts as fresh-write with prior-art inspiration only.

## Agent file template

Every cycle-#7 (and onward) agent file follows this shape:

```yaml
---
name: <agent-id>
description: <one-line trigger description>
model: <claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5>
color: <pick from existing palette>
---

# Adapted from <plugin-url> (MIT)   # only if applicable

<Agent-specific 5-10 line prompt focused on the agent's narrow job. Reference RESOLVED_* env vars, file paths, and behaviors specific to this agent's scope. Include a misroute safety net for drafting agents.>

Follow the SWS agent contract: source ${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh <agent-id>, then ${CLAUDE_PLUGIN_ROOT}/scripts/agent_should_run.sh <agent-id> || exit 0. See ${CLAUDE_PLUGIN_ROOT}/references/agent-contract.md for the full contract.
```

The agent file stays under ~30 lines. Cross-cutting rules live here, not in the agent file. Future fixes touch this contract document, not seven agent files.
