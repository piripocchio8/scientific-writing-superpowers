---
name: humanize
description: "This skill should be used when the user invokes /sws:humanize <file>, says 'humanize this draft', 'strip AI-tells from <file>', 'make this read less like ChatGPT' — and the cwd is an SWS project. Dispatches the humanizer agent (Haiku 4.5) on a single markdown file. The agent runs sws_lint_ai_tells.py to identify block-severity AI tells, then rewrites flagged constructions while preserving meaning, chemistry formulae, and citation keys. Output: <file-without-extension>-humanized.md alongside the input."
version: 0.1.0
---

# /sws:humanize — Strip AI-writing tells from a draft

# Adapted from https://github.com/matsuikentaro1/humanizer_academic (MIT). matsuikentaro1's `humanizer_academic` skill is the canonical prior-art pattern for this task; SWS adapts the same approach as a standalone skill that dispatches the SWS `humanizer` agent.

Dispatches the `humanizer` agent on one markdown file. The agent uses `sws_lint_ai_tells.py` for detection (block-severity tells must be rewritten; warn-severity tells are judgment calls). Output preserves chemistry formulae (`H2O`, `Ca2+` stay plain ASCII — style-enforcer formats them later) and citation keys (`[Smith2023; doi:...]` and `[CITATION_NEEDED: ...]` placeholders are not edited).

## Steps

1. **Resolve `$PAPER_ROOT`.** Marker check. If absent, print "not an SWS project (no .sws-project.local.md found)" and exit.
2. **Validate input.** The first positional argument is the markdown file. If missing or not a `.md` file, print usage and exit. Resolve to an absolute path.
3. **Dispatch `humanizer`** via the Task tool. Pass `PAPER_ROOT`, `CLAUDE_PLUGIN_ROOT`, and the file path. The agent:
   - Runs `sws_lint_ai_tells.py <file> --json` to enumerate findings.
   - Rewrites every block-severity span; judges warn-severity case-by-case.
   - Re-runs the linter on its output. Loops until exit 0.
   - Writes `<file-stem>-humanized.md` next to the input.
4. **Print summary:** input path, output path, findings caught (block + warn), and rewrites applied.

## When to invoke

- Explicit `/sws:humanize <file.md>`.
- User says "humanize this", "strip the AI tells from <file>", "make this read less like an LLM".
- Useful as a standalone post-pass on any markdown draft (Intro, Discussion, response-to-reviewers letter, cover letter) without running the whole `/sws:revise-paper` pipeline.

Do NOT invoke when:
- The marker is missing.
- The argument is a `.docx` (style-enforcer territory) or `.xlsx`.
- The user wants the full revision chain (use `/sws:revise-paper` instead — that already includes the humanizer pass).

## Routing note

Inside `/sws:revise-paper` and `/sws:revise-section`, the humanizer runs automatically after `reviser-*`. This standalone skill is for the case where the user wants only the AI-tells cleanup pass without first running a reviser — e.g., on hand-written prose that the user just wants tightened up.
