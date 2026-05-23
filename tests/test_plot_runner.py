"""Unit tests for sws_plot_runner.py — D6a font-floor + width-bounds enforcement.

Uses matplotlib Agg backend; no display required.
All fixtures are synthetic (inline plot scripts as strings).
"""
from __future__ import annotations

import importlib
import sys
import textwrap
import types
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Conditionally import matplotlib; skip entire module if absent.
# ---------------------------------------------------------------------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.text as mtext
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

pytestmark = pytest.mark.skipif(not HAS_MATPLOTLIB, reason="matplotlib not installed")

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import sws_plot_runner as runner  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plot_script(font_size: float, width_in: float, tmp_path: Path) -> Path:
    """Write a minimal plot script that creates a figure of the given width and font size."""
    script_src = textwrap.dedent(f"""\
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=({width_in!r}, 3.0))
        ax.plot([0, 1], [0, 1])
        ax.set_xlabel("Time (s)", fontsize={font_size!r})
        ax.set_ylabel("Value", fontsize={font_size!r})
        ax.set_title("Test figure", fontsize={font_size!r})
        ax.tick_params(labelsize={font_size!r})
    """)
    script = tmp_path / "plot_test.py"
    script.write_text(script_src)
    return script


# ---------------------------------------------------------------------------
# (a) rcParams font floor is applied before script runs
# ---------------------------------------------------------------------------

def test_rcparams_font_floor_applied(tmp_path):
    """Runner must inject rcParams so that font.size >= 8 before executing the user script."""
    # Write a script that reads matplotlib.rcParams['font.size'] and writes it to a file.
    probe_path = tmp_path / "font_size_probe.txt"
    script_src = textwrap.dedent(f"""\
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(2.953, 3.0))
        ax.plot([0, 1], [0, 1])
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        with open({str(probe_path)!r}, "w") as fh:
            fh.write(str(matplotlib.rcParams.get("font.size", 0)))
    """)
    script = tmp_path / "probe.py"
    script.write_text(script_src)

    result = runner.run(script_path=script, width_cm=7.5, out_dir=tmp_path)

    assert probe_path.exists(), "probe script did not run"
    injected_size = float(probe_path.read_text().strip())
    assert injected_size >= 8.0, (
        f"rcParams font.size was {injected_size} — floor not applied"
    )


# ---------------------------------------------------------------------------
# (b) Figure containing <8 pt text -> FAIL listing the offending element
# ---------------------------------------------------------------------------

def test_small_font_returns_fail(tmp_path):
    """A figure with an xlabel set to 5 pt must return pass=False and name the element."""
    script = _make_plot_script(font_size=5.0, width_in=2.953, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=7.5, out_dir=tmp_path)

    assert result["pass"] is False, "Expected FAIL for 5 pt text"
    assert len(result["offending_elements"]) > 0, "Expected at least one offending element listed"
    # The offending element descriptions must include a font-size mention
    combined = " ".join(str(e) for e in result["offending_elements"])
    assert "font" in combined.lower() or "pt" in combined.lower() or "size" in combined.lower(), (
        f"offending_elements should describe a font issue: {result['offending_elements']}"
    )


def test_small_font_element_names_artist(tmp_path):
    """The offending-element entry must identify which text artist violated the floor."""
    script = _make_plot_script(font_size=5.0, width_in=2.953, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=7.5, out_dir=tmp_path)

    assert result["pass"] is False
    # At minimum the entry must carry a font_size value smaller than 8
    sizes = [e.get("font_size") for e in result["offending_elements"] if isinstance(e, dict)]
    assert any(s is not None and s < 8.0 for s in sizes), (
        f"No offending element reports font_size < 8: {result['offending_elements']}"
    )


# ---------------------------------------------------------------------------
# (c) Width outside allowed set -> FAIL
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_width_cm", [
    5.0,   # below single-column (7.5 cm)
    10.0,  # between single and double (8–11.9 cm gap)
    17.0,  # above double-column hard max (16 cm)
])
def test_bad_width_returns_fail(tmp_path, bad_width_cm):
    """Widths outside {7.5 cm} and {12–16 cm} must return pass=False."""
    # Convert cm to inches for the script figsize
    width_in = bad_width_cm / 2.54
    script = _make_plot_script(font_size=9.0, width_in=width_in, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=bad_width_cm, out_dir=tmp_path)

    assert result["pass"] is False, (
        f"Expected FAIL for width {bad_width_cm} cm — got PASS"
    )
    assert "width" in result.get("error", "").lower() or any(
        "width" in str(e).lower() for e in result.get("offending_elements", [])
    ), f"FAIL message should mention width: {result}"


# ---------------------------------------------------------------------------
# (d) Valid figure -> PASS with width + min-font recorded
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("width_cm,width_in", [
    (7.5, 2.953),   # single-column
    (12.0, 4.724),  # double-column minimum
    (16.0, 6.299),  # double-column hard max
])
def test_valid_figure_passes_and_records_metrics(tmp_path, width_cm, width_in):
    """A figure with 9 pt text and an allowed width must return pass=True
    with width_in and min_font_pt recorded in the result."""
    script = _make_plot_script(font_size=9.0, width_in=width_in, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=width_cm, out_dir=tmp_path)

    assert result["pass"] is True, (
        f"Expected PASS for width {width_cm} cm / 9 pt text — got FAIL: {result}"
    )
    assert "width_in" in result, "Result must record width_in"
    assert "min_font_pt" in result, "Result must record min_font_pt"
    assert result["min_font_pt"] >= 8.0, (
        f"min_font_pt {result['min_font_pt']} should be >= 8 for a 9 pt figure"
    )
    assert abs(result["width_in"] - width_in) < 0.05, (
        f"Recorded width_in {result['width_in']} far from expected {width_in}"
    )


def test_valid_figure_saves_to_out_dir(tmp_path):
    """Runner must save the figure file to out_dir and report the path."""
    script = _make_plot_script(font_size=9.0, width_in=2.953, tmp_path=tmp_path)
    result = runner.run(script_path=script, width_cm=7.5, out_dir=tmp_path)

    assert result["pass"] is True
    assert "figure_path" in result, "Result must include figure_path"
    assert Path(result["figure_path"]).exists(), (
        f"figure_path {result['figure_path']} does not exist on disk"
    )
