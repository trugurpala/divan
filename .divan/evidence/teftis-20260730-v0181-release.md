# v0.18.1 immutable release evidence

- Version: v0.18.1
- Source commit: f367de92e09b4f56e205d7e2883d988b3b4d2797
- Implementation PR: https://github.com/trugurpala/divan/pull/58
- Release: https://github.com/trugurpala/divan/releases/tag/v0.18.1
- Release workflow: https://github.com/trugurpala/divan/actions/runs/30500376337
- Evidence date: 2026-07-30

## Identity

The lightweight `v0.18.1` tag resolves directly to the source commit above.
GitHub reports the Release as published, immutable, non-draft, and
non-prerelease. The checksum manifest independently records the same tag and
source commit.

## Required main and publication workflows

All nine recorded runs completed successfully at the source commit:

- candidate-review: `30500376313`
- wiki-sync: `30500376336`
- scorecard: `30500376310`
- site-tests: `30500376344`
- compatibility: `30500376308`
- codeql: `30500376316`
- release: `30500376337`
- quality-gate: `30500376321`
- Pages build and deployment: `30500375882`

The quality gate passed Ruff, the Clean Code debt ratchet, mypy across 90
first-party source files, and 580 tests with 13 expected platform skips and
77% branch coverage. The release workflow also passed Codex lifecycle canaries
on Ubuntu, macOS, and Windows.

## Downloaded asset readback

Every asset was downloaded again. Recomputed SHA-256 values match the GitHub
asset digest and the published checksum manifests:

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 398769 | `42beb7d4c546ddfd9f8eef6e742059c6b8c4b5d8e51df46a9335c591e84dc017` |
| `divan-project.pyz.sha256` | 84 | `5d0c7eed0ab5ba01955ffa082abad28d73dca6620d85ced1457fc003f30e8879` |
| `divan-v0.18.1.sha256` | 416 | `d2c1c0be0b58f1d8335a5a2275680c80b7e211e437b22bcd025db2984a553dec` |
| `divan-v0.18.1.spdx.json` | 6832 | `c76e60ab1bc8addf3d9b81e3ba1cddc985fdd563675065c3a202b1633d1ccee7` |
| `divan-v0.18.1.zip` | 6174814 | `a5892629e98866c0b7774f6c1e6f594d058d074e8a0ee7d1dd775a18d5454950` |

The checksum manifest records tag `v0.18.1` and source commit `f367de92`.
The SBOM is SPDX 2.3, uses the CC0-1.0 data license, and names
`Divan-v0.18.1`.

## Attestations

Strict `gh attestation verify --deny-self-hosted-runners` succeeded for all
five downloaded assets against repository `trugurpala/divan`. This binds the
published bytes to the repository's trusted release workflow and source
commit.

## Remote Windows auto-install canary

The canary used the public `v0.18.1` ref and an isolated Codex skills/state
root. The simulated AppX launch barrier was diagnosed as `access-denied`, and
doctor emitted one exact next command for the explicit `auto` profile.

The checksum-backed remote install then:

- selected `verified-skill-fallback`, not native;
- recorded version `0.18.1`, ref `v0.18.1`, source commit `f367de92`, and
  archive SHA-256 `a5892629...`;
- discovered exactly 41 manifest rows and 41 Divan skill directories from a
  fresh process;
- verified every installed target and kept an unrelated user skill;
- reported native commands, agents, hooks, MCP configuration, and native
  lifecycle as unavailable.

Canonical rollback removed only the 41 Divan-owned directories. The unrelated
skill remained and the ownership pointer stayed as an audit trail.

## Public surfaces and bounded claims

The first public readback returned HTTP 200 for both Pages and Wiki and exposed
v0.18.1. It also exposed stale “latest published v0.18.0 / release candidate”
labels. This publication-truth change corrects the tracked README, Pages, and
Wiki sources; their normal protected workflows must converge before issue #57
is closed.

This record proves release identity, assets, provenance, automated host
lifecycle canaries, the remote checksum-backed fallback, and its safe removal.
It does not prove faster delivery, better model quality, native capabilities
inside fallback, or adoption by an independent non-owner. Issue #34 therefore
remains open and the v1 score stays 7/8.
