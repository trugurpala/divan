# Divan Desktop MVP

Divan Desktop is a thin presentation and operator layer over Divan Core. The UI must never become the source of truth for task state, execution authority, review verdicts, or release evidence.

## Product boundary

- **Divan Core** owns task lifecycle, engine selection, mandates, evidence, review/release gates.
- **Execution engines** own replaceable runtime mechanics such as worktrees and agent terminals.
- **Desktop shell** renders state and submits explicit operator actions through `DesktopApi`.

## MVP screens

1. **Projects** — open/register a repository and show engine readiness.
2. **Tasks** — create a task and follow `draft → planned → running → review → passed → approval → merged → released`.
3. **Agents** — show execution engine sessions and terminal status without making terminal output the task state.
4. **Evidence** — list immutable evidence records and verify their SHA-256 digest.
5. **Approval Gate** — display changed files, tests, reviewer verdict, risk and mandate before mutation/merge.
6. **Settings** — discover Git, Codex, Claude, OpenCode, Orca/other engines and Windows/WSL capabilities.

## Windows packaging target

The product artifact is `Divan-Setup-x64.exe`. Packaging is intentionally downstream of the stable core API and real runtime verification. Installer completion requires a Windows runner that proves install, first launch, runtime discovery, project open, task execution, approval gate and uninstall.

## UI contract

Desktop code should use `divan_runtime.desktop_api.DesktopApi` rather than importing runtime internals. API v1 starts with:

- `capabilities()`
- `engine_status()`
- task serialization

Future commands must preserve stable JSON-shaped responses and explicit error codes.
