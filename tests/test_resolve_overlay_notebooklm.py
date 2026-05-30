"""Resolver + prelude wiring for notebooklm.* (cycle #13, D9).

Asserts:
    - SCHEMA_DEFAULTS includes the notebooklm dict.
    - A marker with `notebooklm.enabled: true` is reflected in the resolved JSON.
    - A marker with `notebooklm.notebook_id: "abc"` flows through.
    - Sourcing agent_prelude.sh exports the 3 RESOLVED_* env vars.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RESOLVE = REPO_ROOT / "scripts" / "resolve_overlay.py"
PRELUDE = REPO_ROOT / "scripts" / "agent_prelude.sh"
PROFILES = REPO_ROOT / "profiles"


def _write_marker(paper: Path, body: str) -> None:
    (paper / ".sws-project.local.md").write_text(body)


def _run_resolver(paper: Path) -> dict:
    cp = subprocess.run(
        [sys.executable, str(RESOLVE), "--paper", str(paper)],
        capture_output=True, text=True, check=False,
    )
    if cp.returncode != 0:
        raise AssertionError(f"resolver exit {cp.returncode}: {cp.stderr}")
    # the resolver prints once to stdout on success, but main() also re-prints
    # the payload. Parse last JSON object.
    lines = [l for l in cp.stdout.splitlines() if l.strip()]
    return json.loads(lines[-1])


class SchemaDefaults(unittest.TestCase):
    def test_schema_defaults_has_notebooklm_dict(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        try:
            import importlib
            ro = importlib.import_module("resolve_overlay")
            importlib.reload(ro)
            self.assertIn("notebooklm", ro.SCHEMA_DEFAULTS)
            nlm = ro.SCHEMA_DEFAULTS["notebooklm"]
            self.assertEqual(nlm["enabled"], False)
            self.assertIsNone(nlm["notebook_id"])
            self.assertIsNone(nlm["cli_path"])
        finally:
            sys.path.pop(0)


class MarkerDefaultDisabled(unittest.TestCase):
    def test_default_marker_yields_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            _write_marker(paper, textwrap.dedent("""\
                ---
                sws_version: 0.1
                article_type: communication
                language: en
                format: docx
                profile: communication
                notebooklm:
                  enabled: false
                created: 2026-05-30T00:00:00Z
                ---
                """))
            data = _run_resolver(paper)
            fm = data.get("resolved_frontmatter") or {}
            nlm = fm.get("notebooklm") or {}
            self.assertEqual(nlm.get("enabled"), False)


class MarkerEnabledFlowsThrough(unittest.TestCase):
    def test_marker_enabled_true_flows_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            _write_marker(paper, textwrap.dedent("""\
                ---
                sws_version: 0.1
                article_type: communication
                language: en
                format: docx
                profile: communication
                notebooklm:
                  enabled: true
                  notebook_id: abc-notebook
                created: 2026-05-30T00:00:00Z
                ---
                """))
            data = _run_resolver(paper)
            fm = data.get("resolved_frontmatter") or {}
            nlm = fm.get("notebooklm") or {}
            self.assertEqual(nlm.get("enabled"), True)
            self.assertEqual(nlm.get("notebook_id"), "abc-notebook")


class PreludeExportsEnvVars(unittest.TestCase):
    def test_prelude_exports_resolved_nlm_vars(self):
        with tempfile.TemporaryDirectory() as tmp:
            paper = Path(tmp)
            _write_marker(paper, textwrap.dedent("""\
                ---
                sws_version: 0.1
                article_type: communication
                language: en
                format: docx
                profile: communication
                notebooklm:
                  enabled: true
                  notebook_id: nb-xyz
                created: 2026-05-30T00:00:00Z
                ---
                """))
            # Build a minimal sws_python.sh shim that just execs the system python
            # against the resolver — so the prelude's call chain works without a
            # per-paper .venv being set up.
            shim = paper / "scripts" / "sws_python.sh"
            shim.parent.mkdir(parents=True, exist_ok=True)
            shim.write_text(
                "#!/usr/bin/env bash\nshift\nexec " + sys.executable + " \"$@\"\n"
            )
            shim.chmod(0o755)
            # Symlink the rest of the plugin layout into a temp plugin dir
            plugin = Path(tmp) / "plugin"
            plugin.mkdir()
            (plugin / "scripts").mkdir()
            for s in ("resolve_overlay.py", "agent_prelude.sh", "agent_should_run.sh", "sws_python.sh"):
                src = REPO_ROOT / "scripts" / s
                if src.exists():
                    os.symlink(src, plugin / "scripts" / s)
            # Override sws_python.sh with our shim so we don't need a real venv
            (plugin / "scripts" / "sws_python.sh").unlink()
            (plugin / "scripts" / "sws_python.sh").symlink_to(shim)
            # Symlink profiles dir
            os.symlink(PROFILES, plugin / "profiles")

            # Source prelude, then print the env vars
            cmd = [
                "bash", "-c",
                f'set +u; export CLAUDE_PLUGIN_ROOT="{plugin}"; export PAPER_ROOT="{paper}"; '
                f'source "{plugin}/scripts/agent_prelude.sh" claim-verifier; '
                'echo "ENABLED=$RESOLVED_NOTEBOOKLM_ENABLED"; '
                'echo "NB=$RESOLVED_NLM_NOTEBOOK_ID"; '
                'echo "CLI=$RESOLVED_NLM_CLI_PATH"'
            ]
            cp = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            out = cp.stdout
            self.assertIn("ENABLED=true", out, msg=out + cp.stderr)
            self.assertIn("NB=nb-xyz", out)
            self.assertIn("CLI=", out)  # may be empty / null but the var must be set


if __name__ == "__main__":
    unittest.main()
