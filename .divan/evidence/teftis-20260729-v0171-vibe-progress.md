# v0.17.1 release evidence

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

Pending PR, protected merge, immutable tag, Release assets, Pages, and Wiki
readback. These states are not claimed until their identifiers are recorded
here.

## v1 boundary

This owner-led release does not satisfy independent-adoption issue #34. v1
readiness remains 7/8.
