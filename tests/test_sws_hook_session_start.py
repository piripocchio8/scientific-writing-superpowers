"""Tests for sws_hook_session_start.py — pure stdlib + unittest."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PYTHON = sys.executable
HOOK = str(Path(__file__).resolve().parent.parent / "scripts" / "sws_hook_session_start.py")

MARKER_CONTENT = """\
---
sws_version: 0.1
article_type: communication
language: en
format: docx
target_journal: chembiochem
target_call: null
---

# test marker
"""

FUNDING_MARKER_CONTENT = """\
---
sws_version: 0.1
article_type: funding-proposal
language: it
format: docx
target_journal: null
target_call: PRIN2025
---

# test funding marker
"""


def _run_hook(cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, HOOK],
        input="{}",
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _write_marker(tmp: str, content: str = MARKER_CONTENT) -> None:
    (Path(tmp) / ".sws-project.local.md").write_text(content)


def _write_passport(tmp: str, history: list) -> None:
    memory_dir = Path(tmp) / "claude_memory"
    memory_dir.mkdir(exist_ok=True)
    passport = {"sws_version": "0.1", "cycle": 0, "history": history}
    (memory_dir / "passport.json").write_text(json.dumps(passport))


class TestSessionStart(unittest.TestCase):
    def test_no_op_when_no_marker(self):
        """Without a marker, hook produces no output and exits 0."""
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_hook(tmp)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_prints_passport_summary_when_history_present(self):
        """Last cycle number and file count appear in stdout."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp)
            _write_passport(tmp, [
                {
                    "cycle": 1,
                    "timestamp": "2026-05-12T10:00:00Z",
                    "agent": None,
                    "file": ["Manuscript/paper.docx"],
                    "change_summary": None,
                    "next_step": None,
                }
            ])
            result = _run_hook(tmp)
            self.assertEqual(result.returncode, 0)
            self.assertIn("last cycle #1", result.stdout)
            self.assertIn("1 file(s)", result.stdout)

    def test_no_output_when_history_empty(self):
        """Empty history list produces no passport-summary line."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp)
            _write_passport(tmp, [])
            result = _run_hook(tmp)
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("last cycle", result.stdout)

    def test_prints_journal_style_nudge_when_overlay_missing(self):
        """When no overlay exists and article is not funding-proposal, nudge appears."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp)
            _write_passport(tmp, [])
            # No Manuscript/_journal-style directory
            result = _run_hook(tmp)
            self.assertEqual(result.returncode, 0)
            self.assertIn("resolve-journal-style", result.stdout)

    def test_no_nudge_for_funding_proposal(self):
        """funding-proposal article type suppresses the journal-style nudge."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp, FUNDING_MARKER_CONTENT)
            _write_passport(tmp, [])
            result = _run_hook(tmp)
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("resolve-journal-style", result.stdout)

    def test_no_nudge_when_overlay_present(self):
        """When a .md overlay file exists in _journal-style/, no nudge is printed."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp)
            _write_passport(tmp, [])
            overlay_dir = Path(tmp) / "Manuscript" / "_journal-style"
            overlay_dir.mkdir(parents=True)
            (overlay_dir / "chembiochem.md").write_text("# ChemBioChem style")
            result = _run_hook(tmp)
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("resolve-journal-style", result.stdout)


if __name__ == "__main__":
    unittest.main()
