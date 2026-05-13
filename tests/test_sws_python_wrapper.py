"""Tests for scripts/sws_python.sh — per-paper venv wrapper."""
import os
import pathlib
import subprocess
import tempfile
import unittest

WRAPPER = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "sws_python.sh"


class TestSwsPythonWrapper(unittest.TestCase):
    def test_exits_2_when_venv_missing(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run(
                [str(WRAPPER), d, "-c", "print(1)"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 2)
            self.assertIn("/sws:install-deps", r.stderr)

    def test_invokes_python_when_venv_present(self):
        with tempfile.TemporaryDirectory() as d:
            venv_bin = pathlib.Path(d) / ".venv" / "bin"
            venv_bin.mkdir(parents=True)
            py = venv_bin / "python"
            py.write_text('#!/usr/bin/env bash\necho "OK $@"\n')
            py.chmod(0o755)
            r = subprocess.run(
                [str(WRAPPER), d, "-c", "print(1)"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0)
            self.assertIn("OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
