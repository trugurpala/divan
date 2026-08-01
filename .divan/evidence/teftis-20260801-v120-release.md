# v1.2.0 Publication Evidence

- Version: v1.2.0
- Source commit: c90162f79ba0a7065520eb4568978d8ef69d4cc1
- Evidence date: 2026-08-01 UTC

## Authority

- Pull request: https://github.com/trugurpala/divan/pull/86
- Immutable tag and Release:
  https://github.com/trugurpala/divan/releases/tag/v1.2.0
- Published commit: `c90162f79ba0a7065520eb4568978d8ef69d4cc1`
- Release state: non-draft, non-prerelease, immutable
- Release workflow:
  https://github.com/trugurpala/divan/actions/runs/30697713112

The lightweight `v1.2.0` tag and GitHub Release resolve to the merge commit.
The Release publishes the seven assets produced by the release workflow. This
evidence follow-up records the completed publication; it does not move the tag
or replace a Release asset.

## Main and publication workflows

The published commit passed every current publication workflow:

- quality-gate: https://github.com/trugurpala/divan/actions/runs/30697713110
- compatibility: https://github.com/trugurpala/divan/actions/runs/30697713111
- codeql: https://github.com/trugurpala/divan/actions/runs/30697713123
- scorecard: https://github.com/trugurpala/divan/actions/runs/30697713106
- site-tests: https://github.com/trugurpala/divan/actions/runs/30697713126
- wiki-sync: https://github.com/trugurpala/divan/actions/runs/30697713144
- candidate-review: https://github.com/trugurpala/divan/actions/runs/30697713113
- Pages: https://github.com/trugurpala/divan/actions/runs/30697712508
- release: https://github.com/trugurpala/divan/actions/runs/30697713112
- upstream-watch: https://github.com/trugurpala/divan/actions/runs/30697914987

The canonical local verification passed 755 tests with 14 expected
platform-specific skips. Ruff, mypy, Clean Code, prose, hygiene, release,
Agent Skills, plugin schemas, and `git diff --check` passed. PR checks repeated
the quality gate, CodeQL, dependency review, browser/site tests, Wiki sync, and
the Linux/macOS/Windows compatibility matrix before merge.

## Downloaded asset readback

All seven Release assets were downloaded into a new temporary audit directory.
The local path is intentionally omitted. Every locally recomputed SHA-256
matched GitHub's asset digest and the checksum sidecars. Strict
`gh attestation verify` succeeded for the ZIP, SBOM, project runner, and host
installer artifacts.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `divan-project.pyz` | 599576 | `6e1643ade1457fee829cdd77e591c0415b8238290e101550b65408741e3636b1` |
| `divan-project.pyz.sha256` | 84 | `3d7e5920dd131e489b22d32ba68b73fe4581ed0fb6f73dac73af5c4b43442c50` |
| `divan-v1.2.0.sha256` | 572 | `aace9bebb96dec42c4c0e8656b5bcba04dd1e88dce838c8caf5d6dc44e346f11` |
| `divan-v1.2.0.spdx.json` | 7896 | `a217da7f53cb2403735a2e99beef748268ea0bf1f782d84678875548a280155a` |
| `divan-v1.2.0.zip` | 5540706 | `e47324bd2851559b80e6bb4d5d59989cfbdaad79f48773044c422492c4040094` |
| `divan.pyz` | 11302532 | `191ab7f9ec5b772ad21271a6418bca692253de51f583fa9eed65cf33cb83a44f` |
| `divan.pyz.sha256` | 76 | `0ea0570514b34203730b996a58f947da51b9e186f7d908b2df4e4982ea36651b` |

The downloaded project runner validated 18 frameworks, 19 impact rules, nine
modules, 12 roles, and 11 workflows. Live README, Pages, and Wiki readbacks
returned v1.2.0. Issue #85 was updated by the bounded Nobet workflow and closed
with zero review debt.

## Windows and Codex readback

The checksum-verified `divan.pyz` was exercised against the current Windows
Codex installation. Its write-free preview listed only Divan-owned changes.
The old marketplace entry was explicitly replaced through the native Codex CLI
because the CLI list response omitted the pinned ref and the Divan installer
correctly refused to guess. The final marketplace ref is `v1.2.0`; all five
packs are enabled; `ui-pack` is 0.2.0; and `doctor --host codex --json` returned
`healthy` with an empty issues list and empty next command.

This proves the bounded v1.2.0 publication and the exercised Windows/Codex
lifecycle. It does not claim universal host coverage, speed gain, quality
improvement, third-party endorsement, or market adoption.
