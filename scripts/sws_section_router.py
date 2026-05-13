"""Section→agent router. Single source of truth for /sws:draft-section
and /sws:draft-paper dispatch. Mirrors the tables in
skills/draft-section/SKILL.md.

The router is profile-aware (publication vs funding-proposal) but does NOT
read the per-profile agents_inactive list — that gating happens in
agent_should_run.sh, after dispatch. The router's only job is to map
section_id + profile → agent_id.
"""
from __future__ import annotations

from typing import Optional


class RouteError(ValueError):
    pass


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


def route_section(section_id: str, profile: str) -> str:
    """Map section_id + profile → agent_id.

    - section_id is lowercased and stripped before lookup.
    - For ``profile == "funding-proposal"``: uses the funding map; falls
      back to ``drafter-flagship`` for unknown ids (proposal sections are
      almost all rationale prose).
    - For any other profile (full-article, perspective, communication,
      review-paper, mini-review, editorial, methodological-paper,
      commentary-reply): uses the publication map; falls back to
      ``drafter-fast`` for unknown narrative ids.

    Raises ``RouteError`` if the section_id is empty.
    """
    if not section_id:
        raise RouteError("empty section id")
    key = section_id.strip().lower()
    if profile == "funding-proposal":
        if key in _FUNDING_PROPOSAL_MAP:
            return _FUNDING_PROPOSAL_MAP[key]
        return "drafter-flagship"
    return _PUBLICATION_MAP.get(key, "drafter-fast")
