"""Tests for sws_resolve_call_rules.py."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

import yaml

PYTHON = sys.executable
ROOT = pathlib.Path(__file__).resolve().parent.parent
HELPER = ROOT / "scripts" / "sws_resolve_call_rules.py"
SYNTH = ROOT / "tests" / "fixtures" / "synthesizer_outputs"
CALLS = ROOT / "tests" / "fixtures" / "calls"
sys.path.insert(0, str(ROOT / "scripts"))
import sws_resolve_call_rules as helper_mod  # noqa: E402


def make_paper(d: pathlib.Path, profile: str = "funding-proposal") -> pathlib.Path:
    (d / ".sws-project.local.md").write_text(
        f"---\nprofile: {profile}\n---\n"
    )
    return d


def run_helper(paper: pathlib.Path, *,
               slug: str | None = None,
               fixture: pathlib.Path | None = None,
               source_text: pathlib.Path | None = None,
               noninteractive: bool = True) -> subprocess.CompletedProcess:
    cmd = [PYTHON, str(HELPER), "--paper", str(paper)]
    if slug:
        cmd += ["--slug", slug]
    if noninteractive:
        cmd += ["--noninteractive"]
    env = os.environ.copy()
    if fixture:
        env["SWS_TEST_FIXTURE_SYNTH_OUTPUT"] = str(fixture)
    if source_text:
        env["SWS_TEST_FIXTURE_SOURCE_TEXT"] = str(source_text)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestProfileGate(unittest.TestCase):
    def test_aborts_when_profile_not_funding_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp), profile="communication")
            r = run_helper(d, fixture=SYNTH / "prin_2024.yaml")
            self.assertEqual(r.returncode, 1)
            self.assertIn("funding-proposal", r.stderr)

    def test_aborts_when_marker_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            r = run_helper(d, fixture=SYNTH / "prin_2024.yaml")
            self.assertEqual(r.returncode, 4)


class TestHeuristicExtractor(unittest.TestCase):
    def test_extracts_deadline_iso(self):
        text = "Deadline: 2026-01-31. Page limit 12."
        result = helper_mod.heuristic_extract(text)
        self.assertEqual(result.get("deadline"), "2026-01-31")

    def test_extracts_deadline_natural(self):
        text = "Submission deadline 31 January 2026. Max 15 pages."
        result = helper_mod.heuristic_extract(text)
        self.assertIn("31 January 2026", result.get("deadline", ""))

    def test_extracts_page_limit(self):
        text = "Proposal length: max. 12 pages, references excluded."
        result = helper_mod.heuristic_extract(text)
        self.assertEqual(result.get("page_limit"), 12)

    def test_extracts_budget(self):
        text = "Budget: €500,000 per project."
        result = helper_mod.heuristic_extract(text)
        self.assertIn("500,000", result.get("budget", ""))


class TestQAWizardPath(unittest.TestCase):
    def test_no_source_uses_qa_wizard_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d, fixture=SYNTH / "qa_wizard.yaml")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            payload = json.loads(r.stdout)
            self.assertIsNone(payload["source"])
            overlay = d / "Manuscript" / "_call" / "qa-wizard.md"
            self.assertTrue(overlay.exists())

    def test_qa_wizard_writes_5_field_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d, slug="erc-starting", fixture=SYNTH / "qa_wizard.yaml")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            overlay_path = d / "Manuscript" / "_call" / "erc-starting.md"
            self.assertTrue(overlay_path.exists())
            block = overlay_path.read_text().split("\n---", 1)[0].split("---", 1)[1]
            parsed = yaml.safe_load(block)
            for k in ("program", "deadline", "page_limit", "abstract_style"):
                self.assertIn(k, parsed)


class TestUploadedSourcePath(unittest.TestCase):
    def test_source_file_drives_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            (d / "Manuscript" / "call").mkdir(parents=True)
            src = d / "Manuscript" / "call" / "prin_2024.md"
            src.write_text((CALLS / "prin_2024.md").read_text())
            r = run_helper(d, fixture=SYNTH / "prin_2024.yaml",
                          source_text=CALLS / "prin_2024.md")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            overlay = d / "Manuscript" / "_call" / "prin_2024.md"
            self.assertTrue(overlay.exists())

    def test_heuristics_merge_into_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            (d / "Manuscript" / "call").mkdir(parents=True)
            (d / "Manuscript" / "call" / "prin_2024.md").write_text(
                (CALLS / "prin_2024.md").read_text()
            )
            r = run_helper(d, fixture=SYNTH / "prin_2024.yaml",
                          source_text=CALLS / "prin_2024.md")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            payload = json.loads(r.stdout)
            self.assertEqual(payload["heuristics"]["page_limit"], 12)
            # The heuristics merged into the overlay because the fixture didn't override them.
            overlay = d / "Manuscript" / "_call" / "prin_2024.md"
            text = overlay.read_text()
            block = text.split("\n---", 1)[0].split("---", 1)[1]
            parsed = yaml.safe_load(block)
            self.assertEqual(parsed.get("page_limit"), 12)

    def test_archive_on_re_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            (d / "Manuscript" / "call").mkdir(parents=True)
            (d / "Manuscript" / "call" / "prin_2024.md").write_text(
                (CALLS / "prin_2024.md").read_text()
            )
            r1 = run_helper(d, fixture=SYNTH / "prin_2024.yaml",
                            source_text=CALLS / "prin_2024.md")
            self.assertEqual(r1.returncode, 0, msg=r1.stderr)
            r2 = run_helper(d, fixture=SYNTH / "prin_2024.yaml",
                            source_text=CALLS / "prin_2024.md")
            self.assertEqual(r2.returncode, 0, msg=r2.stderr)
            archive = d / "Manuscript" / "_call" / "_archive"
            self.assertTrue(archive.exists())
            self.assertEqual(len(list(archive.glob("prin_2024-*.md"))), 1)

    def test_underscore_files_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            (d / "Manuscript" / "call").mkdir(parents=True)
            (d / "Manuscript" / "call" / "_scratch.md").write_text("ignore me")
            r = run_helper(d, fixture=SYNTH / "qa_wizard.yaml")
            # No usable source → falls to Q&A path → uses 'qa-wizard' slug.
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            payload = json.loads(r.stdout)
            self.assertIsNone(payload["source"])


class TestMissingFixture(unittest.TestCase):
    def test_no_fixture_in_noninteractive_returns_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d)
            self.assertEqual(r.returncode, 3)


if __name__ == "__main__":
    unittest.main()
