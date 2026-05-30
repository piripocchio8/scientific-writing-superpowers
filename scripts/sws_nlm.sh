#!/usr/bin/env bash
# sws_nlm.sh - CLI wrapper around notebooklm-mcp-cli.
#
# Single point of contact between SWS and the upstream NLM binary
# (jacob-bd/notebooklm-mcp-cli, MIT). All NLM-consuming agents call
# the nlm-librarian agent; only nlm-librarian calls this script;
# only this script invokes the upstream binary.
#
# Subcommands (locked v0.1 surface area — see D3):
#   probe                       Detect binary + auth state; honors the
#                               notebooklm.enabled marker flag.
#   query <question> [--notebook <id>]
#                               Run a query against the configured notebook.
#                               Prints normalized JSON on stdout.
#   list-notebooks              Enumerate the user's notebooks (JSON list).
#
# Exit codes:
#   0   success (or graceful-degrade when notebooklm.enabled=false)
#   2   usage error / unknown subcommand
#   4   binary not found on PATH and no marker cli_path set
#   5   binary present but probe failed (auth, version mismatch, malformed output)
#
# Environment (set by agent_prelude.sh):
#   RESOLVED_NOTEBOOKLM_ENABLED   "true" | "false"   (default: false)
#   RESOLVED_NLM_NOTEBOOK_ID      string             (optional)
#   RESOLVED_NLM_CLI_PATH         absolute path      (optional override)
#   SWS_NLM_PROBE_RESULT          ok|disabled|missing|auth|error   (cache; R4)
#
# All consumer-facing messages go to stderr. All JSON return-shape data
# goes to stdout. Bash + stdlib python3 only.

set -uo pipefail

# ---------------------------------------------------------------------------
# Defaults (so the wrapper works when called outside an agent context, e.g. tests)
# ---------------------------------------------------------------------------
: "${RESOLVED_NOTEBOOKLM_ENABLED:=false}"
: "${RESOLVED_NLM_NOTEBOOK_ID:=}"
: "${RESOLVED_NLM_CLI_PATH:=}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
die_usage() {
    cat >&2 <<EOF
sws_nlm.sh: usage:
  sws_nlm.sh probe
  sws_nlm.sh query <question> [--notebook <id>]
  sws_nlm.sh list-notebooks
EOF
    exit 2
}

detect_binary() {
    # D4 discovery order. Print the resolved binary path on stdout.
    if [[ -n "${RESOLVED_NLM_CLI_PATH}" && -x "${RESOLVED_NLM_CLI_PATH}" ]]; then
        printf '%s\n' "${RESOLVED_NLM_CLI_PATH}"
        return 0
    fi
    if command -v notebooklm-mcp-cli >/dev/null 2>&1; then
        command -v notebooklm-mcp-cli
        return 0
    fi
    if command -v notebooklm >/dev/null 2>&1; then
        command -v notebooklm
        return 0
    fi
    return 1
}

emit_degrade_json() {
    # Args: fallback_reason  fallback_message  notebook_id  query
    # Prints the degrade-shape JSON on stdout (D8) and returns nothing else.
    local reason="$1" msg="$2" nb="${3:-}" q="${4:-}"
    SWS_NLM_REASON="$reason" SWS_NLM_MSG="$msg" \
        SWS_NLM_NB="$nb" SWS_NLM_Q="$q" python3 -c '
import json, os
out = {
    "ok": False,
    "answer": "",
    "sources": [],
    "notebook_id": os.environ.get("SWS_NLM_NB", ""),
    "query": os.environ.get("SWS_NLM_Q", ""),
    "fallback": os.environ.get("SWS_NLM_REASON", "error"),
    "fallback_message": os.environ.get("SWS_NLM_MSG", ""),
}
print(json.dumps(out))
'
}

cache_set() {
    # Best-effort cache of the probe result for the rest of the session (R4).
    # We export, but a sub-shell invocation can't propagate to the parent.
    # Callers that want session-wide caching set SWS_NLM_PROBE_RESULT themselves
    # after the first probe call; this just records the value for the current
    # invocation.
    export SWS_NLM_PROBE_RESULT="$1"
}

