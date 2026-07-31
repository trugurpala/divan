# v1.0.1 Publication Evidence

- Version: v1.0.1
- Source commit: 62f30f39d78be6b15e39f6e2aa9b7c19e7fb0949
- Evidence date: 2026-07-31 UTC

## Authority

- Pull request: https://github.com/trugurpala/divan/pull/69
- Immutable tag and Release:
  https://github.com/trugurpala/divan/releases/tag/v1.0.1
- Published commit: `62f30f39d78be6b15e39f6e2aa9b7c19e7fb0949`
- Release state: non-draft, non-prerelease
- Release workflow:
  https://github.com/trugurpala/divan/actions/runs/30595833748

The lightweight `v1.0.1` tag and Release target resolve to the same
GitHub-verified commit. The Release publishes the exact seven assets produced
by the release workflow.

## Main and publication workflows

Every workflow triggered for the published commit completed successfully:

- quality-gate:
  https://github.com/trugurpala/divan/actions/runs/30595833787
- compatibility:
  https://github.com/trugurpala/divan/actions/runs/30595833737
- codeql:
  https://github.com/trugurpala/divan/actions/runs/30595833777
- scorecard:
  https://github.com/trugurpala/divan/actions/runs/30595833847
- site-tests:
  https://github.com/trugurpala/divan/actions/runs/30595833743
- wiki-sync:
  https://github.com/trugurpala/divan/actions/runs/30595833842
- Pages:
  https://github.com/trugurpala/divan/actions/runs/30595832660
- release:
  https://github.com/trugurpala/divan/actions/runs/30595833748

The canonical local verification ran 698 tests with 14 expected
platform-specific skips and ended with clean hygiene and clean-code gates. PR
#69 repeated two full quality runs; CodeQL, dependency review, Playwright, Wiki,
and the Linux/macOS/Windows Claude/Codex compatibility matrix also passed. The
release workflow separately verified the standalone bootstrap on clean Codex
hosts, waited for Pages and Wiki, checked the live site in Chromium, and then
published the Release.

## Downloaded asset readback

All seven Release assets were downloaded into a new local temporary directory.
Every locally recomputed SHA-256 matched the master manifest and GitHub's asset
digest. Both sidecars matched their runner. Strict
`gh attestation verify --deny-self-hosted-runners` verification succeeded for
every asset.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 570094 | `14586a276797fd136f890bcc7076138094961b3b66f2e4ca8c2e8a68c2ad70ea` |
| `divan-project.pyz.sha256` | 84 | `7cc5665cdf19652792a54beef0244f1ae7e28607b1a628a9c0324fc6b595139f` |
| `divan-v1.0.1.sha256` | 572 | `760e8c95f5b83115ea410a927a18598089fe4ea55a2e081b0028068681a70041` |
| `divan-v1.0.1.spdx.json` | 7896 | `6f7796ca240efaacaeaaa8defd09802be64f74e6c28e4c0ac910f91821fdc4ae` |
| `divan-v1.0.1.zip` | 6350736 | `c00c796060e17195d8f825ba1115cfa2b1058cf82988c34421f81eb88e94a70f` |
| `divan.pyz` | 11265901 | `4f41890776d8e24fae5d5d2d411fd565ab2a88f8e9c5ae270ddf87b76c2af9bb` |
| `divan.pyz.sha256` | 76 | `2c384e1ac0eb3e22075eff7489cae4b3f1345d45a985625614f99985814d21fd` |

## Real Windows/Codex upgrade

The downloaded and checksum-verified `divan.pyz` was run against the existing
native Codex installation on Windows 11:

1. `doctor --host codex --json` reported only the old marketplace ref.
2. The write-free update preview listed only the five Divan packages and the
   Divan marketplace.
3. `update --host codex --ref v1.0.1 --execute` completed as `VERIFIED` and
   produced transaction `upgrade-20260731T012044Z-cc3ff7ca.json`.
4. A second execute returned `NO-OP - installed Divan already matches target`.
5. Final doctor returned `healthy` with no issues.

The installed marketplace resolves to the published commit and exact
`v1.0.1` tag. All five packages are enabled and all 41 skills are present.
Unrelated marketplaces and plugins remained installed.

This proves the packaged upgrade defect reproduced by v1.0.0 is repaired for
this bounded Windows/Codex path. It does not claim universal host coverage,
speed gain, quality improvement, third-party endorsement, or market adoption.
