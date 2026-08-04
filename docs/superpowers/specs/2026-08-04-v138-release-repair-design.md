# Divan v1.3.8 Release Identity Repair Design

**Goal:** Publish a new installable Divan release whose default-branch commit,
immutable tag, embedded runner source identity, checksums, SBOM, and GitHub
quality evidence all refer to the same verified source.

## Proven root cause

The published `v1.3.7` release is internally inconsistent:

- `refs/tags/v1.3.7` resolves to
  `c563893e63b0fc0ec65095ba80ab0dedc9f2d495`, whose `VERSION` is `1.3.6`;
- the published checksum manifest and both Python runners declare
  `source_commit=23815a2ed1d07096662a7c4e5333ba4700fb8ab5` and version `1.3.7`;
- the declared source commit is not the tag commit and its GitHub
  `quality-gate` failed on Ruff import ordering;
- `origin/main` is `b2c02ef980e144cbc2fd3cd07e98031e7cc0196e`,
  while the local checkout contains a mixed set of uncommitted product,
  recovery, release, documentation, and test changes.

The secure installer is correct to reject this release. Download hashes alone
prove transport integrity; they do not repair a broken source-identity chain.

## Decision

Divan will publish a new `v1.3.8` release from a clean, isolated branch based on
the current default branch. The existing `v1.3.7` tag and Release remain
immutable historical evidence and will not be moved, replaced, or deleted.

The release branch will receive only reviewed changes from the existing dirty
checkout. Each included path must belong to one of these bounded deliverables:

1. host installation/recovery and least-privilege release publication;
2. typed plan continuation without execution authority;
3. host-neutral UI/UX Pro Max adaptation, provenance, and tests;
4. versioned public surfaces and release evidence required by those changes.

Any path that cannot be tied to one of these deliverables is excluded.

## Architecture

### Isolated source assembly

An ignored project-local worktree on branch `codex/v138-release-repair` starts
from the approved design commit. A reviewed path manifest transfers selected
tracked diffs and new files from the original checkout without altering or
cleaning that checkout.

Targeted behavior tests run before the first product commit. The branch is then
committed so Divan's clean-source identity checks can run against a real,
immutable commit rather than an uncommitted tree.

### Release identity guard

The trusted release path must fail closed unless all of these values are equal:

- the current verified `main` commit;
- the new immutable `refs/tags/v1.3.8` commit;
- the source commit recorded by `divan.pyz`;
- the source commit recorded by `divan-project.pyz`;
- the source commit recorded by the checksum/release bundle.

The build job may execute source-selected build code only with read-only
repository permissions and no persisted Git credential, environment secret,
OIDC authority, or release write permission. The publish job may not execute
downloaded code. It accepts only the exact digest-verified asset bundle and
uses trusted current-main guards to compare tag, source, version, file set, and
hashes.

### Version and public surfaces

`scripts/release.py` is the only version-preparation path. It synchronizes
`VERSION`, runtime markers, marketplace manifests, README aliases, Wiki/source
pages, site copies, changelog, blueprint, progress state, installer examples,
and the release manifest for `1.3.8`.

No manual search-and-replace may substitute for this path. Generated or paired
surfaces must remain byte- or contract-equivalent according to their existing
tests.

### GitHub delivery

The implementation branch is pushed and opened as one pull request against
`main`. It is merged only after all required checks succeed. The release
workflow then operates from the resulting exact `main` commit.

The new tag and GitHub Release are terminal only when post-publication checks
re-read GitHub and prove:

- default branch and release source are the intended commits;
- tag commit equals every embedded source commit;
- all expected assets exist exactly once with no extras;
- SHA-256 values match downloaded bytes;
- SBOM and attestations are present when required by the workflow;
- the documented installer dry-run accepts `v1.3.8` without mutation.

## Error and recovery behavior

- A tag/source/version mismatch stops before host mutation or publication.
- A failed, skipped, missing, or still-running required CI check is not success.
- An existing `v1.3.8` tag or Release with different bytes stops publication;
  the workflow does not overwrite it.
- Interrupted publication is resumed only through recorded release evidence and
  exact remote-state comparison.
- A local dirty-source failure is reported as blocked rather than bypassed.
- Existing user changes in the original checkout are never reset, stashed,
  cleaned, or silently included.

## Cost and dependency boundary

- No paid API, subscription, proprietary runtime, or new global dependency is
  introduced.
- Existing GitHub repository and Actions mechanisms are used. If GitHub
  presents a billing or paid-runner requirement, publication stops for explicit
  user approval.
- Downloaded release programs are inspected as archives before any optional
  dry-run; they are not trusted merely because they are attached to a Release.

## Verification

The work is accepted only when:

- each release-identity regression test is observed failing before its minimal
  implementation fix and passing afterward;
- focused host install, recovery, release guard, workflow, continuation, UI/UX,
  bootstrap, provenance, and public-surface tests pass;
- deterministic builds produce byte-identical assets from the same source;
- `python scripts/verify.py --coverage` and `git diff --check` pass from the
  clean release branch;
- the pull request's required checks are green;
- the merged `main` commit, immutable `v1.3.8` tag, embedded source identities,
  release checksums, and downloaded asset bytes match;
- the safe install dry-run succeeds without applying host changes.
