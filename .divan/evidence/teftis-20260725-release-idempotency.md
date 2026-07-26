# Immutable release idempotency evidence

Verified on 2026-07-25 for
[issue #38](https://github.com/trugurpala/divan/issues/38).

## Regression

The first post-release documentation merges exposed a release workflow
regression:

- [run 30130364496](https://github.com/trugurpala/divan/actions/runs/30130364496)
  failed for `main` commit
  `70262a22f52f986e847887de780af2ed74a0ab50`.
- [run 30130917879](https://github.com/trugurpala/divan/actions/runs/30130917879)
  reproduced the failure for `main` commit
  `3d14d49730e2fc000555ead24912819ef70aad71`.
- Publish job `89603338526` stopped at
  `Sürüm notunu üret ve etiketi/Release sayfasını eşitle` with:
  `HATA: v0.16.0 etiketi 5513e73d5faa8657a22d813ecfec763a6089bea0
  commit'inde; 70262a22f52f986e847887de780af2ed74a0ab50 uzerine
  tasinmayacak.`

The workflow correctly refused to move the immutable tag, but it selected
current `GITHUB_SHA` before checking whether that version was already
published. Every same-version `main` commit therefore failed instead of
verifying the existing Release.

## Repair

[PR #39](https://github.com/trugurpala/divan/pull/39) implemented two explicit
release modes and merged as
`da5c2a7c30f77a60706520b7ad5f0eafa21a8e82`:

- A missing version tag builds and publishes from current `GITHUB_SHA`.
- An existing version tag must be an ancestor of current `main`. The workflow
  checks out that immutable commit in a detached temporary worktree, runs the
  tagged release/runner/SBOM builders, and compares all five assets
  byte-for-byte with the existing Release.
- `TZ=UTC` makes Git ZIP timestamps deterministic across environments.
- A Release that already exists sets `published_release=true`, so provenance
  attestation is skipped rather than duplicated.
- No `--clobber` or tag movement path was introduced.

## Test-first and local verification

- The new workflow regression test failed first because tagged-source
  reconstruction and the `published_release` contract did not exist.
- A second red test exposed timezone-sensitive ZIP headers; it passed after
  `TZ=UTC` became an explicit workflow environment contract.
- `python -m unittest tests.test_workflows -v`: 15 passed.
- `python -m unittest discover -s tests -p 'test_*.py'`: 496 passed, 11
  platform-specific skips.
- Branch coverage: 74%, above the enforced 64% floor.
- Ruff, mypy across 61 source files, Clean Code, actionlint 1.7.10, hygiene,
  standards, handoff, Company OS, release, Wiki, catalog, v1, and eval
  contract checks passed.
- A local detached worktree at the immutable tag regenerated all five
  `v0.16.0` assets. With `TZ=UTC`, every byte matched the downloaded Release
  asset.
- Company OS classified every changed path with no unclassified path.

## Pull request and main verification

All PR checks passed:

| Workflow | Run |
|---|---:|
| Quality Gate | `30131472555` |
| CodeQL | `30131472604` |
| Site Tests | `30131472539` |
| Dependency Review | `30131472619` |

All workflows triggered by merge commit `da5c2a7c` passed:

| Workflow | Run |
|---|---:|
| Release | [`30131579254`](https://github.com/trugurpala/divan/actions/runs/30131579254) |
| Quality Gate | `30131579256` |
| CodeQL | `30131579255` |
| Site Tests | `30131579253` |
| Scorecard | `30131579294` |
| Pages build and deployment | `30131579005` |

In release publish job `89607060446`, the three clean-host jobs passed, asset
generation passed, the already-published attestation step was skipped, and the
immutable publish/verify step passed. Its final readback was:
`v0.16.0 Release varliklari byte-byte dogrulandi; hicbir varlik
degistirilmedi.`

## Immutable post-merge readback

The tag still resolves to
`5513e73d5faa8657a22d813ecfec763a6089bea0`. All five assets were downloaded
again after the successful main workflow; their recomputed digests still
matched the GitHub Releases API:

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 341459 | `f67a089e4af7638208f3f81b987116d6fb6cd180422c371d08db2115a7681758` |
| `divan-project.pyz.sha256` | 84 | `33107a1e879e2d85c7cb788399354ed83eed2330b380a26406683d58c41e4e27` |
| `divan-v0.16.0.sha256` | 416 | `c24dbe51df4d953b3c01c1ca8d8b67797d2017ca9dda9f739940b71160ee5a37` |
| `divan-v0.16.0.spdx.json` | 6843 | `b4af718972ea8319eff987b1077421ee22a4bf75cd9c9cbc4e5b00f0d98163b1` |
| `divan-v0.16.0.zip` | 6024428 | `5c5ed8fdcc76fe24de634da37fa070d1e3d935048c6864413bbb9225465489a7` |

The Artifact Attestations endpoint still returned exactly two attestations for
each asset digest, proving that the successful idempotent run created no
duplicate attestation. Pages and Wiki still returned `v0.16.0` and
`Fermanını seç`.

## Verification boundary

Issue #38 is closed by the merged and post-merge-proven repair. This change
does not constitute a non-owner adoption receipt, owner canary, or
transactional global-host update. The independent-adoption gate remains
pending and v1 remains 7/8.
