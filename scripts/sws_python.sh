#!/usr/bin/env bash
# Resolves the per-paper Python interpreter at <paper>/.venv/bin/python.
# Usage: sws_python.sh <paper-root> <python-script-or-args...>
# Exits 2 with one-line instruction if venv is missing.
set -eu
PAPER_ROOT="${1:?usage: sws_python.sh <paper-root> <script-or-args...>}"
shift
PY="$PAPER_ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
    echo "sws: per-paper venv not found at $PY — run /sws:install-deps to bootstrap deps" >&2
    exit 2
fi
exec "$PY" "$@"
