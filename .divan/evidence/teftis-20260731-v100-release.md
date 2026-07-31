# v1.0.0 Publication Evidence

- Version: v1.0.0
- Source commit: 2f73e0514d97d4ec9597b3d313f20c82d7770b77
- Evidence date: 2026-07-31 UTC

## Authority

- Pull request: https://github.com/trugurpala/divan/pull/67
- Immutable tag and Release:
  https://github.com/trugurpala/divan/releases/tag/v1.0.0
- Published commit: `2f73e0514d97d4ec9597b3d313f20c82d7770b77`
- Release state: non-draft, non-prerelease
- Release workflow:
  https://github.com/trugurpala/divan/actions/runs/30592062578

The `main` head, lightweight `v1.0.0` tag, Release target, master checksum
identity, bootstrap identity, and project-runner identity all resolve to the
same commit. Both runners report version `1.0.0`, ref `v1.0.0`, and the
canonical repository.

## Main and publication workflows

Every workflow triggered for the published commit completed successfully:

- quality-gate:
  https://github.com/trugurpala/divan/actions/runs/30592062579
- compatibility:
  https://github.com/trugurpala/divan/actions/runs/30592062565
- codeql:
  https://github.com/trugurpala/divan/actions/runs/30592062608
- scorecard:
  https://github.com/trugurpala/divan/actions/runs/30592062561
- site-tests:
  https://github.com/trugurpala/divan/actions/runs/30592062569
- wiki-sync:
  https://github.com/trugurpala/divan/actions/runs/30592062573
- Pages:
  https://github.com/trugurpala/divan/actions/runs/30592062254
- release:
  https://github.com/trugurpala/divan/actions/runs/30592062578

The canonical local verification ran 697 tests with 14 expected
platform-specific skips and ended with a clean hygiene gate. The main quality
workflow repeated the full local gates and both official schema validators.
The release workflow separately passed clean Codex lifecycle checks on
Windows, macOS, and Linux, waited for Pages and Wiki, and verified the live
site in Chromium before publication.

## Downloaded asset readback

All seven Release assets were downloaded into a new local temporary directory.
Every locally recomputed SHA-256 matched the master manifest and GitHub's asset
digest. Both sidecars matched their runner. Strict
`gh attestation verify --deny-self-hosted-runners` verification succeeded for
every asset.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 570094 | `03a2c0ae4796a88fa53838001e2d665935f615723d6f858c29703f191fccfbe1` |
| `divan-project.pyz.sha256` | 84 | `0c1bac2bcc61ccf65a512e546e0c9f33208822afaf021443bcd94e979b5b0b8d` |
| `divan-v1.0.0.sha256` | 572 | `2d5b1a2316fcdbfe14760e9c8a7a15262c9cbcfe1460ffd87b6e76a158f50ff0` |
| `divan-v1.0.0.spdx.json` | 7896 | `2daaa5da702c4b14c9a07fc5ee07e14a2ac538e75f6bb71cda63fbfaa75e87d0` |
| `divan-v1.0.0.zip` | 6346785 | `c6ffeac8e7f5e75bc1dac2720d87e4a8566876863fefe4fc9374fea043dbb82b` |
| `divan.pyz` | 11265172 | `263f229f85aac704b7bdcf27594c05970e06b01dfcdb4907b3f4ac599e729daa` |
| `divan.pyz.sha256` | 76 | `543a18d81c7c5ed6df497b2fa09a52a2742783440433202a9e06eef6a6598b0d` |

The SPDX document names Divan v1.0.0, contains exactly the five marketplace
packages, and binds its namespace to the published commit.

## Stable claim boundary

v1.0.0 freezes the tested public contract: one Divan repository, five modular
packages, 41 skills, Claude Code and Codex host lifecycles, the stdlib-only
Divan Engine, owner-first Divan Nizamı governance, the installed Divan Project
Contract, evidence-backed goals, and local Seyir.

The 8/8 score and clean-room receipt prove this bounded technical contract.
They do not prove an independent-user count, third-party endorsement, market
adoption, speed gain, revenue increase, or quality improvement.
