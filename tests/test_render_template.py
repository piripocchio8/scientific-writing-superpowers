"""Tests for sws_render_template.py — pure stdlib + unittest."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sws_render_template  # noqa: E402


class TestRenderTemplate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_template(self, name, content):
        p = self.root / name
        p.write_text(content)
        return p

    def test_happy_path(self):
        tpl = self._write_template("t.template", "hello ${name}")
        out = self.root / "out.md"
        sws_render_template.render(tpl, {"name": "world"}, out)
        self.assertEqual(out.read_text(), "hello world")

    def test_missing_variable_raises_keyerror(self):
        tpl = self._write_template("t.template", "hello ${name}")
        out = self.root / "out.md"
        with self.assertRaises(KeyError):
            sws_render_template.render(tpl, {}, out)

    def test_unicode_in_variable(self):
        tpl = self._write_template("t.template", "author: ${first_author}")
        out = self.root / "out.md"
        sws_render_template.render(tpl, {"first_author": "Müller"}, out)
        self.assertEqual(out.read_text(), "author: Müller")

    def test_creates_parent_dirs(self):
        tpl = self._write_template("t.template", "${x}")
        out = self.root / "deep" / "nested" / "out.md"
        sws_render_template.render(tpl, {"x": "y"}, out)
        self.assertTrue(out.exists())
        self.assertEqual(out.read_text(), "y")

    def test_cli_main_happy_path(self):
        tpl = self._write_template("t.template", "${greeting}")
        vars_path = self.root / "vars.json"
        vars_path.write_text(json.dumps({"greeting": "hi"}))
        out = self.root / "out.md"
        rc = sws_render_template.main([
            "--template", str(tpl),
            "--vars-file", str(vars_path),
            "--out", str(out),
        ])
        self.assertEqual(rc, 0)
        self.assertEqual(out.read_text(), "hi")

    def test_cli_returns_2_on_missing_variable(self):
        tpl = self._write_template("t.template", "${missing}")
        vars_path = self.root / "vars.json"
        vars_path.write_text(json.dumps({"other": "value"}))
        out = self.root / "out.md"
        rc = sws_render_template.main([
            "--template", str(tpl),
            "--vars-file", str(vars_path),
            "--out", str(out),
        ])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
