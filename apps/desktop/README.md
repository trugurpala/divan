# Ottoman Desktop

Tauri 2 + React desktop shell over the authoritative Ottoman Core runtime.

Ottoman Desktop is task-first rather than terminal-first: project selection, task lifecycle, Codex/Claude/OpenCode worker execution, independent review, evidence/diff inspection and guarded approval/merge all flow through the Core contract. Orca remains an optional, replaceable execution engine.

## Yerel prompt kütüphanesi

`Prompt kütüphanesi` ekranı, [f/prompts.chat](https://github.com/f/prompts.chat)
deposunun `f1c515686725fcd84a90d361b9eeb11eb15edb17` commit'indeki CC0-1.0
`prompts.csv` verisinin yerel, 2.109 şablonluk kopyasını arar. Yerel kopyada
katkıcı e-posta adresleri anonimleştirilir; prompt içinde rastlanan e-posta
biçimleri de gösterilmeden önce maskelenir. Bir şablon
seçmek otomatik ajan çalıştırmaz: önce normal Ottoman görevi oluşur; ardından
aynı planlama, açık çalıştırma izni, bağımsız review ve onay kapıları uygulanır.
Kaynak/izin kaydı `UPSTREAM.md` ve `THIRD_PARTY_LICENSES.md` içindedir.

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

This builds the self-contained core sidecar and a current-user NSIS installer (`*-setup.exe`). End users do not need a separate Python installation.

## Stable Windows release

Stable artifacts are intentionally produced only by the protected GitHub Actions release lanes:

1. Merge an all-green Desktop candidate to `main`.
2. Run `Desktop Real-User Acceptance` on a protected self-hosted Windows x64 runner carrying the dedicated desktop acceptance label and genuine Codex + Claude Code logins.
3. Provision the `production-release` environment with Windows Authenticode signing configuration and Tauri updater key/HTTPS endpoint material.
4. Run `Desktop Stable Candidate` for the exact same `main` commit and pass the successful acceptance workflow run ID.
5. Promote only the signed, source-bound, attested artifacts produced by that workflow.

Unsigned beta builds, stale acceptance evidence, source-mismatched Core binaries and synthetic PASS results are not stable-release evidence.
