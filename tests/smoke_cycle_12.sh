#!/usr/bin/env bash
# smoke_cycle_12.sh — 12-step e2e for cycle #12 (Submission orchestration).
#
# Steps 1-3:   bootstrap from fixture; venv-stub; marker
# Step  4:     sws_response_matrix.py happy path (shape a, 2 reviewers x 3)
# Step  5:     sws_response_matrix.py idempotent re-parse preserves filled fields
# Step  6:     sws_disclosure_writer.py writes the wiley-template body
# Step  7:     sws_review_round.py find returns 1
# Step  8:     sws_review_round.py inventory 1 reports comments+matrix present
# Step  9:     sws_section_router.py submit cover-letter routes correctly
# Step 10:     sws_run_cycle.py --dry-run prints plan with should_run flags
# Step 11:     sws_run_cycle.py --only=disclosure dispatches disclosure step only
# Step 12:     Captured-fixture cover-letter passes the AI-tells linter
#
# All dispatches use deterministic scripts. No live LLM calls.
# Per D20 the cover-letter agent dispatch is exercised by manual testing only.
#
# Expected summary: 12 passed, 0 failed
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$REPO/scripts"
FIXTURES="$REPO/tests/fixtures/sample-cycle-12"

TMP="$(mktemp -d)"
trap "rm -rf '$TMP'" EXIT

PASS=0
FAIL=0
step() { printf "\n--- Step %s: %s ---\n" "$1" "$2"; }
ok()   { PASS=$((PASS+1)); printf "  OK\n"; }
ko()   { FAIL=$((FAIL+1)); printf "  FAIL: %s\n" "${1:-}"; }

# Resolve python with yaml.
if python3 -c "import yaml" 2>/dev/null; then
    PY="$(command -v python3)"
elif [[ -n "${SWS_SMOKE_PYTHON:-}" && -x "${SWS_SMOKE_PYTHON}" ]]; then
    PY="$SWS_SMOKE_PYTHON"
else
    echo "FAIL: no python with yaml (set SWS_SMOKE_PYTHON)" >&2
    exit 1
fi

PAPER="$TMP/paper"
mkdir -p "$PAPER"
cp -R "$FIXTURES"/. "$PAPER"/

# The marker file `.sws-project.local.md` is gitignored repo-wide; write it
# inline here (same pattern as cycle_11 smoke).
cat > "$PAPER/.sws-project.local.md" <<'MARKER'
---
sws_version: 0.1
article_type: full-article
language: en
format: docx
target_journal: chembiochem
target_call: null
notebooklm:
  enabled: false
created: 2026-05-30T00:00:00Z
---

# sample-cycle-12 (inline marker; fixture .sws-project.local.md is gitignored)
MARKER

# Make .venv/bin/python symlink so sws_python.sh can resolve.
mkdir -p "$PAPER/.venv/bin"
ln -s "$PY" "$PAPER/.venv/bin/python"

# ---------------------------------------------------------------------------
# Step 1: marker is in place
# ---------------------------------------------------------------------------
step 1 "fixture marker copied"
if [[ -f "$PAPER/.sws-project.local.md" ]]; then ok; else ko "marker missing"; fi

# ---------------------------------------------------------------------------
# Step 2: drafts copied
# ---------------------------------------------------------------------------
step 2 "fixture drafts copied"
count="$(ls "$PAPER"/_drafts/*.md 2>/dev/null | wc -l | tr -d ' ')"
if [[ "$count" == "4" ]]; then ok; else ko "expected 4 drafts, found $count"; fi

# ---------------------------------------------------------------------------
# Step 3: review reports + reviewer-comments copied
# ---------------------------------------------------------------------------
step 3 "fixture review reports copied"
if [[ -f "$PAPER/_review/peer-reviewer/report.md" \
   && -f "$PAPER/_review/claim-verifier/report.md" \
   && -f "$PAPER/_review/bibliography-fidelity-checker/report.md" \
   && -f "$PAPER/_review/round-1/reviewer-comments.md" ]]; then
    ok
