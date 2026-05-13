"""Tests for sws_resolve_journal_style.py.

Synthesizer is bypassed via SWS_TEST_FIXTURE_SYNTH_OUTPUT in tests.
"""
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
HELPER = ROOT / "scripts" / "sws_resolve_journal_style.py"
FIXTURES = ROOT / "tests" / "fixtures"
SYNTH = FIXTURES / "synthesizer_outputs"


def make_paper(d: pathlib.Path, profile: str = "communication") -> pathlib.Path:
    (d / ".sws-project.local.md").write_text(
        f"---\nprofile: {profile}\n---\n"
    )
    return d


def run_helper(paper: pathlib.Path, slug: str, *,
               fixture: pathlib.Path | None = None,
               url: str | None = None,
               noninteractive: bool = True) -> subprocess.CompletedProcess:
    cmd = [PYTHON, str(HELPER), "--paper", str(paper), "--slug", slug]
    if url:
        cmd += ["--url", url]
    if noninteractive:
        cmd += ["--noninteractive"]
    env = os.environ.copy()
    if fixture:
        env["SWS_TEST_FIXTURE_SYNTH_OUTPUT"] = str(fixture)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestResolveJournalStyle(unittest.TestCase):
    def test_url_map_lookup_for_known_slug(self):
        # No --url flag; chembiochem is in journal-url-map.yaml.
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem.yaml")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            overlay = d / "Manuscript" / "_journal-style" / "chembiochem.md"
            self.assertTrue(overlay.exists())

    def test_unknown_slug_without_url_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d, "not-in-map", fixture=SYNTH / "chembiochem.yaml")
            self.assertEqual(r.returncode, 2)
            self.assertIn("no URL on file", r.stderr)

    def test_unknown_slug_with_url_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d, "custom-journal",
                           url="https://example.org/authors",
                           fixture=SYNTH / "chembiochem.yaml")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            overlay = d / "Manuscript" / "_journal-style" / "custom-journal.md"
            self.assertTrue(overlay.exists())

    def test_aborts_when_profile_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            (d / ".sws-project.local.md").write_text("---\nprofile: null\n---\n")
            r = run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem.yaml")
            self.assertEqual(r.returncode, 1)
            self.assertIn("no profile set", r.stderr)

    def test_aborts_when_marker_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            r = run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem.yaml")
            self.assertEqual(r.returncode, 4)
            self.assertIn("not an SWS project", r.stderr)

    def test_no_archive_on_first_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem.yaml")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            archive = d / "Manuscript" / "_journal-style" / "_archive"
            self.assertFalse(archive.exists())

    def test_archive_created_on_re_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r1 = run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem.yaml")
            self.assertEqual(r1.returncode, 0, msg=r1.stderr)
            r2 = run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem-alt.yaml")
            self.assertEqual(r2.returncode, 0, msg=r2.stderr)
            archive = d / "Manuscript" / "_journal-style" / "_archive"
            self.assertTrue(archive.exists())
            archives = list(archive.glob("chembiochem-*.md"))
            self.assertEqual(len(archives), 1)

    def test_diff_summary_printed_on_re_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem.yaml")
            r2 = run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem-alt.yaml")
            self.assertEqual(r2.returncode, 0)
            payload = json.loads(r2.stdout)
            self.assertIn("diff", payload)
            # ref_cap changed 50 -> 60
            self.assertIn("ref_cap", payload["diff"])

    def test_overlay_content_only_confirmed_fields(self):
        # D18 — overlay should contain exactly the synthesizer's emitted fields.
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d, "chembiochem", fixture=SYNTH / "chembiochem.yaml")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            overlay = d / "Manuscript" / "_journal-style" / "chembiochem.md"
            text = overlay.read_text()
            self.assertTrue(text.startswith("---\n"))
            block = text[4:].split("\n---", 1)[0]
            parsed = yaml.safe_load(block)
            # Synthesizer fixture has exactly 3 keys; overlay should match.
            self.assertEqual(set(parsed.keys()), {"ref_cap", "word_total", "abstract_style"})

    def test_no_fixture_in_noninteractive_returns_3(self):
        # When neither fixture nor URL chain is set up in noninteractive mode,
        # the helper aborts rather than guessing.
        with tempfile.TemporaryDirectory() as tmp:
            d = make_paper(pathlib.Path(tmp))
            r = run_helper(d, "chembiochem")
            self.assertEqual(r.returncode, 3)


if __name__ == "__main__":
    unittest.main()
