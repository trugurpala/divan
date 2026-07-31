# v0.18.2 immutable release evidence

- Version: v0.18.2
- Source commit: d3a2a41f9b88c3639f9832c24dd898fd8b88cbe4
- Implementation PR: https://github.com/trugurpala/divan/pull/60
- Release: https://github.com/trugurpala/divan/releases/tag/v0.18.2
- Release workflow: https://github.com/trugurpala/divan/actions/runs/30545714518
- Evidence date: 2026-07-30

## Identity and required workflows

The lightweight `v0.18.2` tag resolves directly to the source commit above.
GitHub reports a published, non-draft, non-prerelease Release. The checksum
manifest records the same tag and full source commit.

All required main and publication workflows completed successfully:

- candidate-review: `30545712154`
- compatibility: `30545712293`
- codeql: `30545712211`
- Pages build and deployment: `30545708746`
- quality-gate: `30545716216`
- release: `30545714518`
- scorecard: `30545714383`
- site-tests: `30545714292`
- wiki-sync: `30545714352`

The quality gate passed 646 tests on Linux with 11 expected platform skips,
Ruff, the Clean Code debt ratchet, mypy across 99 first-party source files,
coverage, actionlint, deterministic runners, and final hygiene. Compatibility
and release canaries passed on Linux, macOS, and Windows.

## Downloaded asset readback

All seven assets were downloaded again. Recomputed SHA-256 values match both
the GitHub asset digests and the published checksum manifest:

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 501421 | `cc3ed7f131c49013697a9389681701ad88d7b25fad57cbde8ebb579ca35a17dd` |
| `divan-project.pyz.sha256` | 84 | `03be085ac8dbdfe1c7c00ce55b37b673efaea36f3b271c7bb64c9174d0cf1b4a` |
| `divan-v0.18.2.sha256` | 575 | `fe5079496c21ca365ff5c4de7980647504286cdd94cf3e917a2603e7f59f0f15` |
| `divan-v0.18.2.spdx.json` | 7898 | `5a442b44054003c93d3958173055dc8b6fc3df02948120e4c161e6bbf3dcee7d` |
| `divan-v0.18.2.zip` | 6271440 | `25d18562b458119fd1d03e74979da451f850dd6136535bfd71d2c2eff34b567e` |
| `divan.pyz` | 11196231 | `48620bd57033ee53ef723f1fd6a9d921e66ca1afec04f94281bfa205b31d0c67` |
| `divan.pyz.sha256` | 76 | `e9f529628e638743e2862689a0e20e2ea232874aff0b5135bbccf6c5e7ca1749` |

The source archive opened successfully with 1192 entries. Executing the
downloaded `divan.pyz doctor --json` reported its embedded source as v0.18.2
and produced an actionable next command without mutating the host.

## Provenance and public readback

Strict `gh attestation verify --deny-self-hosted-runners` succeeded for all
seven downloaded assets against `trugurpala/divan`. Pages returned HTTP 200
and exposed v0.18.2. The raw published Wiki Home returned HTTP 200 and exposed
v0.18.2. The release workflow independently waited for those surfaces and ran
the live Chromium interaction check before publishing the immutable Release.

This record proves release identity, downloaded bytes, provenance, automated
host lifecycle canaries, the local progress surface, and public convergence.
It does not prove faster delivery, better model quality, or adoption by an
independent non-owner. Issue #34 therefore remains open and v1 remains 7/8.