else
    ko "review reports missing"
fi

# ---------------------------------------------------------------------------
# Step 4: response-matrix parser happy path (shape a)
# ---------------------------------------------------------------------------
step 4 "sws_response_matrix.py parses shape-a reviewer-comments"
"$PY" "$SCRIPTS/sws_response_matrix.py" \
    "$PAPER/_review/round-1/reviewer-comments.md" >/dev/null
MATRIX="$PAPER/_review/round-1/response-matrix.json"
if [[ -f "$MATRIX" ]] && \
   "$PY" -c "import json,sys; d=json.load(open('$MATRIX')); sys.exit(0 if len(d)==6 and any(c['id']=='R1.1' for c in d) else 1)"
then
    ok
else
    ko "matrix.json malformed or wrong count"
fi

# ---------------------------------------------------------------------------
# Step 5: idempotent re-parse preserves filled fields
# ---------------------------------------------------------------------------
step 5 "sws_response_matrix.py preserves response_text on re-parse (R3)"
"$PY" - <<PYEOF
import json
m = json.load(open("$MATRIX"))
for c in m:
    if c["id"] == "R1.1":
        c["status"] = "accepted"
        c["response_text"] = "We softened the abstract phrasing per the reviewer's note."
open("$MATRIX", "w").write(json.dumps(m, indent=2))
PYEOF
"$PY" "$SCRIPTS/sws_response_matrix.py" \
    "$PAPER/_review/round-1/reviewer-comments.md" >/dev/null
if "$PY" -c "
import json
m = json.load(open('$MATRIX'))
r11 = next(c for c in m if c['id']=='R1.1')
assert r11['status'] == 'accepted', r11
assert 'softened' in r11['response_text'], r11
"; then ok; else ko "R1.1 fields lost on re-parse"; fi

# ---------------------------------------------------------------------------
# Step 6: disclosure writer renders wiley template
# ---------------------------------------------------------------------------
step 6 "sws_disclosure_writer.py renders wiley template"
RESOLVED_DISCLOSURE_REQUIRED=true "$PY" "$SCRIPTS/sws_disclosure_writer.py" \
    --paper-root "$PAPER" 2>/dev/null
DISC="$PAPER/_submission/ai-disclosure.md"
if [[ -f "$DISC" ]] && grep -q "Wiley" "$DISC"; then
    ok
else
    ko "disclosure not written or wrong template"
fi

# ---------------------------------------------------------------------------
# Step 7: review-round find returns 1
# ---------------------------------------------------------------------------
step 7 "sws_review_round.py find returns 1"
N="$("$PY" "$SCRIPTS/sws_review_round.py" --paper-root "$PAPER" find)"
if [[ "$N" == "1" ]]; then ok; else ko "expected 1, got $N"; fi

# ---------------------------------------------------------------------------
# Step 8: review-round inventory 1 reports comments+matrix present
# ---------------------------------------------------------------------------
step 8 "sws_review_round.py inventory reports comments+matrix present"
INV="$("$PY" "$SCRIPTS/sws_review_round.py" --paper-root "$PAPER" inventory 1)"
if echo "$INV" | grep -q "comments: present" \
   && echo "$INV" | grep -q "matrix: present" \
   && echo "$INV" | grep -q "response: absent"; then
    ok
else
    ko "inventory output unexpected: $INV"
fi

# ---------------------------------------------------------------------------
# Step 9: section-router 'submit' axis routes cover-letter
# ---------------------------------------------------------------------------
step 9 "sws_section_router.route_section('cover-letter','full-article','submit')"
ROUTE="$("$PY" -c "
import sys
sys.path.insert(0, '$SCRIPTS')
from sws_section_router import route_section
print(route_section('cover-letter', 'full-article', action='submit'))
")"
if [[ "$ROUTE" == "skill:/sws:write-cover-letter" ]]; then ok; else ko "route was $ROUTE"; fi

