"""Extract citation-bearing claims from _drafts/*-revised.md.

Each claim is one sentence containing at least one ``[@key]`` citation.
Multi-key citations (``[@a2020; @b2021]``) are flattened into a single
claim with all keys attached. Section id is derived from the filename
prefix (e.g. ``introduction-revised.md`` → ``introduction``).

Output schema (one entry per claim):
{
  "section": "<section-id>",
  "claim": "<sentence text>",
  "citation_keys": ["key1", "key2"],
  "verification_status": "pending",
  "source_match": []
}

verification_status and source_match are populated by the claim-verifier
agent after this script runs; the script itself never queries any external
source.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict


_CITATION_RE = re.compile(r"\[@([^\]]+)\]")
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _section_id_from_filename(path: Path) -> str:
    name = path.stem
    if name.endswith("-revised"):
        name = name[: -len("-revised")]
    return name


def _split_sentences(text: str) -> List[str]:
    text = text.replace("\n", " ")
    parts = _SENTENCE_END_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _parse_citation_keys(raw: str) -> List[str]:
    return [k.strip().lstrip("@") for k in raw.split(";") if k.strip()]


def extract_claims_from_drafts(drafts_dir: Path) -> List[Dict]:
    """Return list of claim dicts across all -revised.md files in drafts_dir."""
    claims: List[Dict] = []
    files = sorted(drafts_dir.glob("*-revised.md"))
    for f in files:
        section = _section_id_from_filename(f)
        body = f.read_text(encoding="utf-8")
        for sentence in _split_sentences(body):
            matches = _CITATION_RE.findall(sentence)
            if not matches:
                continue
            keys: List[str] = []
            for m in matches:
                keys.extend(_parse_citation_keys(m))
            seen = set()
            unique_keys = [k for k in keys if not (k in seen or seen.add(k))]
            claims.append(
                {
                    "section": section,
                    "claim": sentence.strip(),
                    "citation_keys": unique_keys,
                    "verification_status": "pending",
                    "source_match": [],
                }
            )
    return claims


def write_claims_json(drafts_dir: Path, out_path: Path) -> None:
    claims = extract_claims_from_drafts(drafts_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(claims, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract citation-bearing claims from _drafts/*-revised.md")
    parser.add_argument("drafts_dir", type=Path, help="Directory containing *-revised.md files")
    parser.add_argument("--out", type=Path, required=True, help="Output path for claims.json")
    args = parser.parse_args(argv)

    if not args.drafts_dir.is_dir():
        print(f"error: drafts_dir not found: {args.drafts_dir}", file=sys.stderr)
        return 2

    write_claims_json(args.drafts_dir, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
