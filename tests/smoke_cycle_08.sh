#!/usr/bin/env bash
# Cycle-#8 end-to-end smoke. Exercises the revising pipeline:
#   1.  Bootstrap: copy fixture, create .venv symlink, write marker
#   2.  agent_prelude resolves correctly (perspective, RESOLVED_OK=1)
#   3.  reviser-full should_run → exit 0
#   4.  reviser-fast should_run → exit 0
#   5.  humanizer should_run → exit 0
#   6.  style-enforcer should_run → exit 0
#   7.  consistency-checker should_run → exit 0
#   8.  sws_consistency_check.py writes _review/consistency-report.md
#   9.  sws_lint_ai_tells.py on intro.md → exit 1 (seeded delve is block)
#  10.  sws_lint_ai_tells.py on conclusion.md → exit 0 (no block hits)
#  11.  sws_write_docx.py produces a valid .docx
#  12.  sws_apply_chemistry_format.py --dry-run reports candidate transforms
#  13.  Section router action axis: revise→reviser-fast, consistency, style, lint
#  14.  sws_lint_ai_tells.py --json returns valid JSON
#  15.  chemistry-formatting.md has all 6 categories
#
# The smoke copies the gitignored-marker fixture to a tmpdir (so
# .sws-project.local.md and .venv/ can be created on the fly), then runs
# the underlying python helpers directly.
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC_FIXTURE="$REPO/tests/fixtures/cycle_08_paper"
TMP="$(mktemp -d)"
trap "rm -rf $TMP" EXIT
FIXTURE="$TMP/cycle_08_paper"

# ---------------------------------------------------------------------------
# Bootstrap: copy committed fixture skeleton, then generate the marker + venv
# that are gitignored. Start clean so prior runs don't bleed in.
# ---------------------------------------------------------------------------
cp -r "$SRC_FIXTURE" "$FIXTURE"
rm -rf "$FIXTURE/.venv" "$FIXTURE/.sws-project.local.md"
mkdir -p "$FIXTURE/.venv/bin"
# Resolve a python interpreter that has PyYAML, python-docx, and openpyxl.
if python3 -c "import yaml, docx, openpyxl" 2>/dev/null; then
    ln -s "$(command -v python3)" "$FIXTURE/.venv/bin/python"
elif [[ -n "${SWS_SMOKE_PYTHON:-}" && -x "${SWS_SMOKE_PYTHON}" ]]; then
    ln -s "${SWS_SMOKE_PYTHON}" "$FIXTURE/.venv/bin/python"
else
    echo "FAIL: no python with PyYAML found for smoke (system python3 needs pyyaml installed, or set SWS_SMOKE_PYTHON to a python that has it)" >&2
    exit 1
fi
cat > "$FIXTURE/.sws-project.local.md" <<'MARKER'
---
profile: perspective
language: en
format: docx
---
MARKER

PASS=0
FAIL=0
step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  OK\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

# ---------------------------------------------------------------------------
# Step 1: Bootstrap verification
# ---------------------------------------------------------------------------
step 1 "bootstrap: marker exists with profile: perspective"
if grep -q "profile: perspective" "$FIXTURE/.sws-project.local.md" \
    && [[ -x "$FIXTURE/.venv/bin/python" ]]; then ok; else ko "marker or venv missing"; fi

# ---------------------------------------------------------------------------
# Step 2: agent_prelude resolves correctly
# ---------------------------------------------------------------------------
step 2 "agent_prelude resolves RESOLVED_PROFILE_ID=perspective, RESOLVED_OK=1"
PRELUDE_ID="$(
  CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash -c "source '$REPO/scripts/agent_prelude.sh' reviser-fast; printf '%s' \"\$RESOLVED_PROFILE_ID\"" 2>&1
)" || true
PRELUDE_OK="$(
  CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash -c "source '$REPO/scripts/agent_prelude.sh' reviser-fast; printf '%s' \"\$RESOLVED_OK\"" 2>&1
)" || true
if [[ "$PRELUDE_ID" == "perspective" && "$PRELUDE_OK" == "1" ]]; then ok
else ko "RESOLVED_PROFILE_ID='$PRELUDE_ID' RESOLVED_OK='$PRELUDE_OK'"; fi

