#!/usr/bin/env python3
"""Master orchestrator step planner for /sws:run-cycle.

Computes the ordered step plan for a paper based on the resolved profile,
marker fields, and on-disk artifacts (D9). Supports `--dry-run` and `--only`
filtering (D14). Emits the plan as JSON so the SKILL.md bash body can read +
dispatch each step.

Steps (D9):
    1  outline       skip if outline.md exists
    2  draft         skip if _drafts/*.md exist
    3  revise        skip if any _drafts/*.revised.md newer than _drafts/*.md
    4  review        skip if _review/{peer-reviewer,claim-verifier,bibliography-fidelity-checker}
                     all populated with a report.md
    5  cover-letter  skip if _submission/cover-letter.md exists; conditional on
                     RESOLVED_COVER_LETTER_REQUIRED + cover-letter-writer active
    6  disclosure    skip if _submission/ai-disclosure.md exists; conditional on
                     RESOLVED_DISCLOSURE_REQUIRED
    7  response      only if any _review/round-<N>/reviewer-comments.md exists;
                     skip if response-to-reviewers.md present for that round;
                     conditional on response-to-reviewers active

Final action (real run only): write ONE passport entry with phase=submit,
change_summary listing the steps dispatched, next_step indicating any
remaining TODOs.

Stale-detection (R4): with 5-second mtime tolerance, surfaces a `stale` flag
on a step whose output predates a source file. Advisory only — does NOT
override `should_run` (D10).

CLI:
    sws_run_cycle.py [--paper-root <path>] [--dry-run] [--only=<csv>]

Exit codes:
    0  plan computed (and dispatched if not --dry-run)
    2  marker not found / not an SWS project
    3  invalid --only value
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


STEP_NAMES = (
    "outline",
    "draft",
    "revise",
    "review",
    "cover-letter",
    "disclosure",
    "response",
)

STEP_SKILLS = {
    "outline": "/sws:outline-paper",
    "draft": "/sws:draft-paper",
    "revise": "/sws:revise-paper",
    "review": "/sws:review-paper",
    "cover-letter": "/sws:write-cover-letter",
    "disclosure": "/sws:disclose-ai-usage",
    "response": "/sws:respond-to-reviewers",
}

STALE_TOLERANCE_SECONDS = 5.0


# ---------------------------------------------------------------------------
# Marker + profile helpers
# ---------------------------------------------------------------------------

def read_marker(paper_root: Path) -> dict | None:
    marker = paper_root / ".sws-project.local.md"
    if not marker.exists():
        return None
    text = marker.read_text()
    if not text.startswith("---\n"):
        return {}
    if yaml is None:
        return {}
    try:
        end = text.index("\n---", 4)
        return yaml.safe_load(text[4:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}


def read_profile_agents(profile_id: str) -> tuple[list[str], list[str]]:
    """Return (active, inactive) agent lists for a profile id."""
    if yaml is None:
        return ([], [])
    repo_root = Path(__file__).resolve().parent.parent
    profile_path = repo_root / "profiles" / f"{profile_id}.md"
    if not profile_path.exists():
        return ([], [])
    text = profile_path.read_text()
    if not text.startswith("---\n"):
        return ([], [])
    try:
        end = text.index("\n---", 4)
        fm = yaml.safe_load(text[4:end]) or {}
    except (ValueError, yaml.YAMLError):
        return ([], [])
    return (fm.get("agents_active") or [], fm.get("agents_inactive") or [])


# ---------------------------------------------------------------------------
# Stale detection (R4)
# ---------------------------------------------------------------------------

def is_stale(artifact: Path, sources: list[Path], tolerance: float = STALE_TOLERANCE_SECONDS) -> bool:
    """True if any source mtime is newer than artifact + tolerance."""
    if not artifact.exists():
        return False
    a_mtime = artifact.stat().st_mtime
    for src in sources:
        if not src.exists():
            continue
        if src.stat().st_mtime > a_mtime + tolerance:
            return True
    return False


# ---------------------------------------------------------------------------
# Per-step predicates
# ---------------------------------------------------------------------------

def _drafts_dir(paper_root: Path) -> Path:
    return paper_root / "_drafts"


def _review_subdir_populated(paper_root: Path, name: str) -> bool:
    p = paper_root / "_review" / name / "report.md"
    return p.exists()


def _round_dirs(paper_root: Path) -> list[tuple[int, Path]]:
    rev = paper_root / "_review"
    if not rev.exists():
        return []
    rounds = []
    for child in rev.iterdir():
        if not child.is_dir():
            continue
        m = re.match(r"^round-(\d+)$", child.name)
        if m:
            rounds.append((int(m.group(1)), child))
    rounds.sort()
    return rounds


def plan_steps(paper_root: Path) -> list[dict]:
    """Compute the ordered step plan for `paper_root`. Pure: does not dispatch."""
    marker = read_marker(paper_root) or {}
    # Profile-id can come from marker (article_type) — see resolve_overlay.py logic.
    profile_id = marker.get("article_type") or marker.get("profile") or "full-article"
    active, inactive = read_profile_agents(profile_id)

    cover_required = (
        os.environ.get("RESOLVED_COVER_LETTER_REQUIRED", "").strip().lower() == "true"
    )
    disclosure_required = (
        os.environ.get("RESOLVED_DISCLOSURE_REQUIRED", "").strip().lower() == "true"
    )
    cover_active = "cover-letter-writer" in active and "cover-letter-writer" not in inactive
    response_active = "response-to-reviewers" in active and "response-to-reviewers" not in inactive

    drafts_dir = _drafts_dir(paper_root)
    drafts = sorted(drafts_dir.glob("*.md")) if drafts_dir.exists() else []
    # Exclude revised.md siblings from the canonical-draft list.
    canonical_drafts = [d for d in drafts if not d.name.endswith(".revised.md")]
    revised_drafts = [d for d in drafts if d.name.endswith(".revised.md")]

    outline_md = paper_root / "outline.md"
    submission_dir = paper_root / "_submission"
    cover_letter = submission_dir / "cover-letter.md"
    ai_disclosure = submission_dir / "ai-disclosure.md"
    rounds = _round_dirs(paper_root)

    steps: list[dict] = []

    # Step 1 — outline
    steps.append({
        "step": 1,
        "name": "outline",
        "skill": STEP_SKILLS["outline"],
        "should_run": not outline_md.exists(),
        "reason": "outline.md missing" if not outline_md.exists() else "outline.md exists",
        "stale": False,
    })

    # Step 2 — draft
    steps.append({
        "step": 2,
        "name": "draft",
        "skill": STEP_SKILLS["draft"],
        "should_run": len(canonical_drafts) == 0,
        "reason": "no _drafts/*.md found" if not canonical_drafts else f"{len(canonical_drafts)} drafts present",
        "stale": False,
    })

    # Step 3 — revise
    revise_done = bool(revised_drafts) and all(
        not is_stale(revised, [paper_root / "_drafts" / revised.name.replace(".revised.md", ".md")])
        for revised in revised_drafts
    )
    steps.append({
        "step": 3,
        "name": "revise",
        "skill": STEP_SKILLS["revise"],
        "should_run": not revise_done,
        "reason": "no revised drafts" if not revised_drafts else "revised drafts present",
        "stale": False,
    })

    # Step 4 — review
    review_subdirs = ("peer-reviewer", "claim-verifier", "bibliography-fidelity-checker")
    review_done = all(_review_subdir_populated(paper_root, s) for s in review_subdirs)
    steps.append({
        "step": 4,
        "name": "review",
        "skill": STEP_SKILLS["review"],
        "should_run": not review_done,
        "reason": "all 3 review reports present" if review_done else "review reports missing",
        "stale": False,
    })

    # Step 5 — cover-letter
    if not cover_required or not cover_active:
        cl_reason = "cover_letter not required for this profile"
        steps.append({
            "step": 5,
            "name": "cover-letter",
            "skill": STEP_SKILLS["cover-letter"],
            "should_run": False,
            "reason": cl_reason,
            "stale": False,
        })
    else:
        cl_exists = cover_letter.exists()
        cl_stale = is_stale(cover_letter, canonical_drafts) if cl_exists else False
        steps.append({
            "step": 5,
            "name": "cover-letter",
            "skill": STEP_SKILLS["cover-letter"],
            "should_run": not cl_exists,
            "reason": "cover-letter.md missing" if not cl_exists else "cover-letter.md exists",
            "stale": cl_stale,
        })

    # Step 6 — disclosure
    if not disclosure_required:
        steps.append({
            "step": 6,
            "name": "disclosure",
            "skill": STEP_SKILLS["disclosure"],
            "should_run": False,
            "reason": "disclosure not required for this profile",
            "stale": False,
        })
    else:
        steps.append({
            "step": 6,
            "name": "disclosure",
            "skill": STEP_SKILLS["disclosure"],
            "should_run": not ai_disclosure.exists(),
            "reason": "ai-disclosure.md missing" if not ai_disclosure.exists() else "ai-disclosure.md exists",
            "stale": False,
        })

    # Step 7 — response (only if a reviewer-comments.md exists for any round)
    pending_round = None
    for n, rd in rounds:
        if (rd / "reviewer-comments.md").exists() and not (rd / "response-to-reviewers.md").exists():
            pending_round = n
            break
    if not response_active:
        steps.append({
            "step": 7,
            "name": "response",
            "skill": STEP_SKILLS["response"],
            "should_run": False,
            "reason": "response-to-reviewers inactive for this profile",
            "stale": False,
            "round": None,
        })
    elif not rounds:
        steps.append({
            "step": 7,
            "name": "response",
            "skill": STEP_SKILLS["response"],
            "should_run": False,
            "reason": "no _review/round-<N>/reviewer-comments.md present",
            "stale": False,
            "round": None,
        })
    elif pending_round is None:
        steps.append({
            "step": 7,
            "name": "response",
            "skill": STEP_SKILLS["response"],
            "should_run": False,
            "reason": "all rounds have a response-to-reviewers.md",
            "stale": False,
            "round": None,
        })
    else:
        steps.append({
            "step": 7,
            "name": "response",
            "skill": STEP_SKILLS["response"],
            "should_run": True,
            "reason": f"round-{pending_round}/reviewer-comments.md present, response missing",
            "stale": False,
            "round": pending_round,
        })

    return steps


# ---------------------------------------------------------------------------
# Dispatch (Phase 4)
# ---------------------------------------------------------------------------

# Script-dispatch path (D2/D9 Phase-4 finalisation). For agent-backed steps
# we emit a MANUAL directive so the orchestrating user-context can pick it
# up. For deterministic-script steps the bash SKILL.md body invokes the
# corresponding script.

SCRIPT_DISPATCH = {
    "disclosure": "scripts/sws_disclosure_writer.py",
    # other steps require either bigger subskills or agent invocation; the
    # SKILL.md case-statement maps step->command.
}


def render_dispatch_plan(steps: list[dict]) -> str:
    """Render a human-readable plan summary for the SKILL.md to consume."""
    lines = []
    for s in steps:
        marker = "RUN" if s["should_run"] else "SKIP"
        stale = " (stale)" if s.get("stale") else ""
        round_s = f" round={s['round']}" if s.get("round") else ""
        lines.append(
            f"  step={s['step']} name={s['name']} {marker}{stale}{round_s} reason={s['reason']}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--paper-root", default=os.getcwd())
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--only",
        default=None,
        help="CSV of step names to include (skips all others)",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit the plan as JSON (instead of human-readable)",
    )
    args = ap.parse_args(argv)

    paper_root = Path(args.paper_root).resolve()
    marker = read_marker(paper_root)
    if marker is None:
        print(
            "sws_run_cycle: not an SWS project (no .sws-project.local.md). "
            "Run /sws:init-project first.",
            file=sys.stderr,
        )
        return 2

    steps = plan_steps(paper_root)

    if args.only:
        only = {name.strip() for name in args.only.split(",") if name.strip()}
        unknown = only - set(STEP_NAMES)
        if unknown:
            print(
                f"sws_run_cycle: unknown step name(s) in --only: {sorted(unknown)}. "
                f"Valid: {list(STEP_NAMES)}",
                file=sys.stderr,
            )
            return 3
        steps = [s if s["name"] in only else {**s, "should_run": False, "reason": "not in --only filter"}
                 for s in steps]

    if args.json:
        print(json.dumps(steps, indent=2, sort_keys=True))
    else:
        print("sws_run_cycle: step plan")
        print(render_dispatch_plan(steps))

    if args.dry_run:
        return 0

    # Phase-4 dispatch: emit a structured plan the SKILL.md bash body acts on.
    # Each "RUN" step prints a dispatch directive line on stdout for the
    # caller's case-statement.
    dispatch_lines = []
    for s in steps:
        if not s["should_run"]:
            continue
        script = SCRIPT_DISPATCH.get(s["name"])
        if script:
            dispatch_lines.append(f"DISPATCH script {s['name']} {script}")
        else:
            dispatch_lines.append(f"DISPATCH manual {s['name']} {s['skill']}")
    if dispatch_lines:
        print("\nsws_run_cycle: dispatch directives", file=sys.stderr)
        for d in dispatch_lines:
            print(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
