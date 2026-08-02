# Install Divan from this repository

This guide is for Codex and Claude desktop agents when a user says “install
Divan from this repository”. The agent must perform the work; the user should
not need to copy terminal commands.

## Required sequence

1. Read `AGENTS.md`, `divan-install.json`, and the current GitHub Release.
2. Resolve the newest non-draft, non-prerelease GitHub Release. Do not install
   from `main`, `master`, a moving branch, or an unpinned checkout.
3. Download the release runner and its `.sha256` file from that same release.
   Verify SHA-256 before executing anything. Keep the release tag and source
   commit together in the result.
4. Inspect the host. Use native installation when its marketplace and plugin
   path can be proven. For Codex, `profile auto` may select the verified skill
   fallback when the native CLI is unavailable.
5. Run the preview command from `divan-install.json`. Preview must not write
   host state.
6. Run the execute command only after the preview is understandable. Preserve
   every unrelated marketplace and plugin. Never overwrite an existing
   unproven `divan` entry.
7. Run the doctor command after execution. Only a real `doctor_status` of
   `healthy` is `READY` and only that result may be called installed. A
   fallback is verified skill content, not a native READY installation.
8. Check every machine-readable result field in `divan-install.json`, including
   `source_ref`, `source_commit`, `package_count`, `skill_count`,
   `restart_required`, `next_action`, and `recovery_command`.
9. On failure, show one short reason and the single `recovery_command`. Do not
   claim success, retry mutations, or hide the transaction journal.
10. On native READY or verified fallback, tell the user to close the desktop
    application completely and open a new session. The next session discovers
    Divan automatically; daily use is ordinary natural language, not a CLI.

## Safety boundaries

- Do not change PATH, shell profiles, credentials, or unrelated extensions.
- Do not remove or modify another marketplace or plugin.
- Do not weaken checksum, immutable-ref, source-commit, provenance, or doctor
  checks.
- Do not expose user names, home paths, tokens, API keys, or customer data.
- Do not report native commands, agents, hooks, MCP, or lifecycle features for
  the verified skill fallback.
