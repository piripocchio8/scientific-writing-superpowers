"""Section→agent router. Single source of truth for /sws:draft-section,
/sws:draft-paper, /sws:revise-section, /sws:revise-paper, and related
dispatch. Mirrors the tables in skills/draft-section/SKILL.md and
skills/revise-section/SKILL.md.

The router has two axes:
  - action: draft (default) | revise | consistency | style | lint
  - profile: publication profile or funding-proposal (applies within action=draft)

The router is profile-aware (publication vs funding-proposal) but does NOT
read the per-profile agents_inactive list — that gating happens in
agent_should_run.sh, after dispatch. The router's only job is to map
section_id + action + profile → agent_id (or script sentinel).
"""
from __future__ import annotations

from typing import Optional


class RouteError(ValueError):
    pass


# ---------------------------------------------------------------------------
# action=draft maps (cycle-#7, unchanged)
# ---------------------------------------------------------------------------

_PUBLICATION_MAP = {
    "intro": "drafter-flagship",
    "introduction": "drafter-flagship",
    "abstract": "drafter-flagship",
    "discussion": "drafter-flagship",
    "conclusion": "drafter-flagship",
    "conclusions": "drafter-flagship",
    "methods": "methods-writer",
    "experimental": "methods-writer",
    "experimental section": "methods-writer",
    "materials": "methods-writer",
    "statistical analysis": "methods-writer",
    "computational details": "methods-writer",
    "software": "methods-writer",
    "data availability": "methods-writer",
    "results": "drafter-fast",
    "results and discussion": "drafter-flagship",
    "figure_caption": "caption-writer",
}

_FUNDING_PROPOSAL_MAP = {
    "state of the art": "drafter-flagship",
    "state-of-the-art": "drafter-flagship",
    "vision": "drafter-flagship",
    "objectives": "drafter-flagship",
    "workplan": "drafter-flagship",
    "methodology": "drafter-flagship",
    "approach": "drafter-flagship",
    "impact": "drafter-flagship",
    "risk management": "drafter-flagship",
    "deliverables": "drafter-flagship",
    "timeline": "drafter-flagship",
    "budget": "proposal-budget-helper",
    "compliance": "proposal-compliance-helper",
    "figure_caption": "caption-writer",
}

# ---------------------------------------------------------------------------
# action=revise map (cycle-#8, D12)
# "full" is a special key dispatched by /sws:revise-paper only.
# All other section ids → reviser-fast; "full" → reviser-full.
# Unknown section ids fall back to reviser-fast.
# ---------------------------------------------------------------------------

_REVISE_MAP = {
    "intro": "reviser-fast",
    "introduction": "reviser-fast",
    "abstract": "reviser-fast",
    "discussion": "reviser-fast",
    "conclusion": "reviser-fast",
    "conclusions": "reviser-fast",
    "methods": "reviser-fast",
    "experimental": "reviser-fast",
    "experimental section": "reviser-fast",
    "results": "reviser-fast",
    "results and discussion": "reviser-fast",
    "figure_caption": "reviser-fast",
    "full": "reviser-full",
}

# ---------------------------------------------------------------------------
# action=consistency / style / lint: wildcard maps (cycle-#8, D12)
# lint sentinel is a script path, not an agent id.
# ---------------------------------------------------------------------------

_CONSISTENCY_WILDCARD = "consistency-checker"
_STYLE_WILDCARD = "style-enforcer"
_LINT_SENTINEL = "script:sws_lint_ai_tells.py"

# Valid action values
_VALID_ACTIONS = frozenset({"draft", "revise", "consistency", "style", "lint"})


def route_section(
    section_id: str,
    profile: str,
    action: str = "draft",
) -> str:
    """Map section_id + profile + action → agent_id (or script sentinel).

    action values:
      - ``draft`` (default): cycle-#7 behaviour unchanged. profile selects
        between the publication map and the funding-proposal map.
      - ``revise``: most section ids → ``reviser-fast``; ``full`` →
        ``reviser-full`` (dispatched by /sws:revise-paper). Unknown ids
        fall back to ``reviser-fast``.
      - ``consistency``: any section_id → ``consistency-checker``.
      - ``style``: any section_id → ``style-enforcer``.
      - ``lint``: any section_id → sentinel string
        ``"script:sws_lint_ai_tells.py"`` (callers parse this to invoke the
        script rather than dispatching an agent).

    section_id is lowercased and stripped before lookup.

    Raises ``RouteError`` if section_id is empty or action is unrecognised.
    """
    if not section_id:
        raise RouteError("empty section id")
    if action not in _VALID_ACTIONS:
        raise RouteError(f"unknown action: {action!r}; valid: {sorted(_VALID_ACTIONS)}")

    key = section_id.strip().lower()

    if action == "revise":
        return _REVISE_MAP.get(key, "reviser-fast")

    if action == "consistency":
        return _CONSISTENCY_WILDCARD

    if action == "style":
        return _STYLE_WILDCARD

    if action == "lint":
        return _LINT_SENTINEL

    # action == "draft" — cycle-#7 behaviour
    if profile == "funding-proposal":
        if key in _FUNDING_PROPOSAL_MAP:
            return _FUNDING_PROPOSAL_MAP[key]
        return "drafter-flagship"
    return _PUBLICATION_MAP.get(key, "drafter-fast")
