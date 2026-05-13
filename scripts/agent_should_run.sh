#!/usr/bin/env bash
# Thin wrapper over resolve_overlay.py --agent <id>.
# Exit 0 if the agent may run, non-zero otherwise.
#
# Usage:  agent_should_run.sh <agent-id>
#
# Pre-conditions (caller must export):
#   CLAUDE_PLUGIN_ROOT
#   PAPER_ROOT
set -u

AGENT_ID="${1:-}"
if [[ -z "$AGENT_ID" ]]; then
    echo "sws: agent_should_run.sh requires an agent id" >&2
    exit 1
fi

: "${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT must be set}"
: "${PAPER_ROOT:?PAPER_ROOT must be set}"

JSON="$(
  "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
    "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_overlay.py" \
    --paper "$PAPER_ROOT" --agent "$AGENT_ID" 2>/dev/null
)" || { echo "sws: resolver failed for ${AGENT_ID}" >&2; exit 2; }

# Use python3 to read profile_set and should_run.
RESULT="$(SWS_JSON_PAYLOAD="$JSON" python3 -c '
import json, os, sys
data = json.loads(os.environ["SWS_JSON_PAYLOAD"])
profile_set = bool(data.get("profile_set"))
should_run = data.get("should_run")
ok = profile_set and (should_run is None or should_run)
print("1" if ok else "0")
')"

if [[ "$RESULT" == "1" ]]; then
    exit 0
else
    exit 3
fi
