#!/usr/bin/env bash
# Cycle-#7 end-to-end smoke. Exercises:
#   1. fixture marker has profile: perspective
#   2. agent_prelude resolves correctly for outline-architect
#   3. /sws:prepare-lit-context (manifest export from canned zotero collection)
#   4. outline-architect should_run for perspective
#   4b. outline baseline sidecar written for a stub outline
#   5. drafter-flagship should_run for perspective
#   5b. section router maps 'intro' → drafter-flagship for perspective
#   6. switch fixture to funding-proposal profile
#   7. call PDF dropped into Manuscript/call/
#   8. proposal-budget-helper should_run for funding-proposal
#   9. proposal-compliance-helper should_run for funding-proposal
#   9b. methods-writer is BLOCKED for funding-proposal (D8)
#  10. switch back to perspective + caption-writer always-active invariant
#  11. ai-writing-tells.md catalog has 40-60 patterns
#
# The smoke copies the gitignored-marker fixture to a tmpdir (so .sws-project
# .local.md and .venv/ can be created on the fly), then runs the underlying
# python helpers directly. Skill-level UI is exercised via the model in
# regular use; the smoke exercises the machinery the skills shell out to.
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC_FIXTURE="$REPO/tests/fixtures/cycle_07_paper"
TMP="$(mktemp -d)"
trap "rm -rf $TMP" EXIT
FIXTURE="$TMP/cycle_07_paper"

# Bootstrap: copy committed fixture skeleton, then generate the marker +
# venv that are gitignored. The cp -r picks up any local-only marker /
# venv that exist on the developer's machine; remove them to start clean.
cp -r "$SRC_FIXTURE" "$FIXTURE"
rm -rf "$FIXTURE/.venv" "$FIXTURE/.sws-project.local.md"
mkdir -p "$FIXTURE/.venv/bin"
# Resolve a python interpreter that has PyYAML (the resolver needs it).
if python3 -c "import yaml" 2>/dev/null; then
    ln -s "$(command -v python3)" "$FIXTURE/.venv/bin/python"
elif [[ -n "${SWS_SMOKE_PYTHON:-}" && -x "${SWS_SMOKE_PYTHON}" ]]; then
    ln -s "${SWS_SMOKE_PYTHON}" "$FIXTURE/.venv/bin/python"
else
    echo "FAIL: no python with PyYAML found for smoke (system python3 needs pyyaml installed, or set SWS_SMOKE_PYTHON to a python that has it)" >&2
    exit 1
fi
cat > "$FIXTURE/.sws-project.local.md" <<EOF
---
profile: perspective
language: en
format: docx
---
EOF

PASS=0
FAIL=0
step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  PASS\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

# Step 1: fixture marker has profile: perspective
step 1 "fixture marker has profile: perspective"
if grep -q "profile: perspective" "$FIXTURE/.sws-project.local.md"; then ok; else ko; fi

# Step 2: agent_prelude resolves for outline-architect
step 2 "agent_prelude resolves for outline-architect (RESOLVED_PROFILE_ID=perspective)"
PRELUDE_OUT="$(
  CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
  bash -c "source '$REPO/scripts/agent_prelude.sh' outline-architect; printf '%s' \"\$RESOLVED_PROFILE_ID\"" 2>&1
)" || true
if [[ "$PRELUDE_OUT" == "perspective" ]]; then ok; else ko "got '$PRELUDE_OUT'"; fi

# Step 3: zotero manifest export from canned collection
step 3 "/sws:prepare-lit-context (manifest export)"
"$REPO/scripts/sws_python.sh" "$FIXTURE" \
    "$REPO/scripts/sws_extract_zotero_manifest.py" \
    --input "$REPO/tests/fixtures/zotero_collections/perspective_collection.json" \
    --paper "$FIXTURE" >/dev/null 2>&1 || true
if [[ -f "$FIXTURE/_lit/zotero-manifest.md" ]]; then ok; else ko "manifest not written"; fi

# Step 4: outline-architect should_run for perspective
step 4 "outline-architect should_run for perspective"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" outline-architect; then ok; else ko; fi

