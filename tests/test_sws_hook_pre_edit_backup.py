"""Tests for sws_hook_pre_edit_backup.py — pure stdlib + unittest.

Each test invokes the hook as a subprocess with a JSON event piped to stdin,
running inside a tempfile.TemporaryDirectory with a synthesized marker file.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PYTHON = sys.executable
HOOK = str(Path(__file__).resolve().parent.parent / "scripts" / "sws_hook_pre_edit_backup.py")

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

LATEX_MARKER_CONTENT = """\
---
sws_version: 0.1
article_type: communication
language: en
format: latex
target_journal: jacs
target_call: null
---

# test marker latex
"""


def _run_hook(event: dict, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _write_marker(tmp: str, content: str = MARKER_CONTENT) -> None:
    (Path(tmp) / ".sws-project.local.md").write_text(content)


class TestPreEditBackup(unittest.TestCase):
    def test_no_op_when_no_marker(self):
        """Without a marker, hook exits 0 and creates no backup."""
        with tempfile.TemporaryDirectory() as tmp:
            docx = Path(tmp) / "paper.docx"
            docx.write_bytes(b"PK dummy")
            event = {"tool_name": "Edit", "tool_input": {"file_path": str(docx)}}
            result = _run_hook(event, tmp)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(any(p.name.startswith("paper.backup") for p in Path(tmp).iterdir()))

    def test_backs_up_docx_when_marker_present(self):
        """When marker is present and target is .docx, backup file is created."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp)
            docx = Path(tmp) / "paper.docx"
            docx.write_bytes(b"PK dummy")
            event = {"tool_name": "Edit", "tool_input": {"file_path": str(docx)}}
            result = _run_hook(event, tmp)
            self.assertEqual(result.returncode, 0)
            backup = Path(tmp) / "paper.backup_pre_edit.docx"
            self.assertTrue(backup.exists(), f"Backup not found in {list(Path(tmp).iterdir())}")

    def test_no_op_for_unrelated_extension(self):
        """A .txt file is never backed up, even with a marker present."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp)
            txt = Path(tmp) / "notes.txt"
            txt.write_text("hello")
            event = {"tool_name": "Edit", "tool_input": {"file_path": str(txt)}}
            result = _run_hook(event, tmp)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(any(p.name.startswith("notes.backup") for p in Path(tmp).iterdir()))

    def test_backs_up_tex_when_format_latex(self):
        """With format: latex, .tex files are backed up."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp, LATEX_MARKER_CONTENT)
            tex = Path(tmp) / "paper.tex"
            tex.write_text("\\documentclass{article}")
            event = {"tool_name": "Write", "tool_input": {"file_path": str(tex)}}
            result = _run_hook(event, tmp)
            self.assertEqual(result.returncode, 0)
            backup = Path(tmp) / "paper.backup_pre_write.tex"
            self.assertTrue(backup.exists(), f"Backup not found in {list(Path(tmp).iterdir())}")

    def test_no_op_for_tex_when_format_docx(self):
        """With format: docx (default), .tex files are not backed up."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp, MARKER_CONTENT)  # format: docx
            tex = Path(tmp) / "paper.tex"
            tex.write_text("\\documentclass{article}")
            event = {"tool_name": "Edit", "tool_input": {"file_path": str(tex)}}
            result = _run_hook(event, tmp)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(any(p.name.startswith("paper.backup") for p in Path(tmp).iterdir()))

    def test_no_op_when_target_does_not_exist(self):
        """If the target file does not exist yet (first Write), no backup is created."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp)
            event = {"tool_name": "Write", "tool_input": {"file_path": str(Path(tmp) / "new.docx")}}
            result = _run_hook(event, tmp)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(any(p.name.startswith("new.backup") for p in Path(tmp).iterdir()))

    def test_returns_nonzero_when_backup_fails(self):
        """If the directory is read-only so the backup cannot be written, hook exits non-zero."""
        import os
        with tempfile.TemporaryDirectory() as tmp:
            _write_marker(tmp)
            # Place the docx inside a subdirectory that we then make read-only.
            subdir = Path(tmp) / "docs"
            subdir.mkdir()
            docx = subdir / "paper.docx"
            docx.write_bytes(b"PK dummy")
            # Make the directory read-only: backup write will get EPERM.
            os.chmod(subdir, 0o555)
            try:
                event = {"tool_name": "Edit", "tool_input": {"file_path": str(docx)}}
                result = _run_hook(event, tmp)
                self.assertNotEqual(result.returncode, 0)
            finally:
                os.chmod(subdir, 0o755)


if __name__ == "__main__":
    unittest.main()
