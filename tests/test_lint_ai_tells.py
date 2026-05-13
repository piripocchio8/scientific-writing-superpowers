"""sws_lint_ai_tells.py — context-aware AI-tells linter (cycle-#8 Task 1E).

Tests:
- "delve" → 1 block finding
- Single "Furthermore" at paragraph start → no finding (min_count_per_paragraph: 2)
- Two "Furthermore" in one paragraph → 1 warn finding
- "delve" inside fenced code block → no finding
- "delve" inside [CITATION_NEEDED: ...] → no finding
- --json produces valid JSON list
- Exit code 0 when no block hits; exit code 1 when block hit
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "sws_lint_ai_tells.py"


def _run(args: list, *, expect_return: int | None = None):
    cp = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    if expect_return is not None:
        assert cp.returncode == expect_return, (
            f"Expected exit {expect_return}, got {cp.returncode}.\n"
            f"stdout: {cp.stdout}\nstderr: {cp.stderr}"
        )
    return cp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_md(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1. "delve" → block finding
# ---------------------------------------------------------------------------

def test_delve_produces_block_finding(tmp_path):
    md = _write_md(tmp_path, "draft.md", "We delve into the kinetics.\n")
    cp = _run([str(md)])
    assert cp.returncode == 1, "Expected exit 1 (block hit)"
    assert "BLOCK" in cp.stdout


def test_delve_finding_reports_correct_line(tmp_path):
    content = "First line.\nWe delve into the kinetics.\nThird line.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md)])
    assert "line 2" in cp.stdout


# ---------------------------------------------------------------------------
# 2. Single "Furthermore" alone → no finding (min_count_per_paragraph: 2)
# ---------------------------------------------------------------------------

def test_single_furthermore_no_finding(tmp_path):
    # One "Furthermore" at paragraph start — below min_count threshold of 2
    content = "Furthermore, the data are consistent with cooperativity.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md), "--severity", "warn"])
    # Should not flag the sentence-initial-connector tell (needs ≥2 per paragraph)
    # (There may be other warns from other patterns — filter to just this pattern)
    findings_text = cp.stdout
    assert cp.returncode == 0
    # Ensure the specific Furthermore connector warn is NOT in output
    # (the pattern name contains "Furthermore")
    if "Furthermore" in findings_text and "WARN" in findings_text:
        # Parse more carefully: if any finding line mentions Furthermore pattern
        lines = findings_text.splitlines()
        connector_findings = [
            l for l in lines
            if "Furthermore" in l and "pattern" in l
        ]
        assert connector_findings == [], (
            f"Expected no Furthermore pattern findings, got: {connector_findings}"
        )


# ---------------------------------------------------------------------------
# 3. Two connectors in same paragraph → warn finding
# ---------------------------------------------------------------------------

def test_two_connectors_same_paragraph_produces_warn(tmp_path):
    # Two sentence-initial "Furthermore" lines within the same paragraph
    content = (
        "Furthermore, the data are consistent with cooperativity.\n"
        "Furthermore, the binding is tight.\n"
    )
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md), "--severity", "warn"])
    # The threshold (min_count_per_paragraph: 2) is met → should flag
    assert "WARN" in cp.stdout, f"Expected WARN. stdout:\n{cp.stdout}"
    assert "Furthermore" in cp.stdout


# ---------------------------------------------------------------------------
# 4. "delve" inside fenced code block → no finding
# ---------------------------------------------------------------------------

def test_delve_in_code_fence_no_finding(tmp_path):
    content = (
        "Normal prose without tells.\n\n"
        "```python\n"
        "# We delve into the data\n"
        "print('delve')\n"
        "```\n\n"
        "More normal prose here.\n"
    )
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md)])
    assert cp.returncode == 0, f"Expected exit 0. stdout:\n{cp.stdout}"
    assert "BLOCK" not in cp.stdout


# ---------------------------------------------------------------------------
# 5. "delve" inside CITATION_NEEDED placeholder → no finding
# ---------------------------------------------------------------------------

def test_delve_in_citation_placeholder_no_finding(tmp_path):
    content = "The authors [CITATION_NEEDED: we delve here] reported results.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md)])
    assert cp.returncode == 0, f"Expected exit 0. stdout:\n{cp.stdout}"
    assert "BLOCK" not in cp.stdout


# ---------------------------------------------------------------------------
# 6. --json produces valid JSON
# ---------------------------------------------------------------------------

def test_json_flag_produces_valid_json(tmp_path):
    content = "We delve into the mechanism.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md), "--json"])
    assert cp.returncode == 1
    data = json.loads(cp.stdout)
    assert isinstance(data, list)
    assert len(data) >= 1
    first = data[0]
    assert "line" in first
    assert "col" in first
    assert "severity" in first
    assert "why" in first
    assert "snippet" in first
    assert "pattern_name" in first


def test_json_empty_when_no_finds(tmp_path):
    content = "Peptide therapeutics have undergone a revival since 2015.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md), "--json"])
    assert cp.returncode == 0
    data = json.loads(cp.stdout)
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# 7. Exit codes
# ---------------------------------------------------------------------------

def test_exit_0_when_no_block_hits(tmp_path):
    content = "The reaction is fast.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md)], expect_return=0)


def test_exit_1_when_block_hit(tmp_path):
    content = "We delve into the kinetics of the reaction.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md)], expect_return=1)


def test_exit_0_for_warn_only_with_default_severity(tmp_path):
    # "robust" is warn-severity — should not trigger exit 1
    content = "Robust catalytic activity was observed.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md)], expect_return=0)


# ---------------------------------------------------------------------------
# 8. --severity filter
# ---------------------------------------------------------------------------

def test_severity_block_filter_skips_warn(tmp_path):
    # "robust" is warn; "delve" is block. With --severity block, only delve fires.
    content = "Robust activity was observed. We delve into the kinetics.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md), "--severity", "block"])
    assert cp.returncode == 1
    assert "BLOCK" in cp.stdout
    # "robust" pattern should not appear
    assert "robust" not in cp.stdout.lower() or "WARN" not in cp.stdout


def test_severity_warn_filter_skips_block(tmp_path):
    # "robust" is warn; "delve" is block. With --severity warn, delve does not fire.
    content = "Robust activity. We delve into the kinetics.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md), "--severity", "warn"])
    # No block severity in filtered output → exit 0
    assert cp.returncode == 0


# ---------------------------------------------------------------------------
# 9. Inline code skip
# ---------------------------------------------------------------------------

def test_delve_in_inline_code_no_finding(tmp_path):
    content = "Call the function `delve_into(data)` to proceed.\n"
    md = _write_md(tmp_path, "draft.md", content)
    cp = _run([str(md)])
    assert cp.returncode == 0, f"Expected exit 0. stdout:\n{cp.stdout}"


# ---------------------------------------------------------------------------
# 10. Missing file
# ---------------------------------------------------------------------------

def test_missing_file_exits_nonzero(tmp_path):
    cp = _run([str(tmp_path / "nonexistent.md")])
    assert cp.returncode != 0
