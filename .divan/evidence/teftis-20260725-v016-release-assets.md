# v0.16.0 post-merge release asset evidence

Verified on 2026-07-25 for
[issue #35](https://github.com/trugurpala/divan/issues/35).

## Immutable release identity

- Release: https://github.com/trugurpala/divan/releases/tag/v0.16.0
- Release ID: `359124924`
- Tag and source commit:
  `v0.16.0` → `5513e73d5faa8657a22d813ecfec763a6089bea0`
- Release workflow:
  https://github.com/trugurpala/divan/actions/runs/30073144850
- Release workflow conclusion: `success`
- Published at: `2026-07-24T06:45:42Z`
- Draft/prerelease: `false` / `false`

## Recomputed assets

Every asset below was downloaded again from the immutable release URL. The
SHA-256 values were recomputed from the downloaded bytes and matched the digest
returned by the GitHub Releases API.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 341459 | `f67a089e4af7638208f3f81b987116d6fb6cd180422c371d08db2115a7681758` |
| `divan-project.pyz.sha256` | 84 | `33107a1e879e2d85c7cb788399354ed83eed2330b380a26406683d58c41e4e27` |
| `divan-v0.16.0.sha256` | 416 | `c24dbe51df4d953b3c01c1ca8d8b67797d2017ca9dda9f739940b71160ee5a37` |
| `divan-v0.16.0.spdx.json` | 6843 | `b4af718972ea8319eff987b1077421ee22a4bf75cd9c9cbc4e5b00f0d98163b1` |
| `divan-v0.16.0.zip` | 6024428 | `5c5ed8fdcc76fe24de634da37fa070d1e3d935048c6864413bbb9225465489a7` |

## Cross-checks

- `divan-v0.16.0.sha256` listed the exact recomputed digests for the ZIP, SPDX
  SBOM, runner, and runner checksum. It also bound
  `source_commit=5513e73d5faa8657a22d813ecfec763a6089bea0` and `tag=v0.16.0`.
- `sha256sum --check divan-project.pyz.sha256` returned
  `divan-project.pyz: OK`.
- The ZIP contained `divan-v0.16.0/VERSION` with exact content `0.16.0`.
- The runner executed `--help` and exposed the Project OS command surface. Its
  embedded `divan-project-source.json` contained schema 2, version `0.16.0`,
  ref `v0.16.0`, and the immutable source commit above.
- The SBOM parsed as SPDX `SPDX-2.3`, was named `Divan-v0.16.0`, and contained
  five packages.

## Attestations

The GitHub Artifact Attestations endpoint returned HTTP 200 and two
attestations for each of the five asset digests:

- `https://in-toto.io/attestation/release/v0.2`
- `https://slsa.dev/provenance/v1`

The SLSA statement named `.github/workflows/release.yml` from
`refs/heads/main` and listed all five assets with the recomputed SHA-256
subjects. The release statement bound the same assets to
`pkg:github/trugurpala/divan@v0.16.0` and source SHA-1
`5513e73d5faa8657a22d813ecfec763a6089bea0`.

Canonical query pattern:
`https://api.github.com/repos/trugurpala/divan/attestations/sha256:<digest>`.
Temporary signed bundle URLs were intentionally not recorded.

## Live readback

- https://trugurpala.github.io/divan/ returned `v0.16.0` and
  `Fermanını seç`.
- https://raw.githubusercontent.com/wiki/trugurpala/divan/Home.md returned
  `v0.16.0` and `Fermanını seç`.

## Repository verification

The branch was committed before the complete suite because the Project OS
development-source contract intentionally rejects a dirty checkout.

- `python -m unittest discover -s tests -v`: 495 passed, 11
  platform-specific skips.
- Branch coverage: 74%, above the enforced 64% floor.
- Ruff: all checks passed.
- mypy: no issues in 61 source files.
- Clean Code: the exact-symbol debt baseline remained valid.
- Hygiene, 5-package/41-skill validation, handoff, catalog, v1, release,
  20-page Wiki, Company OS, and 4-skill/13-case eval contract checks passed.
- `scripts/v1.py --check` remained valid at 7/8; no gate file changed.
- Company OS classified every changed path and `git diff --check` passed.

## Verification boundary

This record closes the asset/checksum/SBOM/attestation gap for issue #35. No
owner canary, transactional global-host update, or non-owner adoption task was
executed in this review. No adoption receipt is inferred from release
publication. The independent-adoption gate remains pending and v1 remains 7/8.
