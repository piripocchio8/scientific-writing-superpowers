---
name: install-deps
description: "This skill should be used when the user invokes /sws:install-deps, says 'install SWS Python deps', 'bootstrap the venv for this paper', or 'refresh my SWS environment'. Creates the per-paper .venv/ at <paper>/.venv/ from the system python3, then installs the deps listed in the plugin's requirements/sws-deps.txt. Idempotent — safe to re-run. If the marker has format: latex, also installs pylatexenc."
version: 0.1.0
---

# /sws:install-deps — Bootstrap per-paper venv

This skill creates the per-paper `.venv/` and installs the SWS default Python dependencies into it. The plugin never reuses a developer mamba env or a global interpreter — every SWS paper has its own isolated `.venv/`.

Called automatically by `/sws:init-project` on first run. Re-runnable manually when deps drift or the venv was deleted.

## When to invoke

- User explicitly types `/sws:install-deps`.
- User asks "install SWS deps", "create the SWS venv here", "bootstrap my SWS environment", "refresh deps", or similar — **and** the cwd contains a valid `.sws-project.local.md` marker.

Do NOT invoke when:
- The cwd is not an SWS paper (no marker). Print "not an SWS project (no .sws-project.local.md found)" and exit.

## Steps

1. **Resolve `$PAPER_ROOT`.** Current working directory must contain `.sws-project.local.md`. If absent, print the not-an-SWS-project line and exit.

2. **Parse the marker.** Read `.sws-project.local.md` and extract `format` (docx | latex).

3. **Create the venv (idempotent).** If `$PAPER_ROOT/.venv/bin/python` already exists, skip step 4 and 5; print `venv already present at $PAPER_ROOT/.venv/ — re-running pip install to refresh deps` and proceed to step 6.

   ```bash
   python3 -m venv "$PAPER_ROOT/.venv"
   ```

4. **Confirm the venv is usable.** Verify `$PAPER_ROOT/.venv/bin/python --version` runs.

5. **Upgrade pip in the venv** so wheel-based installs work cleanly:

   ```bash
   "$PAPER_ROOT/.venv/bin/python" -m pip install --upgrade pip
   ```

6. **Install plugin default deps.**

   ```bash
   "$PAPER_ROOT/.venv/bin/pip" install -r "${CLAUDE_PLUGIN_ROOT}/requirements/sws-deps.txt"
   ```

7. **If `format: latex` in marker, also install pylatexenc.**

   ```bash
   "$PAPER_ROOT/.venv/bin/pip" install "pylatexenc>=2.10"
   ```

8. **Print confirmation:** one line with paper root, venv path, and the count of installed packages.

## Notes

- All plugin Python utilities invoke through `scripts/sws_python.sh "$PAPER_ROOT" <script.py>` which resolves the per-paper venv.
- If pip is unreachable (offline / network issue), surface the error verbatim — do not retry silently.
- Re-running this skill is safe and refreshes versions if `requirements/sws-deps.txt` has changed.
