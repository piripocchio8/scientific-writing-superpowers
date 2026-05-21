#!/usr/bin/env bash
# smoke_cycle_09.sh — 18-step e2e for cycle #9 (Review pipeline).
#
# Four fixture variants cover all fidelity-checker code paths:
#   variant_1: D9c — no zotero skill, no Zotero desktop
#   variant_2: D9a — no zotero skill, Zotero desktop mocked
#   variant_3: D9b — zotero skill mocked + library < 10 items
#   variant_4: D9  — zotero skill mocked + library >= 10 + seeded violation
#
# Steps 1–8:  bootstrap and cycle-08 baseline (agent_prelude + agent_should_run)
# Step  9:    sws_claim_extract.py → _review/claim-verifier/claims.json
# Steps 10–13: fidelity-checker across all 4 variants via _harness.py
# Step 14:    peer-reviewer agent file exists; _review/peer-reviewer/ creatable
# Step 15:    orchestrator skill references all 3 atomic skills
# Step 16:    sws_claim_extract.py degrades gracefully (no NLM/notebooklm import)
# Step 17:    claim-verifier + fidelity-checker gated off in funding-proposal
# Step 18:    README banner + plugin.json version check
#
# Expected summary: 18 passed, 0 failed
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HARNESS="$REPO/tests/fixtures/cycle_09/_harness.py"

# Source variants (committed fixtures)
SRC_V1="$REPO/tests/fixtures/cycle_09/variant_1_no_zotero"
SRC_V2="$REPO/tests/fixtures/cycle_09/variant_2_zotero_desktop_only"
SRC_V3="$REPO/tests/fixtures/cycle_09/variant_3_skill_empty_library"
SRC_V4="$REPO/tests/fixtures/cycle_09/variant_4_skill_populated"

TMP="$(mktemp -d)"
trap "rm -rf '$TMP'" EXIT

# Working copies (gitignored artefacts created fresh each run)
V1="$TMP/variant_1"
V2="$TMP/variant_2"
V3="$TMP/variant_3"
V4="$TMP/variant_4"

# ---------------------------------------------------------------------------
# Bootstrap: copy committed fixture skeletons, generate .venv + markers
# ---------------------------------------------------------------------------
for SRC_DEST in "$SRC_V1:$V1" "$SRC_V2:$V2" "$SRC_V3:$V3" "$SRC_V4:$V4"; do
    SRC="${SRC_DEST%%:*}"
    DEST="${SRC_DEST##*:}"
    cp -r "$SRC" "$DEST"
    rm -rf "$DEST/.venv" "$DEST/.sws-project.local.md"
    mkdir -p "$DEST/.venv/bin"
    if python3 -c "import yaml, docx, openpyxl" 2>/dev/null; then
        ln -s "$(command -v python3)" "$DEST/.venv/bin/python"
    elif [[ -n "${SWS_SMOKE_PYTHON:-}" && -x "${SWS_SMOKE_PYTHON}" ]]; then
        ln -s "${SWS_SMOKE_PYTHON}" "$DEST/.venv/bin/python"
    else
        echo "FAIL: no python with PyYAML found (set SWS_SMOKE_PYTHON)" >&2
        exit 1
    fi
    # Variant funding-proposal marker written in step 17 separately
    cat > "$DEST/.sws-project.local.md" <<'MARKER'
---
profile: perspective
language: en
format: docx
---
MARKER
done

PASS=0
FAIL=0
step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  OK\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

# ---------------------------------------------------------------------------
# Step 1: Bootstrap verification
# ---------------------------------------------------------------------------
step 1 "bootstrap: markers exist with profile: perspective + .venv in all 4 variants"
ALL_OK=1
for V in "$V1" "$V2" "$V3" "$V4"; do
    if ! grep -q "profile: perspective" "$V/.sws-project.local.md" 2>/dev/null \
       || ! [[ -x "$V/.venv/bin/python" ]]; then
        ALL_OK=0
        break
    fi
done
if [[ "$ALL_OK" -eq 1 ]]; then ok; else ko "marker or venv missing in at least one variant"; fi