probe_binary() {
    # Returns 0 + prints "ok|disabled|missing|auth|error" on stdout.
    # Honors RESOLVED_NOTEBOOKLM_ENABLED and the SWS_NLM_PROBE_RESULT cache.

    if [[ "${SWS_NLM_PROBE_RESULT:-}" != "" ]]; then
        printf '%s\n' "$SWS_NLM_PROBE_RESULT"
        return 0
    fi

    if [[ "${RESOLVED_NOTEBOOKLM_ENABLED}" != "true" ]]; then
        cache_set "disabled"
        printf 'disabled\n'
        return 0
    fi

    local bin
    if ! bin="$(detect_binary)"; then
        cache_set "missing"
        printf 'missing\n'
        return 0
    fi

    # Ask the binary itself for a version / auth signal. We treat any non-zero
    # exit OR an obvious "not authorized" / "not configured" stderr fragment
    # as auth failure (the upstream CLI's exact contract is documented at
    # references/nlm-librarian-pattern.md last_tested_version).
    local ver_out ver_rc
    ver_out="$("$bin" --version 2>&1)"
    ver_rc=$?
    if [[ $ver_rc -ne 0 ]]; then
        cache_set "auth"
        printf 'auth\n'
        return 0
    fi
    # Some installs print to stderr when unconfigured.
    if printf '%s' "$ver_out" | grep -qiE 'unauthorized|not configured|auth (failed|required)'; then
        cache_set "auth"
        printf 'auth\n'
        return 0
    fi

    cache_set "ok"
    printf 'ok\n'
    return 0
}

validate_json_or_error() {
    # Read stdin; if it parses as JSON, print it back; else exit 5 with a
    # stderr "unexpected format" message (R3).
    SWS_NLM_JSON_BLOB="$(cat)"
    if ! SWS_NLM_JSON_BLOB="$SWS_NLM_JSON_BLOB" python3 -c '
import json, os, sys
try:
    json.loads(os.environ["SWS_NLM_JSON_BLOB"])
except Exception as exc:
    print(f"ERR:{exc}", file=sys.stderr)
    sys.exit(1)
' 2>/dev/null; then
        printf 'sws_nlm: NLM binary returned an unexpected format; check binary version.\n' >&2
        exit 5
    fi
    printf '%s' "$SWS_NLM_JSON_BLOB"
}

# ---------------------------------------------------------------------------
# Subcommand dispatch
# ---------------------------------------------------------------------------
SUBCMD="${1:-}"
[[ -z "$SUBCMD" ]] && die_usage
shift || true

