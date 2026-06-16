#!/usr/bin/env bash
# Fake notebooklm-mcp-cli stub for cycle-13 tests + smoke.
#
# Behavior (must match the contract sws_nlm.sh expects):
#   --version           -> prints a fake version banner; exit 0
#   query <q> [--notebook <id>]
#                       -> prints minimal JSON {answer, sources[]}; exit 0
#   list-notebooks      -> prints a fake JSON list; exit 0
#   anything else       -> exit 2 (usage error)
#
# Auth-failure mode is exposed via FAKE_NLM_AUTH_FAIL=1 (the stub
# then prints "Unauthorized" to stderr on --version).
case "$1" in
    --version)
        if [[ "${FAKE_NLM_AUTH_FAIL:-0}" = "1" ]]; then
            echo "Unauthorized: auth not configured" >&2
            exit 1
        fi
        echo "fake-notebooklm-mcp-cli 0.0.1-test"
        ;;
    query)
        if [[ "${FAKE_NLM_MALFORMED:-0}" = "1" ]]; then
            echo "this is not json"
        else
            echo '{"answer":"fake answer","sources":[{"title":"S1","snippet":"x","page":1}]}'
        fi
        ;;
    list-notebooks)
        echo '[{"id":"nb1","title":"Test Notebook"}]'
        ;;
    *)
        echo "fake-notebooklm-mcp-cli: unknown subcommand: $1" >&2
        exit 2
        ;;
esac