# ---------------------------------------------------------------------------
# Step 2: agent_prelude resolves correctly (variant_1 / perspective)
# ---------------------------------------------------------------------------
step 2 "agent_prelude resolves RESOLVED_PROFILE_ID=perspective, RESOLVED_OK=1"
PRELUDE_ID="$(
  CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
  bash -c "source '$REPO/scripts/agent_prelude.sh' claim-verifier; printf '%s' \"\$RESOLVED_PROFILE_ID\"" 2>&1
)" || true
PRELUDE_OK="$(
  CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
  bash -c "source '$REPO/scripts/agent_prelude.sh' claim-verifier; printf '%s' \"\$RESOLVED_OK\"" 2>&1
)" || true
if [[ "$PRELUDE_ID" == "perspective" && "$PRELUDE_OK" == "1" ]]; then ok
else ko "RESOLVED_PROFILE_ID='$PRELUDE_ID' RESOLVED_OK='$PRELUDE_OK'"; fi

# ---------------------------------------------------------------------------
# Steps 3–7: agent_should_run for all 5 cycle-#8 revising agents (regression)
# ---------------------------------------------------------------------------
step 3 "reviser-full should_run for perspective (cycle-08 regression)"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
    bash "$REPO/scripts/agent_should_run.sh" reviser-full 2>/dev/null; then ok; else ko; fi

step 4 "reviser-fast should_run for perspective (cycle-08 regression)"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
    bash "$REPO/scripts/agent_should_run.sh" reviser-fast 2>/dev/null; then ok; else ko; fi

step 5 "humanizer should_run for perspective (cycle-08 regression)"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
    bash "$REPO/scripts/agent_should_run.sh" humanizer 2>/dev/null; then ok; else ko; fi

step 6 "style-enforcer should_run for perspective (cycle-08 regression)"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
    bash "$REPO/scripts/agent_should_run.sh" style-enforcer 2>/dev/null; then ok; else ko; fi

step 7 "consistency-checker should_run for perspective (cycle-08 regression)"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
    bash "$REPO/scripts/agent_should_run.sh" consistency-checker 2>/dev/null; then ok; else ko; fi

# ---------------------------------------------------------------------------
# Step 8: cycle-09 review agents should_run for perspective
# ---------------------------------------------------------------------------
step 8 "claim-verifier + bibliography-fidelity-checker + peer-reviewer should_run for perspective"
CV_OK=0; BF_OK=0; PR_OK=0
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
    bash "$REPO/scripts/agent_should_run.sh" claim-verifier 2>/dev/null && CV_OK=1 || true
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
    bash "$REPO/scripts/agent_should_run.sh" bibliography-fidelity-checker 2>/dev/null && BF_OK=1 || true
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$V1" \
    bash "$REPO/scripts/agent_should_run.sh" peer-reviewer 2>/dev/null && PR_OK=1 || true
if [[ "$CV_OK" -eq 1 && "$BF_OK" -eq 1 && "$PR_OK" -eq 1 ]]; then ok
else ko "claim-verifier=$CV_OK bibliography-fidelity-checker=$BF_OK peer-reviewer=$PR_OK"; fi

# ---------------------------------------------------------------------------
# Step 9: sws_claim_extract.py on variant_1 → claims.json with ≥1 claim
# ---------------------------------------------------------------------------
step 9 "sws_claim_extract.py produces claims.json with >=1 claim"
mkdir -p "$V1/_review/claim-verifier"
CLAIMS_JSON="$V1/_review/claim-verifier/claims.json"
"$REPO/scripts/sws_python.sh" "$V1" \
    "$REPO/scripts/sws_claim_extract.py" \
    "$V1/_drafts" \
    --out "$CLAIMS_JSON" >/dev/null 2>&1 || true

if [[ -f "$CLAIMS_JSON" ]]; then
    CLAIM_COUNT="$(python3 -c "import json; d=json.load(open('$CLAIMS_JSON')); print(len(d))" 2>/dev/null)" || CLAIM_COUNT=0
    if [[ "$CLAIM_COUNT" -ge 1 ]]; then ok
    else ko "claims.json exists but contains 0 claims"; fi
else
    ko "claims.json not produced at $CLAIMS_JSON"
fi

# ---------------------------------------------------------------------------
# Step 10: fidelity-checker on variant_1 (D9c — no zotero) via harness
# ---------------------------------------------------------------------------
step 10 "fidelity-checker on variant_1 (D9c): status.json ran=false, skip_reason=no-zotero-installation-detected"
mkdir -p "$V1/_review/bibliography-fidelity-checker"
if python3 "$HARNESS" variant_1 "$V1" >/dev/null 2>&1; then
    ok
