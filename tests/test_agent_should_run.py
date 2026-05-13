"""agent_should_run.sh: thin wrapper exit codes per spec.

Exit 0 = agent allowed to run (profile_set true, agent in agents_active
not in agents_inactive). Exit non-zero otherwise.
"""
import os
import sys
import subprocess
from pathlib import Path
import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "agent_should_run.sh"
# Use the test runner's interpreter — it has PyYAML installed (the resolver
# needs it). System python3 may not.
PYTHON = sys.executable


def _run(paper_root: Path, agent_id: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(REPO)
    env["PAPER_ROOT"] = str(paper_root)
    return subprocess.run(
        ["bash", str(SCRIPT), agent_id],
        env=env, capture_output=True, text=True
    )


@pytest.fixture
def perspective_paper(tmp_path):
    """Minimal SWS-initialized paper with profile=perspective."""
    paper = tmp_path / "paper"
    paper.mkdir()
    # Create the .venv so sws_python.sh succeeds.
    venv_bin = paper / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").symlink_to(PYTHON)
    # Marker
    (paper / ".sws-project.local.md").write_text(
        "---\nprofile: perspective\nlanguage: en\nformat: docx\n---\n"
    )
    return paper


def test_returns_zero_for_active_agent(perspective_paper):
    # outline-architect is active for perspective (not in inactive list)
    cp = _run(perspective_paper, "outline-architect")
    assert cp.returncode == 0, f"stderr: {cp.stderr}"


def test_returns_nonzero_for_inactive_agent(perspective_paper):
    # methods-writer is in perspective's agents_inactive list
    cp = _run(perspective_paper, "methods-writer")
    assert cp.returncode != 0


def test_returns_nonzero_when_profile_unset(tmp_path):
    paper = tmp_path / "paper"
    paper.mkdir()
    venv_bin = paper / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").symlink_to(PYTHON)
    (paper / ".sws-project.local.md").write_text(
        "---\nprofile: null\nlanguage: en\nformat: docx\n---\n"
    )
    cp = _run(paper, "outline-architect")
    assert cp.returncode != 0


def test_returns_nonzero_for_missing_agent_arg(perspective_paper):
    cp = _run(perspective_paper, "")
    assert cp.returncode != 0
