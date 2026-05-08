"""Tests for sws_fs_index.py — pure stdlib + unittest, runs under pymol25."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import sws_fs_index  # noqa: E402


class TestFilesystemIndex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Fixture tree:
        #   Manuscript/paper.docx                    -> included
        #   Manuscript/_archive/old.docx             -> excluded (_archive)
        #   Figures/main/fig1.png                    -> included
        #   .git/HEAD                                -> excluded (.git)
        #   paper.backup_pre_edit.docx               -> excluded (backup pattern)
        #   scratch/note.md                          -> included
        (self.root / "Manuscript").mkdir()
        (self.root / "Manuscript" / "paper.docx").write_bytes(b"abc")
        (self.root / "Manuscript" / "_archive").mkdir()
        (self.root / "Manuscript" / "_archive" / "old.docx").write_bytes(b"x")
        (self.root / "Figures" / "main").mkdir(parents=True)
        (self.root / "Figures" / "main" / "fig1.png").write_bytes(b"png")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "HEAD").write_text("ref: ...")
        (self.root / "paper.backup_pre_edit.docx").write_bytes(b"bk")
        (self.root / "scratch").mkdir()
        (self.root / "scratch" / "note.md").write_text("# note")

    def tearDown(self):
        self.tmp.cleanup()

    def test_index_includes_manuscript_and_figures(self):
        manifest = sws_fs_index.build_index(self.root)
        paths = {entry["path"] for entry in manifest["files"]}
        self.assertIn("Manuscript/paper.docx", paths)
        self.assertIn("Figures/main/fig1.png", paths)
        self.assertIn("scratch/note.md", paths)

    def test_index_excludes_archives_git_and_backups(self):
        manifest = sws_fs_index.build_index(self.root)
        paths = {entry["path"] for entry in manifest["files"]}
        self.assertNotIn("Manuscript/_archive/old.docx", paths)
        self.assertNotIn(".git/HEAD", paths)
        self.assertNotIn("paper.backup_pre_edit.docx", paths)

    def test_manifest_metadata_fields(self):
        manifest = sws_fs_index.build_index(self.root)
        self.assertIn("version", manifest)
        self.assertIn("generated", manifest)
        self.assertIn("root", manifest)
        self.assertIsInstance(manifest["files"], list)
        for entry in manifest["files"]:
            self.assertIn("path", entry)
            self.assertIn("size_bytes", entry)
            self.assertIn("mtime", entry)
            self.assertIn("ext", entry)

    def test_cli_writes_json(self):
        out_path = self.root / "claude_memory" / "fs_index.json"
        out_path.parent.mkdir()
        rc = sws_fs_index.main(["--root", str(self.root), "--out", str(out_path)])
        self.assertEqual(rc, 0)
        self.assertTrue(out_path.exists())
        data = json.loads(out_path.read_text())
        self.assertEqual(Path(data["root"]).resolve(), self.root.resolve())
        self.assertGreaterEqual(len(data["files"]), 3)


if __name__ == "__main__":
    unittest.main()
