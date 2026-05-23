---
sws_artifact: zenodo-db-layout
artifact_version: 0.1
locked: 2026-05-22
used_by: [agents/data-curator.md, agents/plot-maker.md, skills/curate-data/SKILL.md, skills/make-figure/SKILL.md]
---

# Zenodo_db/ layout (v0.1 — locked D5)

The `Zenodo_db/` directory inside a paper root is the local data-authority layout. It is marker-scoped (only present in SWS projects). Writes pass through the cycle-#5 backup hook.

## Directory structure

```
Zenodo_db/
├── data/         # source .xlsx (the data authority) + raw exports (CSV, TXT)
├── scripts/      # fit + plot scripts, co-located with the data they consume
├── figures/      # plot-maker outputs — PNG, PDF, SVG; regenerable from data/ + scripts/
├── manifest.json # provenance spine: each entry links dataset → script → figure(s)
└── _archive/     # superseded data/figure versions; filenames must include a UTC timestamp
```

## manifest.json schema

`manifest.json` is the single source of figure provenance. Every figure in `figures/` must have an entry here.

```json
[
  {
    "dataset": "data/measurements.xlsx",
    "sheet": "Kinetics",
    "script": "scripts/plot_kinetics.py",
    "figures": ["figures/fig1_kinetics.png", "figures/fig1_kinetics.pdf"],
    "generated_at": "2026-05-22T14:30:00Z",
    "journal_style": "acs-jacs",
    "width_in": 2.953,
    "min_font_pt": 9.0,
    "notes": ""
  }
]
```

**Required keys per entry:**
- `dataset` — relative path inside `Zenodo_db/` to the source `.xlsx` (or other data file)
- `sheet` — worksheet name within the dataset (use `"all"` for single-sheet workbooks)
- `script` — relative path inside `Zenodo_db/` to the plot/fit script that produced the figure(s)
- `figures` — list of relative paths inside `Zenodo_db/` to the produced figure files
- `generated_at` — ISO-8601 UTC timestamp of the last successful regeneration
- `journal_style` — the resolved journal-style overlay id at time of generation (empty string if none resolved)
- `notes` — free text; empty string if unused

**Optional D6a keys per entry** (written by `plot-maker` from `sws_plot_runner.py` output; omitted for non-figure entries):
- `width_in` — actual figure width in inches as built and checked against the D6a width bands
- `min_font_pt` — measured minimum effective font size in pt across the figure's text artists

**Invariant:** `sws_data_manifest.py` writes `manifest.json` atomically (write to `.manifest.json.tmp`, then rename). `plot-maker` always updates `manifest.json` in the same step as writing the figure. Orphaned figures (in `figures/` but no manifest entry) are flagged by `sws_data_manifest.py --check`.

## Formula resolution rule (D4)

`data-curator` reads `.xlsx` files through `sws_xlsx_resolve.py`, which calls `sws_read_xlsx.py` with `data_only=True`. If a formula cell has no cached value (returns `None`), the script exits non-zero with the message:

> `Cell <sheet>!<ref> is a formula with no cached value. Open and save this workbook in Excel or LibreOffice so values cache, then re-run /sws:curate-data.`

The user opens and saves the workbook once; all formula cells cache their values and subsequent runs proceed.

## _archive/ convention

Before overwriting any file in `data/` or `figures/`, the previous version is moved to `_archive/` with a UTC-timestamp suffix:

```
_archive/measurements_20260521T103000Z.xlsx
_archive/fig1_kinetics_20260521T103000Z.png
```

This is handled by the cycle-#5 `PreToolUse` backup hook and is not the agent's responsibility.
