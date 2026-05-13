"""Generate tests/fixtures/manuscripts/styled_ok.docx.

Run from the repo root:
    python3 tests/fixtures/manuscripts/_gen_styled_ok.py

The script calls sws_write_docx.py on a hardcoded markdown sample that
exercises all five SWS paragraph styles (SWS-H1, SWS-H2, SWS-Body,
SWS-Caption, SWS-References).  Commit the resulting .docx binary alongside
this generator.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "sws_write_docx.py"
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "styled_ok.docx"

SAMPLE_MARKDOWN = """\
# Introduction

Peptide therapeutics have undergone a significant revival over the past decade.
Cell-penetrating peptides offer a route to intracellular targets previously
considered undruggable.

# Results

## Synthesis and Characterization

The target compound was obtained in 87% isolated yield after HPLC purification.
Spectroscopic data were consistent with the proposed structure.

**Figure 1.** Synthetic route to the key intermediate showing the cyclization step.

**Table 1.** Inhibitory activity (IC50) of compounds 1-5 against thrombin.

## Biological Evaluation

All compounds showed >70% cell viability at 10 μM in HEK293 cells.
The lead compound exhibited an IC50 of 1.2 μM against thrombin.

# Discussion

These data support the mechanism proposed by Smith et al.
The stereochemical outcome is consistent with in vitro selectivity studies.

# Conclusion

We have demonstrated a concise route to potent thrombin inhibitors.
Further studies will address in vivo pharmacokinetics.

## References

1. Smith J. et al. *Nature Chemistry* 2024, 16, 123–131.
2. Jones A. B.; Brown C. D. *J. Am. Chem. Soc.* 2023, 145, 4567–4578.
3. Lee E. et al. *Angew. Chem. Int. Ed.* 2022, 61, e202200001.
"""


def main() -> int:
    tmp_md = HERE / "_tmp_sample.md"
    try:
        tmp_md.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
        cp = subprocess.run(
            [sys.executable, str(SCRIPT), str(OUTPUT), "--from-markdown", str(tmp_md)],
            capture_output=True, text=True,
        )
        if cp.returncode != 0:
            print(f"ERROR (exit {cp.returncode}):\n{cp.stderr}", file=sys.stderr)
            return cp.returncode
        print(f"Generated: {OUTPUT}")
        return 0
    finally:
        if tmp_md.exists():
            tmp_md.unlink()


if __name__ == "__main__":
    sys.exit(main())
