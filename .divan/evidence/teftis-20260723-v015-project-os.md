# v0.15.0 local Project OS release-candidate evidence

Date: 2026-07-24

Candidate branch: `codex/v015-project-os`

Approved implementation head: `1a94b61`

Prepared version: `0.15.0`

## Scope

This is public-safe local preparation evidence. It records no token, secret,
personal path, unrelated plugin identity, hidden reasoning, tag, Release,
deployment, or global-install claim.

The candidate adds a portable supervised Project OS while preserving the
published distribution shape:

- five Divan packages;
- 41 discoverable skills;
- English canonical machine interfaces and public technical documentation;
- first-class Turkish localization;
- v1 readiness at 7/8, with independent non-owner adoption still pending.

## Review and preflight

Independent whole-branch review approved `1a94b61` after the implementation
closed provider, SEO, project-initialization, recovery, and mutation-authority
findings test-first.

Before version preparation, the clean candidate passed:

- `python -m unittest discover -s tests -v`: 452 passed, 10
  platform-specific skips;
- `coverage report --fail-under=64`: 71% branch coverage;
- Ruff: clean;
- mypy over `scripts` and `evals`: clean;
- Clean Code debt ratchet: clean;
- repository validation: five packages, 41 skills, no name collision;
- handoff, catalog, v1, release, standards, candidate registry, Wiki, and eval
  contract checks: clean;
- actionlint 1.7.10: clean;
- Agent Skills `skills-ref` 0.1.1: all 41 skills valid;
- Claude Code 2.1.212 strict validation: marketplace and all five packages
  valid;
- `git diff --check`: clean.

## Deterministic preparation

`python scripts/release.py --prepare 0.15.0` changed the controlled version
surfaces from `0.14.1` to `0.15.0`. Human-authored CHANGELOG, Blueprint,
progress, and this evidence record were then updated explicitly. No tag, push,
release, deployment, or host mutation was performed.

## Remaining delivery boundary

The release is not public until a protected pull request is green and merged,
and the immutable `main` commit is separately proven across tag, GitHub
Release, source ZIP, checksum, SPDX SBOM, provenance, project runner, Pages,
Wiki, and both global hosts. Independent adoption evidence remains outside this
release and the v1 scorecard therefore remains 7/8.
