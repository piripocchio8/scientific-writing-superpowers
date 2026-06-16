"""Tests for scripts/sws_nlm.sh — the CLI wrapper around notebooklm-mcp-cli (cycle #13).

Each test sets up a temp directory with a fake `notebooklm-mcp-cli` stub script
when needed, prepends it to PATH, and invokes the wrapper via subprocess. The
wrapper itself uses bash + python3 only — no third-party deps.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
WRAPPER = REPO_ROOT / "scripts" / "sws_nlm.sh"
FIXTURE_STUB = REPO_ROOT / "tests" / "fixtures" / "sample-cycle-13" / "fake_notebooklm_mcp_cli.sh"


def _stub_path(tmp: Path, name: str = "notebooklm-mcp-cli", env: dict | None = None) -> Path:
    """Copy the fixture stub into tmp under the requested binary name + chmod +x."""
    dest = tmp / name
    dest.write_text(FIXTURE_STUB.read_text())
    dest.chmod(0o755)
    return dest


def _run(args, env_overrides=None, expect_clean_env=True) -> subprocess.CompletedProcess:
    env = {} if expect_clean_env else os.environ.copy()
    # Always start from a clean slate for the SWS_NLM_* vars so cached probe
    # results from prior tests do not leak.
    env.update({
        "PATH": "/usr/bin:/bin",  # nothing in here resolves notebooklm-mcp-cli
        "RESOLVED_NOTEBOOKLM_ENABLED": "false",
        "RESOLVED_NLM_NOTEBOOK_ID": "",
        "RESOLVED_NLM_CLI_PATH": "",
    })
    # Clear any cached probe result inherited from the surrounding environment
    # BEFORE applying explicit test overrides (so the override wins).
    env.pop("SWS_NLM_PROBE_RESULT", None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(WRAPPER), *args],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class ProbeDisabled(unittest.TestCase):
    def test_probe_disabled_exits_0_with_stderr_notice(self):
        cp = _run(["probe"])
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertIn("disabled", cp.stderr.lower())


class ProbeMissing(unittest.TestCase):
    def test_probe_enabled_no_binary_exits_4(self):
        cp = _run(["probe"], env_overrides={"RESOLVED_NOTEBOOKLM_ENABLED": "true"})
        self.assertEqual(cp.returncode, 4, msg=cp.stderr)
        self.assertIn("not found", cp.stderr.lower())


class ProbeOk(unittest.TestCase):
    def test_probe_with_stub_returns_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _stub_path(tmp)
            cp = _run(
                ["probe"],
                env_overrides={
                    "RESOLVED_NOTEBOOKLM_ENABLED": "true",
                    "PATH": f"{tmp}:/usr/bin:/bin",
                },
            )
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertIn("probe ok", cp.stderr.lower())


class ProbeAuth(unittest.TestCase):
    def test_auth_failure_exits_5(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _stub_path(tmp)
            cp = _run(
                ["probe"],
                env_overrides={
                    "RESOLVED_NOTEBOOKLM_ENABLED": "true",
                    "PATH": f"{tmp}:/usr/bin:/bin",
                    "FAKE_NLM_AUTH_FAIL": "1",
                },
            )
            self.assertEqual(cp.returncode, 5, msg=cp.stderr)


class QueryHappyPath(unittest.TestCase):
    def test_query_returns_normalized_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _stub_path(tmp)
            cp = _run(
                ["query", "what is foo?"],
                env_overrides={
                    "RESOLVED_NOTEBOOKLM_ENABLED": "true",
                    "PATH": f"{tmp}:/usr/bin:/bin",
                },
            )
            self.assertEqual(cp.returncode, 0, msg=cp.stderr + cp.stdout)
            data = json.loads(cp.stdout)
            self.assertTrue(data["ok"])
            self.assertEqual(data["answer"], "fake answer")
            self.assertEqual(data["fallback"], "none")
            self.assertEqual(data["query"], "what is foo?")
            self.assertEqual(len(data["sources"]), 1)
            self.assertEqual(data["sources"][0]["page"], 1)


class QueryDegradeDisabled(unittest.TestCase):
    def test_query_with_disabled_returns_degrade_json_exit_0(self):
        cp = _run(["query", "anything"])
        self.assertEqual(cp.returncode, 0)
        data = json.loads(cp.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["fallback"], "disabled")


class QueryDegradeMissing(unittest.TestCase):
    def test_query_with_enabled_but_no_binary_returns_degrade_json(self):
        cp = _run(
            ["query", "anything"],
            env_overrides={"RESOLVED_NOTEBOOKLM_ENABLED": "true"},
        )
        self.assertEqual(cp.returncode, 0)
        data = json.loads(cp.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["fallback"], "missing")


class QueryMalformedExit5(unittest.TestCase):
    def test_query_malformed_binary_output_exits_5(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _stub_path(tmp)
            cp = _run(
                ["query", "anything"],
                env_overrides={
                    "RESOLVED_NOTEBOOKLM_ENABLED": "true",
                    "PATH": f"{tmp}:/usr/bin:/bin",
                    "FAKE_NLM_MALFORMED": "1",
                },
            )
            self.assertEqual(cp.returncode, 5, msg=cp.stdout + cp.stderr)
            self.assertIn("unexpected format", cp.stderr.lower())


class ListNotebooksHappy(unittest.TestCase):
    def test_list_notebooks_returns_json_array(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _stub_path(tmp)
            cp = _run(
                ["list-notebooks"],
                env_overrides={
                    "RESOLVED_NOTEBOOKLM_ENABLED": "true",
                    "PATH": f"{tmp}:/usr/bin:/bin",
                },
            )
            self.assertEqual(cp.returncode, 0, msg=cp.stderr + cp.stdout)
            data = json.loads(cp.stdout)
            self.assertIsInstance(data, list)
            self.assertEqual(data[0]["id"], "nb1")


class ProbeCache(unittest.TestCase):
    def test_cached_probe_result_skips_reprobing(self):
        # When SWS_NLM_PROBE_RESULT=ok, probe should print 'ok' without ever
        # consulting the binary — i.e. even with no binary on PATH, exit 0 is fine.
        cp = _run(
            ["probe"],
            env_overrides={
                "RESOLVED_NOTEBOOKLM_ENABLED": "true",
                "SWS_NLM_PROBE_RESULT": "ok",
            },
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertIn("probe ok", cp.stderr.lower())


class CliPathOverride(unittest.TestCase):
    def test_cli_path_overrides_path_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            stub = _stub_path(tmp, name="some-other-name")
            cp = _run(
                ["probe"],
                env_overrides={
                    "RESOLVED_NOTEBOOKLM_ENABLED": "true",
                    "RESOLVED_NLM_CLI_PATH": str(stub),
                },
            )
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)


class UsageErrors(unittest.TestCase):
    def test_no_args_exits_2(self):
        cp = _run([])
        self.assertEqual(cp.returncode, 2)
        self.assertIn("usage", cp.stderr.lower())

    def test_unknown_subcommand_exits_2(self):
        cp = _run(["frobnicate"])
        self.assertEqual(cp.returncode, 2)

    def test_query_without_question_exits_2(self):
        cp = _run(["query"])
        self.assertEqual(cp.returncode, 2)


class SubcommandSurface(unittest.TestCase):
    """D3: locked v0.1 surface area — only probe / query / list-notebooks."""

    def test_only_three_subcommands_are_recognized(self):
        for sub in ("upload", "delete", "search-history", "config"):
            cp = _run([sub])
            self.assertNotEqual(cp.returncode, 0, msg=f"{sub!r} should not be accepted")


if __name__ == "__main__":
    unittest.main()
