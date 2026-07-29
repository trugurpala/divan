# v0.17.0 immutable release evidence

Verified on 2026-07-29 after
[PR #49](https://github.com/trugurpala/divan/pull/49).

## Publication identity

- Version: v0.17.0
- Source commit: 8b711b6f0ebb696ce971d83c90833bb59acf3c34
- Source tree: `9f35f1989e26e1f9b38dceaaa2485b4120344283`
- Release: https://github.com/trugurpala/divan/releases/tag/v0.17.0
- Release ID: `361750779`
- Release workflow:
  https://github.com/trugurpala/divan/actions/runs/30453034011
- Release workflow conclusion: `success`
- Published at: `2026-07-29T12:48:47Z`
- Draft/prerelease: `false` / `false`

The lightweight tag `v0.17.0` and the Release target both resolve to the exact
source commit above.

## Pull-request and main gates

All seven pull-request workflows for head
`8c5429025f779f3ab018095b0da38b6ed999e19a` completed successfully before the
expected-head-locked squash merge:

- candidate-review `30452696079`
- quality-gate `30452696336`
- compatibility `30452696911`
- site-tests `30452696943`
- codeql `30452697090`
- dependency-review `30452700163`
- wiki-sync `30452700287`

The merged commit then completed the publication surface:

- candidate-review `30453034022`
- codeql `30453034030`
- compatibility `30453034010`
- quality-gate `30453034067`
- release `30453034011`
- scorecard `30453034039`
- site-tests `30453033999`
- wiki-sync `30453034046`
- Pages build and deployment `30453033150`

The release matrix passed Codex install/discover/remove on Linux, macOS, and
Windows. Its publish job passed repository gates, official schema validators,
Pages/Wiki convergence, live Chromium interaction, release creation, asset
attestation, and immutable release verification.

## Recomputed assets

Every asset was downloaded from the public Release URL. The SHA-256 values
below were recomputed from those bytes and matched both GitHub's digest field
and the published checksum manifests.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 374149 | `2550621de8dae91ddd76136f1f959aa7ff58660e302512f163581f97dd24d2a9` |
| `divan-project.pyz.sha256` | 84 | `0b315e9248f0e30abde1b6ce23d9db9d0761d88b63daee406c2448940b9be3ea` |
| `divan-v0.17.0.sha256` | 416 | `9eed4482403acaddd022541464d04e25bfc9aaa70283903270d9502a0ceb1a7d` |
| `divan-v0.17.0.spdx.json` | 6830 | `55d71529f826ea9c0bd336b6b0b3f18dfba3d4e29e5764fb927c2489863b4b20` |
| `divan-v0.17.0.zip` | 6101434 | `1d563d914d25ab35267f0e758632a8a6ce1db3e7a9a93a7cf60485e3c31a98f0` |

The release checksum manifest binds the ZIP, SPDX SBOM, runner, runner
checksum, `source_commit=8b711b6f0ebb696ce971d83c90833bb59acf3c34`,
and `tag=v0.17.0`.

## Package inspection

- The ZIP contains `divan-v0.17.0/VERSION` with exact content `0.17.0`.
- The standalone runner validates nine modules, 12 roles, 11 workflows, 18
  framework records, and 17 impact rules.
- Its schema-2 source envelope binds version `0.17.0`, ref `v0.17.0`, repository
  `https://github.com/trugurpala/divan`, and the immutable source commit.
- The SBOM parses as SPDX `SPDX-2.3` with data license `CC0-1.0`, five packages,
  and a document namespace bound to the release commit.

## Attestations

GitHub's Artifact Attestations endpoint returned two attestations for each of
the five recomputed asset digests:

- `https://in-toto.io/attestation/release/v0.2`
- `https://slsa.dev/provenance/v1`

Temporary signed bundle URLs are intentionally not recorded.

## Live readback and public-truth repair

- GitHub Pages returned HTTP 200 and exposed `v0.17.0`, `Hükümdar`, and Divan
  Engine.
- The Wiki Home and Divan Engine sources exposed `v0.17.0`, the nine-module
  contract, and Hükümdar-first authority.
- The first independent readback also caught stale candidate wording that still
  named v0.16.0 as the latest published release. The publication-truth
  follow-up updates README, Pages, Wiki, roadmap, install, changelog, and
  progress sources together. That correction does not move the immutable tag
  or replace any Release asset.

## Verification boundary

Publication proves the release identity, package bytes, supply-chain metadata,
cross-platform release gates, and public delivery surfaces. It does not prove a
quality multiplier or independent adoption. No owner canary or maintainer
fixture closes issue #34; v1 remains 7/8 until a non-owner produces
reproducible, privacy-bounded evidence.
