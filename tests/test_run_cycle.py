"""Tests for sws_run_cycle.py — planner + dry-run + --only (cycle-12 D9 / D10 / D14)."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from sws_run_cycle import (  # noqa: E402
    STEP_NAMES, is_stale, main, plan_steps, render_dispatch_plan,
)


MARKER_TEMPLATE = """\
---
sws_version: 0.1
article_type: {article_type}
language: en
format: docx
target_journal: chembiochem
---

# test
"""


@contextmanager
def env(**overrides):
    backup = {}
    for k, v in overrides.items():
        backup[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    try:
        yield
    finally:
        for k, v in backup.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _make_paper(tmp, article_type="full-article"):
    paper = Path(tmp) / "paper"
    paper.mkdir()
    (paper / ".sws-project.local.md").write_text(MARKER_TEMPLATE.format(article_type=article_type))
    return paper


class PlannerStepsTests(unittest.TestCase):
    def test_empty_paper_plans_outline_draft_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                plan = plan_steps(paper)
        by_name = {s["name"]: s for s in plan}
        self.assertTrue(by_name["outline"]["should_run"])
        self.assertTrue(by_name["draft"]["should_run"])
        self.assertTrue(by_name["review"]["should_run"])
        # cover-letter required + no file => RUN
        self.assertTrue(by_name["cover-letter"]["should_run"])
        # disclosure required + no file => RUN
        self.assertTrue(by_name["disclosure"]["should_run"])
        # response: no rounds => SKIP
        self.assertFalse(by_name["response"]["should_run"])

    def test_idempotency_existing_outline_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            (paper / "outline.md").write_text("- abstract\n- intro\n")
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                plan = plan_steps(paper)
        by_name = {s["name"]: s for s in plan}
        self.assertFalse(by_name["outline"]["should_run"])

    def test_idempotency_existing_drafts_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            (paper / "_drafts").mkdir()
            (paper / "_drafts" / "intro.md").write_text("Intro draft text.\n")
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                plan = plan_steps(paper)
        by_name = {s["name"]: s for s in plan}
        self.assertFalse(by_name["draft"]["should_run"])

    def test_idempotency_review_done_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            for sub in ("peer-reviewer", "claim-verifier", "bibliography-fidelity-checker"):
                d = paper / "_review" / sub
                d.mkdir(parents=True)
                (d / "report.md").write_text("# report\n")
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                plan = plan_steps(paper)
        by_name = {s["name"]: s for s in plan}
        self.assertFalse(by_name["review"]["should_run"])

    def test_cover_letter_not_required_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, article_type="editorial")
            with env(RESOLVED_COVER_LETTER_REQUIRED="false",
                     RESOLVED_DISCLOSURE_REQUIRED="false"):
                plan = plan_steps(paper)
        by_name = {s["name"]: s for s in plan}
        self.assertFalse(by_name["cover-letter"]["should_run"])
        self.assertIn("not required", by_name["cover-letter"]["reason"])
        self.assertFalse(by_name["disclosure"]["should_run"])

    def test_cover_letter_skipped_when_inactive_in_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, article_type="funding-proposal")
            # funding-proposal has cover-letter-writer INACTIVE
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                plan = plan_steps(paper)
        by_name = {s["name"]: s for s in plan}
        self.assertFalse(by_name["cover-letter"]["should_run"])

    def test_response_run_when_reviewer_comments_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            rd = paper / "_review" / "round-1"
            rd.mkdir(parents=True)
            (rd / "reviewer-comments.md").write_text("## Reviewer 1\n1. comment\n")
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                plan = plan_steps(paper)
        by_name = {s["name"]: s for s in plan}
        self.assertTrue(by_name["response"]["should_run"])
        self.assertEqual(by_name["response"]["round"], 1)

    def test_response_skip_when_already_responded(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            rd = paper / "_review" / "round-1"
            rd.mkdir(parents=True)
            (rd / "reviewer-comments.md").write_text("## Reviewer 1\n1. comment\n")
            (rd / "response-to-reviewers.md").write_text("# response\n")
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                plan = plan_steps(paper)
        by_name = {s["name"]: s for s in plan}
        self.assertFalse(by_name["response"]["should_run"])


class StaleDetectionTests(unittest.TestCase):
    def test_is_stale_returns_false_when_artifact_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "absent.txt"
            src = Path(tmp) / "src.txt"
            src.write_text("x")
            self.assertFalse(is_stale(artifact, [src]))

    def test_is_stale_returns_false_when_artifact_newer(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.txt"
            src.write_text("x")
            time.sleep(0.05)
            artifact = Path(tmp) / "out.txt"
            artifact.write_text("y")
            self.assertFalse(is_stale(artifact, [src]))

    def test_is_stale_with_5s_tolerance(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "out.txt"
            artifact.write_text("y")
            src = Path(tmp) / "src.txt"
            src.write_text("x")
            # Bump src mtime ~7s into future to clearly exceed 5s tolerance.
            now = time.time()
            os.utime(src, (now + 10, now + 10))
            self.assertTrue(is_stale(artifact, [src]))


class CLITests(unittest.TestCase):
    def test_marker_missing_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            errbuf = io.StringIO()
            with redirect_stderr(errbuf):
                rc = main(["--paper-root", tmp])
            self.assertEqual(rc, 2)

    def test_dry_run_emits_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            buf = io.StringIO()
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                with redirect_stdout(buf):
                    rc = main(["--paper-root", str(paper), "--dry-run"])
            self.assertEqual(rc, 0)
            self.assertIn("step plan", buf.getvalue())

    def test_json_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            buf = io.StringIO()
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                with redirect_stdout(buf):
                    rc = main(["--paper-root", str(paper), "--dry-run", "--json"])
            self.assertEqual(rc, 0)
            plan = json.loads(buf.getvalue())
            self.assertEqual({s["name"] for s in plan}, set(STEP_NAMES))

    def test_only_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            buf = io.StringIO()
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                with redirect_stdout(buf):
                    rc = main(["--paper-root", str(paper), "--dry-run", "--json",
                               "--only=cover-letter,disclosure"])
            self.assertEqual(rc, 0)
            plan = json.loads(buf.getvalue())
            run_names = {s["name"] for s in plan if s["should_run"]}
            self.assertEqual(run_names, {"cover-letter", "disclosure"})

    def test_only_unknown_step_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp)
            errbuf = io.StringIO()
            with env(RESOLVED_COVER_LETTER_REQUIRED="true",
                     RESOLVED_DISCLOSURE_REQUIRED="true"):
                with redirect_stderr(errbuf):
                    rc = main(["--paper-root", str(paper), "--dry-run",
                               "--only=cover-letter,notastep"])
            self.assertEqual(rc, 3)


if __name__ == "__main__":
    unittest.main()
