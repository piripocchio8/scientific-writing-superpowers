---
name: set-profile
description: "This skill should be used when the user invokes /sws:set-profile, says 'set the writing profile', 'change the profile to <name>', 'switch this paper to a communication / full-article / funding-proposal / etc.', or otherwise asks to set or update the SWS profile for the current paper. Validates the name against the 9 locked v0.1 ids, rewrites the profile field in .sws-project.local.md, and leaves all journal-style and call overlays untouched."
version: 0.1.0
---

# /sws:set-profile — Set or change the writing profile

This skill writes the `profile` field in the current paper's `.sws-project.local.md` marker. It does not touch journal-style or call overlays — overlays are keyed by slug, not by profile, so switching profiles preserves them.

## Usage

`/sws:set-profile <name>`

`<name>` must be one of the 9 v0.1 locked ids:

- `full-article`
- `communication`
- `perspective`
- `review-paper`
- `mini-review`
- `editorial`
- `methodological-paper`
- `commentary-reply`
- `funding-proposal`

## When to invoke

- User explicitly types `/sws:set-profile <name>`.
- User says "set the profile to <name>", "change my profile to <name>", "switch this paper to a <name>", or similar — **and** the cwd contains a valid `.sws-project.local.md` marker.

Do NOT invoke when:
- The cwd has no marker. Print "not an SWS project (no .sws-project.local.md found)" and exit.

## Steps

1. **Resolve `$PAPER_ROOT`.** Current working directory must contain `.sws-project.local.md`. If absent, print the not-an-SWS-project line and exit.

2. **Validate the name.** Run the helper to check the name against the plugin's `profiles/` directory:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sws_python.sh" "$PAPER_ROOT" \
       "${CLAUDE_PLUGIN_ROOT}/scripts/sws_set_profile.py" \
       --paper "$PAPER_ROOT" --name "<name>"
   ```

3. **Handle exit codes.** The helper prints `profile: <new> (was: <old>)` on success and exits 0. On invalid name it exits 1 with a clear stderr message listing the 9 valid ids. On missing marker it exits 2.

4. **Hand back to the user.** No further model action needed. Overlays at `Manuscript/_journal-style/` and `Manuscript/_call/` are deliberately untouched (D11).

## Notes

- Switching profile **does not** invalidate existing journal-style or call overlays. They remain on disk and the resolver still loads them on the next read. If the user is switching from a publication profile to `funding-proposal`, the journal overlay becomes irrelevant (call overlay applies instead) — no cleanup needed.
- This skill is the safe path for changing profile after `/sws:init-project`. Re-running init-project is a heavier operation that re-scans the directory tree.
