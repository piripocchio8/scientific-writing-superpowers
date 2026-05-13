"""Tests for scripts/sws_set_profile.py."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

PYTHON = sys.executable
ROOT = pathlib.Path(__file__).resolve().parent.parent
HELPER = ROOT / "scripts" / "sws_set_profile.py"
PROFILES_FIXTURE = ROOT / "tests" / "fixtures" / "profiles"

MARKER_WITH_PROFILE = """\
---
sws_version: 0.1
article_type: communication
profile: communication
language: en
format: docx
target_journal: chembiochem
target_call: null
---

# test
"""

MARKER_NULL_PROFILE = """\
---
sws_version: 0.1
profile: null
language: en
format: docx
---
"""


def run_helper(paper: pathlib.Path, name: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(HELPER), "--paper", str(paper), "--name", name,
         "--profiles-dir", str(PROFILES_FIXTURE)],
        capture_output=True, text=True,
    )


class TestSetProfile(unittest.TestCase):
    def test_valid_name_rewrites_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            marker = d / ".sws-project.local.md"
            marker.write_text(MARKER_NULL_PROFILE)
            r = run_helper(d, "full-article")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            text = marker.read_text()
            self.assertIn("profile: full-article", text)

    def test_invalid_name_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            (d / ".sws-project.local.md").write_text(MARKER_NULL_PROFILE)
            r = run_helper(d, "bogus-profile")
            self.assertEqual(r.returncode, 1)
            self.assertIn("not a valid profile", r.stderr)
            # All valid names should appear in the error message.
            for name in (
                "full-article", "communication", "perspective",
                "review-paper", "mini-review", "editorial",
                "methodological-paper", "commentary-reply",
                "funding-proposal",
            ):
                self.assertIn(name, r.stderr)

    def test_missing_marker_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            r = run_helper(d, "communication")
            self.assertEqual(r.returncode, 2)
            self.assertIn("not an SWS project", r.stderr)

    def test_overlays_untouched(self):
        # D11 / Q12=A — switching profile preserves journal-style and call overlays.
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            (d / ".sws-project.local.md").write_text(MARKER_WITH_PROFILE)
            overlay_dir = d / "Manuscript" / "_journal-style"
            overlay_dir.mkdir(parents=True)
            overlay_file = overlay_dir / "chembiochem.md"
            overlay_content = "---\nref_cap: 50\n---\n# ChemBioChem overlay\n"
            overlay_file.write_text(overlay_content)
            call_dir = d / "Manuscript" / "_call"
            call_dir.mkdir(parents=True)
            call_overlay = call_dir / "prin_2024.md"
            call_content = "---\nword_total: 9000\n---\n"
            call_overlay.write_text(call_content)

            r = run_helper(d, "funding-proposal")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertEqual(overlay_file.read_text(), overlay_content)
            self.assertEqual(call_overlay.read_text(), call_content)

    def test_one_line_confirmation_printed(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            (d / ".sws-project.local.md").write_text(MARKER_WITH_PROFILE)
            r = run_helper(d, "full-article")
            self.assertEqual(r.returncode, 0)
            lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
            self.assertEqual(len(lines), 1)
            self.assertIn("profile: full-article", lines[0])
            self.assertIn("was: communication", lines[0])


if __name__ == "__main__":
    unittest.main()
