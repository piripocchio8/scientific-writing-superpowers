"""Tests for sws_hook_stop_passport.py — pure stdlib + unittest."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PYTHON = sys.executable
HOOK = str(Path(__file__).resolve().parent.parent / "scripts" / "sws_hook_stop_passport.py")

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

PASSPORT_STUB = {"sws_version": "0.1", "cycle": 0, "history": []}


def _run_hook(event: dict, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _setup(tmp: str, passport_content=None) -> Path:
    """Write marker and passport.json; return passport path."""
    (Path(tmp) / ".sws-project.local.md").write_text(MARKER_CONTENT)
    memory_dir = Path(tmp) / "claude_memory"
    memory_dir.mkdir(exist_ok=True)
    passport_path = memory_dir / "passport.json"
    content = passport_content if passport_content is not None else PASSPORT_STUB
    passport_path.write_text(json.dumps(content))
    return passport_path


def _edit_event(file_path: str) -> dict:
    return {"tool_uses": [{"tool_name": "Edit", "tool_input": {"file_path": file_path}}]}


def _transcript_event(transcript_path: str) -> dict:
    return {"transcript_path": transcript_path}


def _write_transcript(transcript_path: str, file_path: str) -> None:
    """Write a minimal JSONL transcript with one Edit tool_use block."""
    line = json.dumps({
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "Edit",
                    "input": {"file_path": file_path, "old_string": "x", "new_string": "y"},
                }
            ],
        }
    })
    Path(transcript_path).write_text(line + "\n")


class TestStopPassport(unittest.TestCase):
    def test_no_op_when_no_marker(self):
        """Without a marker, hook exits 0 and passport is untouched."""
        with tempfile.TemporaryDirectory() as tmp:
            memory_dir = Path(tmp) / "claude_memory"
            memory_dir.mkdir()
            passport_path = memory_dir / "passport.json"
            passport_path.write_text(json.dumps(PASSPORT_STUB))
            event = _edit_event(str(Path(tmp) / "paper.docx"))
            result = _run_hook(event, tmp)
            self.assertEqual(result.returncode, 0)
            data = json.loads(passport_path.read_text())
            self.assertEqual(data["history"], [])

    def test_no_op_when_passport_missing(self):
        """If passport.json doesn't exist, hook exits 0 without creating it."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".sws-project.local.md").write_text(MARKER_CONTENT)
            event = _edit_event(str(Path(tmp) / "paper.docx"))
            result = _run_hook(event, tmp)
            self.assertEqual(result.returncode, 0)
            self.assertFalse((Path(tmp) / "claude_memory" / "passport.json").exists())

    def test_no_op_when_no_files_modified(self):
        """Empty tool_uses list produces no passport entry."""
        with tempfile.TemporaryDirectory() as tmp:
            passport_path = _setup(tmp)
            result = _run_hook({"tool_uses": []}, tmp)
            self.assertEqual(result.returncode, 0)
            data = json.loads(passport_path.read_text())
            self.assertEqual(data["history"], [])

    def test_appends_entry_with_modified_files(self):
        """When a file was modified (via transcript_path), a history entry is appended."""
        with tempfile.TemporaryDirectory() as tmp:
            passport_path = _setup(tmp)
            fp = str(Path(tmp) / "Manuscript" / "paper.docx")
            transcript_file = str(Path(tmp) / "session.jsonl")
            _write_transcript(transcript_file, fp)
            result = _run_hook(_transcript_event(transcript_file), tmp)
            self.assertEqual(result.returncode, 0)
            data = json.loads(passport_path.read_text())
            self.assertEqual(len(data["history"]), 1)
            entry = data["history"][0]
            self.assertIn("cycle", entry)
            self.assertIn("timestamp", entry)
            self.assertIsNone(entry["agent"])
            self.assertIsNone(entry["change_summary"])
            self.assertIsNone(entry["next_step"])
            self.assertIsInstance(entry["file"], list)
            self.assertEqual(len(entry["file"]), 1)
            # Path must be relative, not absolute.
            self.assertFalse(Path(entry["file"][0]).is_absolute())

    def test_increments_cycle_number(self):
        """Each Stop call increments the cycle number."""
        with tempfile.TemporaryDirectory() as tmp:
            passport_path = _setup(tmp)
            fp = str(Path(tmp) / "paper.docx")
            # First stop
            _run_hook(_edit_event(fp), tmp)
            data1 = json.loads(passport_path.read_text())
            cycle1 = data1["history"][0]["cycle"]
            # Second stop
            _run_hook(_edit_event(fp), tmp)
            data2 = json.loads(passport_path.read_text())
            cycle2 = data2["history"][1]["cycle"]
            self.assertEqual(cycle2, cycle1 + 1)
            self.assertEqual(len(data2["history"]), 2)

    def test_handles_corrupt_passport_gracefully(self):
        """Corrupt passport.json causes exit 0 without crashing."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".sws-project.local.md").write_text(MARKER_CONTENT)
            memory_dir = Path(tmp) / "claude_memory"
            memory_dir.mkdir()
            passport_path = memory_dir / "passport.json"
            passport_path.write_text("NOT VALID JSON {{{{")
            fp = str(Path(tmp) / "paper.docx")
            result = _run_hook(_edit_event(fp), tmp)
            self.assertEqual(result.returncode, 0)
            # File should remain untouched (still corrupt)
            self.assertEqual(passport_path.read_text(), "NOT VALID JSON {{{{")


    def test_extracts_from_legacy_tool_uses_event(self):
        """Fallback: old event['tool_uses'] shape still extracts files when no transcript_path."""
        with tempfile.TemporaryDirectory() as tmp:
            passport_path = _setup(tmp)
            fp = str(Path(tmp) / "paper.docx")
            # No transcript_path — only the legacy tool_uses payload.
            result = _run_hook(_edit_event(fp), tmp)
            self.assertEqual(result.returncode, 0)
            data = json.loads(passport_path.read_text())
            self.assertEqual(len(data["history"]), 1)
            entry = data["history"][0]
            self.assertIsInstance(entry["file"], list)
            self.assertEqual(len(entry["file"]), 1)
            self.assertFalse(Path(entry["file"][0]).is_absolute())

    @unittest.skipUnless(sys.platform == "darwin", "macOS-only: /tmp -> /private/tmp symlink")
    def test_symlinked_paths_canonicalize_correctly(self):
        """/tmp paths relativize correctly even when cwd resolves to /private/tmp."""
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            # On macOS, tmp is under /tmp but cwd.resolve() → /private/tmp/...
            # Verify that the symlink actually differs before asserting the fix.
            canonical = str(Path(tmp).resolve())
            if tmp == canonical:
                self.skipTest("/tmp and /private/tmp appear identical on this system")
            passport_path = _setup(tmp)
            manuscript_dir = Path(tmp) / "Manuscript"
            manuscript_dir.mkdir()
            fp = str(Path(tmp) / "Manuscript" / "paper.docx")
            transcript_file = str(Path(tmp) / "session.jsonl")
            _write_transcript(transcript_file, fp)
            # Run the hook with cwd set to the /tmp-prefixed path.
            result = _run_hook(_transcript_event(transcript_file), tmp)
            self.assertEqual(result.returncode, 0)
            data = json.loads(passport_path.read_text())
            self.assertEqual(len(data["history"]), 1)
            entry = data["history"][0]
            self.assertIsInstance(entry["file"], list)
            self.assertEqual(len(entry["file"]), 1)
            # Must be relative, NOT an absolute /private/tmp/... leak.
            self.assertFalse(Path(entry["file"][0]).is_absolute(),
                             f"Expected relative path, got absolute: {entry['file'][0]}")
            self.assertEqual(entry["file"][0], "Manuscript/paper.docx")


if __name__ == "__main__":
    unittest.main()
