"""Validate _voice/profile.md against the cycle-10 schema (D12 / voice-profile-schema.md)."""
from __future__ import annotations

import unittest

import yaml

VALID = """---
sws_artifact: voice-profile
artifact_version: 0.1
calibrated: 2026-05-23
recent_weighted: true
feature_targets:
  sentence_len_mean: { target: 24.0, band: [20.0, 28.0] }
  hedge_density: { target: 1.8, band: [1.0, 2.6] }
convergence:
  self_band: [0.74, 0.91]
  gamma: 0.42
sections: [global, introduction, results, discussion]
---

# Voice profile

## Global voice
Measured, evidence-led prose with short topic sentences.

## Section deltas

### Introduction
Slightly more rhetorical; opens with the gap.

### Results
Headline finding first, then the data.

### Discussion
Interpretive; longer sentences.
"""

INVALID_NO_DELTAS = """---
sws_artifact: voice-profile
artifact_version: 0.1
feature_targets:
  hedge_density: { target: 1.8, band: [1.0, 2.6] }
sections: [global]
---

# Voice profile

## Global voice
Only a global block, no section deltas.
"""

INVALID_BAND = """---
sws_artifact: voice-profile
artifact_version: 0.1
feature_targets:
  hedge_density: { target: 5.0, band: [1.0, 2.6] }
sections: [global, introduction, results, discussion]
---

# Voice profile

## Global voice
x

## Section deltas

### Introduction
x

### Results
x

### Discussion
x
"""


def validate_profile(text: str) -> None:
    """Raise AssertionError if the profile.md violates the schema."""
    assert text.startswith("---\n"), "must start with frontmatter"
    end = text.index("\n---", 4)
    fm = yaml.safe_load(text[4:end])
    body = text[end + 4 :]
    assert fm.get("sws_artifact") == "voice-profile", "wrong sws_artifact"
    targets = fm.get("feature_targets") or {}
    assert targets, "feature_targets required"
    for key, spec in targets.items():
        lo, hi = spec["band"]
        assert lo <= spec["target"] <= hi, f"target out of band: {key}"
    assert "## Global voice" in body, "missing Global voice block"
    assert "## Section deltas" in body, "missing Section deltas block"
    for sec in ["### Introduction", "### Results", "### Discussion"]:
        assert sec in body, f"missing section delta {sec}"


class TestVoiceProfileSchema(unittest.TestCase):
    def test_valid_profile_passes(self):
        validate_profile(VALID)  # no raise

    def test_missing_section_deltas_rejected(self):
        with self.assertRaises(AssertionError):
            validate_profile(INVALID_NO_DELTAS)

    def test_target_out_of_band_rejected(self):
        with self.assertRaises(AssertionError):
            validate_profile(INVALID_BAND)


if __name__ == "__main__":
    unittest.main()
