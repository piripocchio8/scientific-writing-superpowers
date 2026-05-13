#!/usr/bin/env bash
# Cycle #6 e2e smoke. Runs the 7-step walkthrough from the spec against a
# bootstrapped dummy paper. Prints PASS/FAIL per step. Exit code reflects
# overall result (0 = all green, non-zero = first failure).
set -eu
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap "rm -rf $TMP" EXIT

# Bootstrap a dummy paper: copy marker fixture and create a minimal .venv/
# (python3 -m venv); skip pip install for speed via SWS_TEST_SKIP_PIP=1.
cp -r "$PLUGIN_ROOT/tests/fixtures/papers/dummy_paper/." "$TMP/"
export PAPER_ROOT="$TMP"
export CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT"
export SWS_TEST_SKIP_PIP=1

# Bootstrap a minimal .venv/bin/ layout. We don't run `python3 -m venv` here
# because the resolver needs PyYAML — letting the venv's site-packages take
# over would hide the host's yaml. Instead, we make .venv/bin/python a direct
# symlink to a python that has PyYAML. The sws_python.sh wrapper only requires
# .venv/bin/python to exist and be executable.
#
# Resolution order: system python3 (if PyYAML available) → $SWS_SMOKE_PYTHON
# (developer override, set to any python interpreter with PyYAML installed).
mkdir -p "$TMP/.venv/bin"
if python3 -c "import yaml" 2>/dev/null; then
    ln -s "$(command -v python3)" "$TMP/.venv/bin/python"
elif [[ -n "${SWS_SMOKE_PYTHON:-}" && -x "${SWS_SMOKE_PYTHON}" ]]; then
    ln -s "${SWS_SMOKE_PYTHON}" "$TMP/.venv/bin/python"
else
    echo "FAIL: no python with PyYAML found for smoke (system python3 needs pyyaml installed, or set SWS_SMOKE_PYTHON to a python that has it)" >&2
    exit 1
fi

PASS=0
FAIL=0
say_pass() { echo "PASS $*"; PASS=$((PASS+1)); }
say_fail() { echo "FAIL $*"; FAIL=$((FAIL+1)); }

# Step 1: set-profile communication
if "$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
     "$PLUGIN_ROOT/scripts/sws_set_profile.py" \
     --paper "$PAPER_ROOT" --name communication \
     | grep -q "profile: communication"; then
    say_pass "step 1 (set-profile communication)"
else
    say_fail "step 1 (set-profile communication)"
    exit 1
fi

# Step 2: resolve-journal-style chembiochem (using synthesizer fixture)
SWS_TEST_FIXTURE_SYNTH_OUTPUT="$PLUGIN_ROOT/tests/fixtures/synthesizer_outputs/chembiochem.yaml" \
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
    "$PLUGIN_ROOT/scripts/sws_resolve_journal_style.py" \
    --paper "$PAPER_ROOT" --slug chembiochem --noninteractive >/dev/null

if [[ -f "$PAPER_ROOT/Manuscript/_journal-style/chembiochem.md" ]]; then
    say_pass "step 2 (overlay written)"
else
    say_fail "step 2 (overlay missing)"
    exit 1
fi
if [[ ! -d "$PAPER_ROOT/Manuscript/_journal-style/_archive" ]]; then
    say_pass "step 2b (no archive on first resolve)"
else
    say_fail "step 2b (archive should not exist on first resolve)"
    exit 1
fi

# Step 3: re-run with different fixture → archive populated
SWS_TEST_FIXTURE_SYNTH_OUTPUT="$PLUGIN_ROOT/tests/fixtures/synthesizer_outputs/chembiochem-alt.yaml" \
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
    "$PLUGIN_ROOT/scripts/sws_resolve_journal_style.py" \
    --paper "$PAPER_ROOT" --slug chembiochem --noninteractive >/dev/null

if ls "$PAPER_ROOT/Manuscript/_journal-style/_archive/" 2>/dev/null | grep -q "chembiochem-"; then
    say_pass "step 3 (re-resolve archives)"
else
    say_fail "step 3 (archive missing)"
    exit 1
fi

# Step 4: agent_prelude active for drafter
if bash -c "source '$PLUGIN_ROOT/scripts/agent_prelude.sh' drafter; [[ \"\$RESOLVED_OK\" == \"1\" ]] && [[ -n \"\$RESOLVED_REF_CAP\" ]]"; then
    say_pass "step 4 (drafter prelude OK, REF_CAP set)"
else
    say_fail "step 4 (drafter prelude failed)"
    exit 1
fi

# Step 5: agent gated by matrix
# proposal-budget-helper is inactive in communication profile → RESOLVED_OK should be 0.
if bash -c "source '$PLUGIN_ROOT/scripts/agent_prelude.sh' proposal-budget-helper; [[ \"\$RESOLVED_OK\" == \"0\" ]]" 2>/dev/null; then
    say_pass "step 5 (proposal-budget-helper gated off in communication)"
else
    say_fail "step 5 (matrix gating broken)"
    exit 1
fi

# Step 6: set profile null → agent aborts
python3 -c "
import sys
sys.path.insert(0, '$PLUGIN_ROOT/scripts')
from sws_hook_utils import write_marker_field
from pathlib import Path
write_marker_field(Path('$PAPER_ROOT/.sws-project.local.md'), 'profile', None)
"
if bash -c "source '$PLUGIN_ROOT/scripts/agent_prelude.sh' drafter; [[ \"\$RESOLVED_OK\" == \"0\" ]]" 2>/dev/null; then
    say_pass "step 6 (drafter aborts with profile null)"
else
    say_fail "step 6 (drafter ran with profile null)"
    exit 1
fi

# Step 7: funding-proposal → call rules
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
    "$PLUGIN_ROOT/scripts/sws_set_profile.py" \
    --paper "$PAPER_ROOT" --name funding-proposal >/dev/null

mkdir -p "$PAPER_ROOT/Manuscript/call"
cp "$PLUGIN_ROOT/tests/fixtures/calls/prin_2024.md" "$PAPER_ROOT/Manuscript/call/"
SWS_TEST_FIXTURE_SYNTH_OUTPUT="$PLUGIN_ROOT/tests/fixtures/synthesizer_outputs/prin_2024.yaml" \
SWS_TEST_FIXTURE_SOURCE_TEXT="$PAPER_ROOT/Manuscript/call/prin_2024.md" \
"$PLUGIN_ROOT/scripts/sws_python.sh" "$PAPER_ROOT" \
    "$PLUGIN_ROOT/scripts/sws_resolve_call_rules.py" \
    --paper "$PAPER_ROOT" --noninteractive >/dev/null

if [[ -f "$PAPER_ROOT/Manuscript/_call/prin_2024.md" ]]; then
    say_pass "step 7 (call overlay written from uploaded source)"
else
    say_fail "step 7 (call overlay missing)"
    exit 1
fi

echo
echo "smoke result: $PASS pass, $FAIL fail"
if [[ "$FAIL" -eq 0 ]]; then
    echo "smoke PASS"
    exit 0
else
    echo "smoke FAIL"
    exit 1
fi
