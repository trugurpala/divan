# ADR 0011: Codex auto-install chooses the strongest honest route

- Status: Accepted
- Date: 2026-07-30
- Owner: Hükümdar
- Issue: #57

## Context

Codex Desktop may expose a Codex CLI path that is missing, not executable, or
blocked by Windows package ACLs. Treating every launch failure as “not found”
is misleading. Requiring users to diagnose the package boundary and then find
a separate fallback installer is also unnecessarily difficult.

Divan already has two valid installation mechanisms:

1. the native Codex plugin lifecycle,
2. the transactional, checksum-backed 41-skill fallback.

They do not provide the same capabilities and must not be presented as equal.

## Decision

Divan adds an explicit `--profile auto` option for `--host codex` installs.
Plain installs remain native and unchanged.

The auto profile classifies the CLI as:

- `healthy`,
- `missing`,
- `not-executable`,
- `access-denied`,
- `invalid-json`.

`healthy` keeps the native plugin route. The three launch failures select the
verified skill fallback. `invalid-json` blocks because the host executed but
its protocol is incompatible.

The fallback reuses the canonical platform installer. It must verify the
immutable ref, source commit, release archive SHA-256, exactly 41 skill names,
and every installed tree SHA-256. Its result explicitly marks native commands,
agents, hooks, MCP configuration, and native lifecycle as unavailable.

## Consequences

- A Codex Desktop user gets one preview-first command and one execution command.
- No ACL change, elevation, hidden MCP installation, or silent fallback occurs.
- Existing unrelated skills remain outside Divan ownership.
- Native and fallback capability claims stay machine-readable.
- Mixed Claude-native/Codex-fallback transactions remain out of scope until one
  atomic rollback boundary can cover both.

