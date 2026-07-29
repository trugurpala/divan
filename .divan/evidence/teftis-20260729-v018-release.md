# v0.18.0 immutable release evidence

- Version: v0.18.0
- Source commit: 3bbbd95881a7c33f64e3e9f8d23824e3eef8977e
- Implementation PR: https://github.com/trugurpala/divan/pull/54
- Release PR: https://github.com/trugurpala/divan/pull/55
- Release: https://github.com/trugurpala/divan/releases/tag/v0.18.0
- Release workflow: https://github.com/trugurpala/divan/actions/runs/30493811167
- Evidence date: 2026-07-29

## Identity

The lightweight `v0.18.0` tag resolves directly to the source commit above.
GitHub reports the Release as published, non-draft, and non-prerelease. The
checksum manifest independently records the same tag and source commit.

## Required main and publication workflows

All recorded runs completed successfully at the source commit:

- release: `30493811167`
- codeql: `30493811208`
- scorecard: `30493811193`
- quality-gate: `30493811197`
- site-tests: `30493811169`
- compatibility: `30493811211`
- wiki-sync: `30493811185`
- Pages build and deployment: `30493810388`

The release workflow includes clean Codex install, discovery, and removal
canaries on Linux, macOS, and Windows plus the release gates. This is host
lifecycle evidence; it is not independent-user adoption evidence.

## Downloaded asset readback

Every asset was downloaded again. Recomputed SHA-256 values match the GitHub
asset digest and the published checksum manifests:

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 398769 | `e9ab469b958cfb3bf1cd99aa0cba540283525a878c2169271d21f36f5d150f02` |
| `divan-project.pyz.sha256` | 84 | `520246a1f0858c75de595904bab6c60f8db31b472d3ca4d54cd316f34e20b46f` |
| `divan-v0.18.0.sha256` | 416 | `306e1750dc98a787edc972a41806dbd0b21b57372b5aaa7a03dc8d3974ff2be2` |
| `divan-v0.18.0.spdx.json` | 6832 | `5adf0ebda2ca10fcf0e969f4c1479f30a4865c8d0c12a25fd07350c76566af40` |
| `divan-v0.18.0.zip` | 6150930 | `86a7c8f0304badf8d461817db7a426abf4aab204d8a38d3fc7412fef45b24e39` |

The ZIP contains `divan-v0.18.0/VERSION` with `0.18.0`. The SPDX 2.3 SBOM
names `Divan-v0.18.0`, records five packages, and binds its document namespace
to the source commit. The downloaded project runner returns `status: valid`.

## Attestations

Strict `gh attestation verify` succeeded for all five assets with:

- repository `trugurpala/divan`;
- signer workflow `trugurpala/divan/.github/workflows/release.yml`;
- source digest `3bbbd95881a7c33f64e3e9f8d23824e3eef8977e`;
- source ref `refs/heads/main`.

The GitHub attestations API returns exactly two records per asset:
`https://in-toto.io/attestation/release/v0.2` and
`https://slsa.dev/provenance/v1`.

## Public surfaces and bounded claims

Pages and Wiki returned HTTP 200 and exposed v0.18.0 plus Nizâm-ı Sefer. The
first post-release readback also exposed stale “candidate/latest v0.17.1”
labels; the publication-evidence PR corrects those versioned sources and the
normal Pages/Wiki workflows must converge before that PR is complete.

This record proves release identity, assets, provenance, automated host
lifecycle canaries, and public-surface convergence. It does not prove faster
delivery, better model quality, support beyond the evidence-backed host tier,
or adoption by an independent non-owner. Issue #34 therefore remains open and
the v1 score stays 7/8.
