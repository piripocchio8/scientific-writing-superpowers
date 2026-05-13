"""Extract a Zotero collection export into <paper>/_lit/zotero-manifest.md.

Used by /sws:prepare-lit-context. Reads the JSON the user's `zotero` skill
emits (or any equivalent format) and produces a markdown file with YAML
frontmatter + per-item bullet entries per the schema in the cycle-#7 spec.

Pure stdlib output formatting; no PyYAML dependency.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


class ManifestBuildError(ValueError):
    pass


_DEFAULT_CAP_TOKENS = 15000
_TOKENS_PER_CHAR = 0.25  # rough


def _first_author_lastname(creators) -> str:
    for c in creators:
        if c.get("creatorType") in (None, "author") and c.get("lastName"):
            return c["lastName"].strip().replace(" ", "")
    raise ManifestBuildError("no first-author lastName found")


def _extract_year(date_field):
    if not date_field:
        return None
    s = str(date_field).strip()
    # Expect formats: "2023", "2024-03", "2024-03-15"
    if len(s) >= 4 and s[:4].isdigit():
        return s[:4]
    return None


def _summarize_for_manifest(item) -> dict:
    return {
        "key": item.get("key", "UNKNOWN"),
        "first_author": _first_author_lastname(item.get("creators", [])),
        "year": _extract_year(item.get("date")) or "n.d.",
        "title": (item.get("title") or "").strip(),
        "doi": item.get("DOI"),
        "key_claims": (item.get("abstractNote") or "").strip()[:280],
    }


def _estimate_tokens(char_count: int) -> int:
    return int(char_count * _TOKENS_PER_CHAR)


def build_manifest(data: dict, cap_token_budget: int = _DEFAULT_CAP_TOKENS) -> dict:
    items_in = data.get("items", [])
    items_out: list[dict] = []
    accumulated_chars = 0
    truncated = False
    for raw in items_in:
        try:
            entry = _summarize_for_manifest(raw)
        except ManifestBuildError:
            raise
        as_text = json.dumps(entry)
        if _estimate_tokens(accumulated_chars + len(as_text)) > cap_token_budget:
            truncated = True
            break
        accumulated_chars += len(as_text)
        items_out.append(entry)

    return {
        "frontmatter": {
            "exported_from": data.get("collection", "<unknown>"),
            "exported_at": data.get("exported_at") or datetime.now(timezone.utc).isoformat(),
            "item_count": len(items_out),
            "cap_token_budget": cap_token_budget,
            "truncated": truncated,
        },
        "items": items_out,
    }


def render_manifest_md(manifest: dict) -> str:
    fm = manifest["frontmatter"]
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{k}: null")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    for it in manifest["items"]:
        lines.append(f"- key: {it['key']}")
        lines.append(f"  first_author: {it['first_author']}")
        lines.append(f"  year: {it['year']}")
        lines.append(f"  title: {json.dumps(it['title'], ensure_ascii=False)}")
        lines.append(f"  doi: {it['doi'] if it['doi'] else 'null'}")
        lines.append(f"  key_claims: {json.dumps(it['key_claims'], ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to Zotero export JSON")
    p.add_argument("--paper", required=True, help="Path to user paper root")
    p.add_argument("--cap-tokens", type=int, default=_DEFAULT_CAP_TOKENS)
    args = p.parse_args(argv)

    data = json.loads(Path(args.input).read_text())
    try:
        manifest = build_manifest(data, cap_token_budget=args.cap_tokens)
    except ManifestBuildError as exc:
        print(f"sws: {exc}", file=sys.stderr)
        return 2
    md = render_manifest_md(manifest)
    out = Path(args.paper) / "_lit" / "zotero-manifest.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md)
    print(f"sws: wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
