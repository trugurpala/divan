# Divan v1.3.7

### Added

- Added an aligned release-surface preparation for `v1.3.7` with host-state and
  onboarding surfaces synchronized as immutable source for this branch.

### Changed

- Synchronized public-facing surfaces that should resolve to the current release:
  README files (including bilingual variants), onboarding docs, `docs/Home`,
  marketplace manifests, installer defaults, and runtime version markers.
- Refreshed install and verification command examples so they point to the
  `v1.3.7` release line.

### Fixed

- Eliminated remaining `v1.3.6` source references in public install and host
  command texts.
- Removed stale onboarding reference drift that could appear after a `VERSION`
  bump when only runtime surfaces were updated.

### Verification

- `scripts/release.py --check`, `python scripts/prose.py --check --json`, and full
  `python scripts/verify.py` pass after 1.3.7 surface synchronization.

## Sabitlenmiş kurulum

- Claude Code/Desktop Code + Codex: `python scripts/divan.py install --host both --ref v1.3.7 --execute`.
- Önce dry-run için aynı komutu `--execute` olmadan çalıştırın.
- Eski-host fallback varlıkları: `divan-v1.3.7.zip` ve `divan-v1.3.7.sha256`.

Yükseltmeden önce [kurulum](https://github.com/trugurpala/divan/wiki/Kurulum) ve [kaldırma/geri alma](https://github.com/trugurpala/divan/wiki/Kaldirma) rehberlerini okuyun.
