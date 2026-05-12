#!/usr/bin/env python3
"""SWS init-project orchestration utility.

Functions exposed (built incrementally across cycle-#2 tasks 6-10):
    slugify(name)                  — normalize first_author family name
    validate_inputs(inputs)        — Q5b conditional rules (target_journal/call)
    scan_conflicts(root)           — 6-class smart-merge detection scan
    build_plan(inputs, resolutions)— assemble ordered op list
    apply_plan(plan)               — atomic apply with rollback

CLI subcommands wrap these for skill invocation:
    python sws_init_project.py scan --root <dir>
    python sws_init_project.py plan --inputs <vars.json> --resolutions <res.json>
    python sws_init_project.py apply --plan <plan.json>
"""
from __future__ import annotations
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


def slugify(name: str) -> str:
    """Normalize first_author family name: NFD-decompose → drop non-ASCII →
    lowercase → strip apostrophes/hyphens.

    Examples:
        Smith → smith
        Müller → muller
        O'Brien → obrien
        Smith-Jones → smithjones

    Raises ValueError on empty/whitespace input.
    """
    s = name.strip()
    if not s:
        raise ValueError("first_author cannot be empty")

    # Step 1: NFD decompose to separate base from combining marks
    decomposed = unicodedata.normalize("NFD", s)

    # Step 2: Remove combining characters (diacritics)
    no_combining = "".join(c for c in decomposed if not unicodedata.combining(c))

    # Step 3: Map precomposed non-ASCII chars that don't decompose to ASCII equivalents
    # (e.g., ø → o, æ → ae)
    mapping = {
        'ø': 'o', 'Ø': 'o',
        'ð': 'd', 'Ð': 'd',
        'þ': 'th', 'Þ': 'th',
        'ß': 'ss',
        'æ': 'ae', 'Æ': 'ae',
        'œ': 'oe', 'Œ': 'oe',
    }

    result = ""
    for c in no_combining:
        if ord(c) > 127:  # Non-ASCII
            result += mapping.get(c, '')
        else:
            result += c

    # Step 4: Keep only alphanumeric (strips apostrophes, hyphens, spaces, etc.)
    cleaned = "".join(c for c in result if c.isalnum())
    return cleaned.lower()


ARTICLE_TYPES = (
    "full-article", "communication", "perspective", "review-paper",
    "mini-review", "editorial", "methodological-paper",
    "commentary-reply", "funding-proposal",
)
LANGUAGES = ("en", "it")
FORMATS = ("docx", "latex")


@dataclass
class Conflict:
    cls: str           # "C1".."C6"
    path: str          # relative to project root
    suggested_action: str
    options: list = field(default_factory=list)


def validate_inputs(inputs: dict) -> tuple[bool, str]:
    """Enforce Q5b conditional rules + enum validation.

    Returns (True, "ok") if inputs pass; (False, error_msg) otherwise.
    """
    article_type = inputs.get("article_type")
    if article_type not in ARTICLE_TYPES:
        return False, (
            f"article_type must be one of {ARTICLE_TYPES}; got {article_type!r}"
        )

    language = inputs.get("language")
    if language not in LANGUAGES:
        return False, f"language must be one of {LANGUAGES}; got {language!r}"

    fmt = inputs.get("format")
    if fmt not in FORMATS:
        return False, f"format must be one of {FORMATS}; got {fmt!r}"

    co_authors = inputs.get("co_authors_present")
    if not isinstance(co_authors, bool):
        return False, (
            f"co_authors_present must be bool; got {type(co_authors).__name__}"
        )

    target_journal = inputs.get("target_journal")
    target_call = inputs.get("target_call")

    if article_type == "funding-proposal":
        if not target_call:
            return False, (
                "article_type=funding-proposal requires target_call"
            )
        if target_journal:
            return False, (
                "article_type=funding-proposal must have target_journal=null; "
                f"got {target_journal!r}"
            )
    else:
        if not target_journal:
            return False, (
                f"article_type={article_type} requires target_journal"
            )
        if target_call:
            return False, (
                f"article_type={article_type} must have target_call=null; "
                f"got {target_call!r}"
            )

    return True, "ok"


def scan_conflicts(root) -> list[Conflict]:
    """Walk root for the 6 detection classes; return ordered Conflict list.

    Class definitions per
    docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md
    locked_decisions.Q1_existing_files_behavior.detection_set.
    """
    root = Path(root)
    conflicts: list[Conflict] = []

    # C1: root *.docx
    for docx in sorted(root.glob("*.docx")):
        conflicts.append(Conflict(
            cls="C1",
            path=docx.name,
            suggested_action=f"Move to Manuscript/{docx.name}",
            options=["Y", "n", "skip", "manual"],
        ))

    # C2: loose Figures/* with no main/ or SI/ subfolder
    figures_dir = root / "Figures"
    if figures_dir.is_dir():
        has_main = (figures_dir / "main").is_dir()
        has_si = (figures_dir / "SI").is_dir()
        if not (has_main or has_si):
            loose = []
            for ext in ("png", "jpg", "jpeg", "svg", "pdf"):
                loose.extend(figures_dir.glob(f"*.{ext}"))
            if loose:
                conflicts.append(Conflict(
                    cls="C2",
                    path="Figures/",
                    suggested_action="Move loose figures into Figures/main/",
                    options=["Y", "n", "skip", "manual"],
                ))

    # C3: claude_material/
    if (root / "claude_material").is_dir():
        conflicts.append(Conflict(
            cls="C3",
            path="claude_material/",
            suggested_action="Rename to scratch/",
            options=["Y", "n", "skip", "manual"],
        ))

    # C4: existing root CLAUDE.md
    if (root / "CLAUDE.md").is_file():
        conflicts.append(Conflict(
            cls="C4",
            path="CLAUDE.md",
            suggested_action="[r]eplace / [a]ppend (under '## SWS-managed' section) / [s]kip",
            options=["replace", "append", "skip"],
        ))

    # C5: existing claude_memory/
    if (root / "claude_memory").is_dir():
        conflicts.append(Conflict(
            cls="C5",
            path="claude_memory/",
            suggested_action="[k]eep / [m]ove to _archive/ / [r]eplace",
            options=["keep", "move", "replace"],
        ))

    # C6: existing .sws-project.local.md
    if (root / ".sws-project.local.md").is_file():
        conflicts.append(Conflict(
            cls="C6",
            path=".sws-project.local.md",
            suggested_action=(
                "Re-init flow: load existing values, prompt edits per field, write merged"
            ),
            options=["proceed", "abort"],
        ))

    return conflicts


