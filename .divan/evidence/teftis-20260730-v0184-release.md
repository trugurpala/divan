# v0.18.4 immutable release evidence

- Version: v0.18.4
- Source commit: 2eb36bdd24e383c90e1e62e53ad1c6c5d5730000
- Implementation PR: https://github.com/trugurpala/divan/pull/64
- Release: https://github.com/trugurpala/divan/releases/tag/v0.18.4
- Release workflow: https://github.com/trugurpala/divan/actions/runs/30586836114
- Evidence date: 2026-07-30

## Identity and required workflows

The lightweight `v0.18.4` tag resolves directly to the source commit above.
GitHub reports the Release as immutable, published, non-draft, and
non-prerelease. The checksum manifest records the same tag and full source
commit.

All required main and publication workflows completed successfully:

- candidate-review: `30586836106`
- compatibility: `30586836193`
- codeql: `30586836132`
- Pages build and deployment: `30586835491`
- quality-gate: `30586836154`
- release: `30586836114`
- scorecard: `30586836088`
- site-tests: `30586836171`
- wiki-sync: `30586836196`

The main quality gate ran 695 tests twice, with 76% branch coverage in the
instrumented run. Ruff, the Clean Code debt ratchet, mypy across 107
first-party source files, actionlint, the Agent Skills validator, and Claude
Code's strict plugin validator passed. Compatibility and release canaries
passed on Linux, macOS, and Windows.

## Downloaded asset readback

All seven assets were downloaded again. Recomputed SHA-256 values match both
the GitHub asset digests and the published checksum manifest:

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 569525 | `ef4a1d71148a59b6c2dd659a9c4f8df762186d1a8dcd1616173bc5f5a725060a` |
| `divan-project.pyz.sha256` | 84 | `a7bba08644d723197472100058e36ff95dab7d4a5b80975e821e1c5c24c5d38f` |
| `divan-v0.18.4.sha256` | 575 | `ef01f24eeb194e9e93333ff180feeed0a2b07f40189c93b5f0255b527857c438` |
| `divan-v0.18.4.spdx.json` | 7898 | `f77ebdbc3eb543a4fe53ef8b3a98f9dd47139a73427b175a6c07cf2dae99df87` |
| `divan-v0.18.4.zip` | 6339441 | `717d796031dd43e1b7d958beaa4407a8c54029be6ddaa97fd8933ace057b2963` |
| `divan.pyz` | 11264607 | `babb3daee39044728c704016e9af468f4528f14455e909e2f6697c4808d1f948` |
| `divan.pyz.sha256` | 76 | `a71b39a0a103967517275759c6cfa9e7e712554d3b8a2592d03b5e7d28a956f3` |

The portable project runner embeds source repository
`https://github.com/trugurpala/divan`, version `0.18.4`, ref `v0.18.4`, and
the exact source commit above.

## Provenance and public readback

Strict `gh attestation verify --deny-self-hosted-runners` succeeded for all
seven downloaded assets against `trugurpala/divan`. Pages returned HTTP 200
and exposed v0.18.4. The raw published Wiki Home returned HTTP 200 and exposed
v0.18.4. The default-branch README was also read back.

## Clean-room finding

The released runner was installed into a separate local Git repository and
correctly recognized the real VERIFIED goal and its implementation, regression
test, and verification artifacts. Its write-free preview selected the bounded
native test command.

Execution then failed closed before running project tests because Windows
resolved the extensionless npm `codex` shim first and returned access denied,
while the adjacent `codex.cmd --version` command passed. The repository's own
Windows lifecycle canaries remained green because they did not exercise this
clean-room host-version probe. The v0.18.5 source line adds a regression-tested
Windows shim resolver.

## Bounded claim

This record proves v0.18.4 release identity, downloaded bytes, provenance,
automated host lifecycle canaries, and public convergence. It does not satisfy
the final v1 gate because the released clean-room proof stopped before sealing
a valid receipt. v1 therefore remains 7/8 here.
