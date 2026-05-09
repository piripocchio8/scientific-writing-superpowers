"""Tests for sws_check_env.py — pure stdlib + unittest."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sws_check_env  # noqa: E402


class TestCheckEnv(unittest.TestCase):
    def test_passes_on_current_python(self):
        ok, msg = sws_check_env.check_env()
        self.assertTrue(ok)
        self.assertEqual(msg, "ok")

    def test_fails_on_old_python(self):
        fake_version = (3, 8, 0, "final", 0)
        with mock.patch.object(sys, "version_info", fake_version):
            ok, msg = sws_check_env.check_env()
        self.assertFalse(ok)
        self.assertIn("3.9", msg)
        self.assertIn("3.8", msg)

    def test_main_returns_0_on_pass(self):
        rc = sws_check_env.main()
        self.assertEqual(rc, 0)

    def test_main_returns_1_on_fail(self):
        fake_version = (3, 8, 0, "final", 0)
        with mock.patch.object(sys, "version_info", fake_version):
            rc = sws_check_env.main()
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
