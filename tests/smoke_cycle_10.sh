#!/usr/bin/env bash
# smoke_cycle_10.sh — e2e for cycle #10 (style calibration).
#
# Deterministic: the Haiku voice-similarity call is STUBBED via SWS_HAIKU_STUB.
# Exercises the full sws_stylometry.py pipeline against the synthetic fixture
# corpus (3 author + 2 field + 1 heldout) and asserts the calibrator wiring.
#
# Step  1: fixtures present
# Step  2: --vector emits the 17-key feature vector
# Step  3: --fit-weights emits weights + w_h summing to 1
# Step  4: --self-band emits a band on the author vectors
# Step  5: --distance heldout-vs-author + --rbf similarity in [0,1]
# Step  6: keep-best monotonicity (held-out improves toward the band)
# Step  7: a written profile.md passes the schema validator
# Step  8: prelude exports VOICE_PROFILE when _voice/profile.md present
# Step  9: style-calibrator agent + calibrate-style skill files exist + parse
# Step 10: D14 — calibrator inactive in editorial via agent_should_run
#
# Expected summary: 10 passed, 0 failed
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
FX="$REPO/tests/fixtures/cycle_10"
PYBIN="${SWS_SMOKE_PYTHON:-python3}"

TMP="$(mktemp -d)"
trap "rm -rf '$TMP'" EXIT

PASS=0
FAIL=0
step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  OK\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

# ---------------------------------------------------------------------------
# Step 1: fixtures present
# ---------------------------------------------------------------------------
step 1 "synthetic fixture corpus present (3 author + 2 field + 1 heldout)"
ALL=1
for f in author_1 author_2 author_3 field_1 field_2 heldout_1; do
    [[ -f "$FX/$f.txt" ]] || ALL=0
done
if [[ "$ALL" -eq 1 ]]; then ok; else ko "missing fixture file"; fi

# ---------------------------------------------------------------------------
# Step 2: --vector emits the 17-key feature vector
# ---------------------------------------------------------------------------
step 2 "--vector emits 17-key feature JSON"
VEC="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --vector "$(cat "$FX/author_1.txt")")"
NKEYS="$(printf '%s' "$VEC" | "$PYBIN" -c 'import json,sys; print(len(json.load(sys.stdin)))')"
if [[ "$NKEYS" -eq 17 ]]; then ok; else ko "expected 17 keys, got $NKEYS"; fi

# ---------------------------------------------------------------------------
# Step 3: --fit-weights -> weights + w_h sum to 1
# ---------------------------------------------------------------------------
step 3 "--fit-weights emits normalized weights (sum + w_h == 1)"
"$PYBIN" - "$FX" "$TMP" <<'PY'
import sys, json, itertools, pathlib
sys.path.insert(0, "scripts")
import sws_stylometry as sm  # noqa
fx, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
author = [sm.feature_vector((fx / f"author_{i}.txt").read_text()) for i in (1,2,3)]
field = [sm.feature_vector((fx / f"field_{i}.txt").read_text()) for i in (1,2)]
pos = list(itertools.combinations(author, 2))
neg = [[a, f] for a in author for f in field]
(tmp / "pos.json").write_text(json.dumps([[a,b] for a,b in pos]))
(tmp / "neg.json").write_text(json.dumps(neg))
PY
WJSON="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --fit-weights "$TMP/pos.json" "$TMP/neg.json" --lam 0.3 --pos-haiku 0.9,0.9,0.9 --neg-haiku 0.2,0.2,0.2,0.2,0.2,0.2)"
printf '%s' "$WJSON" > "$TMP/weights.json"
SUM_OK="$(printf '%s' "$WJSON" | "$PYBIN" -c 'import json,sys; d=json.load(sys.stdin); print("1" if abs(sum(d["weights"].values())+d["w_h"]-1.0)<1e-6 else "0")')"
if [[ "$SUM_OK" == "1" ]]; then ok; else ko "weights+w_h do not sum to 1"; fi

