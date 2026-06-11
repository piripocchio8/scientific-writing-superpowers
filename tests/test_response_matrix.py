"""Tests for sws_response_matrix.py (cycle-12 D5 / D6 / R3)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from sws_response_matrix import (  # noqa: E402
    detect_shape, infer_severity, main, merge_with_existing,
    parse_shape_a, parse_shape_b, parse_shape_c,
)


SHAPE_A = """\
## Reviewer 1
1. The novelty claim in the abstract overreaches.
2. Figure 3 lacks error bars.
## Reviewer 2
- Methodology is sound but Section 4.2 needs clarification.
- The introduction must cite ref. X.
"""

SHAPE_B = """\
1. The introduction misses ref. X.
2. Equation 3 needs derivation.
3. Consider expanding the discussion.
"""

SHAPE_C = """\
R1.1: The novelty claim overreaches.
R1.2: Figure 3 lacks error bars.
R2.1: Section 4.2 needs clarification.
"""

UNSHAPED = "Just a wall of prose with no structure whatsoever.\n"


class ShapeDetectionTests(unittest.TestCase):
    def test_detects_shape_a(self):
        self.assertEqual(detect_shape(SHAPE_A.splitlines()), "a")

    def test_detects_shape_b(self):
        self.assertEqual(detect_shape(SHAPE_B.splitlines()), "b")

    def test_detects_shape_c(self):
        self.assertEqual(detect_shape(SHAPE_C.splitlines()), "c")

    def test_unshaped_returns_none(self):
        self.assertIsNone(detect_shape(UNSHAPED.splitlines()))


class ParseTests(unittest.TestCase):
    def test_shape_a_parses_2_reviewers(self):
        out = parse_shape_a(SHAPE_A.splitlines())
        self.assertEqual(len(out), 4)
        ids = [c["id"] for c in out]
        self.assertEqual(ids, ["R1.1", "R1.2", "R2.1", "R2.2"])
        # reviewer field is correct int
        self.assertEqual(out[0]["reviewer"], 1)
        self.assertEqual(out[2]["reviewer"], 2)

    def test_shape_b_implicit_reviewer_1(self):
        out = parse_shape_b(SHAPE_B.splitlines())
        self.assertEqual(len(out), 3)
        self.assertTrue(all(c["reviewer"] == 1 for c in out))
        self.assertEqual([c["id"] for c in out], ["R1.1", "R1.2", "R1.3"])

    def test_shape_c_prefixed_ids(self):
        out = parse_shape_c(SHAPE_C.splitlines())
        self.assertEqual(len(out), 3)
        self.assertEqual([c["id"] for c in out], ["R1.1", "R1.2", "R2.1"])
        # Verify R2.1 reviewer
        r21 = next(c for c in out if c["id"] == "R2.1")
        self.assertEqual(r21["reviewer"], 2)

    def test_default_fields_present(self):
        out = parse_shape_a(SHAPE_A.splitlines())
        c = out[0]
        self.assertEqual(c["status"], "pending")
        self.assertEqual(c["response_text"], "")
        self.assertEqual(c["edits_made"], [])
        self.assertEqual(c["line_refs"], [])
        self.assertIn("severity_inferred", c)


class SeverityTests(unittest.TestCase):
    def test_must_is_major(self):
        self.assertEqual(infer_severity("This must be cited."), "major")

    def test_should_is_major(self):
        self.assertEqual(infer_severity("This should be clarified."), "major")

    def test_consider_is_suggestion(self):
        self.assertEqual(infer_severity("Consider rephrasing."), "suggestion")

    def test_might_is_suggestion(self):
        self.assertEqual(infer_severity("You might cite that."), "suggestion")

    def test_neutral_is_minor(self):
        self.assertEqual(infer_severity("The phrasing is awkward."), "minor")


class IdempotencyTests(unittest.TestCase):
    """R3 — re-parse preserves agent-filled fields when id is unchanged."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.in_path = self.dir / "reviewer-comments.md"
        self.in_path.write_text(SHAPE_A)
        self.out_path = self.dir / "response-matrix.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_preserves_status_response_text_edits_line_refs(self):
        # First parse.
        self.assertEqual(main([str(self.in_path), "--out", str(self.out_path)]), 0)
        data = json.loads(self.out_path.read_text())
        # Simulate agent filling fields on R1.1.
        for c in data:
            if c["id"] == "R1.1":
                c["status"] = "accepted"
                c["response_text"] = "Agreed; reworded."
                c["edits_made"] = ["abstract: softened novelty claim"]
                c["line_refs"] = ["_drafts/abstract.md:3"]
        self.out_path.write_text(json.dumps(data))

        # Re-parse — fields should survive.
        self.assertEqual(main([str(self.in_path), "--out", str(self.out_path)]), 0)
        data2 = json.loads(self.out_path.read_text())
        r11 = next(c for c in data2 if c["id"] == "R1.1")
        self.assertEqual(r11["status"], "accepted")
        self.assertEqual(r11["response_text"], "Agreed; reworded.")
        self.assertEqual(r11["edits_made"], ["abstract: softened novelty claim"])
        self.assertEqual(r11["line_refs"], ["_drafts/abstract.md:3"])

    def test_new_comments_appended(self):
        self.assertEqual(main([str(self.in_path), "--out", str(self.out_path)]), 0)
        # Add a new comment to the source.
        extra = SHAPE_A + "## Reviewer 3\n1. A wholly new concern.\n"
        self.in_path.write_text(extra)
        self.assertEqual(main([str(self.in_path), "--out", str(self.out_path)]), 0)
        data2 = json.loads(self.out_path.read_text())
        self.assertIn("R3.1", [c["id"] for c in data2])

    def test_deleted_comments_dropped(self):
        self.assertEqual(main([str(self.in_path), "--out", str(self.out_path)]), 0)
        # Remove all of Reviewer 2.
        shortened = "## Reviewer 1\n1. The novelty claim in the abstract overreaches.\n"
        self.in_path.write_text(shortened)
        self.assertEqual(main([str(self.in_path), "--out", str(self.out_path)]), 0)
        data2 = json.loads(self.out_path.read_text())
        ids = [c["id"] for c in data2]
        self.assertEqual(ids, ["R1.1"])


class CLIShapeFailureTests(unittest.TestCase):
    def test_unrecognised_shape_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            in_path = Path(tmp) / "bad.md"
            in_path.write_text(UNSHAPED)
            self.assertEqual(main([str(in_path)]), 3)

    def test_missing_input_exits_1(self):
        self.assertEqual(main(["/nonexistent/path/to/missing.md"]), 1)


class MergeFunctionTests(unittest.TestCase):
    def test_merge_with_no_existing(self):
        new = [{"id": "R1.1", "reviewer": 1, "text": "x", "severity_inferred": "minor",
                "status": "pending", "response_text": "", "edits_made": [], "line_refs": []}]
        with tempfile.TemporaryDirectory() as tmp:
            merged = merge_with_existing(new, Path(tmp) / "nonexistent.json")
            self.assertEqual(merged, new)


if __name__ == "__main__":
    unittest.main()
