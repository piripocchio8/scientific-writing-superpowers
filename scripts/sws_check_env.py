#!/usr/bin/env python3
"""SWS environment preflight.

Run before any SWS Python utility. Returns clear error message + non-zero
exit if Python is missing or too old. Skills invoke this first to fail
fast with a useful diagnostic instead of letting the model thrash on
phantom errors.
"""
from __future__ import annotations
import sys

MIN_PYTHON = (3, 9)


def check_env() -> tuple[bool, str]:
    """Returns (ok, message). ok=True means env is fine."""
    if sys.version_info < MIN_PYTHON:
        return (
            False,
            f"SWS requires Python >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}. "
            f"Detected {sys.version_info[0]}.{sys.version_info[1]}. "
            f"Activate or install a compatible env."
        )
    return (True, "ok")


def main() -> int:
    ok, msg = check_env()
    if not ok:
        print(msg, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
