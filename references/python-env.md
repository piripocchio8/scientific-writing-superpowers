---
sws_artifact: python-env
artifact_version: 0.1
locked: 2026-05-08
sources:
  - claude_memory/feedback_python_env.md (user's preferred local env: pymol25 mamba)
  - docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md (python_env_policy)

policy:
  min_python: "3.9"
  reference_local_env_for_dev: pymol25 (mamba) at /Users/piripocchio8/opt/miniconda3/envs/pymol25/bin/python
  shipped_runtime_invocation: python3 (whatever's on PATH that meets min_python)
  deps_state_v0_1_through_cycle_4: stdlib-only
  first_real_dep_cycle: 5  # likely python-docx for OOXML manipulation
  setup_infrastructure_cycle: 5  # requirements.txt at repo root + scripts/sws_setup_env.sh

preflight:
  utility: scripts/sws_check_env.py
  invoked_by: every SWS skill before calling a Python utility
  failure_action: print clear error to stderr, exit 1, do not invoke the broken tool
  fallback_inline_pattern: |
    python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' \
      || { echo "SWS requires Python >= 3.9. Activate or install a compatible env, then re-run."; exit 1; }

stdlib_modules_used_through_cycle_4:
  cycle_1: [pathlib, json, datetime, fnmatch, sys, argparse]   # sws_fs_index.py
  cycle_2: [pathlib, json, sys, argparse, string.Template, unicodedata, shutil, tempfile]   # sws_render_template.py + sws_init_project.py + sws_check_env.py

testing:
  framework: unittest (Python stdlib)
  test_runner: "python -m unittest <module> -v"
  reference_env_for_local_test_runs: pymol25 (per claude_memory/feedback_python_env.md)
  mocking: unittest.mock
---

# Python env policy

Frontmatter is the source of truth. Body is orientation.

SWS commits to stdlib-only through cycle #4 to keep first-time-user friction at zero — no `pip install`, no virtualenv, no compatibility surface to debug. When cycle #5 introduces the first OOXML manipulation (drafter), it ships `requirements.txt` and `scripts/sws_setup_env.sh` together; the upgrade is documented in that cycle's plan.

Skills invoke Python utilities through `scripts/sws_check_env.py` first. The check is a one-line preflight: if Python is missing or too old, print a clear error and exit non-zero. Skills then know to abort without burning model tokens debugging a phantom error.
