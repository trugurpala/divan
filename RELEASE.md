# Divan Release Guide

## Prepare

Use `python scripts/release.py --prepare <version>` so every deterministic
surface moves together. Write the changelog and product decision record, then
run the one canonical local gate:

```bash
python scripts/verify.py
git diff --check
```

## Publish

A reviewed pull request must pass every required check before merge. The
default-branch release workflow verifies clean hosts, Pages, Wiki and live site
behavior before creating the tag, GitHub Release, checksums, SBOM and
attestations.

Release construction and publication use separate authority domains. The build
job has `contents: read`, does not persist the checkout credential, and has no
environment secret, OIDC, attestation or repository-write authority. It may
rebuild from an existing remote tag, then transfers the exact eight-file bundle
through immutable, full-SHA-pinned GitHub artifact actions. The
`production-release` job downloads only that run's artifact ID, requires its
transport digest and bundle hashes to match, and never executes downloaded
code. Only that final job receives the narrow publication permissions.

Before dispatch, `production-release` must require its reviewer and allow only
`main`. Its `DIVAN_RELEASE_ADMIN_TOKEN` secret must be a fine-grained token or
GitHub App token with repository Administration read access. The workflow uses
it only to read the immutable-release setting and stable-tag ruleset, unsets it
before running repository Python, and stops if it is absent. Stable `v*` tags
must have active update and deletion protection with no bypass actor.

If the remote tag already exists but its Release is missing, the workflow
rebuilds every asset from that exact tag commit after proving it belongs to the
current `main` history and that its `VERSION` matches. A draft, mutable Release,
duplicate Release record, or missing/extra/duplicate asset stops the workflow;
it is never deleted, overwritten, or repaired automatically.

## Rollback

Do not move or overwrite an immutable tag. If publication fails before a tag
exists, fix the source through a new pull request. If a published release has a
defect, document the impact and publish a new patch version. Host installation
rollback uses the exact recovery command printed by `doctor`; see
[docs/Kaldirma.md](docs/Kaldirma.md).

## Evidence

After publication, read the tag target, release assets, checksums, attestations,
README, Pages and Wiki from their remote sources. Record only verified facts.
