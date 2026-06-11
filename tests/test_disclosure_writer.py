"""Tests for sws_disclosure_writer.py (cycle-12 D7, R6)."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "sws_disclosure_writer.py"
PYTHON = sys.executable


MARKER = """\
---
sws_version: 0.1
article_type: full-article
language: en
format: docx
target_journal: chembiochem
---

# test marker
"""


@contextmanager
def env(**overrides):
    """Apply env overrides, restore previous values."""
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


def _make_paper(tmp, overlay_template_id=None):
    paper = Path(tmp) / "paper"
    paper.mkdir()
    (paper / ".sws-project.local.md").write_text(MARKER)
    if overlay_template_id is not None:
        overlay_dir = paper / "Manuscript" / "_journal-style"
        overlay_dir.mkdir(parents=True)
        (overlay_dir / "chembiochem.md").write_text(
            f"---\ndisclosure:\n  template_id: {overlay_template_id}\n---\n"
        )
    return paper


def _run(paper, extra_args=None, env_extra=None):
    args = [PYTHON, str(SCRIPT), "--paper-root", str(paper)]
    if extra_args:
        args.extend(extra_args)
    e = os.environ.copy()
    e.update(env_extra or {})
    return subprocess.run(args, capture_output=True, text=True, env=e)


class GateTests(unittest.TestCase):
    def test_disclosure_not_required_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, overlay_template_id="wiley")
            r = _run(paper, env_extra={"RESOLVED_DISCLOSURE_REQUIRED": "false"})
            self.assertEqual(r.returncode, 0)
            self.assertIn("not required", r.stderr)
            # nothing should have been written
            self.assertFalse((paper / "_submission" / "ai-disclosure.md").exists())

    def test_required_unset_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, overlay_template_id="wiley")
            r = _run(paper)  # no env
            self.assertEqual(r.returncode, 0)
            self.assertFalse((paper / "_submission" / "ai-disclosure.md").exists())


class TemplateTests(unittest.TestCase):
    def _render_check(self, tid, expected_phrase):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, overlay_template_id=tid)
            r = _run(paper, env_extra={"RESOLVED_DISCLOSURE_REQUIRED": "true"})
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out = (paper / "_submission" / "ai-disclosure.md").read_text()
            self.assertIn(expected_phrase, out, msg=f"template {tid} body missing expected phrase")

    def test_icmje(self):
        self._render_check("icmje", "manuscript preparation")

    def test_wiley(self):
        self._render_check("wiley", "Wiley")

    def test_rsc(self):
        self._render_check("rsc", "RSC")

    def test_acs(self):
        self._render_check("acs", "ACS")


class FallbackTests(unittest.TestCase):
    def test_missing_template_id_falls_back_icmje(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, overlay_template_id=None)  # no overlay
            r = _run(paper, env_extra={"RESOLVED_DISCLOSURE_REQUIRED": "true"})
            self.assertEqual(r.returncode, 0)
            self.assertIn("falling back", r.stderr.lower())
            out = (paper / "_submission" / "ai-disclosure.md").read_text()
            self.assertIn("manuscript preparation", out)

    def test_unknown_template_id_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, overlay_template_id="nonexistent_template")
            r = _run(paper, env_extra={"RESOLVED_DISCLOSURE_REQUIRED": "true"})
            self.assertEqual(r.returncode, 3)


class LastVerifiedTests(unittest.TestCase):
    def test_last_verified_printed_to_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, overlay_template_id="acs")
            r = _run(paper, env_extra={"RESOLVED_DISCLOSURE_REQUIRED": "true"})
            self.assertEqual(r.returncode, 0)
            self.assertIn("last_verified", r.stderr)


class UseCategoriesTests(unittest.TestCase):
    def test_override_use_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = _make_paper(tmp, overlay_template_id="icmje")
            r = _run(
                paper,
                extra_args=["--use-categories", "foo, bar, baz"],
                env_extra={"RESOLVED_DISCLOSURE_REQUIRED": "true"},
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out = (paper / "_submission" / "ai-disclosure.md").read_text()
            self.assertIn("foo, bar, baz", out)


if __name__ == "__main__":
    unittest.main()
