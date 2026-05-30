"""Tests for sws_review_round.py (cycle-12 D3)."""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from sws_review_round import (  # noqa: E402
    cmd_find, cmd_init, cmd_inventory, existing_rounds, main,
)


class InitTests(unittest.TestCase):
    def test_init_no_existing_creates_round_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cmd_init(paper, None)
            self.assertEqual(rc, 0)
            self.assertTrue((paper / "_review" / "round-1" / "reviewer-comments.md").exists())

    def test_init_explicit_n(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cmd_init(paper, 3)
            self.assertEqual(rc, 0)
            self.assertTrue((paper / "_review" / "round-3" / "reviewer-comments.md").exists())

    def test_init_with_existing_round_increments(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            (paper / "_review" / "round-1").mkdir(parents=True)
            (paper / "_review" / "round-1" / "reviewer-comments.md").write_text("# r1")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cmd_init(paper, None)
            self.assertEqual(rc, 0)
            self.assertTrue((paper / "_review" / "round-2" / "reviewer-comments.md").exists())

    def test_init_idempotent_does_not_overwrite_existing_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            (paper / "_review" / "round-1").mkdir(parents=True)
            existing_content = "USER CONTENT"
            (paper / "_review" / "round-1" / "reviewer-comments.md").write_text(existing_content)
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_init(paper, 1)
            self.assertEqual(
                (paper / "_review" / "round-1" / "reviewer-comments.md").read_text(),
                existing_content,
            )

    def test_init_rejects_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            errbuf = io.StringIO()
            with redirect_stderr(errbuf):
                rc = cmd_init(paper, 0)
            self.assertEqual(rc, 2)


class FindTests(unittest.TestCase):
    def test_find_none_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_find(paper)
            self.assertEqual(buf.getvalue().strip(), "none")

    def test_find_returns_highest(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            for n in (1, 2, 5):
                (paper / "_review" / f"round-{n}").mkdir(parents=True)
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_find(paper)
            self.assertEqual(buf.getvalue().strip(), "5")

    def test_existing_rounds_skips_non_round_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            (paper / "_review" / "peer-reviewer").mkdir(parents=True)
            (paper / "_review" / "round-2").mkdir(parents=True)
            self.assertEqual(existing_rounds(paper), [2])


class InventoryTests(unittest.TestCase):
    def test_inventory_all_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            cmd_init(paper, 1)
            # remove the template the init created so all are absent
            (paper / "_review" / "round-1" / "reviewer-comments.md").unlink()
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_inventory(paper, 1)
            txt = buf.getvalue()
            self.assertIn("comments: absent", txt)
            self.assertIn("matrix: absent", txt)
            self.assertIn("response: absent", txt)
            self.assertIn("edits: absent", txt)

    def test_inventory_mixed_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            cmd_init(paper, 1)
            (paper / "_review" / "round-1" / "response-matrix.json").write_text("[]")
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_inventory(paper, 1)
            txt = buf.getvalue()
            self.assertIn("comments: present", txt)
            self.assertIn("matrix: present", txt)
            self.assertIn("response: absent", txt)
            self.assertIn("edits: absent", txt)

    def test_inventory_missing_round_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            errbuf = io.StringIO()
            with redirect_stderr(errbuf):
                rc = cmd_inventory(paper, 99)
            self.assertEqual(rc, 2)


class CLITests(unittest.TestCase):
    def test_main_find(self):
        with tempfile.TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(["--paper-root", tmp, "find"])
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), "none")


if __name__ == "__main__":
    unittest.main()
