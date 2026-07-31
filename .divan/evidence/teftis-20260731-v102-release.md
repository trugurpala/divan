# v1.0.2 Publication Evidence

- Version: v1.0.2
- Source commit: f227e2d30ab1a6f010a3d5acf18740f6eab09e70
- Evidence date: 2026-07-31 UTC

## Authority

- Pull request: https://github.com/trugurpala/divan/pull/80
- Immutable tag and Release:
  https://github.com/trugurpala/divan/releases/tag/v1.0.2
- Published commit: `f227e2d30ab1a6f010a3d5acf18740f6eab09e70`
- Release state: non-draft, non-prerelease, immutable
- Release workflow:
  https://github.com/trugurpala/divan/actions/runs/30646054323

The lightweight `v1.0.2` tag and Release target resolve to the same
GitHub-verified commit. The Release publishes the exact seven assets produced
by the release workflow.

## Main and publication workflows

Every workflow triggered for the published commit completed successfully:

- quality-gate:
  https://github.com/trugurpala/divan/actions/runs/30646054367
- compatibility:
  https://github.com/trugurpala/divan/actions/runs/30646054266
- codeql:
  https://github.com/trugurpala/divan/actions/runs/30646054342
- scorecard:
  https://github.com/trugurpala/divan/actions/runs/30646054316
- site-tests:
  https://github.com/trugurpala/divan/actions/runs/30646054310
- wiki-sync:
  https://github.com/trugurpala/divan/actions/runs/30646054295
- candidate-review:
  https://github.com/trugurpala/divan/actions/runs/30646054355
- Pages:
  https://github.com/trugurpala/divan/actions/runs/30646053173
- release:
  https://github.com/trugurpala/divan/actions/runs/30646054323

The canonical local verification for PR #80 ran 707 tests with 14 expected
platform-specific skips and ended with clean hygiene and clean-code gates.
`git diff --check` was also clean. GitHub repeated the quality gate, CodeQL,
candidate review, Playwright/site checks, Wiki sync, Scorecard, Pages, and the
Linux/macOS/Windows compatibility matrix before the PR was merged to `main`.

## Downloaded asset readback

All seven Release assets were downloaded into a new local temporary audit
directory. The local path is intentionally omitted from this public evidence.
Every locally recomputed SHA-256 matched GitHub's asset digest and the release
sidecar files. Strict `gh attestation verify` returned one valid attestation for
every asset.

| Asset | Bytes | SHA-256 | Attestations |
|---|---:|---|---:|
| `divan-project.pyz` | 599576 | `e9a35c096fc2577323a7c7ba4cd55a756fd3494396ebd3cf86098d422d754cf4` | 1 |
| `divan-project.pyz.sha256` | 84 | `d4d3468aa74287bd6f7783aee36e7ff48bf209638ad3fd8931e1f2fe1b4a1e45` | 1 |
| `divan-v1.0.2.sha256` | 572 | `0d47e5d220340ad0eda70bb5afc47c6accbf10b407856d5aede72b8335a9d2f4` | 1 |
| `divan-v1.0.2.spdx.json` | 7896 | `81b460f1b0c5b7e282a9efeae8f39393c333a441f38e31b238ea680b55a46210` | 1 |
| `divan-v1.0.2.zip` | 6381437 | `b29740ccd40073213d0c23a0769882be043126f884f4bb569e9c584e2a1a5258` | 1 |
| `divan.pyz` | 11295432 | `bbd618811ae6fcc37a673bcebcf6c085b1aa3d30e9dfac850dabb2f8ea8b52fc` | 1 |
| `divan.pyz.sha256` | 76 | `be0fb101ea4ebda4e49d023ce6cbc13d02f12e73800940c63b2f62c7d2d4baa0` | 1 |

## Real Windows/Codex install readback

The downloaded and checksum-verified `divan.pyz` was tested against the native
Codex installation on Windows 11:

1. Initial `doctor --host codex --ref v1.0.2 --json` reported only a marketplace
   ref attention item while the native Codex CLI itself was healthy.
2. The write-free install preview listed only the Divan marketplace and five
   Divan packages.
3. The guarded installer refused to overwrite the existing Divan marketplace
   because the old marketplace ref could not be proven, and it rolled the
   transaction back instead of changing unrelated plugins.
4. The same bounded repair was then applied through the native `codex.cmd`
   plugin lifecycle: remove only the Divan marketplace, re-add
   `https://github.com/trugurpala/divan.git` with `--ref v1.0.2`, and reinstall
   `sadrazam`, `core-pack`, `ui-pack`, `react-pack`, and `zanaat-pack`.
5. Final `python scripts/divan.py doctor --host codex --ref v1.0.2 --json`
   returned `healthy`, `recommended_mode: native`, and no host issues.

`codex.cmd plugin list --json` showed the five Divan packages enabled from the
Divan marketplace while unrelated personal, bundled, and primary-runtime
plugins remained installed and enabled. `codex.cmd plugin marketplace list
--json` does not display the pinned ref, so the pinned-source claim is bounded
to Divan doctor and the successful native lifecycle calls rather than that
display output.

This proves the v1.0.2 quiet-discovery release, its Release assets, and the
bounded Windows/Codex v1.0.2 install readback for this environment. It does not
claim universal host coverage, speed gain, quality improvement, third-party
endorsement, or market adoption.
