#!/usr/bin/env bash
# smoke_cycle_13.sh — 10-step e2e for cycle #13 (NLM integration + v0.1 banner flip).
#
# Steps:
#   1. bootstrap tmp dir from fixture
#   2. probe with marker notebooklm.enabled=false -> exit 0, stderr "disabled"
#   3. probe with marker notebooklm.enabled=true, no stub on PATH -> exit 4
#   4. probe with stub on PATH -> exit 0
#   5. query through wrapper -> valid JSON, ok=true, sources[] non-empty
#   6. resolver+prelude pipeline: enabled=true + notebook_id flows to RESOLVED_*
#   7. unit-test sweep: tests.test_sws_nlm_wrapper + tests.test_nlm_librarian_dispatch +
#      tests.test_consumer_nlm_degrade + tests.test_resolve_overlay_notebooklm
#   8. confirm no consumer agent references sws_nlm.sh (D5)
#   9. banner gate (tests.test_banner_v01) -- passes post-Phase-6, fails before
#  10. summary line "SMOKE PASS: 10/10"
#
# Reads:
#   tests/fixtures/sample-cycle-13/fake_notebooklm_mcp_cli.sh
#   tests/fixtures/sample-cycle-13/marker.template
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
WRAPPER="$REPO/scripts/sws_nlm.sh"
FIXTURE_DIR="$REPO/tests/fixtures/sample-cycle-13"
STUB="$FIXTURE_DIR/fake_notebooklm_mcp_cli.sh"
MARKER_TEMPLATE="$FIXTURE_DIR/marker.template"

TMP="$(mktemp -d)"
trap "rm -rf '$TMP'" EXIT

PASS=0
FAIL=0
step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  OK\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

PAPER="$TMP/paper"
mkdir -p "$PAPER" "$TMP/bin_dir"

step 1 "Bootstrap fixture marker"
sed 's/__NLM_ENABLED__/false/; s/__NLM_NOTEBOOK_ID__/null/' "$MARKER_TEMPLATE" > "$PAPER/.sws-project.local.md"
test -f "$PAPER/.sws-project.local.md" && ok || ko "marker not written"

step 2 "Probe with notebooklm.enabled=false -> exit 0 'disabled'"
unset SWS_NLM_PROBE_RESULT
out="$(bash "$WRAPPER" probe 2>&1)" && rc=0 || rc=$?
if [[ $rc -eq 0 ]] && echo "$out" | grep -qi disabled; then ok; else ko "rc=$rc out=$out"; fi

step 3 "Probe enabled=true, no stub on PATH -> exit 4"
unset SWS_NLM_PROBE_RESULT
PATH_SAVED="$PATH"
PATH="/usr/bin:/bin" RESOLVED_NOTEBOOKLM_ENABLED=true \
    bash "$WRAPPER" probe 2>/dev/null && rc=0 || rc=$?
if [[ $rc -eq 4 ]]; then ok; else ko "expected exit 4, got $rc"; fi

step 4 "Probe with stub on PATH -> exit 0"
unset SWS_NLM_PROBE_RESULT
cp "$STUB" "$TMP/bin_dir/notebooklm-mcp-cli"
chmod +x "$TMP/bin_dir/notebooklm-mcp-cli"
PATH="$TMP/bin_dir:/usr/bin:/bin" RESOLVED_NOTEBOOKLM_ENABLED=true \
    bash "$WRAPPER" probe 2>/dev/null && rc=0 || rc=$?
if [[ $rc -eq 0 ]]; then ok; else ko "expected exit 0, got $rc"; fi

step 5 "Query through wrapper -> valid JSON, ok=true, sources non-empty"
unset SWS_NLM_PROBE_RESULT
qjson="$(PATH="$TMP/bin_dir:/usr/bin:/bin" RESOLVED_NOTEBOOKLM_ENABLED=true \
    bash "$WRAPPER" query "what is foo?" 2>/dev/null)"
qok="$(echo "$qjson" | python3 -c '
import json, sys
d = json.loads(sys.stdin.read())
assert d["ok"] is True, d
assert len(d["sources"]) > 0, d
assert d["fallback"] == "none", d
print("YES")
' 2>/dev/null || true)"
if [[ "$qok" = "YES" ]]; then ok; else ko "qjson=$qjson"; fi

step 6 "Resolver+prelude: enabled=true + notebook_id -> RESOLVED_*"
sed 's/__NLM_ENABLED__/true/; s/__NLM_NOTEBOOK_ID__/nb-xyz/' "$MARKER_TEMPLATE" > "$PAPER/.sws-project.local.md"
# Set up a plugin-shape with a sws_python shim so prelude can call resolver
PLUGIN="$TMP/plugin"
mkdir -p "$PLUGIN/scripts"
ln -sf "$REPO/scripts/resolve_overlay.py" "$PLUGIN/scripts/resolve_overlay.py"
ln -sf "$REPO/scripts/agent_prelude.sh"   "$PLUGIN/scripts/agent_prelude.sh"
ln -sf "$REPO/scripts/agent_should_run.sh" "$PLUGIN/scripts/agent_should_run.sh"
cat > "$PLUGIN/scripts/sws_python.sh" <<'PYSHIM'
#!/usr/bin/env bash
shift
exec python3 "$@"
PYSHIM
chmod +x "$PLUGIN/scripts/sws_python.sh"
ln -sf "$REPO/profiles" "$PLUGIN/profiles"

prelude_out="$(bash -c '
set +u
export CLAUDE_PLUGIN_ROOT="'"$PLUGIN"'"
export PAPER_ROOT="'"$PAPER"'"
source "$CLAUDE_PLUGIN_ROOT/scripts/agent_prelude.sh" claim-verifier
echo "ENABLED=$RESOLVED_NOTEBOOKLM_ENABLED"
echo "NB=$RESOLVED_NLM_NOTEBOOK_ID"
' 2>/dev/null)"
if echo "$prelude_out" | grep -q "ENABLED=true" && echo "$prelude_out" | grep -q "NB=nb-xyz"; then
    ok
else
    ko "prelude_out=$prelude_out"
fi

step 7 "Unit-test sweep"
if python3 -m unittest tests.test_sws_nlm_wrapper tests.test_nlm_librarian_dispatch tests.test_consumer_nlm_degrade tests.test_resolve_overlay_notebooklm >/dev/null 2>&1; then
    ok
else
    ko "unittest failed"
fi

step 8 "D5 enforcement: no consumer references sws_nlm.sh"
offenders="$(grep -l "sws_nlm.sh" "$REPO/agents/"*.md | grep -v nlm-librarian.md || true)"
if [[ -z "$offenders" ]]; then ok; else ko "D5 violation: $offenders"; fi

step 9 "Banner gate (tests.test_banner_v01)"
if python3 -m unittest tests.test_banner_v01 >/dev/null 2>&1; then
    ok
else
    ko "banner gate not yet flipped (Phase 6 pending) — expected fail pre-flip"
fi

step 10 "Summary"
echo
echo "smoke_cycle_13.sh: $PASS passed, $FAIL failed (10 total)"
if [[ $FAIL -eq 0 ]]; then
    echo "SMOKE PASS: 10/10"
    exit 0
else
    echo "SMOKE FAIL"
    exit 1
fi
