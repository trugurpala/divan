# v0.18.3 immutable release evidence

- Version: v0.18.3
- Source commit: 294958620e6382fe10296ab15246e100fab84764
- Implementation PR: https://github.com/trugurpala/divan/pull/63
- Release: https://github.com/trugurpala/divan/releases/tag/v0.18.3
- Release workflow: https://github.com/trugurpala/divan/actions/runs/30583470071
- Evidence date: 2026-07-30

## Identity and required workflows

The lightweight `v0.18.3` tag resolves directly to the source commit above.
GitHub reports Release ID `362734025` as immutable, published, non-draft, and
non-prerelease. The checksum manifest records the same tag and full source
commit.

All required main and publication workflows completed successfully:

- candidate-review: `30583470333`
- compatibility: `30583470402`
- codeql: `30583470074`
- Pages build and deployment: `30583468138`
- quality-gate: `30583470061`
- release: `30583470071`
- scorecard: `30583470222`
- site-tests: `30583470085`
- wiki-sync: `30583470026`

The main quality gate ran 687 tests twice: once with 76% branch coverage and
11 expected Linux platform skips, then through the canonical clean verifier.
Ruff, the Clean Code debt ratchet, mypy across 107 first-party source files,
actionlint, the Agent Skills validator, and Claude Code's strict plugin
validator passed. Compatibility and release canaries passed on Linux, macOS,
and Windows.

## Downloaded asset readback

All seven assets were downloaded again. Recomputed SHA-256 values match both
the GitHub asset digests and the published checksum manifest:

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 565041 | `4052f11bcd6125dcdf94b6c826711573e9ce502a12d81e427f44fd21f81ed734` |
| `divan-project.pyz.sha256` | 84 | `749593069596f9b770f0ce31d1d229611314c238fb5e4173118ac669b197957d` |
| `divan-v0.18.3.sha256` | 575 | `92194a333420146d3cc29eacb85f342727caaa682ad194cc8397679d07aa2cc1` |
| `divan-v0.18.3.spdx.json` | 7898 | `649812592a138fe1fa2938db2c3fb0f18e5d09ce35b2058bb66563c73ebfc0ff` |
| `divan-v0.18.3.zip` | 6332244 | `560f50bedfc7514d3031c14880edb42cd5d2b04466eaa5ed3f0332315262fedd` |
| `divan.pyz` | 11260123 | `a34ef489e0186ee4a5f3e290b7469b445adf22eb10dde9e6564d9245c7d8c00e` |
| `divan.pyz.sha256` | 76 | `b661749cbd9a720fa125acc03b8629c2c30477beacb6d40d83ee569b612a549c` |

The portable project runner embeds source repository
`https://github.com/trugurpala/divan`, version `0.18.3`, ref `v0.18.3`, and
the exact source commit above.

## Provenance and public readback

Strict `gh attestation verify --deny-self-hosted-runners` succeeded for all
seven downloaded assets against `trugurpala/divan`. Pages returned HTTP 200
and exposed v0.18.3. The raw published Wiki Home returned HTTP 200 and exposed
v0.18.3. The default-branch README was also read back.

The first README readback correctly exposed the v0.18.3 source but still named
v0.18.2 as the latest published release. This tracked follow-up records
v0.18.3 as published rather than rewriting the immutable tag.

## Bounded claim

This record proves release identity, downloaded bytes, provenance, automated
host lifecycle canaries, and public convergence. A real local canary then
showed that v0.18.3 could not atomically add implementation and regression-test
artifacts to an existing goal receipt; a common `VERSION` file also caused a
false distinct-project rejection, and a small bugfix composed redundant
workflows. Those findings are fixed in the v0.18.4 source line.

This release evidence does not satisfy the final v1 gate. Only a
privacy-reviewed `valid-clean-room-adoption` receipt produced by a released
runner with real VERIFIED evidence may do that; v1 therefore remains 7/8 here.
