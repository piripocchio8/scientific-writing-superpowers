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
import argparse
import json
import shutil
import sys
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
            suggested_action="[r]eplace with SWS template / [a]ppend SWS-managed section / [s]kip (leave file untouched)",
            options=["replace", "append", "skip"],
        ))

    # C5: existing claude_memory/
    if (root / "claude_memory").is_dir():
        conflicts.append(Conflict(
            cls="C5",
            path="claude_memory/",
            suggested_action="[k]eep existing (no SWS writes inside) / [r]eplace MEMORY.md + passport.json only",
            options=["keep", "replace"],
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

    # Resolution gates — C4/C5 control whether SWS writes inside their conflict area.
    # Default to None (no conflict present) when no entry, meaning fresh-init → write.
    c4_resolution = resolutions.get("C4")  # None if no C4 conflict, else "replace"|"skip"
    c5_resolution = resolutions.get("C5")  # None if no C5 conflict, else "replace"|"keep"

    # 3. render_template ops

    # Marker: always render (C6=abort gates the whole flow at the skill level, not here).
    ops.append(Op(
        kind="render_template",
        source="templates/sws-project-marker.template",
        dest=".sws-project.local.md",
        reason="marker file",
        extra={"vars": _marker_vars(inputs)},
    ))

    # CLAUDE.md: render only on fresh init (no C4 conflict) or explicit replace.
    if c4_resolution is None or c4_resolution == "replace":
        ops.append(Op(
            kind="render_template",
            source="templates/manuscript-claude-md.template",
            dest="CLAUDE.md",
            reason="per-paper CLAUDE.md",
            extra={"vars": _claude_md_vars(inputs)},
        ))

    # C4=append: emit append_sws_section op (no render_template for CLAUDE.md in this case).
    if c4_resolution == "append":
        ops.append(Op(
            kind="append_sws_section",
            dest="CLAUDE.md",
            reason="smart-merge C4 (append SWS section)",
            extra={"short_handle": inputs["short_handle"]},
        ))

    # MEMORY.md + passport.json: render only on fresh init (no C5 conflict) or explicit replace.
    # (Same gate for both — they live inside claude_memory/.)
    if c5_resolution is None or c5_resolution == "replace":
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


SWS_MARKER_OPEN = "<!-- SWS-managed start: do not hand-edit between the markers below -->"
SWS_MARKER_CLOSE = "<!-- SWS-managed end -->"


def _build_sws_section(short_handle: str) -> str:
    """Return the marker-delimited SWS-managed block for C4=append.

    Idempotent: re-running with the same or different short_handle replaces
    only the content between the open/close markers, leaving the user's
    surrounding content untouched.
    """
    return (
        f"{SWS_MARKER_OPEN}\n\n"
        "## SWS-managed\n\n"
        f"This manuscript directory is SWS-bootstrapped (`{short_handle}`). "
        "Canonical project metadata lives in `.sws-project.local.md`; agents "
        "reading this CLAUDE.md should look there for `article_type`, "
        "`language`, `format`, `target_journal`/`target_call`, etc.\n\n"
        "Where to find context:\n\n"
        "- `.sws-project.local.md` — active SWS settings.\n"
        "- `claude_memory/MEMORY.md` — session-state index; update as you work.\n"
        "- `Manuscript/_journal-style/<slug>.md` — journal-specific overlay "
        "(run `/sws:resolve-journal-style` if missing).\n"
        "- SWS plugin canonical references: `references/folder-topology.md`, "
        "`references/marker-schema.md`, `references/docx-style.md`, "
        "`references/python-env.md`.\n\n"
        f"{SWS_MARKER_CLOSE}"
    )


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


def apply_plan(plan: list, project_root, plugin_root) -> tuple[bool, list[str]]:
    """Execute plan ops in order; rollback on per-op failure or exception.

    Returns (ok, log). On success, log contains executed-op messages.
    On failure, log contains executed-op messages + rollback messages.
    User-pre-existing files are touched only via the resolutions the user
    accepted at scan-prompt time.
    """
    project_root = Path(project_root).resolve()
    plugin_root = Path(plugin_root).resolve()
    log: list[str] = []
    undo: list[Op] = []

    try:
        for op in plan:
            _execute_op(op, project_root, plugin_root, undo)
            log.append(f"OK  {op.kind:16s} {op.dest or op.source}")
    except Exception as e:
        log.append(f"FAIL {op.kind:16s} {op.dest or op.source}: {e!r}")
        log.append("--- rolling back ---")
        for undo_op in reversed(undo):
            try:
                _rollback_op(undo_op, project_root)
                log.append(f"UNDO {undo_op.kind:15s} {undo_op.dest or undo_op.source}")
            except Exception as ue:
                log.append(f"UNDO-FAIL {undo_op.kind}: {ue!r}")
        return False, log

    return True, log


def _execute_op(op, project_root, plugin_root, undo: list) -> None:
    """Execute a single op; record undo info on success."""
    if op.kind == "mkdir":
        target = project_root / op.dest
        if target.exists():
            return  # idempotent — pre-existing dir, do not record undo
        target.mkdir(parents=True, exist_ok=False)
        undo.append(op)

    elif op.kind == "mv":
        src = project_root / op.source
        dest = project_root / op.dest
        if not src.exists():
            raise FileNotFoundError(f"source missing: {op.source}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        undo.append(op)

    elif op.kind == "mv_glob":
        # source like "Figures/*.{png,jpg,...}", dest is a directory
        # For v0.1 simplicity we expand a fixed set of extensions.
        import re
        m = re.match(r"^(.+?)/\*\.\{([^}]+)\}$", op.source)
        if not m:
            raise ValueError(f"unsupported mv_glob source: {op.source}")
        src_dir = project_root / m.group(1)
        exts = m.group(2).split(",")
        moved = []
        for ext in exts:
            for f in sorted(src_dir.glob(f"*.{ext}")):
                target = project_root / op.dest / f.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(target))
                moved.append((str(f), str(target)))
        undo.append(Op(kind="mv_glob", extra={"moved": moved}))

    elif op.kind == "render_template":
        # late import to avoid cycle on import-time
        sys.path.insert(0, str(plugin_root / "scripts"))
        import sws_render_template
        tpl = plugin_root / op.source
        out = project_root / op.dest
        sws_render_template.render(tpl, op.extra.get("vars", {}), out)
        undo.append(op)

    elif op.kind == "write_json":
        out = project_root / op.dest
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(op.extra["content"], indent=2, sort_keys=True))
        undo.append(op)

    elif op.kind == "append_sws_section":
        target = project_root / op.dest
        if not target.exists():
            raise FileNotFoundError(
                f"CLAUDE.md not found at {op.dest}; C4=append requires it to exist"
            )
        original_content = target.read_text()
        block = _build_sws_section(op.extra["short_handle"])
        if SWS_MARKER_OPEN in original_content and SWS_MARKER_CLOSE in original_content:
            # Replace existing SWS-managed section in place
            start = original_content.index(SWS_MARKER_OPEN)
            end = original_content.index(SWS_MARKER_CLOSE) + len(SWS_MARKER_CLOSE)
            new_content = original_content[:start] + block + original_content[end:]
        else:
            # Append at end with a single blank-line separator
            sep = "\n\n" if not original_content.endswith("\n") else (
                "\n" if not original_content.endswith("\n\n") else ""
            )
            new_content = original_content + sep + block + "\n"
        target.write_text(new_content)
        op.extra["_original_content"] = original_content
        undo.append(op)

    else:
        raise ValueError(f"unknown op kind: {op.kind}")


def _rollback_op(op, project_root) -> None:
    """Reverse a previously-executed op."""
    if op.kind == "mkdir":
        target = project_root / op.dest
        if target.is_dir():
            # rmdir only if empty; if non-empty (subsequent ops added contents),
            # the contents were created by other ops which we'll roll back first.
            try:
                target.rmdir()
            except OSError:
                shutil.rmtree(target)

    elif op.kind == "mv":
        # reverse the move
        src = project_root / op.dest
        dest = project_root / op.source
        if src.exists():
            shutil.move(str(src), str(dest))

    elif op.kind == "mv_glob":
        for original, moved_to in reversed(op.extra.get("moved", [])):
            if Path(moved_to).exists():
                shutil.move(moved_to, original)

    elif op.kind == "render_template":
        target = project_root / op.dest
        if target.exists():
            target.unlink()

    elif op.kind == "write_json":
        target = project_root / op.dest
        if target.exists():
            target.unlink()

    elif op.kind == "append_sws_section":
        target = project_root / op.dest
        original = op.extra.get("_original_content")
        if original is not None and target.exists():
            target.write_text(original)


def _cli_scan(args):
    conflicts = scan_conflicts(args.root)
    print(json.dumps([
        {"cls": c.cls, "path": c.path, "suggested_action": c.suggested_action,
         "options": c.options}
        for c in conflicts
    ], indent=2))
    return 0


def _cli_plan(args):
    inputs = json.loads(Path(args.inputs).read_text())
    resolutions = json.loads(Path(args.resolutions).read_text()) if args.resolutions else {}
    conflicts_data = json.loads(Path(args.conflicts).read_text()) if args.conflicts else []
    conflicts = [Conflict(**c) for c in conflicts_data]
    ok, msg = validate_inputs(inputs)
    if not ok:
        print(msg, file=sys.stderr)
        return 2
    plan = build_plan(inputs, conflicts=conflicts, resolutions=resolutions)
    print(json.dumps([
        {"kind": op.kind, "source": op.source, "dest": op.dest,
         "reason": op.reason, "extra": op.extra}
        for op in plan
    ], indent=2))
    return 0


def _cli_apply(args):
    plan_data = json.loads(Path(args.plan).read_text())
    plan = [Op(**op) for op in plan_data]
    ok, log = apply_plan(plan, project_root=args.root, plugin_root=args.plugin_root)
    for line in log:
        print(line)
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--root", default=".")
    p_scan.set_defaults(func=_cli_scan)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--inputs", required=True)
    p_plan.add_argument("--conflicts")
    p_plan.add_argument("--resolutions")
    p_plan.set_defaults(func=_cli_plan)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--plan", required=True)
    p_apply.add_argument("--root", default=".")
    p_apply.add_argument("--plugin-root", required=True)
    p_apply.set_defaults(func=_cli_apply)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
