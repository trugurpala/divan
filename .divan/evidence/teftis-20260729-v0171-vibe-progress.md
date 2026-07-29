# v0.17.1 release evidence

## Publication identity

- Version: v0.17.1
- Source commit: 4144e096fdcdf07f2caab50585a831beb4f3f60b
- Release: https://github.com/trugurpala/divan/releases/tag/v0.17.1
- Release workflow: https://github.com/trugurpala/divan/actions/runs/30482056816
- Release workflow conclusion: `success`
- Published at: `2026-07-29T18:57:12Z`
- Draft/prerelease: `false` / `false`

## Scope

Vibe-friendly, evidence-bound progress communication for substantial Divan
tasks. No runtime module, external repository, MCP server, or third-party
dependency is added.

## Local verification

- Implementation commit: `77ebd18ca7746dc17b3aac1c87d879ef4e3a0909`
- Canonical Windows verifier: passed.
- Unit tests: 544 passed, 14 platform-specific skips.
- Repository contract: 5 packages, 41 skills, 151 release surfaces.
- Hygiene, handoff, catalog, v1 scorecard, release consistency, eval contract,
  and final post-test hygiene: passed.
- Focused Windows CLI, Project OS, and provider suite: 129 passed, 7
  platform-specific skips.
- Independent whole-change review: no open P0-P3 findings; approved for the
  local release gate.

The tests establish the skill contract and synchronized publication surfaces.
They do not establish a new real-agent A/B improvement claim.

## GitHub delivery

- PR: `#52`.
- Protected squash merge: `4144e096fdcdf07f2caab50585a831beb4f3f60b`.
- Release workflow: `30482056816`, successful on the exact merge commit.
- Immutable tag and public Release: `v0.17.1`.
- Five assets were downloaded and matched their GitHub SHA-256 digests:
  `divan-project.pyz`, its checksum, the release checksum manifest, SPDX SBOM,
  and release ZIP.
- Every asset has two GitHub attestations.
- Pages and Wiki returned HTTP 200 and exposed v0.17.1 after publication.

## v1 boundary

This owner-led release does not satisfy independent-adoption issue #34. v1
readiness remains 7/8.
