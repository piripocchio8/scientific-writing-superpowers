#!/usr/bin/env python3
"""SWS template renderer — string.Template-based, stdlib-only.

Renders a .template file with ${var} substitutions into an output path.
Strict mode: missing variables raise KeyError. CLI returns rc 2 on
missing-variable, 0 on success.

Usage:
    python sws_render_template.py --template <path> --vars-file <vars.json> --out <path>
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from string import Template


def render(template_path, vars_dict, out_path) -> None:
    """Render template_path with vars_dict to out_path. Strict on missing vars."""
    template_text = Path(template_path).read_text()
    template = Template(template_text)
    rendered = template.substitute(vars_dict)  # raises KeyError on missing var
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True)
    parser.add_argument("--vars-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    vars_dict = json.loads(Path(args.vars_file).read_text())
    try:
        render(args.template, vars_dict, args.out)
    except KeyError as e:
        print(f"Missing template variable: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
