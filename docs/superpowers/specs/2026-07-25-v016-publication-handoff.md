# v0.16.0 Publication Handoff Design

## Problem

Divan v0.16.0 is tagged and publicly reachable, but the two canonical handoff
documents still tell the next maintainer to push the already-merged release
branch and open its PR. `scripts/handoff.py --check` passes because it checks
only file presence and the next-step heading.

## Root cause

The handoff has no bounded publication-state contract. A free-form progress
document can therefore contradict the immutable release without failing a
quality gate. Company OS also leaves the Markdown memory/evidence paths
unclassified, so its own impact report cannot select the required checks.

## Selected design

Keep the contract in the existing canonical progress document instead of
creating a second state registry. The `## Yayın durumu` section must contain:

- `Latest published release: v<semver>`
- `Published commit: <40 lowercase hexadecimal characters>`
- `Publication evidence: <repository-relative Markdown path>`

The evidence path must stay inside the repository, resolve to a regular file,
and contain the same version and source commit. The handoff validator compares
the latest-published version with the `## Sıradaki kesin iş` section. If that
section tries to push, open a PR for, or publish the already-published version,
handoff fails.

A newer release candidate remains valid: `VERSION` may be newer than the latest
published release, and its next step may describe the candidate PR. The
published version may never be newer than `VERSION`.

## Durable evidence

The v0.16.0 evidence record contains only observations reproduced in this
review:

- PR #31 is merged;
- tag `v0.16.0` and `main` resolve to
  `5513e73d5faa8657a22d813ecfec763a6089bea0`;
- the GitHub Release page returns HTTP 200;
- Pages and Wiki readbacks contain v0.16.0.

Release asset bytes, attestations, owner canary execution, dual-host global
updates, and independent adoption are explicitly not claimed.

## Impact and testing

Company OS gains an exact `project-memory` rule for `AGENTS.md`, `CLAUDE.md`,
`BLUEPRINT.md`, and Markdown under `.divan/`. It routes those paths to company,
documentation, and release validation.

Tests cover:

1. a valid published-state/evidence fixture;
2. missing or mismatched evidence;
3. a stale next step that republishes the latest release;
4. a newer candidate next step that remains allowed;
5. Company OS classification of all changed memory paths.

This is a handoff correctness patch, not a new Divan release. `VERSION` and the
immutable v0.16.0 release assets remain unchanged.