else
    # Re-run without redirect to capture error
    HARNESS_OUT="$(python3 "$HARNESS" variant_1 "$V1" 2>&1)" || true
    ko "harness variant_1 failed: ${HARNESS_OUT:0:200}"
fi

# ---------------------------------------------------------------------------
# Step 11: fidelity-checker on variant_2 (D9a — zotero desktop only) via harness
#           Asserts D9a verbatim recommendation string
# ---------------------------------------------------------------------------
step 11 "fidelity-checker on variant_2 (D9a): actionable recommendation + verbatim string"
mkdir -p "$V2/_review/bibliography-fidelity-checker"
SQLITE_PATH="$V2/Zotero/zotero.sqlite"
HARNESS_OUT_V2="$(python3 "$HARNESS" variant_2 "$V2" "$SQLITE_PATH" 2>&1)" || true
HARNESS_RC_V2=$?

if [[ "$HARNESS_RC_V2" -ne 0 ]]; then
    ko "harness variant_2 failed: ${HARNESS_OUT_V2:0:200}"
else
    # Also assert the verbatim D9a string in the report.md directly (spec D15 requirement)
    REPORT_V2="$V2/_review/bibliography-fidelity-checker/report.md"
    if grep -q "we recommend installing the zotero plugin in Claude Code" "$REPORT_V2" 2>/dev/null; then
        ok
    else
        ko "D9a verbatim string not found in report.md"
    fi
fi

# ---------------------------------------------------------------------------
# Step 12: fidelity-checker on variant_3 (D9b — skill present + library < 10) via harness
# ---------------------------------------------------------------------------
step 12 "fidelity-checker on variant_3 (D9b): ran=false, skip_reason=zotero-library-too-small"
mkdir -p "$V3/_review/bibliography-fidelity-checker"
if python3 "$HARNESS" variant_3 "$V3" >/dev/null 2>&1; then
    ok
else
    HARNESS_OUT="$(python3 "$HARNESS" variant_3 "$V3" 2>&1)" || true
    ko "harness variant_3 failed: ${HARNESS_OUT:0:200}"
fi

# ---------------------------------------------------------------------------
# Step 13: fidelity-checker on variant_4 (D9 happy — seeded violation) via harness
# ---------------------------------------------------------------------------
step 13 "fidelity-checker on variant_4 (D9 happy): ran=true, >=1 flag, V0.1 LIMITATION in report"
mkdir -p "$V4/_review/bibliography-fidelity-checker"
INDEX_JSON="$V4/mock_zotero_index.json"
if python3 "$HARNESS" variant_4 "$V4" "$INDEX_JSON" >/dev/null 2>&1; then
    FLAGS_JSON="$V4/_review/bibliography-fidelity-checker/flags.json"
    FLAG_COUNT="$(python3 -c "import json; print(len(json.load(open('$FLAGS_JSON'))))" 2>/dev/null)" || FLAG_COUNT=0
    if [[ "$FLAG_COUNT" -ge 1 ]]; then ok
    else ko "flags.json has 0 flags (expected >=1)"; fi
else
    HARNESS_OUT="$(python3 "$HARNESS" variant_4 "$V4" "$INDEX_JSON" 2>&1)" || true
    ko "harness variant_4 failed: ${HARNESS_OUT:0:200}"
fi

# ---------------------------------------------------------------------------
# Step 14: peer-reviewer agent file exists; _review/peer-reviewer/ is creatable
# ---------------------------------------------------------------------------
step 14 "peer-reviewer agent file exists + _review/peer-reviewer/ is creatable"
PEER_REVIEWER_AGENT="$REPO/agents/peer-reviewer.md"
if [[ -f "$PEER_REVIEWER_AGENT" ]]; then
    mkdir -p "$V1/_review/peer-reviewer"
    if [[ -d "$V1/_review/peer-reviewer" ]]; then ok
    else ko "_review/peer-reviewer/ not creatable"; fi
else
    ko "agents/peer-reviewer.md not found"
fi