case "$SUBCMD" in
    probe)
        result="$(probe_binary)"
        case "$result" in
            ok)
                printf 'sws_nlm: probe ok (notebooklm-mcp-cli reachable).\n' >&2
                exit 0
                ;;
            disabled)
                printf 'sws_nlm: NLM disabled in this project; proceeding without NLM.\n' >&2
                exit 0
                ;;
            missing)
                printf 'sws_nlm: notebooklm-mcp-cli binary not found. Install: npm install -g notebooklm-mcp-cli OR pipx install notebooklm-mcp-cli (see references/nlm-librarian-pattern.md). Or set notebooklm.cli_path in your marker.\n' >&2
                exit 4
                ;;
            auth)
                printf 'sws_nlm: NLM binary present but probe failed (auth / version mismatch). Check the tool auth setup.\n' >&2
                exit 5
                ;;
            *)
                printf 'sws_nlm: unknown probe state: %s\n' "$result" >&2
                exit 5
                ;;
        esac
        ;;

    query)
        # Args: <question> [--notebook <id>]
        QUESTION="${1:-}"
        if [[ -z "$QUESTION" ]]; then
            printf 'sws_nlm: query requires a question argument.\n' >&2
            exit 2
        fi
        shift
        NOTEBOOK="$RESOLVED_NLM_NOTEBOOK_ID"
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --notebook)
                    NOTEBOOK="${2:-}"
                    shift 2
                    ;;
                *)
                    printf 'sws_nlm: unknown query option: %s\n' "$1" >&2
                    exit 2
                    ;;
            esac
        done

        probe_state="$(probe_binary)"
        case "$probe_state" in
            disabled)
                emit_degrade_json "disabled" \
                    "NLM disabled in this project; proceeding without NLM." \
                    "$NOTEBOOK" "$QUESTION"
                exit 0
                ;;
            missing)
                emit_degrade_json "missing" \
                    "NLM enabled but notebooklm-mcp-cli binary missing; install it (see references/nlm-librarian-pattern.md) or set notebooklm.cli_path. Proceeding without NLM." \
                    "$NOTEBOOK" "$QUESTION"
                printf 'sws_nlm: query degraded — binary missing.\n' >&2
                exit 0
                ;;
            auth)
                emit_degrade_json "auth" \
                    "NLM auth not configured; check the tool's auth setup and re-run. Proceeding without NLM." \
                    "$NOTEBOOK" "$QUESTION"
                printf 'sws_nlm: query degraded — auth failed.\n' >&2
                exit 5
                ;;
            ok)
                bin="$(detect_binary)"
                raw_args=(query "$QUESTION")
                if [[ -n "$NOTEBOOK" ]]; then
                    raw_args+=(--notebook "$NOTEBOOK")
                fi
                raw="$("$bin" "${raw_args[@]}" 2>/dev/null)"
                rc=$?
                if [[ $rc -ne 0 || -z "$raw" ]]; then
                    printf 'sws_nlm: NLM binary returned an unexpected format; check binary version.\n' >&2
                    exit 5
                fi

                # Validate JSON and normalize to D8 schema.
                normalized="$(SWS_NLM_RAW="$raw" SWS_NLM_NB="$NOTEBOOK" SWS_NLM_Q="$QUESTION" python3 -c '
import json, os, sys
try:
    data = json.loads(os.environ["SWS_NLM_RAW"])
except Exception:
    sys.exit(1)
nb = os.environ.get("SWS_NLM_NB", "")
q  = os.environ.get("SWS_NLM_Q",  "")
answer = data.get("answer") if isinstance(data, dict) else None
sources = data.get("sources") if isinstance(data, dict) else None
if not isinstance(answer, str) or not isinstance(sources, list):
    sys.exit(1)
norm_sources = []
for s in sources:
    if not isinstance(s, dict):
        continue
    norm_sources.append({
        "title":   s.get("title", "") or "",
        "snippet": s.get("snippet", "") or "",
        "page":    s.get("page") if isinstance(s.get("page"), int) else None,
    })
out = {
    "ok": True,
    "answer": answer,
    "sources": norm_sources,
    "notebook_id": nb,
    "query": q,
    "fallback": "none",
    "fallback_message": "",
}
print(json.dumps(out))
' 2>/dev/null)"
                if [[ -z "$normalized" ]]; then
                    printf 'sws_nlm: NLM binary returned an unexpected format; check binary version.\n' >&2
                    exit 5
                fi
                printf '%s\n' "$normalized"
                exit 0
                ;;
        esac
        ;;

    list-notebooks)
        probe_state="$(probe_binary)"
        if [[ "$probe_state" != "ok" ]]; then
            printf 'sws_nlm: list-notebooks unavailable (probe state: %s).\n' "$probe_state" >&2
            exit 5
        fi
        bin="$(detect_binary)"
        raw="$("$bin" list-notebooks 2>/dev/null)"
        rc=$?
        if [[ $rc -ne 0 || -z "$raw" ]]; then
            printf 'sws_nlm: list-notebooks returned an unexpected format.\n' >&2
            exit 5
        fi
        printf '%s' "$raw" | validate_json_or_error
        printf '\n'
        exit 0
        ;;

    *)
        die_usage
        ;;
esac
