---
sws_artifact: python-env
artifact_version: 0.2
locked: 2026-05-13
sources:
  - docs/superpowers/specs/2026-05-08-cycle-02-init-project-design.md (python_env_policy)
  - docs/superpowers/specs/2026-05-12-cycle-06-profile-and-overlay-design.md (D19, D20: per-paper venv discipline)

policy:
  min_python: "3.9"
  shipped_runtime_invocation: "$PAPER_ROOT/.venv/bin/python via scripts/sws_python.sh (cycle-#6+)"
  legacy_pre_cycle_6: "python3 (whatever's on PATH that meets min_python; still used by hooks/fs_index/init-project which are stdlib-only)"
  deps_state_v0_1_through_cycle_4: stdlib-only
  first_real_dep_cycle: 5  # python-docx and friends for OOXML manipulation
  setup_infrastructure_cycle: 6  # requirements/sws-deps.txt + scripts/sws_install_deps.sh + scripts/sws_python.sh

preflight:
  utility: scripts/sws_check_env.py
  invoked_by: every SWS skill that runs a stdlib-only Python utility (hooks, fs_index, init-project)
  failure_action: print clear error to stderr, exit 1, do not invoke the broken tool
  fallback_inline_pattern: |
    python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' \
      || { echo "SWS requires Python >= 3.9. Activate or install a compatible env, then re-run."; exit 1; }
  per_paper_venv_path: "<paper>/.venv/bin/python"
  venv_failure_action: "scripts/sws_python.sh exits 2 with 'run /sws:install-deps to bootstrap deps'"

stdlib_modules_used_pre_cycle_6:
  cycle_1: [pathlib, json, datetime, fnmatch, sys, argparse]   # sws_fs_index.py
  cycle_2: [pathlib, json, sys, argparse, string.Template, unicodedata, shutil, tempfile]   # sws_render_template.py + sws_init_project.py + sws_check_env.py
  cycle_5: [pathlib, json, sys, os, re, datetime, shutil, tempfile]   # all three hooks + sws_hook_utils

deps_from_cycle_6:
  source: requirements/sws-deps.txt
  installed_into: "<paper>/.venv/ at init time"
  list: [PyYAML, python-docx, pdfplumber, lxml, openpyxl, pytest]

testing:
  framework: unittest (Python stdlib)
  test_runner: "python -m unittest discover tests"
  test_runner_requirements: "any Python 3.9+ with PyYAML installed (resolver tests parse profile/overlay frontmatter)"
  mocking: unittest.mock
---

# Python env policy

Frontmatter is the source of truth. Body is orientation.

SWS commits to stdlib-only through cycle #4 to keep first-time-user friction at zero — no `pip install`, no virtualenv, no compatibility surface to debug. When cycle #5 introduces the first OOXML manipulation (drafter), it ships `requirements.txt` and `scripts/sws_setup_env.sh` together; the upgrade is documented in that cycle's plan.

Skills invoke Python utilities through `scripts/sws_check_env.py` first. The check is a one-line preflight: if Python is missing or too old, print a clear error and exit non-zero. Skills then know to abort without burning model tokens debugging a phantom error.
