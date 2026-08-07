# Divan Desktop

Tauri 2 + React desktop shell over the authoritative Divan Core runtime.

Divan Desktop is task-first rather than terminal-first: project selection, task lifecycle, Codex/Claude/OpenCode worker execution, independent review, evidence/diff inspection and guarded approval/merge all flow through the Core contract. Orca remains an optional, replaceable execution engine.

## Development

```powershell
cd apps/desktop
pnpm install
pnpm desktop:dev
```

## Windows beta bundle

```powershell
pnpm desktop:build
```

This builds the self-contained `divan-core` sidecar and a current-user NSIS installer (`*-setup.exe`). End users do not need a separate Python installation.

## Stable Windows release

Stable artifacts are intentionally produced only by the protected GitHub Actions release lanes:

1. Merge an all-green Desktop candidate to `main`.
2. Run `Desktop Real-User Acceptance` on a protected self-hosted Windows x64 runner carrying the dedicated `divan-desktop-acceptance` label and genuine Codex + Claude Code logins.
3. Provision the `production-release` environment with Windows Authenticode signing configuration and Tauri updater key/HTTPS endpoint material.
4. Run `Desktop Stable Candidate` for the exact same `main` commit and pass the successful acceptance workflow run ID.
5. Promote only the signed, source-bound, attested artifacts produced by that workflow.

Unsigned beta builds, stale acceptance evidence, source-mismatched Core binaries and synthetic PASS results are not stable-release evidence.
