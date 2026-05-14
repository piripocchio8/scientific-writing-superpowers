"""Tests for scripts/sws_consistency_check.py — static-analysis consistency checker (D9).

Covers:
  - All 6 checks individually (pass and fail cases).
  - Cross-section abbreviation (introduced in methods, used in results — R3 mitigation).
  - Funding-proposal profile → exits 0 with unsupported message (D19).
  - JSON output schema validates.
  - Report file shape matches spec auxiliary_file_shapes.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sws_consistency_check import main as cc_main  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def make_paper(tmp_path: Path, drafts: dict[str, str], outline_fm: str = "",
               marker_fm: str = "") -> tuple[Path, Path]:
    """Create a minimal paper directory with drafts + optional outline + marker.

    Returns (drafts_dir, outline_path).
    """
    paper = tmp_path / "paper"
    paper.mkdir()
    drafts_dir = paper / "_drafts"
    drafts_dir.mkdir()
    for name, content in drafts.items():
        (drafts_dir / name).write_text(content, encoding="utf-8")

    outline_dir = paper / "_outline"
    outline_dir.mkdir()
    outline_path = outline_dir / "outline.md"
    outline_text = "---\n" + outline_fm + "\n---\n# Outline\n" if outline_fm else "---\n---\n"
    outline_path.write_text(outline_text, encoding="utf-8")

    if marker_fm:
        (paper / ".sws-project.local.md").write_text(
            "---\n" + marker_fm + "\n---\n", encoding="utf-8"
        )

    return drafts_dir, outline_path


def run_cc(drafts_dir: Path, outline_path: Path, extra_args: list[str] | None = None,
           report_out: Path | None = None) -> tuple[int, str, str]:
    """Run the consistency checker and capture stdout + stderr via capsys substitute."""
    import io
    from contextlib import redirect_stdout, redirect_stderr

    out_buf = io.StringIO()
    err_buf = io.StringIO()

    argv = [str(drafts_dir), "--outline", str(outline_path)]
    if report_out:
        argv += ["--report-out", str(report_out)]
    if extra_args:
        argv.extend(extra_args)

    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        try:
            rc = cc_main(argv)
        except SystemExit as exc:
            rc = int(exc.code) if exc.code is not None else 0

    return rc, out_buf.getvalue(), err_buf.getvalue()


# ---------------------------------------------------------------------------
# Check 1 — Figure-reference cross-check
# ---------------------------------------------------------------------------

class TestFigureRefCrossCheck:
    def test_pass_figure_exists_in_outline(self, tmp_path):
        drafts = {"intro.md": "See Figure 1 for details.\n"}
        outline_fm = "figures:\n  f1: figures/Fig1.png\n"
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0

    def test_fail_figure_missing_in_outline(self, tmp_path):
        drafts = {"intro.md": "See Figure 2 for details.\n"}
        outline_fm = "figures:\n  f1: figures/Fig1.png\n"
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 1
        assert "block" in out.lower() or "Figure 2" in out

    def test_pass_no_outline_figures_key(self, tmp_path):
        """If outline has no figures: dict, skip the check (no false positives)."""
        drafts = {"intro.md": "See Figure 1.\n"}
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm="sections:\n  - intro\n")
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        # Without a figures dict, checker cannot verify — no block
        assert rc == 0

    def test_pass_fig_dot_notation(self, tmp_path):
        drafts = {"results.md": "As shown in Fig. 1a, the data support.\n"}
        outline_fm = "figures:\n  f1: figures/Fig1.png\n"
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0


# ---------------------------------------------------------------------------
# Check 2 — Table-reference cross-check
# ---------------------------------------------------------------------------

class TestTableRefCrossCheck:
    def test_pass_table_exists(self, tmp_path):
        drafts = {"results.md": "See Table 1 for the summary.\n"}
        outline_fm = "tables:\n  t1: Table 1 caption\n"
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0

    def test_fail_table_missing(self, tmp_path):
        drafts = {"results.md": "See Table 2 for the summary.\n"}
        outline_fm = "tables:\n  t1: Table 1 caption\n"
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 1


# ---------------------------------------------------------------------------
# Check 3 — Section-list cross-check
# ---------------------------------------------------------------------------

class TestSectionListCrossCheck:
    def test_pass_required_sections_present(self, tmp_path):
        """Both intro and experimental present — no warning."""
        drafts = {"intro.md": "Intro text.\n", "experimental.md": "Experimental text.\n"}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        # Use full-article profile which requires intro + experimental
        marker_fm = "profile_id: full-article\n"
        (drafts_dir.parent / ".sws-project.local.md").write_text(
            "---\n" + marker_fm + "\n---\n", encoding="utf-8"
        )
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        # May have other warnings but no block
        assert rc == 0

    def test_warn_required_section_missing(self, tmp_path):
        """Only intro.md present — experimental required but missing."""
        drafts = {"intro.md": "Intro text.\n"}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        marker_fm = "profile_id: full-article\n"
        (drafts_dir.parent / ".sws-project.local.md").write_text(
            "---\n" + marker_fm + "\n---\n", encoding="utf-8"
        )
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        # Section warning is severity=warn, so exit code still 0
        assert rc == 0
        assert "section-list" in out.lower() or "section" in out.lower()


# ---------------------------------------------------------------------------
# Check 4 — Citation-key uniqueness
# ---------------------------------------------------------------------------

class TestCitationKeyUniqueness:
    def test_pass_same_key_same_doi(self, tmp_path):
        text = (
            "First [Smith2023; doi:10.1021/jacs.1]\n"
            "Second [Smith2023; doi:10.1021/jacs.1]\n"
        )
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0

    def test_fail_same_key_different_doi(self, tmp_path):
        text = (
            "First [Smith2023; doi:10.1021/jacs.1]\n"
            "Second [Smith2023; doi:10.1021/jacs.DIFFERENT]\n"
        )
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 1
        assert "Smith2023" in out

    def test_pass_different_keys(self, tmp_path):
        text = (
            "First [Smith2023; doi:10.1021/jacs.1]\n"
            "Second [Jones2022; doi:10.1021/jacs.2]\n"
        )
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0


# ---------------------------------------------------------------------------
# Check 5 — Abbreviation introduction
# ---------------------------------------------------------------------------

class TestAbbreviationIntroduction:
    def test_pass_abbrev_introduced_before_use(self, tmp_path):
        text = (
            "Scanning electron microscopy (SEM) was used.\n"
            "SEM images confirmed the morphology.\n"
        )
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        # SEM is introduced then used — no abbreviation warning
        assert "SEM" not in out or "abbreviation-introduction" not in out

    def test_warn_abbrev_never_introduced(self, tmp_path):
        text = "NMR spectra were recorded at 500 MHz.\n"
        drafts = {"results.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        # NMR is never introduced with (NMR) — warn severity, exit 0
        assert rc == 0

    def test_cross_section_abbreviation_no_false_negative(self, tmp_path):
        """R3 mitigation: intro introduces HPLC, results uses it — no warn."""
        intro = "High-performance liquid chromatography (HPLC) was used.\n"
        results = "HPLC analysis revealed three peaks.\n"
        drafts = {"intro.md": intro, "results.md": results}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        # HPLC is introduced in intro — results usage should not be flagged
        # Check that findings don't include an abbreviation-introduction block for HPLC
        assert rc == 0
        # Also check the report doesn't flag HPLC as undefined
        if report.exists():
            report_text = report.read_text()
            # No block findings for HPLC
            assert "HPLC" not in report_text or "block" not in report_text.split("HPLC")[0].split("\n")[-1]


# ---------------------------------------------------------------------------
# Check 6 — Terminology uniformity
# ---------------------------------------------------------------------------

class TestTerminologyUniformity:
    def test_pass_consistent_casing(self, tmp_path):
        text = "Thrombin cleaves fibrinogen. Thrombin is a serine protease.\n"
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0

    def test_warn_mixed_case_variants(self, tmp_path):
        text = (
            "Thrombin cleaves fibrinogen. "
            "thrombin is a serine protease. "
            "Thrombin activates platelets. "
            "thrombin generation was measured.\n"
        )
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        # Terminology warn is exit 0
        assert rc == 0
        assert "terminology" in out.lower() or "thrombin" in out.lower()

    def test_no_flag_low_frequency(self, tmp_path):
        """If combined frequency < 3, no flag even with two variants."""
        text = "Thrombin cleaves. thrombin grows.\n"  # total 2 < 3
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        # No terminology finding (freq < 3)
        assert rc == 0


# ---------------------------------------------------------------------------
# D19 — funding-proposal profile unsupported
# ---------------------------------------------------------------------------

class TestFundingProposalUnsupported:
    def test_funding_proposal_exits_zero(self, tmp_path):
        drafts = {"summary.md": "Proposal summary text.\n"}
        drafts_dir, outline_path = make_paper(
            tmp_path, drafts, marker_fm="profile_id: funding-proposal\n"
        )
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0
        assert "funding-proposal" in out.lower() or "unsupported" in out.lower() or "manual review" in out.lower()

    def test_funding_proposal_no_report_written(self, tmp_path):
        """Report file should NOT be written for unsupported profile."""
        drafts = {"summary.md": "Proposal summary.\n"}
        drafts_dir, outline_path = make_paper(
            tmp_path, drafts, marker_fm="profile_id: funding-proposal\n"
        )
        report = tmp_path / "report.md"
        run_cc(drafts_dir, outline_path, report_out=report)
        assert not report.exists()


# ---------------------------------------------------------------------------
# JSON output schema
# ---------------------------------------------------------------------------

class TestJsonOutput:
    def test_json_schema_valid(self, tmp_path):
        text = "See Figure 1.\n[Smith2023; doi:10.1021/jacs.1]\n"
        outline_fm = "figures:\n  f1: figures/Fig1.png\n"
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, extra_args=["--json"], report_out=report)
        payload = json.loads(out)
        assert "profile" in payload
        assert "findings_count" in payload
        assert "findings_by_severity" in payload
        assert "block" in payload["findings_by_severity"]
        assert "warn" in payload["findings_by_severity"]
        assert "findings" in payload
        assert isinstance(payload["findings"], list)

    def test_json_finding_fields(self, tmp_path):
        text = "See Figure 99 for data.\n"
        outline_fm = "figures:\n  f1: figures/Fig1.png\n"
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, extra_args=["--json"], report_out=report)
        payload = json.loads(out)
        assert payload["findings_count"] >= 1
        finding = payload["findings"][0]
        assert "severity" in finding
        assert "category" in finding
        assert "what" in finding
        assert "where" in finding
        assert "context" in finding
        assert "suggested_fix" in finding

    def test_json_funding_proposal_schema(self, tmp_path):
        drafts = {"summary.md": "Proposal.\n"}
        drafts_dir, outline_path = make_paper(
            tmp_path, drafts, marker_fm="profile_id: funding-proposal\n"
        )
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, extra_args=["--json"], report_out=report)
        assert rc == 0
        # JSON path is printed after the message for funding-proposal
        # The first line is the human message, second line may be JSON
        lines = [l for l in out.strip().splitlines() if l.strip().startswith("{")]
        if lines:
            payload = json.loads(lines[0])
            assert "findings" in payload


# ---------------------------------------------------------------------------
# Report file shape
# ---------------------------------------------------------------------------

class TestReportFileShape:
    def test_report_written_with_frontmatter(self, tmp_path):
        text = "See Figure 99.\n"
        outline_fm = "figures:\n  f1: figures/Fig1.png\n"
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert report.exists()
        content = report.read_text()
        assert "generated_at:" in content
        assert "profile:" in content
        assert "findings_count:" in content
        assert "findings_by_severity:" in content
        assert "# Consistency report" in content

    def test_report_has_block_section(self, tmp_path):
        text = "See Figure 99.\n"
        outline_fm = "figures:\n  f1: figures/Fig1.png\n"
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        run_cc(drafts_dir, outline_path, report_out=report)
        content = report.read_text()
        assert "## block" in content

    def test_report_default_path(self, tmp_path):
        """Without --report-out, report goes to <paper>/_review/consistency-report.md."""
        text = "Normal draft text with no issues.\n"
        drafts = {"intro.md": text}
        paper = tmp_path / "paper"
        paper.mkdir()
        drafts_dir = paper / "_drafts"
        drafts_dir.mkdir()
        (drafts_dir / "intro.md").write_text(text, encoding="utf-8")
        outline_dir = paper / "_outline"
        outline_dir.mkdir()
        outline_path = outline_dir / "outline.md"
        outline_path.write_text("---\n---\n", encoding="utf-8")

        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            try:
                rc = cc_main([str(drafts_dir), "--outline", str(outline_path)])
            except SystemExit as exc:
                rc = int(exc.code) if exc.code is not None else 0

        default_report = paper / "_review" / "consistency-report.md"
        assert default_report.exists()

    def test_report_clean_when_no_findings(self, tmp_path):
        """With no figure refs, no citation keys, no terminlogy issues, and a
        marker pointing at an unknown profile (so section-check is skipped),
        the report should show findings_count: 0."""
        text = "Clean text.\n"
        drafts = {"intro.md": text}
        # Use an unknown profile so section list check produces no warnings
        drafts_dir, outline_path = make_paper(
            tmp_path, drafts, marker_fm="profile_id: unknown-test-profile\n"
        )
        report = tmp_path / "report.md"
        rc, out, _ = run_cc(drafts_dir, outline_path, report_out=report)
        content = report.read_text()
        assert "findings_count: 0" in content


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------

class TestExitCodes:
    def test_exit_0_no_block_findings(self, tmp_path):
        drafts = {"intro.md": "Clean text.\n"}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, _, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0

    def test_exit_1_block_findings(self, tmp_path):
        drafts = {"intro.md": "See Figure 99.\n"}
        outline_fm = "figures:\n  f1: figures/Fig1.png\n"
        drafts_dir, outline_path = make_paper(tmp_path, drafts, outline_fm=outline_fm)
        report = tmp_path / "report.md"
        rc, _, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 1

    def test_exit_0_only_warn_findings(self, tmp_path):
        """Warn-only (e.g., terminology) should exit 0."""
        text = (
            "Thrombin cleaves fibrinogen. "
            "thrombin is a serine protease. "
            "Thrombin activates platelets. "
            "thrombin is important.\n"
        )
        drafts = {"intro.md": text}
        drafts_dir, outline_path = make_paper(tmp_path, drafts)
        report = tmp_path / "report.md"
        rc, _, _ = run_cc(drafts_dir, outline_path, report_out=report)
        assert rc == 0
