"""Per-profile activation matrix for cycle-#7 agents.

Mirrors the spec's `agent_activation_matrix_cycle_07_updates`.

Three parameterized test families × 9 profiles = 27 tests:

1. caption-writer is always active (invariant per user instruction
   2026-05-13).
2. Every cycle-#7 agent in a profile's agents_inactive list is BLOCKED
   by agent_should_run.sh.
3. Every cycle-#7 agent NOT in a profile's agents_inactive list is
   ALLOWED by agent_should_run.sh.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
# Use the test runner's interpreter — it has PyYAML installed (the resolver
# needs it). System python3 may not.
PYTHON = sys.executable


def _make_paper(tmp_path, profile_id):
    paper = tmp_path / "paper"
    paper.mkdir()
    venv_bin = paper / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").symlink_to(PYTHON)
    (paper / ".sws-project.local.md").write_text(
        f"---\nprofile: {profile_id}\nlanguage: en\nformat: docx\n---\n"
    )
    return paper


def _can_run(paper, agent_id):
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(REPO)
    env["PAPER_ROOT"] = str(paper)
    cp = subprocess.run(
        ["bash", str(REPO / "scripts" / "agent_should_run.sh"), agent_id],
        env=env, capture_output=True, text=True
    )
    return cp.returncode == 0


# Cycle-#7 agents that have explicit per-profile activation rules
CYCLE_7_AGENTS = [
    "outline-architect", "drafter-flagship", "drafter-fast",
    "methods-writer", "caption-writer",
    "proposal-budget-helper", "proposal-compliance-helper",
]


# Per spec `agent_activation_matrix_cycle_07_updates.per_profile_inactive_additions`.
# Only cycle-#7 agents are listed here; tests skip non-cycle-#7 names in
# the file's agents_inactive (e.g. data-curator, plot-maker,
# response-to-reviewers).
PROFILES = {
    "full-article":         {"inactive": []},
    "communication":        {"inactive": ["methods-writer", "drafter-fast"]},
    "perspective":          {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer"]},
    "review-paper":         {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer"]},
    "mini-review":          {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer"]},
    "editorial":            {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer", "drafter-fast"]},
    "methodological-paper": {"inactive": ["proposal-budget-helper", "proposal-compliance-helper"]},
    "commentary-reply":     {"inactive": ["proposal-budget-helper", "proposal-compliance-helper", "methods-writer"]},
    "funding-proposal":     {"inactive": ["methods-writer", "drafter-fast"]},
}


@pytest.mark.parametrize("profile_id, spec", PROFILES.items())
def test_caption_writer_always_active(tmp_path, profile_id, spec):
    """Invariant from user instruction 2026-05-13."""
    paper = _make_paper(tmp_path, profile_id)
    assert _can_run(paper, "caption-writer"), \
        f"caption-writer must be active for profile={profile_id}"


@pytest.mark.parametrize("profile_id, spec", PROFILES.items())
def test_inactive_agents_blocked(tmp_path, profile_id, spec):
    paper = _make_paper(tmp_path, profile_id)
    for agent in spec["inactive"]:
        if agent not in CYCLE_7_AGENTS:
            continue  # not a cycle-#7 agent (e.g., data-curator)
        assert not _can_run(paper, agent), \
            f"agent={agent} should be INACTIVE for profile={profile_id}"


@pytest.mark.parametrize("profile_id, spec", PROFILES.items())
def test_active_cycle_7_agents_allowed(tmp_path, profile_id, spec):
    paper = _make_paper(tmp_path, profile_id)
    for agent in CYCLE_7_AGENTS:
        if agent in spec["inactive"]:
            continue
        assert _can_run(paper, agent), \
            f"agent={agent} should be ACTIVE for profile={profile_id}"
