"""Verify cycle-11 D10 activation matrix for the 4 data+literature agents
across all 9 profiles."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

ALL_PROFILES = [
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

DATA_ACTIVE_PROFILES = ["full-article", "communication", "methodological-paper"]
DATA_INACTIVE_PROFILES = [p for p in ALL_PROFILES if p not in DATA_ACTIVE_PROFILES]

PLOT_ACTIVE_PROFILES = [
    "full-article", "communication", "methodological-paper", "review-paper", "mini-review"
]
PLOT_INACTIVE_PROFILES = [p for p in ALL_PROFILES if p not in PLOT_ACTIVE_PROFILES]

LIT_ACTIVE_PROFILES = [
    "full-article", "communication", "perspective", "review-paper", "mini-review",
    "editorial", "methodological-paper", "funding-proposal",
]
# commentary-reply has literature-searcher exec-tunable (active but noted)
LIT_ACTIVE_OR_TUNABLE = LIT_ACTIVE_PROFILES + ["commentary-reply"]
LIT_INACTIVE_PROFILES = []  # literature-searcher is active or tunable in all profiles

BIB_ACTIVE_ALL = ALL_PROFILES  # bibliography-curator active in all 9


def _load_frontmatter(profile_id: str) -> dict:
    text = (PROFILES_DIR / f"{profile_id}.md").read_text()
    assert text.startswith("---\n"), f"{profile_id}.md missing YAML frontmatter"
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


# ---------------------------------------------------------------------------
# data-curator
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", DATA_ACTIVE_PROFILES)
def test_data_curator_active_in_data_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "data-curator" in active, f"data-curator must be ACTIVE in {profile_id}"
    assert "data-curator" not in inactive


@pytest.mark.parametrize("profile_id", DATA_INACTIVE_PROFILES)
def test_data_curator_inactive_in_non_data_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "data-curator" not in active, f"data-curator must be INACTIVE in {profile_id}"
    assert "data-curator" in inactive, f"data-curator must be listed in agents_inactive for {profile_id}"


# ---------------------------------------------------------------------------
# plot-maker
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", PLOT_ACTIVE_PROFILES)
def test_plot_maker_active_in_figure_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "plot-maker" in active, f"plot-maker must be ACTIVE in {profile_id}"
    assert "plot-maker" not in inactive


@pytest.mark.parametrize("profile_id", PLOT_INACTIVE_PROFILES)
def test_plot_maker_inactive_in_non_figure_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "plot-maker" not in active, f"plot-maker must be INACTIVE in {profile_id}"
    assert "plot-maker" in inactive, f"plot-maker must be listed in agents_inactive for {profile_id}"


# ---------------------------------------------------------------------------
# literature-searcher
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", LIT_ACTIVE_PROFILES)
def test_literature_searcher_active_in_broad_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "literature-searcher" in active, f"literature-searcher must be ACTIVE in {profile_id}"
    assert "literature-searcher" not in inactive


def test_literature_searcher_active_or_tunable_in_commentary_reply():
    fm = _load_frontmatter("commentary-reply")
    active = fm.get("agents_active") or []
    # exec-tunable means it can appear in active; it must not be in inactive
    inactive = fm.get("agents_inactive") or []
    assert "literature-searcher" in active, \
        "literature-searcher must be ACTIVE (exec-tunable) in commentary-reply"
    assert "literature-searcher" not in inactive


# ---------------------------------------------------------------------------
# bibliography-curator
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile_id", ALL_PROFILES)
def test_bibliography_curator_active_in_all_profiles(profile_id):
    fm = _load_frontmatter(profile_id)
    active = fm.get("agents_active") or []
    inactive = fm.get("agents_inactive") or []
    assert "bibliography-curator" in active, \
        f"bibliography-curator must be ACTIVE in all profiles; missing in {profile_id}"
    assert "bibliography-curator" not in inactive
