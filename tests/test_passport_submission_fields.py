"""Cycle-12 D4: verify passport entries with the additive submission-phase
fields (phase, venue, round) validate, and older entries without them also
validate. The Stop-hook itself does NOT emit the new fields — but the schema
must accept entries written by orchestrated steps (e.g. /sws:run-cycle) that
include them."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PYTHON = sys.executable
HOOK = str(Path(__file__).resolve().parent.parent / "scripts" / "sws_hook_stop_passport.py")

MARKER = """\
---
sws_version: 0.1
article_type: full-article
language: en
format: docx
target_journal: chembiochem
---

# test
"""

LEGACY_ENTRY = {
    "cycle": 1,
    "timestamp": "2026-05-30T00:00:00Z",
    "agent": "drafter-fast",
    "file": ["_drafts/intro.md"],
    "change_summary": "drafted intro",
    "next_step": "review",
}

CYCLE12_ENTRY = {
    **LEGACY_ENTRY,
    "cycle": 2,
    "phase": "submit",
    "venue": "chembiochem",
    "round": 1,
}


REQUIRED_FIELDS = {"cycle", "timestamp", "agent", "file", "change_summary", "next_step"}
CYCLE12_OPTIONAL_FIELDS = {"phase", "venue", "round"}


def _setup_paper(tmp, history):
    paper = Path(tmp) / "paper"
    paper.mkdir()
    (paper / ".sws-project.local.md").write_text(MARKER)
    memory = paper / "claude_memory"
    memory.mkdir()
    passport = memory / "passport.json"
    passport.write_text(json.dumps({
        "sws_version": "0.1",
        "cycle": max((e["cycle"] for e in history), default=0),
        "history": history,
    }))
    return paper, passport


class PassportSchemaTests(unittest.TestCase):
    def test_legacy_entry_has_required_fields(self):
        for f in REQUIRED_FIELDS:
            self.assertIn(f, LEGACY_ENTRY)

    def test_cycle12_entry_has_required_plus_optional(self):
        for f in REQUIRED_FIELDS:
            self.assertIn(f, CYCLE12_ENTRY)
        for f in CYCLE12_OPTIONAL_FIELDS:
            self.assertIn(f, CYCLE12_ENTRY)

    def test_legacy_only_passport_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, passport = _setup_paper(tmp, [LEGACY_ENTRY])
            data = json.loads(passport.read_text())
            self.assertEqual(len(data["history"]), 1)
            self.assertNotIn("phase", data["history"][0])

    def test_mixed_passport_loads_and_preserves_optional(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, passport = _setup_paper(tmp, [LEGACY_ENTRY, CYCLE12_ENTRY])
            data = json.loads(passport.read_text())
            self.assertEqual(len(data["history"]), 2)
            new = data["history"][1]
            self.assertEqual(new["phase"], "submit")
            self.assertEqual(new["venue"], "chembiochem")
            self.assertEqual(new["round"], 1)


class StopHookRegressionTests(unittest.TestCase):
    """Cycle-12 is additive — Stop-hook still emits its existing 5-field entry."""

    def _run_hook(self, event: dict, cwd: str):
        return subprocess.run(
            [PYTHON, HOOK], input=json.dumps(event),
            capture_output=True, text=True, cwd=cwd,
        )

    def test_stop_hook_still_emits_legacy_schema_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper, passport = _setup_paper(tmp, [LEGACY_ENTRY])
            transcript = Path(tmp) / "transcript.jsonl"
            transcript.write_text(json.dumps({
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Edit",
                         "input": {"file_path": str(paper / "_drafts/intro.md")}}
                    ]
                }
            }) + "\n")
            event = {"transcript_path": str(transcript)}
            r = self._run_hook(event, str(paper))
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(passport.read_text())
            # New entry was appended. It must have the 5 legacy required fields and
            # MUST NOT carry phase/venue/round (Stop-hook is additive-document only).
            self.assertEqual(len(data["history"]), 2)
            new = data["history"][-1]
            for f in ("cycle", "timestamp", "agent", "file", "change_summary", "next_step"):
                self.assertIn(f, new)
            for f in CYCLE12_OPTIONAL_FIELDS:
                self.assertNotIn(f, new,
                    f"Stop-hook must not silently add {f}; that's reserved for orchestrated steps")


if __name__ == "__main__":
    unittest.main()