# ---------------------------------------------------------------------------
# Step 10: sws_run_cycle.py --dry-run --json emits plan
# ---------------------------------------------------------------------------
step 10 "sws_run_cycle.py --dry-run --json emits all 7 steps"
PLAN="$(RESOLVED_COVER_LETTER_REQUIRED=true RESOLVED_DISCLOSURE_REQUIRED=true \
    "$PY" "$SCRIPTS/sws_run_cycle.py" --paper-root "$PAPER" --dry-run --json)"
if echo "$PLAN" | "$PY" -c "
import json, sys
plan = json.loads(sys.stdin.read())
names = {s['name'] for s in plan}
expected = {'outline','draft','revise','review','cover-letter','disclosure','response'}
assert names == expected, names
# outline/draft/review should skip (artifacts present); cover-letter should
# skip too because we already wrote ai-disclosure but NOT cover-letter; this
# step is run-mode. Just check that cover-letter has should_run=true.
by_name = {s['name']: s for s in plan}
assert by_name['outline']['should_run'] is False
assert by_name['draft']['should_run'] is False
assert by_name['review']['should_run'] is False
assert by_name['cover-letter']['should_run'] is True
# disclosure already exists from step 6 => skip
assert by_name['disclosure']['should_run'] is False
# response: reviewer-comments present, no response-to-reviewers.md => RUN
assert by_name['response']['should_run'] is True
"; then ok; else ko "plan structure unexpected"; fi

# ---------------------------------------------------------------------------
# Step 11: sws_run_cycle.py --only=disclosure dispatches deterministic step
# ---------------------------------------------------------------------------
step 11 "sws_run_cycle.py --only=disclosure prints DISPATCH directive"
# Remove the existing disclosure so the step becomes RUN under --only.
rm -f "$DISC"
DISPATCH="$(RESOLVED_COVER_LETTER_REQUIRED=true RESOLVED_DISCLOSURE_REQUIRED=true \
    "$PY" "$SCRIPTS/sws_run_cycle.py" --paper-root "$PAPER" --only=disclosure 2>/dev/null)"
if echo "$DISPATCH" | grep -q "DISPATCH script disclosure"; then ok; else ko "no dispatch directive: $DISPATCH"; fi

# ---------------------------------------------------------------------------
# Step 12: captured-fixture cover-letter passes AI-tells linter
# ---------------------------------------------------------------------------
step 12 "captured-fixture cover-letter grep-passes sws_lint_ai_tells.py (D16, D20)"
CL_DIR="$PAPER/_submission"
mkdir -p "$CL_DIR"
cat > "$CL_DIR/cover-letter.md" <<'COVER_LETTER'
Dear {EDITOR_NAME},

<!-- TODO: replace {EDITOR_NAME} with the handling editor's name -->

Please find enclosed our manuscript "Hypothetical Title" for consideration as
a full article in ChemBioChem.

The manuscript reports a small experimental dataset that addresses one of the
open questions in the field around phenomenon X. We measured property P
across three test conditions and found values clustered near the predicted
range. The variation we observed is consistent with measurement noise rather
than a structural effect.

The work fits the journal's chemical biology scope through its focus on
biomolecular interactions in the conditions tested. We believe the dataset
will be useful to readers working on related problems.

The author declares no conflict of interest.

Sincerely,
[Author Name]
COVER_LETTER
if "$PY" "$SCRIPTS/sws_lint_ai_tells.py" "$CL_DIR/cover-letter.md" >/dev/null 2>&1; then
    ok
else
    ko "cover-letter has block-severity AI-tells hits"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf "\n========================================\n"
printf "SMOKE %s: %d passed, %d failed\n" "$([ $FAIL -eq 0 ] && echo PASS || echo FAIL)" "$PASS" "$FAIL"
printf "========================================\n"
exit $FAIL