# ---------------------------------------------------------------------------
# Steps 3–7: agent_should_run for all 5 cycle-#8 revising agents
# ---------------------------------------------------------------------------
step 3 "reviser-full should_run for perspective"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" reviser-full; then ok; else ko; fi

step 4 "reviser-fast should_run for perspective"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" reviser-fast; then ok; else ko; fi

step 5 "humanizer should_run for perspective"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" humanizer; then ok; else ko; fi

step 6 "style-enforcer should_run for perspective"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" style-enforcer; then ok; else ko; fi

step 7 "consistency-checker should_run for perspective"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" consistency-checker; then ok; else ko; fi

# ---------------------------------------------------------------------------
# Step 8: sws_consistency_check.py writes _review/consistency-report.md
# ---------------------------------------------------------------------------
step 8 "sws_consistency_check.py writes _review/consistency-report.md"
"$REPO/scripts/sws_python.sh" "$FIXTURE" \
    "$REPO/scripts/sws_consistency_check.py" \
    "$FIXTURE/_drafts" \
    --outline "$FIXTURE/_outline/outline.md" \
    >/dev/null 2>&1 || true
REPORT="$FIXTURE/_review/consistency-report.md"
if [[ -f "$REPORT" ]]; then
    # Verify it parses as text (non-empty, has a heading)
    if grep -q "^#\|findings\|Consistency" "$REPORT" 2>/dev/null; then ok
    else ko "report exists but looks empty/invalid"; fi
else
    ko "report not written at $REPORT"
fi

# ---------------------------------------------------------------------------
# Step 9: sws_lint_ai_tells.py on intro.md → exit 1 (seeded 'delve')
# ---------------------------------------------------------------------------
step 9 "sws_lint_ai_tells.py on intro.md exits 1 (seeded delve is block-severity)"
LINT_EXIT=0
"$REPO/scripts/sws_python.sh" "$FIXTURE" \
    "$REPO/scripts/sws_lint_ai_tells.py" \
    "$FIXTURE/_drafts/intro.md" >/dev/null 2>&1 || LINT_EXIT=$?
if [[ "$LINT_EXIT" -eq 1 ]]; then ok; else ko "expected exit 1, got $LINT_EXIT"; fi

# ---------------------------------------------------------------------------
# Step 10: sws_lint_ai_tells.py on conclusion.md → exit 0 (no block hits)
# ---------------------------------------------------------------------------
step 10 "sws_lint_ai_tells.py on conclusion.md exits 0 (no block hits)"
LINT_EXIT=0
"$REPO/scripts/sws_python.sh" "$FIXTURE" \
    "$REPO/scripts/sws_lint_ai_tells.py" \
    "$FIXTURE/_drafts/conclusion.md" >/dev/null 2>&1 || LINT_EXIT=$?
if [[ "$LINT_EXIT" -eq 0 ]]; then ok; else ko "expected exit 0, got $LINT_EXIT"; fi

# ---------------------------------------------------------------------------
# Step 11: sws_write_docx.py produces a valid .docx
# ---------------------------------------------------------------------------
step 11 "sws_write_docx.py produces a valid .docx"
DOCX_OUT="$FIXTURE/Manuscript/test.docx"
mkdir -p "$FIXTURE/Manuscript"
"$REPO/scripts/sws_python.sh" "$FIXTURE" \
    "$REPO/scripts/sws_write_docx.py" "$DOCX_OUT" \
    --from-markdown "$FIXTURE/_drafts/intro.md" >/dev/null 2>&1
if [[ -s "$DOCX_OUT" ]]; then
    # Verify python-docx can reopen it
    "$FIXTURE/.venv/bin/python" -c "
import docx as _d; d = _d.Document('$DOCX_OUT'); assert len(d.paragraphs) > 0
" 2>/dev/null && ok || ko "file exists but python-docx cannot reopen it"
else
    ko "docx not produced or zero bytes"
fi

# ---------------------------------------------------------------------------
# Step 12: sws_apply_chemistry_format.py --dry-run reports candidate transforms
# ---------------------------------------------------------------------------
step 12 "sws_apply_chemistry_format.py --dry-run reports candidate transforms"
CHEM_OUT="$("$REPO/scripts/sws_python.sh" "$FIXTURE" \
    "$REPO/scripts/sws_apply_chemistry_format.py" "$DOCX_OUT" \
    --dry-run 2>&1)" || true