# ---------------------------------------------------------------------------
# Step 15: orchestrator skill references all three atomic skills
# ---------------------------------------------------------------------------
step 15 "review-paper/SKILL.md references /sws:verify-claims, /sws:check-fidelity, /sws:peer-review"
ORCHESTRATOR="$REPO/skills/review-paper/SKILL.md"
if [[ -f "$ORCHESTRATOR" ]]; then
    VC=$(grep -c "verify-claims\|sws:verify" "$ORCHESTRATOR" 2>/dev/null) || VC=0
    CF=$(grep -c "check-fidelity\|sws:check" "$ORCHESTRATOR" 2>/dev/null) || CF=0
    PR=$(grep -c "peer-review\|sws:peer" "$ORCHESTRATOR" 2>/dev/null) || PR=0
    if [[ "$VC" -ge 1 && "$CF" -ge 1 && "$PR" -ge 1 ]]; then ok
    else ko "verify-claims=$VC check-fidelity=$CF peer-review=$PR (all must be >=1)"; fi
else
    ko "skills/review-paper/SKILL.md not found"
fi

# ---------------------------------------------------------------------------
# Step 16: sws_claim_extract.py has no NLM/notebooklm import dependencies
# ---------------------------------------------------------------------------
step 16 "sws_claim_extract.py imports without NLM/notebooklm errors"
IMPORT_ERR="$(python3 -c "
import sys; sys.path.insert(0, '$REPO/scripts')
import sws_claim_extract
print('import OK')
" 2>&1)" || true
if echo "$IMPORT_ERR" | grep -q "import OK"; then
    # Confirm no NLM-related import errors
    if echo "$IMPORT_ERR" | grep -qi "notebooklm\|nlm.*error\|ImportError"; then
        ko "unexpected NLM/notebooklm error: ${IMPORT_ERR:0:200}"
    else
        ok
    fi
else
    ko "sws_claim_extract import failed: ${IMPORT_ERR:0:200}"
fi

# ---------------------------------------------------------------------------
# Step 17: profile activation — claim-verifier + bibliography-fidelity-checker
#           exit non-0 for funding-proposal (gated off per D10)
# ---------------------------------------------------------------------------
step 17 "profile gate: claim-verifier + bibliography-fidelity-checker inactive in funding-proposal"
FP="$TMP/funding_proposal_fixture"
cp -r "$V1" "$FP"
cat > "$FP/.sws-project.local.md" <<'FPMARKER'
---
profile: funding-proposal
language: en
format: docx
---
FPMARKER

CV_FP_RC=0
BF_FP_RC=0
PR_FP_RC=0
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FP" \
    bash "$REPO/scripts/agent_should_run.sh" claim-verifier 2>/dev/null || CV_FP_RC=$?
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FP" \
    bash "$REPO/scripts/agent_should_run.sh" bibliography-fidelity-checker 2>/dev/null || BF_FP_RC=$?
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FP" \
    bash "$REPO/scripts/agent_should_run.sh" peer-reviewer 2>/dev/null || PR_FP_RC=$?

# claim-verifier and bibliography-fidelity-checker must be non-0; peer-reviewer must be 0
if [[ "$CV_FP_RC" -ne 0 && "$BF_FP_RC" -ne 0 && "$PR_FP_RC" -eq 0 ]]; then ok
else ko "claim-verifier_rc=$CV_FP_RC bibliography-fidelity-checker_rc=$BF_FP_RC peer-reviewer_rc=$PR_FP_RC (expected non-0, non-0, 0)"; fi

# ---------------------------------------------------------------------------
# Step 18: README banner + plugin.json version
# ---------------------------------------------------------------------------
step 18 "README.md contains '🧪 v0.1 alpha' and plugin.json has version 0.1.0-alpha"
README="$REPO/README.md"
PLUGIN_JSON="$REPO/.claude-plugin/plugin.json"
README_OK=0
PLUGIN_OK=0
if grep -q "🧪.*v0.1 alpha\|v0.1 alpha.*🧪" "$README" 2>/dev/null; then README_OK=1; fi
if grep -q "\"version\": \"0.1.0-alpha\"" "$PLUGIN_JSON" 2>/dev/null; then PLUGIN_OK=1; fi
if [[ "$README_OK" -eq 1 && "$PLUGIN_OK" -eq 1 ]]; then ok
else ko "README_OK=$README_OK PLUGIN_OK=$PLUGIN_OK"; fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf "\nsmoke_cycle_09: %d passed, %d failed\n" "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]] || exit 1
