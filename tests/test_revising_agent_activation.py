"""Per-profile activation matrix for cycle-#8 revising agents (D13).

D13: all 5 cycle-#8 agents are active in all 9 profiles — no per-profile
blocking. Size-aware dispatch lives in the orchestrator skill, not here.

Two parameterized test families × 9 profiles = 18 tests + 1 YAML parse check:

1. For each profile, parse the YAML frontmatter and assert all 5 cycle-#8
   agents appear in `agents_active`.
2. For each (profile, agent) pair, assert `scripts/agent_should_run.sh`
   exits 0 (agent is allowed to run).
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

CYCLE_8_AGENTS = [
    "reviser-full",
    "reviser-fast",
    "humanizer",
    "style-enforcer",
    "consistency-checker",
]

PROFILE_IDS = [
    "full-article",
    "communication",
    "perspective",
    "review-paper",
    "mini-review",
    "editorial",
    "methodological-paper",
    "commentary-reply",
    "funding-proposal",
]


def _parse_frontmatter(profile_id: str) -> dict:
    path = REPO / "profiles" / f"{profile_id}.md"
    text = path.read_text()
    assert text.startswith("---"), f"{profile_id}.md has no frontmatter"
    rest = text[3:]
    end = rest.find("\n---")
    assert end >= 0, f"{profile_id}.md frontmatter not closed"
    block = rest[:end].lstrip("\n")
    return yaml.safe_load(block) or {}


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


# --- Family 1: frontmatter declares all 5 agents in agents_active ---

@pytest.mark.parametrize("profile_id", PROFILE_IDS)
def test_cycle8_agents_in_agents_active_frontmatter(profile_id):
    fm = _parse_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    for agent in CYCLE_8_AGENTS:
        assert agent in active, (
            f"profile={profile_id}: '{agent}' missing from agents_active"
        )


# --- Family 2: agent_should_run.sh exits 0 for every (profile, agent) pair ---

PROFILE_AGENT_PAIRS = [
    (profile_id, agent)
    for profile_id in PROFILE_IDS
    for agent in CYCLE_8_AGENTS
]


@pytest.mark.parametrize("profile_id, agent_id", PROFILE_AGENT_PAIRS)
def test_agent_should_run_exits_0(tmp_path, profile_id, agent_id):
    paper = _make_paper(tmp_path, profile_id)
    assert _can_run(paper, agent_id), (
        f"agent_should_run.sh returned non-zero for "
        f"profile={profile_id}, agent={agent_id}"
    )