# ---------------------------------------------------------------------------
# Step 4: --self-band on author vectors
# ---------------------------------------------------------------------------
step 4 "--self-band emits band_lo<=band_mean<=band_hi in [0,1]"
"$PYBIN" - "$FX" "$TMP" <<'PY'
import sys, json, pathlib
sys.path.insert(0, "scripts")
import sws_stylometry as sm  # noqa
fx, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
author = [sm.feature_vector((fx / f"author_{i}.txt").read_text()) for i in (1,2,3)]
(tmp / "author_vecs.json").write_text(json.dumps(author))
PY
BAND="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --self-band "$TMP/author_vecs.json" --weights "$TMP/weights.json")"
BAND_OK="$(printf '%s' "$BAND" | "$PYBIN" -c 'import json,sys; b=json.load(sys.stdin); print("1" if 0.0<=b["band_lo"]<=b["band_mean"]<=b["band_hi"]<=1.0001 else "0")')"
if [[ "$BAND_OK" == "1" ]]; then ok; else ko "band invariants violated: $BAND"; fi

# ---------------------------------------------------------------------------
# Step 5: --distance heldout-vs-author then --rbf similarity in [0,1]
# ---------------------------------------------------------------------------
step 5 "--distance + --rbf produce a similarity in [0,1] (Haiku stubbed)"
HAIKU_SIM="${SWS_HAIKU_STUB:-0.8}"
"$PYBIN" "$REPO/scripts/sws_stylometry.py" --vector "$(cat "$FX/heldout_1.txt")" > "$TMP/heldout.json"
"$PYBIN" "$REPO/scripts/sws_stylometry.py" --vector "$(cat "$FX/author_1.txt")" > "$TMP/a1.json"
DJSON="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --distance "$TMP/heldout.json" "$TMP/a1.json" --weights "$TMP/weights.json" --haiku-sim "$HAIKU_SIM")"
DVAL="$(printf '%s' "$DJSON" | "$PYBIN" -c 'import json,sys; print(json.load(sys.stdin)["distance"])')"
SIM="$("$PYBIN" "$REPO/scripts/sws_stylometry.py" --rbf "$DVAL" --gamma 0.5)"
SIM_OK="$(printf '%s' "$SIM" | "$PYBIN" -c 'import json,sys; s=json.load(sys.stdin)["similarity"]; print("1" if 0.0<=s<=1.0 else "0")')"
if [[ "$SIM_OK" == "1" ]]; then ok; else ko "rbf similarity out of [0,1]: $SIM"; fi

# ---------------------------------------------------------------------------
# Step 6: keep-best monotonicity
# ---------------------------------------------------------------------------
step 6 "keep_best produces a monotone non-decreasing trajectory"
MONO="$("$PYBIN" -c '
import sys; sys.path.insert(0, "scripts")
import sws_stylometry as sm
seq = sm.keep_best([(1,0.40),(2,0.55),(3,0.50),(4,0.62)])
print("1" if seq == sorted(seq) and seq[-1]==0.62 else "0")
')"
if [[ "$MONO" == "1" ]]; then ok; else ko "keep_best not monotone"; fi

# ---------------------------------------------------------------------------
# Step 7: a written profile.md passes the schema validator
# ---------------------------------------------------------------------------
step 7 "synthetic profile.md passes the voice-profile schema validator"
mkdir -p "$TMP/_voice"
cat > "$TMP/_voice/profile.md" <<'PROF'
---
sws_artifact: voice-profile
artifact_version: 0.1
calibrated: 2026-05-23
recent_weighted: true
feature_targets:
  sentence_len_mean: { target: 8.0, band: [6.0, 11.0] }
  hedge_density: { target: 0.0, band: [0.0, 1.5] }
convergence:
  self_band: [0.74, 0.91]
  gamma: 0.42
sections: [global, introduction, results, discussion]
---

# Voice profile

## Global voice
Short declarative sentences, frequent first-person plural, minimal hedging.

## Section deltas

### Introduction
Opens with the gap, then the aim.

### Results
Headline finding first, then the data.