# Step 4b: outline baseline sidecar written for stub outline
step 4b "outline baseline sidecar written for stub outline"
mkdir -p "$FIXTURE/_outline"
cat > "$FIXTURE/_outline/outline.md" <<'EOF'
---
profile: perspective
sections:
  intro: { word_target: 800, status: planned, key_claims: ["test claim"], figs: [], cites: ["Smith2023; doi:10.xxxx"] }
figures:
  f1: { caption: "", file: "figures/Fig1.png", supports: "Body" }
---
# Outline
## Intro
arc.
EOF
"$REPO/scripts/sws_python.sh" "$FIXTURE" \
    "$REPO/scripts/sws_outline_baseline.py" write \
    "$FIXTURE/_outline/outline.md" >/dev/null 2>&1 || true
if [[ -f "$FIXTURE/_outline/.outline-baseline.sha256" ]]; then ok; else ko "sidecar not written"; fi

# Step 5: drafter-flagship should_run for perspective
step 5 "drafter-flagship should_run for perspective"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" drafter-flagship; then ok; else ko; fi

# Step 5b: section router maps 'intro' → drafter-flagship for perspective
step 5b "section router maps 'intro' → drafter-flagship for perspective"
RESULT="$(
  PYTHONPATH="$REPO/scripts" "$REPO/scripts/sws_python.sh" "$FIXTURE" -c \
      "from sws_section_router import route_section; print(route_section('intro', 'perspective'))" 2>/dev/null
)" || RESULT="<error>"
if [[ "$RESULT" == "drafter-flagship" ]]; then ok; else ko "got '$RESULT'"; fi

# Step 6: switch fixture to funding-proposal
step 6 "switch fixture to funding-proposal profile"
sed -i.bak 's/profile: perspective/profile: funding-proposal/' "$FIXTURE/.sws-project.local.md"
rm -f "$FIXTURE/.sws-project.local.md.bak"
if grep -q "profile: funding-proposal" "$FIXTURE/.sws-project.local.md"; then ok; else ko; fi

# Step 7: drop call PDF into Manuscript/call/ and verify availability
step 7 "call PDF available for resolve-call-rules"
cp "$REPO/tests/fixtures/calls/test_prin_call.pdf" "$FIXTURE/Manuscript/call/" 2>/dev/null || true
if [[ -f "$FIXTURE/Manuscript/call/test_prin_call.pdf" ]]; then ok; else ko; fi

# Step 8: proposal-budget-helper should_run for funding-proposal
step 8 "proposal-budget-helper should_run for funding-proposal"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" proposal-budget-helper; then ok; else ko; fi

# Step 9: proposal-compliance-helper should_run for funding-proposal
step 9 "proposal-compliance-helper should_run for funding-proposal"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" proposal-compliance-helper; then ok; else ko; fi

# Step 9b: methods-writer is BLOCKED for funding-proposal (D8)
step 9b "methods-writer BLOCKED for funding-proposal (D8 rationale-not-procedural)"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" methods-writer 2>/dev/null; then
    ko "methods-writer should be inactive"
else
    ok
fi

# Step 10: switch back to perspective for caption-writer invariant check
step 10 "switch back to perspective + caption-writer should_run (invariant active)"
sed -i.bak 's/profile: funding-proposal/profile: perspective/' "$FIXTURE/.sws-project.local.md"
rm -f "$FIXTURE/.sws-project.local.md.bak"
if CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$FIXTURE" \
    bash "$REPO/scripts/agent_should_run.sh" caption-writer; then ok; else ko; fi

# Step 11: ai-writing-tells.md catalog has 40-60 patterns
step 11 "ai-writing-tells.md has 40-60 patterns"
COUNT=$(grep -c '^- pattern:' "$REPO/references/ai-writing-tells.md" 2>/dev/null || echo 0)
if [[ "$COUNT" -ge 40 && "$COUNT" -le 60 ]]; then ok; else ko "found $COUNT patterns"; fi

printf "\n=== Smoke summary: %d passed, %d failed ===\n" "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]] || exit 1
