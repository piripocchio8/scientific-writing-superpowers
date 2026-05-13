"""Tests for scripts/resolve_overlay.py — the 3-layer merge resolver.

Tests are run via the dev mamba env (PyYAML available). The resolver itself
is intended to be invoked by sws_python.sh through the per-paper .venv/.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

PYTHON = sys.executable
ROOT = pathlib.Path(__file__).resolve().parent.parent
RESOLVER = ROOT / "scripts" / "resolve_overlay.py"
FIXTURES = ROOT / "tests" / "fixtures"


def run_resolver(paper_root: pathlib.Path, agent: str | None = None,
                 profiles_dir: pathlib.Path | None = None) -> tuple[int, dict, str]:
    cmd = [PYTHON, str(RESOLVER), "--paper", str(paper_root)]
    if agent is not None:
        cmd += ["--agent", agent]
    if profiles_dir is not None:
        cmd += ["--profiles-dir", str(profiles_dir)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    payload_text = r.stdout if r.returncode == 0 else r.stderr
    try:
        payload = json.loads(payload_text) if payload_text.strip() else {}
    except json.JSONDecodeError:
        payload = {"_raw": payload_text}
    return r.returncode, payload, r.stderr


def make_paper(d: pathlib.Path, marker_lines: list[str],
               overlays: dict[str, str] | None = None) -> None:
    (d / ".sws-project.local.md").write_text("---\n" + "\n".join(marker_lines) + "\n---\n")
    if overlays:
        for relpath, content in overlays.items():
            full = d / relpath
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)


def write_journal_overlay(d: pathlib.Path, slug: str, content: str) -> None:
    overlay_dir = d / "Manuscript" / "_journal-style"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    (overlay_dir / f"{slug}.md").write_text(content)


def write_call_overlay(d: pathlib.Path, slug: str, content: str) -> None:
    overlay_dir = d / "Manuscript" / "_call"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    (overlay_dir / f"{slug}.md").write_text(content)


PROFILES_FIXTURE = FIXTURES / "profiles"


class TestResolverProfileLayer(unittest.TestCase):
    def test_emits_profile_set_false_for_null_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: null"])
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            self.assertFalse(payload["profile_set"])
            self.assertIsNone(payload["resolved_frontmatter"])

    def test_emits_profile_set_true_for_valid_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication"])
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            self.assertTrue(payload["profile_set"])
            self.assertEqual(payload["profile_id"], "communication")
            self.assertEqual(payload["resolved_frontmatter"]["ref_cap"], 40)

    def test_exits_4_when_marker_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 4)
            self.assertIn("marker not found", payload["error"])

    def test_exits_2_when_profile_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: not-a-real-profile"])
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 2)
            self.assertIn("unknown profile", payload["error"])


class TestResolverScalarMerge(unittest.TestCase):
    def test_profile_scalar_used_when_overlay_omits_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication", "target_journal: chembiochem"])
            write_journal_overlay(d, "chembiochem", "---\nword_total: 4000\n---\n")
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            self.assertEqual(payload["resolved_frontmatter"]["ref_cap"], 40)
            self.assertEqual(payload["resolved_frontmatter"]["word_total"], 4000)

    def test_overlay_scalar_overrides_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication", "target_journal: chembiochem"])
            write_journal_overlay(d, "chembiochem", "---\nref_cap: 50\n---\n")
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            self.assertEqual(payload["resolved_frontmatter"]["ref_cap"], 50)

    def test_overlay_explicit_null_drops_profile_value(self):
        # D17
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication", "target_journal: jacs"])
            write_journal_overlay(d, "jacs", (FIXTURES / "overlays" / "jacs-drops-refcap.md").read_text())
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            self.assertIsNone(payload["resolved_frontmatter"]["ref_cap"])
            self.assertEqual(payload["resolved_frontmatter"]["word_total"], 5000)


class TestResolverListMerge(unittest.TestCase):
    def test_overlay_sections_replaces_profile_sections(self):
        # D14 — overlay sections list replaces profile list entirely.
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication", "target_journal: chembiochem"])
            write_journal_overlay(d, "chembiochem",
                (FIXTURES / "overlays" / "chembiochem-replace-sections.md").read_text())
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            sections = payload["resolved_frontmatter"]["sections"]
            self.assertEqual(len(sections), 2)
            section_ids = [s["id"] for s in sections]
            self.assertEqual(section_ids, ["abstract", "body"])
            # Other overlay fields applied
            self.assertEqual(payload["resolved_frontmatter"]["ref_cap"], 50)

    def test_overlay_empty_sections_replaces_profile(self):
        # D14 corner case — overlay sets sections: [] explicitly.
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication", "target_journal: chembiochem"])
            write_journal_overlay(d, "chembiochem", "---\nsections: []\n---\n")
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            self.assertEqual(payload["resolved_frontmatter"]["sections"], [])

    def test_overlay_absent_sections_inherits_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication", "target_journal: chembiochem"])
            write_journal_overlay(d, "chembiochem", "---\nref_cap: 50\n---\n")
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            self.assertEqual(len(payload["resolved_frontmatter"]["sections"]), 4)


class TestResolverDiagnostics(unittest.TestCase):
    def test_missing_journal_overlay_is_warning_not_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication", "target_journal: chembiochem"])
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 0)
            self.assertTrue(payload["diagnostics"]["missing_journal_overlay"])
            self.assertIsNone(payload["journal_overlay_path"])
            self.assertGreater(len(payload["diagnostics"]["warnings"]), 0)

    def test_malformed_overlay_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            make_paper(d, ["profile: communication", "target_journal: bad"])
            write_journal_overlay(d, "bad",
                (FIXTURES / "overlays" / "malformed.md").read_text())
            code, payload, _ = run_resolver(d, profiles_dir=PROFILES_FIXTURE)
            self.assertEqual(code, 3)
            self.assertIn("malformed", payload["error"].lower())


if __name__ == "__main__":
    unittest.main()
