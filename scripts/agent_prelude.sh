#!/usr/bin/env bash
# Agent prelude: resolves the 3-layer profile/overlay contract and exports
# RESOLVED_* env vars. Source this from any agent prompt's first step.
#
# Usage:  source "${CLAUDE_PLUGIN_ROOT}/scripts/agent_prelude.sh" <agent-id>
#
# Pre-conditions (caller must export):
#   CLAUDE_PLUGIN_ROOT  — absolute path to the SWS plugin directory
#   PAPER_ROOT          — absolute path to the user paper directory
#
# Post-conditions:
#   RESOLVED_OK         — "1" if the agent may run, "0" otherwise
#   RESOLVED_PROFILE_ID — the profile id (string) or "null"
#   RESOLVED_REF_CAP, RESOLVED_WORD_TOTAL, RESOLVED_FIGURES_MAX,
#   RESOLVED_TABLES_MAX, RESOLVED_ABSTRACT_STYLE,
#   RESOLVED_DISCLOSURE_REQUIRED, RESOLVED_COVER_LETTER_REQUIRED,
#   RESOLVED_REFS_STYLE
#
# Never `exit` — we `return` so the calling shell stays alive. Caller checks
# RESOLVED_OK and decides whether to proceed.
set -u

AGENT_ID="${1:-}"
if [[ -z "$AGENT_ID" ]]; then
    echo "sws: agent_prelude.sh requires an agent id" >&2
    export RESOLVED_OK=0
    return 0 2>/dev/null || exit 0
fi

: "${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT must be set}"
: "${PAPER_ROOT:?PAPER_ROOT must be set}"

JSON="$(
  "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
    "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
    --paper "$PAPER_ROOT" --agent "$AGENT_ID" 2>/dev/null
)" || JSON=""

if [[ -z "$JSON" ]]; then
    echo "sws: resolver failed for agent ${AGENT_ID} (no JSON returned)" >&2
    export RESOLVED_OK=0
    return 0 2>/dev/null || exit 0
fi

# Parse with python3 (system) — we read only fixed keys, no yaml needed here.
# Pass the JSON via an env var so we don't fight bash's stdin/heredoc rules.
PARSED="$(SWS_JSON_PAYLOAD="$JSON" python3 -c '
import json, os, sys
try:
    data = json.loads(os.environ.get("SWS_JSON_PAYLOAD", ""))
except Exception as exc:
    print(f"ERR:{exc}", end="")
    sys.exit(0)
fm = data.get("resolved_frontmatter") or {}
def safe(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)
nlm = fm.get("notebooklm") or {}
if not isinstance(nlm, dict):
    nlm = {}
fields = {
    "PROFILE_ID": data.get("profile_id"),
    "REF_CAP": fm.get("ref_cap"),
    "WORD_TOTAL": fm.get("word_total"),
    "FIGURES_MAX": fm.get("figures_max"),
    "TABLES_MAX": fm.get("tables_max"),
    "ABSTRACT_STYLE": fm.get("abstract_style"),
    "DISCLOSURE_REQUIRED": fm.get("disclosure_required"),
    "COVER_LETTER_REQUIRED": fm.get("cover_letter_required"),
    "REFS_STYLE": fm.get("refs_style"),
    # Cycle-13: notebooklm.* flattened to RESOLVED_NOTEBOOKLM_* env vars.
    "NOTEBOOKLM_ENABLED": nlm.get("enabled", False),
    "NLM_NOTEBOOK_ID": nlm.get("notebook_id"),
    "NLM_CLI_PATH": nlm.get("cli_path"),
}
profile_set = bool(data.get("profile_set"))
should_run = data.get("should_run")
ok = profile_set and (should_run is None or should_run)
print("OK=" + ("1" if ok else "0"))
print("PROFILE_SET=" + ("1" if profile_set else "0"))
for k, v in fields.items():
    print(f"{k}={safe(v)}")
')"

if [[ "$PARSED" == ERR:* ]]; then
    echo "sws: failed to parse resolver JSON: ${PARSED#ERR:}" >&2
    export RESOLVED_OK=0
    return 0 2>/dev/null || exit 0
fi

# Set RESOLVED_OK first so callers can branch even if other parsing fails.
RESOLVED_OK_VALUE=0
RESOLVED_PROFILE_SET_VALUE=0
while IFS='=' read -r key value; do
    case "$key" in
        OK) RESOLVED_OK_VALUE="$value" ;;
        PROFILE_SET) RESOLVED_PROFILE_SET_VALUE="$value" ;;
        *) printf -v "RESOLVED_${key}" '%s' "$value"
           export "RESOLVED_${key}" ;;
    esac
done <<< "$PARSED"

export RESOLVED_OK="$RESOLVED_OK_VALUE"
export RESOLVED_PROFILE_SET="$RESOLVED_PROFILE_SET_VALUE"

if [[ "$RESOLVED_PROFILE_SET" -ne 1 ]]; then
    echo "sws: no profile set — run /sws:set-profile <name>. Agent ${AGENT_ID} paused." >&2
elif [[ "$RESOLVED_OK" -ne 1 ]]; then
    echo "sws: agent ${AGENT_ID} not active for resolved profile (${RESOLVED_PROFILE_ID})." >&2
fi

# --- cycle #10: voice profile path (D13) -----------------------------------
# Export VOICE_PROFILE = path to _voice/profile.md if it exists, else empty.
# Voice is a SEPARATE axis from resolve_overlay.py; this is just a path export.
if [[ -f "${PAPER_ROOT}/_voice/profile.md" ]]; then
    export VOICE_PROFILE="${PAPER_ROOT}/_voice/profile.md"
else
    export VOICE_PROFILE=""
fi
