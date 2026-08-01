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

## Rollback

Do not move or overwrite an immutable tag. If publication fails before a tag
exists, fix the source through a new pull request. If a published release has a
defect, document the impact and publish a new patch version. Host installation
rollback uses the exact recovery command printed by `doctor`; see
[docs/Kaldirma.md](docs/Kaldirma.md).

## Evidence

After publication, read the tag target, release assets, checksums, attestations,
README, Pages and Wiki from their remote sources. Record only verified facts.