@dataclass
class Op:
    kind: str       # mkdir | mv | render_template | copy | write_json
    source: str = ""
    dest: str = ""
    reason: str = ""
    extra: dict = field(default_factory=dict)


# Base directories created unconditionally (per references/folder-topology.md)
BASE_DIRS = (
    "Manuscript",
    "Manuscript/_journal-style",
    "Manuscript/_archive",
    "Figures",
    "Figures/main",
    "Figures/SI",
    "Figures/_archive",
    "Tables",
    "Tables/_archive",
    "SI",
    "SI/SI_Figures",
    "Zenodo_db",
    "Zenodo_db/data",
    "Zenodo_db/scripts",
    "Zenodo_db/_archive",
    "scratch",
    "refs",
    "claude_memory",
)


def build_plan(inputs: dict, conflicts: list = None, resolutions: dict = None) -> list[Op]:
    """Assemble ordered op list for atomic apply.

    Order:
      1. mkdir base topology + conditional dirs (call/, refs/nlm_uploads/)
      2. mv ops from conflict resolutions (in C1..C6 order)
      3. render_template ops for marker, per-paper CLAUDE.md, MEMORY.md
      4. write_json ops for passport.json (cycle 0)
    """
    conflicts = conflicts or []
    resolutions = resolutions or {}
    ops: list[Op] = []

    # 1. Base directories
    for d in BASE_DIRS:
        ops.append(Op(kind="mkdir", dest=d, reason="base topology"))

    # 1b. Conditional dirs
    if inputs.get("article_type") == "funding-proposal":
        ops.append(Op(kind="mkdir", dest="call", reason="article_type=funding-proposal"))
    if inputs.get("notebooklm_enabled"):
        ops.append(Op(kind="mkdir", dest="refs/nlm_uploads",
                      reason="notebooklm.enabled=true"))

    # 2. Conflict-resolution mv ops
    for c in conflicts:
        resolution = resolutions.get(c.cls, "skip")
        if resolution in ("accept", "Y"):
            if c.cls == "C1":
                # paper.docx → Manuscript/paper.docx
                src = c.path
                dest = f"Manuscript/{c.path}"
                ops.append(Op(kind="mv", source=src, dest=dest, reason=f"smart-merge C1 ({c.path})"))
            elif c.cls == "C2":
                # loose Figures/*.{png,...} → Figures/main/
                ops.append(Op(kind="mv_glob", source="Figures/*.{png,jpg,jpeg,svg,pdf}",
                              dest="Figures/main/", reason="smart-merge C2"))
            elif c.cls == "C3":
                ops.append(Op(kind="mv", source="claude_material", dest="scratch",
                              reason="smart-merge C3 (legacy hDF rename)"))
            # C4/C5/C6 use option-specific resolutions (replace/append/etc.) handled
            # in the apply layer; for now, build_plan emits a placeholder marker.

    # 3. render_template ops
    ops.append(Op(
        kind="render_template",
        source="templates/sws-project-marker.template",
        dest=".sws-project.local.md",
        reason="marker file",
        extra={"vars": _marker_vars(inputs)},
    ))
    ops.append(Op(
        kind="render_template",
        source="templates/manuscript-claude-md.template",
        dest="CLAUDE.md",
        reason="per-paper CLAUDE.md",
        extra={"vars": _claude_md_vars(inputs)},
    ))
    ops.append(Op(
        kind="render_template",
        source="templates/manuscript-memory-md.template",
        dest="claude_memory/MEMORY.md",
        reason="per-paper MEMORY.md",
        extra={"vars": {}},  # template uses no substitutions
    ))

    # 4. passport.json stub
    ops.append(Op(
        kind="write_json",
        dest="claude_memory/passport.json",
        reason="cycle 0 stub",
        extra={"content": {"sws_version": "0.1", "cycle": 0, "history": []}},
    ))

    return ops


def _marker_vars(inputs: dict) -> dict:
    """Render-time vars dict for the marker template."""
    return {
        "article_type": inputs["article_type"],
        "language": inputs["language"],
        "format": inputs["format"],
        "target_journal": inputs.get("target_journal") or "null",
        "target_call": inputs.get("target_call") or "null",
        "notebooklm_enabled": "true" if inputs["notebooklm_enabled"] else "false",
        "created_iso": inputs["created_iso"],
        "short_handle": inputs["short_handle"],
    }


def _claude_md_vars(inputs: dict) -> dict:
    """Render-time vars dict for the per-paper CLAUDE.md template."""
    return {
        **_marker_vars(inputs),
        "first_author": inputs["first_author"],
        "year": str(inputs["year"]),
        "co_authors_present": "true" if inputs["co_authors_present"] else "false",
    }
