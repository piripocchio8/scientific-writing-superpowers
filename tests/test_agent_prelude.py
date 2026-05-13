"""Tests for scripts/agent_prelude.sh — sourceable resolver wrapper.

The prelude shells out to sws_python.sh which expects a per-paper .venv/.
Tests stub the venv by symlinking .venv/bin/python to the dev Python that
has PyYAML installed.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

PYTHON = sys.executable
ROOT = pathlib.Path(__file__).resolve().parent.parent
PRELUDE = ROOT / "scripts" / "agent_prelude.sh"
PROFILES_FIXTURE = ROOT / "tests" / "fixtures" / "profiles"


def make_paper_with_venv(d: pathlib.Path, marker_text: str,
                          overlays: dict[str, str] | None = None) -> None:
    (d / ".sws-project.local.md").write_text(marker_text)
    venv_bin = d / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    # Symlink .venv/bin/python -> dev python (which has yaml installed).
    (venv_bin / "python").symlink_to(PYTHON)
    if overlays:
        for relpath, content in overlays.items():
            full = d / relpath
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)


def source_prelude(paper_root: pathlib.Path, agent: str) -> tuple[int, str, str]:
    """Run a fresh shell that sources the prelude with monkeypatched profiles dir."""
    # We need the resolver to read fixture profiles. The plugin's profiles dir
    # is not yet populated at this point in implementation (Task 7 fills it).
    # So we wrap by using PLUGIN_ROOT pointing at a tmp dir that mirrors the
    # plugin layout but with profiles dir = fixture dir. Simpler: use the actual
    # plugin root and rely on the resolver --profiles-dir flag. The prelude does
    # not currently pass --profiles-dir; for tests, we override by setting
    # SWS_RESOLVER_PROFILES_DIR (recognized by a small shim).
    #
    # Pragmatic approach: prepare a temp plugin root with required scripts and a
    # profiles/ dir = symlink to fixtures.
    with tempfile.TemporaryDirectory() as plugin_tmp:
        plugin_root = pathlib.Path(plugin_tmp)
        (plugin_root / "scripts").mkdir()
        for f in ("agent_prelude.sh", "sws_python.sh", "resolve_overlay.py"):
            (plugin_root / "scripts" / f).symlink_to(ROOT / "scripts" / f)
        (plugin_root / "profiles").symlink_to(PROFILES_FIXTURE)
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
        env["PAPER_ROOT"] = str(paper_root)
        cmd = ["bash", "-c", f"source '{plugin_root}/scripts/agent_prelude.sh' '{agent}'; env"]
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return r.returncode, r.stdout, r.stderr


def parse_env(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if "=" in line and line.startswith("RESOLVED_"):
            k, _, v = line.partition("=")
            out[k] = v
    return out


COMMUNICATION_MARKER = "---\nprofile: communication\ntarget_journal: chembiochem\n---\n"
NULL_PROFILE_MARKER = "---\nprofile: null\n---\n"


class TestAgentPrelude(unittest.TestCase):
    def test_RESOLVED_OK_0_when_no_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper_with_venv(d, NULL_PROFILE_MARKER)
            code, stdout, stderr = source_prelude(d, "drafter")
            env = parse_env(stdout)
            self.assertEqual(env["RESOLVED_OK"], "0")
            self.assertIn("no profile set", stderr)

    def test_RESOLVED_OK_0_when_agent_inactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper_with_venv(d, COMMUNICATION_MARKER)
            code, stdout, stderr = source_prelude(d, "proposal-budget-helper")
            env = parse_env(stdout)
            self.assertEqual(env["RESOLVED_OK"], "0")
            self.assertIn("not active", stderr)

    def test_RESOLVED_OK_1_and_envvars_set_when_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper_with_venv(d, COMMUNICATION_MARKER)
            code, stdout, stderr = source_prelude(d, "drafter")
            env = parse_env(stdout)
            self.assertEqual(env["RESOLVED_OK"], "1", msg=stderr)
            self.assertEqual(env["RESOLVED_PROFILE_ID"], "communication")
            self.assertEqual(env["RESOLVED_REF_CAP"], "40")

    def test_RESOLVED_REF_CAP_reflects_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper_with_venv(
                d, COMMUNICATION_MARKER,
                overlays={"Manuscript/_journal-style/chembiochem.md": "---\nref_cap: 50\n---\n"},
            )
            code, stdout, stderr = source_prelude(d, "drafter")
            env = parse_env(stdout)
            self.assertEqual(env["RESOLVED_OK"], "1", msg=stderr)
            self.assertEqual(env["RESOLVED_REF_CAP"], "50")

    def test_RESOLVED_PROFILE_ID_reflects_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper_with_venv(d, "---\nprofile: funding-proposal\n---\n")
            code, stdout, stderr = source_prelude(d, "proposal-budget-helper")
            env = parse_env(stdout)
            self.assertEqual(env["RESOLVED_OK"], "1", msg=stderr)
            self.assertEqual(env["RESOLVED_PROFILE_ID"], "funding-proposal")


if __name__ == "__main__":
    unittest.main()
