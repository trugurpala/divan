# v0.18.5 Publication Evidence

- Version: v0.18.5
- Source commit: f65d62a857e744dce0b370414e6686b9c49258d7
- Evidence date: 2026-07-30 UTC

## Authority

- Pull request: https://github.com/trugurpala/divan/pull/65
- Immutable tag and Release:
  https://github.com/trugurpala/divan/releases/tag/v0.18.5
- Published commit: `f65d62a857e744dce0b370414e6686b9c49258d7`
- Release state: immutable, non-draft, non-prerelease
- Release workflow:
  https://github.com/trugurpala/divan/actions/runs/30588385348

The tag, Release target, and embedded portable-runner identity all resolve to
the same commit. The project runner reports version `0.18.5`, ref `v0.18.5`,
the canonical repository, and the published commit.

## Main and publication workflows

Every workflow triggered for the published commit completed successfully:

- quality-gate:
  https://github.com/trugurpala/divan/actions/runs/30588385273
- compatibility:
  https://github.com/trugurpala/divan/actions/runs/30588385302
- codeql:
  https://github.com/trugurpala/divan/actions/runs/30588385342
- scorecard:
  https://github.com/trugurpala/divan/actions/runs/30588385274
- site-tests:
  https://github.com/trugurpala/divan/actions/runs/30588385287
- wiki-sync:
  https://github.com/trugurpala/divan/actions/runs/30588385286
- Pages:
  https://github.com/trugurpala/divan/actions/runs/30588384416
- release:
  https://github.com/trugurpala/divan/actions/runs/30588385348

The main quality job ran 697 tests twice with 14 expected platform-specific
skips and measured 76% line coverage. Its observed wall-clock duration was
7 minutes 3 seconds. The release job separately passed native Codex lifecycle
gates on Windows, macOS, and Linux before publication.

## Downloaded asset readback

All seven Release assets were downloaded into a new local temporary directory.
Each locally recomputed SHA-256 matched GitHub's asset digest. The two sidecars
and the master checksum manifest also matched. Strict
`gh attestation verify --deny-self-hosted-runners` verification succeeded for
every asset.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 570097 | `a949277c371ad245ed48d4e992056eeaf807a5d6e7c601719739b89a8b4e5870` |
| `divan-project.pyz.sha256` | 84 | `6e22e6a4de6c879742333a78cb2a8239d79d755be53a9c5b890ac1eef2d73a33` |
| `divan-v0.18.5.sha256` | 575 | `19f2242f7d00210b29ba59ba9c796d9dc97c586628c1fcd166df8218bd2a6cc1` |
| `divan-v0.18.5.spdx.json` | 7898 | `e235559b7e3540a60c96cd20ad5433c29881bc8b3cc2db7bb6ce1c2d29171dd6` |
| `divan-v0.18.5.zip` | 6342828 | `c302acc6a40a75515d99c31607946a26f723b624f2e2c2e57421e155fb258e89` |
| `divan.pyz` | 11265179 | `0d7d3b815a9cd8f5980a2673fe1b17deda14e0b2b5519fb7e2c5f949ae88dbf7` |
| `divan.pyz.sha256` | 76 | `c970bd352d64f8cef6b6cd40407adfd7287c1fa19d52222f9980da6d9a79db26` |

## Live publication readback

Pages and Wiki returned v0.18.5 and the release workflow's live Chromium check
passed. A separate readback found that their human-facing “latest published”
label still named v0.18.4 even though the immutable v0.18.5 Release existed.
The clean-room evidence change updates README, Pages, Wiki, roadmap, and
progress surfaces to v0.18.5 instead of hiding that one-release lag.

## Clean-room result

The released `divan-project.pyz` initialized a separate Git project at v0.18.5,
recognized its existing goal as `VERIFIED`, observed Codex `0.146.0` through
the Windows `.cmd` launcher, and ran one bounded test-class check successfully.
Both generated receipt formats re-verified offline as
`valid-clean-room-adoption` with `eligible_for_v1: true`.

- JSON receipt:
  `.divan/evidence/verified-clean-room-adoption-v0185.json`
- Markdown receipt:
  `.divan/evidence/verified-clean-room-adoption-v0185.md`
- Source/committed JSON SHA-256:
  `f1fad0e85321428f89bddefe9f871514ef71811f1d7b1c310dd6219c4ab31d8c`
- Source/committed Markdown SHA-256:
  `34af5477123940788922fb8c8115bf208acad8fae82f097f03158595a94813df`

The receipts contain no username, email, absolute path, remote URL, token,
secret, raw command line, or raw command output. This closes the bounded
machine-verifiable clean-room preparation gate. It does not prove an
independent-user count, endorsement, market adoption, speed gain, or quality
improvement.
