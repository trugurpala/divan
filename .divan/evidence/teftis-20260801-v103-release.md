# v1.0.3 Publication Evidence

- Version: v1.0.3
- Source commit: ce0c87103a1e96f62ccabdf63dc6df9ee9b195fb
- Evidence date: 2026-08-01 UTC

## Authority

- Pull request: https://github.com/trugurpala/divan/pull/82
- Immutable tag and Release:
  https://github.com/trugurpala/divan/releases/tag/v1.0.3
- Published commit: `ce0c87103a1e96f62ccabdf63dc6df9ee9b195fb`
- Release state: non-draft, non-prerelease, immutable
- Release workflow:
  https://github.com/trugurpala/divan/actions/runs/30680433604

The lightweight `v1.0.3` tag and Release target resolve to the same merge
commit. The Release publishes the exact seven assets produced by the release
workflow. This evidence follow-up changes public status text only; it does not
move the tag or replace a Release asset.

## Main and publication workflows

The published commit passed the repository's required publication surfaces:

- quality-gate: https://github.com/trugurpala/divan/actions/runs/30680433580
- compatibility: https://github.com/trugurpala/divan/actions/runs/30680433588
- codeql: https://github.com/trugurpala/divan/actions/runs/30680433592
- scorecard: https://github.com/trugurpala/divan/actions/runs/30680433594
- site-tests: https://github.com/trugurpala/divan/actions/runs/30680433598
- wiki-sync: https://github.com/trugurpala/divan/actions/runs/30680433609
- candidate-review: https://github.com/trugurpala/divan/actions/runs/30680433595
- Pages: https://github.com/trugurpala/divan/actions/runs/30680433115
- release: https://github.com/trugurpala/divan/actions/runs/30680433604

The canonical local verification for PR #82 ran 715 tests with 14 expected
platform-specific skips. It validated five packages, 41 skills, and 242
release surfaces; clean-code, hygiene, release, and `git diff --check` gates
passed. An independent whole-branch review found no Critical or Important
blocker. GitHub repeated the quality gate, CodeQL, candidate review,
Playwright/site checks, Wiki sync, Scorecard, Pages, and the Linux/macOS/Windows
compatibility matrix before merge.

## Downloaded asset readback

All seven Release assets were downloaded into a new local temporary audit
directory. The local path is intentionally omitted. Every locally recomputed
SHA-256 matched GitHub's asset digest and both checksum sidecars. Strict
`gh attestation verify` succeeded for every asset.

| Asset | Bytes | SHA-256 | Attestation |
|---|---:|---|---|
| `divan-project.pyz` | 599576 | `74223d1e7d2a6536dfbd005235f169e5e21bf39040877f8aeaf320302c7e7ded` | verified |
| `divan-project.pyz.sha256` | 84 | `db815671b8914ae961beecd76a869b47ca2b5918a8f56d35733e59236e9aad6f` | verified |
| `divan-v1.0.3.sha256` | 572 | `0aa31319fbed6433641ca8cf9d119743bd6ca87fe07408d3a0b17d345f764162` | verified |
| `divan-v1.0.3.spdx.json` | 7896 | `3370809e01ec833f2df2fd1946d53e6cf3e345a774ef6b0223cbd3814752884c` | verified |
| `divan-v1.0.3.zip` | 6398840 | `3629183e9cda0ab6a48a0ef39afbd274aa99e200d60c8661e3ca6a4ecaa294a8` | verified |
| `divan.pyz` | 11295921 | `e8bc74d4bc30e373e4790809780466f76c171b68a18054c3d492fbc7e7a590d3` | verified |
| `divan.pyz.sha256` | 76 | `14442e5e65415a7feb29f3fcd0b7bdcbf69e53bf1e2102773b3c27c02fa027e7` | verified |

## Real Windows/Codex install readback

The downloaded, checksum-verified `divan.pyz` upgraded the installed Divan
marketplace and its five packages on Windows through the native Codex CLI.
The write-free preview listed only Divan-owned changes. The executed update
recorded a verified transaction; final doctor returned `healthy`, an empty
issues list, and an empty `next_command`. Repeating execute returned `NO-OP`.
Unrelated installed plugins remained outside the transaction.

The verified Codex compatibility claim remains deliberately bounded to the
Codex CLI surface exercised by the repository and this readback. Codex Desktop,
IDE extension, and mobile surfaces are not promoted without separate canaries.

This proves the v1.0.3 control-plane release, its immutable assets, and the
bounded Windows/Codex CLI lifecycle in this environment. It does not claim
universal host coverage, speed gain, quality improvement, third-party
endorsement, or market adoption.