### Discussion
Interpretive, slightly longer sentences.
PROF
SCHEMA_OK="$("$PYBIN" - "$TMP/_voice/profile.md" <<'PY'
import sys, yaml, pathlib
sys.path.insert(0, "tests")
from test_voice_profile_schema import validate_profile
try:
    validate_profile(pathlib.Path(sys.argv[1]).read_text())
    print("1")
except Exception as e:
    print("0", e)
PY
)"
if [[ "$SCHEMA_OK" == "1" ]]; then ok; else ko "profile.md schema fail: $SCHEMA_OK"; fi

# ---------------------------------------------------------------------------
# Step 8: prelude exports VOICE_PROFILE when _voice/profile.md present
# ---------------------------------------------------------------------------
step 8 "agent_prelude.sh exports VOICE_PROFILE path when profile.md present"
mkdir -p "$TMP/.venv/bin"
if "$PYBIN" -c "import yaml, docx, openpyxl" 2>/dev/null; then
    ln -sf "$(command -v "$PYBIN")" "$TMP/.venv/bin/python"
elif [[ -n "${SWS_SMOKE_PYTHON:-}" && -x "${SWS_SMOKE_PYTHON}" ]]; then
    ln -sf "${SWS_SMOKE_PYTHON}" "$TMP/.venv/bin/python"
else
    echo "FAIL: no python with PyYAML found (set SWS_SMOKE_PYTHON)" >&2
    exit 1
fi
cat > "$TMP/.sws-project.local.md" <<'M'
---
profile: perspective
language: en
format: docx
---
M
VP="$(CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$TMP" bash -c "source '$REPO/scripts/agent_prelude.sh' drafter-fast; printf '%s' \"\$VOICE_PROFILE\"" 2>/dev/null)"
if [[ "$VP" == "$TMP/_voice/profile.md" ]]; then ok; else ko "VOICE_PROFILE=[$VP]"; fi

# ---------------------------------------------------------------------------
# Step 9: agent + skill files exist and parse
# ---------------------------------------------------------------------------
step 9 "style-calibrator agent + calibrate-style skill exist with valid frontmatter"
GOOD="$("$PYBIN" - "$REPO" <<'PY'
import sys, yaml, pathlib
repo = pathlib.Path(sys.argv[1])
ag = (repo / "agents/style-calibrator.md").read_text()
sk = (repo / "skills/calibrate-style/SKILL.md").read_text()
agfm = yaml.safe_load(ag.split("---", 2)[1])
skfm = yaml.safe_load(sk.split("---", 2)[1])
print("1" if agfm["name"]=="style-calibrator" and skfm["name"]=="calibrate-style" else "0")
PY
)"
if [[ "$GOOD" == "1" ]]; then ok; else ko "agent/skill frontmatter mismatch"; fi

# ---------------------------------------------------------------------------
# Step 10: D14 — calibrator inactive in editorial
# ---------------------------------------------------------------------------
step 10 "agent_should_run: style-calibrator inactive for editorial, active for perspective"
ED="$(mktemp -d)"
trap "rm -rf '$TMP' '$ED'" EXIT
mkdir -p "$ED/.venv/bin"
ln -sf "$(readlink -f "$TMP/.venv/bin/python" 2>/dev/null || echo "$TMP/.venv/bin/python")" "$ED/.venv/bin/python"
cat > "$ED/.sws-project.local.md" <<'M'
---
profile: editorial
language: en
format: docx
---
M
ED_RC=0
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$ED" \
    bash "$REPO/scripts/agent_should_run.sh" style-calibrator 2>/dev/null || ED_RC=$?
PE_RC=0
CLAUDE_PLUGIN_ROOT="$REPO" PAPER_ROOT="$TMP" \
    bash "$REPO/scripts/agent_should_run.sh" style-calibrator 2>/dev/null || PE_RC=$?
if [[ "$ED_RC" -ne 0 && "$PE_RC" -eq 0 ]]; then ok
else ko "editorial_rc=$ED_RC perspective_rc=$PE_RC (expected non-0, 0)"; fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf "\nsmoke_cycle_10: %d passed, %d failed\n" "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]] || exit 1
