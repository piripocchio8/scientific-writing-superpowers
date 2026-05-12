"""Tests for sws_init_project.py — pure stdlib + unittest.

Tests grow incrementally per cycle-#2 task: slugify (Task 6),
validate_inputs (Task 7), scan_conflicts (Task 8), build_plan
(Task 9), apply_plan + rollback (Task 10).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sws_init_project  # noqa: E402


class TestSlugify(unittest.TestCase):
    def test_simple_lowercase(self):
        self.assertEqual(sws_init_project.slugify("Smith"), "smith")

    def test_unicode_umlaut(self):
        self.assertEqual(sws_init_project.slugify("Müller"), "muller")

    def test_apostrophe(self):
        self.assertEqual(sws_init_project.slugify("O'Brien"), "obrien")

    def test_hyphen(self):
        self.assertEqual(sws_init_project.slugify("Smith-Jones"), "smithjones")

    def test_diacritics_combined(self):
        self.assertEqual(sws_init_project.slugify("Søren"), "soren")
        self.assertEqual(sws_init_project.slugify("Şefik"), "sefik")
        self.assertEqual(sws_init_project.slugify("García"), "garcia")

    def test_whitespace_stripped(self):
        self.assertEqual(sws_init_project.slugify("  Smith  "), "smith")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            sws_init_project.slugify("")
        with self.assertRaises(ValueError):
            sws_init_project.slugify("   ")


class TestValidateInputs(unittest.TestCase):
    def _base_inputs(self, **overrides):
        defaults = {
            "article_type": "communication",
            "language": "en",
            "format": "docx",
            "target_journal": "chembiochem",
            "target_call": None,
            "first_author": "smith",
            "year": 2026,
            "co_authors_present": True,
            "notebooklm_enabled": False,
        }
        defaults.update(overrides)
        return defaults

    def test_communication_with_journal_passes(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs())
        self.assertTrue(ok, msg)

    def test_funding_proposal_requires_call(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal=None,
            target_call="prin-2025",
        ))
        self.assertTrue(ok, msg)

    def test_communication_with_call_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            target_call="prin-2025",
        ))
        self.assertFalse(ok)
        self.assertIn("target_call", msg)

    def test_funding_proposal_with_journal_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal="chembiochem",
            target_call="prin-2025",
        ))
        self.assertFalse(ok)
        self.assertIn("target_journal", msg)

    def test_funding_proposal_missing_call_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="funding-proposal",
            target_journal=None,
            target_call=None,
        ))
        self.assertFalse(ok)
        self.assertIn("target_call", msg)

    def test_non_funding_missing_journal_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            target_journal=None,
        ))
        self.assertFalse(ok)
        self.assertIn("target_journal", msg)

    def test_invalid_article_type_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            article_type="not-a-real-type",
        ))
        self.assertFalse(ok)
        self.assertIn("article_type", msg)

    def test_invalid_language_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            language="fr",
        ))
        self.assertFalse(ok)
        self.assertIn("language", msg)

    def test_invalid_format_fails(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            format="rtf",
        ))
        self.assertFalse(ok)
        self.assertIn("format", msg)

    def test_co_authors_present_must_be_bool(self):
        ok, msg = sws_init_project.validate_inputs(self._base_inputs(
            co_authors_present="yes",
        ))
        self.assertFalse(ok)
        self.assertIn("co_authors_present", msg)


class TestScanConflicts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _classes(self, conflicts):
        return sorted(c.cls for c in conflicts)

    def test_empty_dir_no_conflicts(self):
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(conflicts, [])

    def test_root_docx_detected_as_C1(self):
        (self.root / "paper.docx").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].cls, "C1")
        self.assertEqual(conflicts[0].path, "paper.docx")

    def test_loose_figures_detected_as_C2(self):
        (self.root / "Figures").mkdir()
        (self.root / "Figures" / "fig1.png").write_bytes(b"x")
        (self.root / "Figures" / "fig2.pdf").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C2", self._classes(conflicts))

    def test_existing_main_subdir_suppresses_C2(self):
        (self.root / "Figures" / "main").mkdir(parents=True)
        (self.root / "Figures" / "main" / "fig1.png").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertNotIn("C2", self._classes(conflicts))

    def test_claude_material_detected_as_C3(self):
        (self.root / "claude_material").mkdir()
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C3", self._classes(conflicts))

    def test_root_claude_md_detected_as_C4(self):
        (self.root / "CLAUDE.md").write_text("# my notes")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C4", self._classes(conflicts))

    def test_existing_claude_memory_detected_as_C5(self):
        (self.root / "claude_memory").mkdir()
        (self.root / "claude_memory" / "MEMORY.md").write_text("- one")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C5", self._classes(conflicts))

    def test_existing_marker_detected_as_C6(self):
        (self.root / ".sws-project.local.md").write_text("---\nsws_version: 0.1\n---")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("C6", self._classes(conflicts))

    def test_multiple_classes_detected_together(self):
        (self.root / "paper.docx").write_bytes(b"x")
        (self.root / "claude_material").mkdir()
        (self.root / "CLAUDE.md").write_text("notes")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertEqual(self._classes(conflicts), ["C1", "C3", "C4"])

    def test_conflict_has_suggested_action(self):
        (self.root / "paper.docx").write_bytes(b"x")
        conflicts = sws_init_project.scan_conflicts(self.root)
        self.assertIn("Manuscript/", conflicts[0].suggested_action)

    def test_C4_options_include_append(self):
        (self.root / "CLAUDE.md").write_text("# my notes")
        conflicts = sws_init_project.scan_conflicts(self.root)
        c4 = next(c for c in conflicts if c.cls == "C4")
        self.assertIn("append", c4.options)


class TestBuildPlan(unittest.TestCase):
    def _base_inputs(self, **overrides):
        defaults = {
            "article_type": "communication",
            "language": "en",
            "format": "docx",
            "target_journal": "chembiochem",
            "target_call": None,
            "first_author": "smith",
            "year": 2026,
            "co_authors_present": True,
            "notebooklm_enabled": False,
            "short_handle": "smith_et_al_2026",
            "created_iso": "2026-05-08T12:00:00Z",
        }
        defaults.update(overrides)
        return defaults

    def test_fresh_init_no_conflicts_produces_mkdirs_and_renders(self):
        plan = sws_init_project.build_plan(self._base_inputs(), conflicts=[], resolutions={})
        kinds = [op.kind for op in plan]
        self.assertIn("mkdir", kinds)
        self.assertIn("render_template", kinds)
        self.assertIn("write_json", kinds)
        # mkdirs must come before any render that writes inside them
        first_render = next(i for i, op in enumerate(plan) if op.kind == "render_template")
        first_mkdir = next(i for i, op in enumerate(plan) if op.kind == "mkdir")
        self.assertLess(first_mkdir, first_render)

    def test_funding_proposal_creates_call_dir(self):
        inputs = self._base_inputs(
            article_type="funding-proposal",
            target_journal=None,
            target_call="prin-2025",
        )
        plan = sws_init_project.build_plan(inputs, conflicts=[], resolutions={})
        mkdir_dests = [op.dest for op in plan if op.kind == "mkdir"]
        self.assertIn("call", mkdir_dests)

    def test_non_funding_does_not_create_call_dir(self):
        plan = sws_init_project.build_plan(self._base_inputs(), conflicts=[], resolutions={})
        mkdir_dests = [op.dest for op in plan if op.kind == "mkdir"]
        self.assertNotIn("call", mkdir_dests)

    def test_notebooklm_enabled_creates_nlm_uploads(self):
        inputs = self._base_inputs(notebooklm_enabled=True)
        plan = sws_init_project.build_plan(inputs, conflicts=[], resolutions={})
        mkdir_dests = [op.dest for op in plan if op.kind == "mkdir"]
        self.assertIn("refs/nlm_uploads", mkdir_dests)

    def test_C1_accept_produces_mv_op(self):
        from sws_init_project import Conflict
        c = Conflict(cls="C1", path="paper.docx",
                     suggested_action="Move to Manuscript/paper.docx",
                     options=["Y", "n", "skip", "manual"])
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[c],
            resolutions={"C1": "accept"},
        )
        mv_ops = [op for op in plan if op.kind == "mv"]
        self.assertTrue(any(op.source == "paper.docx" and op.dest == "Manuscript/paper.docx"
                            for op in mv_ops))

    def test_C1_skip_produces_no_mv(self):
        from sws_init_project import Conflict
        c = Conflict(cls="C1", path="paper.docx",
                     suggested_action="Move to Manuscript/paper.docx",
                     options=["Y", "n", "skip", "manual"])
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[c],
            resolutions={"C1": "skip"},
        )
        mv_ops = [op for op in plan if op.kind == "mv"]
        self.assertFalse(any(op.source == "paper.docx" for op in mv_ops))

    def test_C3_accept_renames_claude_material_to_scratch(self):
        from sws_init_project import Conflict
        c = Conflict(cls="C3", path="claude_material/",
                     suggested_action="Rename to scratch/",
                     options=["Y", "n", "skip", "manual"])
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[c],
            resolutions={"C3": "accept"},
        )
        mv_ops = [op for op in plan if op.kind == "mv"]
        self.assertTrue(any(op.source == "claude_material" and op.dest == "scratch"
                            for op in mv_ops))

    def test_template_render_ops_use_correct_template_paths(self):
        plan = sws_init_project.build_plan(self._base_inputs(), conflicts=[], resolutions={})
        renders = [op for op in plan if op.kind == "render_template"]
        templates_used = {op.source for op in renders}
        self.assertEqual(templates_used, {
            "templates/sws-project-marker.template",
            "templates/manuscript-claude-md.template",
            "templates/manuscript-memory-md.template",
        })


class TestBuildPlanResolutions(unittest.TestCase):
    """Verify C4/C5 resolutions gate the corresponding render/write ops.

    Regression coverage for the data-loss bug surfaced in Task 12 smoke test.
    """
    def _base_inputs(self, **overrides):
        defaults = {
            "article_type": "communication",
            "language": "en",
            "format": "docx",
            "target_journal": "chembiochem",
            "target_call": None,
            "first_author": "smith",
            "year": 2026,
            "co_authors_present": True,
            "notebooklm_enabled": False,
            "short_handle": "smith_et_al_2026",
            "created_iso": "2026-05-08T12:00:00Z",
        }
        defaults.update(overrides)
        return defaults

    def _c4(self):
        from sws_init_project import Conflict
        return Conflict(cls="C4", path="CLAUDE.md",
                        suggested_action="[r]eplace with SWS template / [a]ppend SWS-managed section / [s]kip (leave file untouched)",
                        options=["replace", "append", "skip"])

    def _c5(self):
        from sws_init_project import Conflict
        return Conflict(cls="C5", path="claude_memory/",
                        suggested_action="[k]eep existing (no SWS writes inside) / [r]eplace MEMORY.md + passport.json only",
                        options=["keep", "replace"])

    def _dests_of_kind(self, plan, kind):
        return [op.dest for op in plan if op.kind == kind]

    def test_fresh_init_emits_all_renders(self):
        plan = sws_init_project.build_plan(self._base_inputs(), conflicts=[], resolutions={})
        render_dests = self._dests_of_kind(plan, "render_template")
        write_json_dests = self._dests_of_kind(plan, "write_json")
        self.assertIn(".sws-project.local.md", render_dests)
        self.assertIn("CLAUDE.md", render_dests)
        self.assertIn("claude_memory/MEMORY.md", render_dests)
        self.assertIn("claude_memory/passport.json", write_json_dests)

    def test_C4_skip_omits_claude_md_render(self):
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[self._c4()],
            resolutions={"C4": "skip"},
        )
        render_dests = self._dests_of_kind(plan, "render_template")
        self.assertNotIn("CLAUDE.md", render_dests)
        # Marker and MEMORY still rendered
        self.assertIn(".sws-project.local.md", render_dests)
        self.assertIn("claude_memory/MEMORY.md", render_dests)

    def test_C4_replace_emits_claude_md_render(self):
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[self._c4()],
            resolutions={"C4": "replace"},
        )
        render_dests = self._dests_of_kind(plan, "render_template")
        self.assertIn("CLAUDE.md", render_dests)

    def test_C5_keep_omits_memory_render_and_passport(self):
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[self._c5()],
            resolutions={"C5": "keep"},
        )
        render_dests = self._dests_of_kind(plan, "render_template")
        write_json_dests = self._dests_of_kind(plan, "write_json")
        self.assertNotIn("claude_memory/MEMORY.md", render_dests)
        self.assertNotIn("claude_memory/passport.json", write_json_dests)
        # Marker and CLAUDE.md still rendered
        self.assertIn(".sws-project.local.md", render_dests)
        self.assertIn("CLAUDE.md", render_dests)

    def test_C5_replace_emits_memory_render_and_passport(self):
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[self._c5()],
            resolutions={"C5": "replace"},
        )
        render_dests = self._dests_of_kind(plan, "render_template")
        write_json_dests = self._dests_of_kind(plan, "write_json")
        self.assertIn("claude_memory/MEMORY.md", render_dests)
        self.assertIn("claude_memory/passport.json", write_json_dests)

    def test_C4_append_emits_append_op_and_omits_render(self):
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[self._c4()],
            resolutions={"C4": "append"},
        )
        render_dests = self._dests_of_kind(plan, "render_template")
        append_dests = self._dests_of_kind(plan, "append_sws_section")
        self.assertNotIn("CLAUDE.md", render_dests)
        self.assertIn("CLAUDE.md", append_dests)
        # Marker + MEMORY/passport still emitted
        self.assertIn(".sws-project.local.md", render_dests)
        self.assertIn("claude_memory/MEMORY.md", render_dests)

    def test_C4_and_C5_both_skip_renders_only_marker(self):
        plan = sws_init_project.build_plan(
            self._base_inputs(),
            conflicts=[self._c4(), self._c5()],
            resolutions={"C4": "skip", "C5": "keep"},
        )
        render_dests = self._dests_of_kind(plan, "render_template")
        write_json_dests = self._dests_of_kind(plan, "write_json")
        self.assertEqual(render_dests, [".sws-project.local.md"])
        self.assertEqual(write_json_dests, [])


class TestApplyPlan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # plugin templates need to be reachable; tests use real templates from repo
        self.plugin_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, plan):
        return sws_init_project.apply_plan(
            plan, project_root=self.root, plugin_root=self.plugin_root,
        )

    def test_mkdir_creates_dirs(self):
        from sws_init_project import Op
        plan = [Op(kind="mkdir", dest="Manuscript"),
                Op(kind="mkdir", dest="Figures/main")]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        self.assertTrue((self.root / "Manuscript").is_dir())
        self.assertTrue((self.root / "Figures" / "main").is_dir())

    def test_mv_moves_file(self):
        from sws_init_project import Op
        (self.root / "paper.docx").write_bytes(b"abc")
        plan = [Op(kind="mkdir", dest="Manuscript"),
                Op(kind="mv", source="paper.docx", dest="Manuscript/paper.docx")]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        self.assertFalse((self.root / "paper.docx").exists())
        self.assertTrue((self.root / "Manuscript" / "paper.docx").exists())

    def test_render_template_uses_renderer(self):
        from sws_init_project import Op
        plan = [
            Op(kind="mkdir", dest="claude_memory"),
            Op(kind="render_template",
               source="templates/manuscript-memory-md.template",
               dest="claude_memory/MEMORY.md",
               extra={"vars": {}}),
        ]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        self.assertTrue((self.root / "claude_memory" / "MEMORY.md").exists())
        content = (self.root / "claude_memory" / "MEMORY.md").read_text()
        self.assertIn("Project marker", content)

    def test_write_json_creates_file(self):
        from sws_init_project import Op
        plan = [
            Op(kind="mkdir", dest="claude_memory"),
            Op(kind="write_json",
               dest="claude_memory/passport.json",
               extra={"content": {"cycle": 0}}),
        ]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        data = json.loads((self.root / "claude_memory" / "passport.json").read_text())
        self.assertEqual(data, {"cycle": 0})

    def test_rollback_on_failed_op(self):
        from sws_init_project import Op
        (self.root / "paper.docx").write_bytes(b"original")
        plan = [
            Op(kind="mkdir", dest="Manuscript"),
            Op(kind="mv", source="paper.docx", dest="Manuscript/paper.docx"),
            # 3rd op intentionally invalid: source missing
            Op(kind="mv", source="nonexistent_source", dest="anywhere"),
        ]
        ok, log = self._run(plan)
        self.assertFalse(ok)
        # rollback should restore paper.docx to root
        self.assertTrue((self.root / "paper.docx").exists())
        self.assertEqual((self.root / "paper.docx").read_bytes(), b"original")
        # Manuscript/paper.docx should be gone
        self.assertFalse((self.root / "Manuscript" / "paper.docx").exists())
        # Manuscript/ dir is created by op 1; rollback removes it
        self.assertFalse((self.root / "Manuscript").exists())

    def test_rollback_does_not_remove_user_files(self):
        from sws_init_project import Op
        (self.root / "user_file.txt").write_text("hands off")
        plan = [
            Op(kind="mkdir", dest="Manuscript"),
            Op(kind="mv", source="nonexistent", dest="anywhere"),
        ]
        ok, log = self._run(plan)
        self.assertFalse(ok)
        # User-pre-existing file untouched
        self.assertEqual((self.root / "user_file.txt").read_text(), "hands off")


class TestAppendSwsSection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.plugin_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, plan):
        return sws_init_project.apply_plan(
            plan, project_root=self.root, plugin_root=self.plugin_root,
        )

    def test_append_sws_section_to_file_without_markers(self):
        from sws_init_project import Op, SWS_MARKER_OPEN, SWS_MARKER_CLOSE
        (self.root / "CLAUDE.md").write_text("# user notes\n\nexisting content\n")
        plan = [Op(kind="append_sws_section", dest="CLAUDE.md",
                   extra={"short_handle": "smith_et_al_2026"})]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        content = (self.root / "CLAUDE.md").read_text()
        self.assertIn("# user notes", content)
        self.assertIn("existing content", content)
        self.assertIn(SWS_MARKER_OPEN, content)
        self.assertIn(SWS_MARKER_CLOSE, content)
        self.assertIn("smith_et_al_2026", content)
        # User content comes before SWS section
        self.assertLess(content.index("existing content"), content.index(SWS_MARKER_OPEN))

    def test_append_sws_section_with_existing_markers_replaces_idempotently(self):
        from sws_init_project import Op, SWS_MARKER_OPEN, SWS_MARKER_CLOSE
        initial = (
            "# user notes\n\n"
            f"{SWS_MARKER_OPEN}\n\nold sws block with old_handle\n\n{SWS_MARKER_CLOSE}\n"
            "\nmore user content below\n"
        )
        (self.root / "CLAUDE.md").write_text(initial)
        plan = [Op(kind="append_sws_section", dest="CLAUDE.md",
                   extra={"short_handle": "new_handle_2027"})]
        ok, log = self._run(plan)
        self.assertTrue(ok, log)
        content = (self.root / "CLAUDE.md").read_text()
        # Old block content gone
        self.assertNotIn("old sws block with old_handle", content)
        # New short_handle in
        self.assertIn("new_handle_2027", content)
        # User content surrounding the markers preserved
        self.assertIn("# user notes", content)
        self.assertIn("more user content below", content)
        # Exactly one open marker and one close marker
        self.assertEqual(content.count(SWS_MARKER_OPEN), 1)
        self.assertEqual(content.count(SWS_MARKER_CLOSE), 1)

    def test_append_sws_section_rollback_restores_original(self):
        from sws_init_project import Op
        original = "# original user content\n"
        (self.root / "CLAUDE.md").write_text(original)
        plan = [
            Op(kind="append_sws_section", dest="CLAUDE.md",
               extra={"short_handle": "smith_2026"}),
            # Force a failure on a subsequent op so rollback kicks in
            Op(kind="mv", source="nonexistent", dest="anywhere"),
        ]
        ok, log = self._run(plan)
        self.assertFalse(ok)
        # CLAUDE.md restored to original
        self.assertEqual((self.root / "CLAUDE.md").read_text(), original)

    def test_append_sws_section_fails_if_claude_md_missing(self):
        from sws_init_project import Op
        plan = [Op(kind="append_sws_section", dest="CLAUDE.md",
                   extra={"short_handle": "smith_2026"})]
        ok, log = self._run(plan)
        self.assertFalse(ok)
        # The error message should mention CLAUDE.md or that the file is missing
        self.assertTrue(any("CLAUDE.md" in line or "not found" in line for line in log),
                        f"Expected failure log to mention missing file; got {log}")


class TestDefaultResolutions(unittest.TestCase):
    """Verify safe-default resolution for each conflict class.

    Defaults are data-loss-safe: accept/append/keep/proceed only.
    Destructive options (replace) never appear in defaults.
    """
    def _conflict(self, cls, **kwargs):
        from sws_init_project import Conflict
        defaults = {"path": "x", "suggested_action": "x", "options": []}
        defaults.update(kwargs)
        return Conflict(cls=cls, **defaults)

    def test_C1_defaults_to_accept(self):
        d = sws_init_project.default_resolutions([self._conflict("C1")])
        self.assertEqual(d, {"C1": "accept"})

    def test_C2_defaults_to_accept(self):
        d = sws_init_project.default_resolutions([self._conflict("C2")])
        self.assertEqual(d, {"C2": "accept"})

    def test_C3_defaults_to_accept(self):
        d = sws_init_project.default_resolutions([self._conflict("C3")])
        self.assertEqual(d, {"C3": "accept"})

    def test_C4_defaults_to_append_not_replace(self):
        d = sws_init_project.default_resolutions([self._conflict("C4")])
        self.assertEqual(d, {"C4": "append"})
        # Make sure we don't default to the destructive option
        self.assertNotEqual(d["C4"], "replace")

    def test_C5_defaults_to_keep_not_replace(self):
        d = sws_init_project.default_resolutions([self._conflict("C5")])
        self.assertEqual(d, {"C5": "keep"})
        self.assertNotEqual(d["C5"], "replace")

    def test_C6_defaults_to_proceed(self):
        d = sws_init_project.default_resolutions([self._conflict("C6")])
        self.assertEqual(d, {"C6": "proceed"})

    def test_all_six_classes_together(self):
        d = sws_init_project.default_resolutions([
            self._conflict("C1"), self._conflict("C2"), self._conflict("C3"),
            self._conflict("C4"), self._conflict("C5"), self._conflict("C6"),
        ])
        self.assertEqual(d, {
            "C1": "accept", "C2": "accept", "C3": "accept",
            "C4": "append", "C5": "keep", "C6": "proceed",
        })

    def test_empty_conflicts_returns_empty_dict(self):
        self.assertEqual(sws_init_project.default_resolutions([]), {})

    def test_unknown_class_is_omitted(self):
        """Forward-compat: a class not in SAFE_DEFAULTS is skipped, not raised."""
        d = sws_init_project.default_resolutions([self._conflict("C99")])
        self.assertEqual(d, {})


if __name__ == "__main__":
    unittest.main()