CHEM_EXIT=$?
# Verify exit 0 and that stdout contains a known chemistry marker
if [[ "$CHEM_EXIT" -eq 0 ]] && \
   (echo "$CHEM_OUT" | grep -qiE "H2O|et al\.|chemical_formulae|latin_abbreviations|species_abbreviated"); then
    ok
else
    ko "exit=$CHEM_EXIT; output did not contain expected chemistry markers. Output: ${CHEM_OUT:0:200}"
fi

# ---------------------------------------------------------------------------
# Step 13: Router action axis
# ---------------------------------------------------------------------------
step 13 "router action axis: revise→reviser-fast, consistency→consistency-checker, style→style-enforcer, lint→script sentinel"
ROUTE_REVISE="$("$FIXTURE/.venv/bin/python" -c "
import sys; sys.path.insert(0, '$REPO/scripts')
from sws_section_router import route_section
print(route_section('intro', 'perspective', 'revise'))
" 2>/dev/null)" || ROUTE_REVISE="<error>"

ROUTE_CONSISTENCY="$("$FIXTURE/.venv/bin/python" -c "
import sys; sys.path.insert(0, '$REPO/scripts')
from sws_section_router import route_section
print(route_section('intro', 'perspective', 'consistency'))
" 2>/dev/null)" || ROUTE_CONSISTENCY="<error>"

ROUTE_STYLE="$("$FIXTURE/.venv/bin/python" -c "
import sys; sys.path.insert(0, '$REPO/scripts')
from sws_section_router import route_section
print(route_section('intro', 'perspective', 'style'))
" 2>/dev/null)" || ROUTE_STYLE="<error>"

ROUTE_LINT="$("$FIXTURE/.venv/bin/python" -c "
import sys; sys.path.insert(0, '$REPO/scripts')
from sws_section_router import route_section
print(route_section('intro', 'perspective', 'lint'))
" 2>/dev/null)" || ROUTE_LINT="<error>"

if [[ "$ROUTE_REVISE" == "reviser-fast" \
   && "$ROUTE_CONSISTENCY" == "consistency-checker" \
   && "$ROUTE_STYLE" == "style-enforcer" \
   && "$ROUTE_LINT" == "script:sws_lint_ai_tells.py" ]]; then
    ok
else
    ko "revise='$ROUTE_REVISE' consistency='$ROUTE_CONSISTENCY' style='$ROUTE_STYLE' lint='$ROUTE_LINT'"
fi

# ---------------------------------------------------------------------------
# Step 14: sws_lint_ai_tells.py --json returns valid JSON
# ---------------------------------------------------------------------------
step 14 "sws_lint_ai_tells.py --json returns valid JSON"
JSON_OUT="$("$REPO/scripts/sws_python.sh" "$FIXTURE" \
    "$REPO/scripts/sws_lint_ai_tells.py" \
    "$FIXTURE/_drafts/intro.md" --json 2>/dev/null)" || true
if echo "$JSON_OUT" | "$FIXTURE/.venv/bin/python" -c \
    "import json,sys; data=json.loads(sys.stdin.read()); assert isinstance(data, list)" 2>/dev/null
then
    ok
else
    ko "output is not valid JSON or not a list. Got: ${JSON_OUT:0:120}"
fi

# ---------------------------------------------------------------------------
# Step 15: chemistry-formatting.md has all 6 categories
# ---------------------------------------------------------------------------
step 15 "chemistry-formatting.md has all 6 required categories"
CATALOG="$REPO/references/chemistry-formatting.md"
MISSING=""
for CAT in latin_abbreviations chemical_formulae species_names species_abbreviated gene_names figure_label_prefix; do
    if ! grep -q "^  ${CAT}:\|^${CAT}:" "$CATALOG" 2>/dev/null; then
        MISSING="$MISSING $CAT"
    fi
done
if [[ -z "$MISSING" ]]; then ok; else ko "missing categories:$MISSING"; fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf "\nsmoke_cycle_08: PASSED %d/15\n" "$PASS"
[[ "$FAIL" -eq 0 ]] || exit 1
