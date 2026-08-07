# Divan Desktop

Tauri 2 + React desktop shell for Divan.

## Development

```powershell
cd apps/desktop
pnpm install
pnpm desktop:dev
```

## Windows bundle

```powershell
pnpm desktop:build
```

The target installer format is NSIS (`*-setup.exe`). The first shell intentionally implements only local runtime discovery and the operator UI. Divan Core remains authoritative; execution/review/release mutations must be wired through the stable core contract rather than reimplemented in React or Rust.
