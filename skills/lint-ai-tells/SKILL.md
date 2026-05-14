---
name: lint-ai-tells
description: "This skill should be used when the user invokes /sws:lint-ai-tells <file.md>, says 'check this file for AI tells', 'run the ai-tells linter', 'lint for AI writing patterns' — and a markdown file path is supplied. No agent dispatch — shells out directly to scripts/sws_lint_ai_tells.py. Severity filter and JSON output available via flags."
version: 0.1.0
---

# /sws:lint-ai-tells — AI-tells linter (script only)

Shells out directly to `scripts/sws_lint_ai_tells.py`. No agent is dispatched. The script reads `references/ai-writing-tells.md` (cycle-#7 catalog) and applies three context-aware rules before flagging a hit (D8, D20).

## Arguments

```
/sws:lint-ai-tells <file.md> [--severity block|warn|all] [--json]
```

- `<file.md>` — required. Path to the markdown file to lint.
- `--severity block|warn|all` — filter output by severity. Default: `all`.
- `--json` — emit findings as JSON (for agent consumption or CI). Default: human-readable.

## Context rules (D8)

The linter applies three refinements on top of a raw pattern match before emitting a finding:

1. **Paragraph-count gating.** For tells with a `linter_rule: min_count_per_paragraph: N` field in the catalog frontmatter, the linter flags only when the pattern fires ≥ N times within the same paragraph. Example: em-dash overuse fires only when ≥ 3 em-dashes appear in one paragraph.
2. **Code-fence skip.** Text inside triple-backtick fences and inline `` `code` `` spans is excluded from matching.
3. **Citation-placeholder skip.** Text inside `[CITATION_NEEDED: ...]` placeholders is excluded (placeholder content is metadata, not prose).

The `linter_rule:` field is optional in `references/ai-writing-tells.md`. Tells without it behave as plain pattern matches (identical to the cycle-#7 grep-pass). Full rule documentation: `scripts/sws_lint_ai_tells.py --help`.

## Exit codes

- `0` — no block-severity findings.
- `1` — at least one block-severity finding.

## How the skill runs it

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
    sws_lint_ai_tells.py <file.md> [--severity ...] [--json]
```

The skill does not gate `/sws:enforce-style` or any other pipeline step on the linter exit code. The linter is informational when invoked standalone. Inside `/sws:revise-paper`, the humanizer agent reads linter output to resolve flagged tells via rewrite.

## When to invoke

- Explicit `/sws:lint-ai-tells <file.md>`.
- User says "check this for AI tells", "lint the intro", "run the ai-tells linter on results.md".

Do NOT invoke when no file path is provided or the file does not exist.
