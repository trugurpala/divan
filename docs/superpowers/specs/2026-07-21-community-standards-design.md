# Divan Community Standards v0.13 Design

## Purpose

Divan v0.13 turns the project's existing quality practices into a public,
machine-readable product contract. The release must make first use easier,
keep Claude and Codex integrations replaceable, prevent quality regressions,
strengthen release provenance, and give contributors one obvious route for
support and changes.

This is a standards-as-code release. It does not add an application framework,
an agent runtime, telemetry, a hosted dashboard, or an automatic third-party
skill installer.

## Current baseline

The v0.12.2 baseline has five packages, 41 skills, 101 passing tests, pinned
GitHub Actions, CodeQL, Ruff, mypy, branch coverage, UTF-8/LF enforcement,
transactional dual-host installation, deterministic publication surfaces,
Pages, Wiki, Discussions, and a complete GitHub community profile.

The audit also found gaps that matter to public adoption:

- `main` has no branch protection or repository ruleset, so green CI is not a
  merge requirement;
- the repository homepage field is empty and there is no `SUPPORT.md`;
- OpenSSF Scorecard, dependency review, release SBOM, and artifact attestation
  are absent;
- installation has safe failure and rollback but no read-only doctor or
  explicit transactional upgrade path;
- `scripts/kur-hostlar.py` and `evals/run.py` have grown beyond 600 lines;
- the current McCabe limit of 25 is a useful legacy ceiling but too permissive
  for new code;
- standards are prose-only and do not define expiring exceptions or
  machine-readable evidence.

The v1 independent-user acceptance gate remains pending. v0.13 must not alter
that status without external evidence.

## Delivery boundary

The work is delivered as one feature release with five independently testable
slices:

1. standards registry and enforcement;
2. doctor and transactional upgrade user experience;
3. clean-code ratchet and focused module extraction;
4. supply-chain and protected-branch controls;
5. contributor, documentation, website, and release surfaces.

Each slice may be reviewed independently, but the public v0.13 release is made
only after all five pass the repository publication contract. Existing user
changes in the primary checkout are outside scope and must remain untouched.

## Architecture

### Standards controller

`registry/community-standards.json` is the canonical data source. It contains
exactly ten entries with stable IDs `DCS-001` through `DCS-010`. Every entry has:

- `id`, `title_tr`, and `title_en`;
- `level`, fixed to `required` for v0.13;
- `purpose`;
- one or more executable `checks`;
- one or more repository `evidence` paths;
- an `exception_policy` value.

`registry/standard-exceptions.json` is the only exception surface. An exception
must identify the DCS rule, exact path or symbol, reason, owner, creation date,
expiry date, and evidence link. Expired, unknown, duplicated, or broader-than-
necessary exceptions fail validation. The initial file is an empty list unless
the measured legacy baseline requires a narrow exception.

`scripts/standartlar.py` provides three stable commands:

```text
python scripts/standartlar.py --check
python scripts/standartlar.py --render
python scripts/standartlar.py --json
```

`--check` is read-only and validates schema, IDs, check commands, evidence
paths, exception expiry, and generated-document parity. `--render` updates only
the generated standards document. `--json` emits a UTF-8 JSON status object and
does not mix human diagnostics into stdout.

`docs/Topluluk-Standartlari.md` is generated deterministically from the
registry. `scripts/validate.py`, the primary CI workflow, the release manifest,
Wiki source, and tests all consume the same contract.

### Host lifecycle boundary

The existing `scripts/kur-hostlar.py` remains the public host lifecycle entry
point. Host-specific command construction and output parsing move behind small
Claude and Codex adapter functions; transaction ownership, journal persistence,
rollback, and legacy migration remain host-neutral.

Two user-facing operations are added:

```text
python scripts/kur-hostlar.py --doctor --host both --ref v0.13.0
python scripts/kur-hostlar.py --upgrade --host both --ref v0.13.0
python scripts/kur-hostlar.py --upgrade --host both --ref v0.13.0 --execute
```

`--doctor` never mutates state. It reports host CLI availability, marketplace
source, installed package version, enablement, incomplete transactions, and the
next exact command. Human output is concise; `--json` provides a stable result
for automation.

`--upgrade` is dry-run by default. Execute mode upgrades only entries whose
Divan provenance and ownership are proven. Before every external mutation it
persists the intended operation. It records the old source/ref/version, removes
only transaction-owned Divan entries, installs the pinned target, verifies both
hosts, and marks the journal complete. Failure restores the previous proven
state. Unknown or conflicting provenance fails closed without changing the
host. Unrelated plugins and marketplaces are never removed, disabled, or
rewritten.

### Clean-code ratchet

New or newly oversized first-party Python code is held to:

- McCabe complexity at most 10 per function;
- at most 50 logical lines per function;
- at most 400 physical lines per module;
- explicit UTF-8 for text subprocesses and file boundaries;
- typed public boundaries and structured errors;
- no silent broad-exception fallback.

The repository branch-coverage floor rises from 55% to the measured 64%
v0.12.2 baseline in v0.13. This prevents the enforced threshold from trailing
the stated non-regression promise. Later releases can raise the floor, but
v0.13 must never lower it or reduce measured coverage below 64%.

Existing violations are recorded by exact path, symbol, and measured value in
`registry/clean-code-baseline.json`. The checker fails if a baseline violation
grows, shrinks, or disappears until the registry is refreshed to the exact
current measurement; it also rejects every new violation.
The existing repository-wide McCabe 25 hard ceiling remains in place during the
ratchet. Baseline entries can only disappear or shrink in the same reviewed
change that refreshes the registry to the exact measurement.

The v0.13 implementation extracts host command adapters and transaction/report
formatting from `scripts/kur-hostlar.py`. It extracts result redaction,
provenance, and judging/reporting units from `evals/run.py` only where
characterization tests demonstrate unchanged behavior. Unrelated refactoring is
out of scope.

### Supply-chain controls

The release adds:

- an OpenSSF Scorecard workflow with a full-SHA-pinned action and minimal
  permissions;
- a pull-request dependency-review workflow;
- a deterministic SPDX JSON SBOM produced from the release manifest, package
  manifests, upstream registry, and third-party license inventory;
- GitHub artifact provenance for the release ZIP and SBOM;
- explicit workflow-level or job-level least-privilege permissions;
- a repository ruleset requiring pull requests and the known green validation
  checks before `main` can change.

The ruleset is applied only after the required workflow names are present on
`main`. Its exact JSON and resulting ruleset ID are recorded as release
evidence. Administrator bypass remains available for repository recovery, but
normal contributor changes use pull requests. GitHub Actions referenced but not
vendored are recorded by immutable SHA and reviewed permissions; copied source
still requires the existing upstream and license process.

The release workflow creates attestations only for artifacts it built from the
tagged commit. It never moves an existing tag or overwrites an existing asset.

### Public and community surfaces

`SUPPORT.md` routes usage questions to GitHub Discussions, reproducible bugs to
the issue form, security reports to private advisories, and skill proposals to
the candidate lifecycle. `CONTRIBUTING.en.md` provides an English equivalent of
the critical contribution contract; the Turkish and English files link to each
other.

README, installation documentation, Wiki source, and the Pages site expose:

- a 30-second product explanation;
- a copyable five-minute install and doctor path;
- upgrade, rollback, and uninstall links;
- a clear statement of what Divan is not;
- the ten DCS rules and their live validation command;
- support and contribution routes;
- truthful v1 and independent-adoption status.

The GitHub repository homepage is set to the Pages URL. Topics are preserved and
reviewed rather than replaced. A 1280x640, under-1-MB social preview reuses the
existing Mühürdar visual identity and must remain legible without relying on
small text. Because GitHub does not expose a stable repository API for this
image, browser configuration is acceptable and its result is captured as
evidence.

## The ten required standards

### DCS-001 — Five-minute first success

A new user gets one pinned installation path, a read-only preview, a doctor
result, and an exact recovery command. Documentation examples must be runnable
on Windows PowerShell and POSIX shells where applicable.

### DCS-002 — Framework-independent core

Host CLIs are adapters at the boundary. Core policy and transaction state use
stdlib data structures and versioned JSON contracts. Host/version support and
deprecation behavior are documented.

### DCS-003 — Small, cohesive code

The clean-code ratchet prevents new complexity, long functions, and oversized
modules while shrinking declared legacy debt. Exceptions are narrow and expire.

### DCS-004 — Explicit data and error contracts

Public automation supports stable structured output. Errors carry an actionable
message and non-zero exit status. Broad exceptions cannot be silently ignored.

### DCS-005 — Tests and evidence before claims

Behavior changes begin with a failing regression test. Unit, transaction,
cross-platform smoke, and publication checks cover the relevant boundary. The
enforced branch-coverage floor and measured suite result are both at least the
recorded 64% baseline. Behavioral-quality claims still require the
existing real-adapter and blinded-judge protocol.

### DCS-006 — Secure supply chain

Dependencies and Actions are immutable or exactly pinned, token permissions are
minimal, pull requests receive dependency review, static analysis remains
enabled, and release artifacts receive an SBOM, checksum, and provenance.

### DCS-007 — Reversible lifecycle

Install, upgrade, doctor, uninstall, recovery, and rollback are explicit and
documented. Mutations are journaled before execution and affect only proven
Divan-owned state.

### DCS-008 — Discoverable synchronized documentation

Turkish and English critical paths, Wiki, Pages, README, release notes, and
version metadata remain synchronized by the publication manifest and CI.

### DCS-009 — Contributor and support readiness

Users can distinguish questions, bugs, security reports, skill proposals, and
acceptance evidence. Contributors get a single local validation sequence and
protected pull-request workflow.

### DCS-010 — Accessible, private, evidence-led operation

Core usage requires no telemetry. Text output works without color, first-party
text remains UTF-8/LF, user backups are not treated as cache, the Pages surface
retains WCAG AA checks, and adoption claims use public evidence rather than
invented metrics.

## Data flow and failure behavior

1. A contributor changes code, registry data, or a public surface.
2. Unit tests validate the smallest behavior first.
3. `standartlar.py --check` verifies registry, clean-code debt, evidence paths,
   and rendered-document parity.
4. The existing audit runs schema, catalog, v1, eval, Wiki, publication, lint,
   type, coverage, and Action validation.
5. Pull-request dependency review, CodeQL, Scorecard, and compatibility jobs run
   with minimal permissions.
6. The repository ruleset blocks merge until required checks pass.
7. Publication prepares v0.13.0 from `VERSION`, builds ZIP/checksum/SBOM,
   verifies Pages and Wiki, then tags and attests immutable artifacts.
8. A clean-host doctor/install/upgrade/rollback rehearsal verifies Claude and
   Codex without touching unrelated plugins.

Malformed registry data, missing evidence, expired exceptions, increased clean-
code debt, untrusted host provenance, incomplete journals, failed artifact
verification, stale public surfaces, or missing required checks are hard
failures. No failure path may silently continue or claim publication.

## Testing strategy

- Unit tests cover registry schema, exact DCS IDs, deterministic rendering,
  exception expiry, JSON output, and clean-code ratcheting.
- Characterization tests freeze existing host command, transaction, recovery,
  and eval behavior before module extraction.
- Doctor fixtures cover missing CLI, healthy install, version drift, disabled
  plugin, foreign marketplace, and interrupted transaction.
- Upgrade fixtures cover dry-run, same-version no-op, successful dual-host
  upgrade, one-host failure, rollback, second interruption, and unrelated plugin
  preservation.
- Workflow tests require full-SHA action pins, explicit permissions, dependency
  review, Scorecard, SBOM, and attestation steps.
- Documentation tests require support routes, bilingual links, current version,
  copyable doctor/upgrade commands, and Pages accessibility landmarks.
- The complete AGENTS.md validation sequence and `git diff --check` run before
  review and again immediately before delivery.

## Release and rollout

The target is v0.13.0 because the release adds public commands and governance
contracts. `scripts/yayin.py --prepare 0.13.0` is used only after implementation
and local verification. README, English README, CHANGELOG, BLUEPRINT, Wiki
sources, Pages sources, package manifests, marketplace manifests, progress, and
release evidence are updated in the same change.

Delivery states remain distinct: feature branch, reviewed PR, merged `main`,
live Pages/Wiki, immutable tag, GitHub Release, artifact attestations, and global
Claude/Codex installation. The final report states exactly which states were
verified. v1.0 remains blocked on independent user evidence.

## Acceptance criteria

The design is complete only when all of the following are true:

1. The registry contains exactly DCS-001 through DCS-010 and all three
   `standartlar.py` commands are tested.
2. Standards, clean-code debt, generated docs, and release surfaces drift closed
   in CI.
3. Doctor is read-only and produces useful human and JSON output for both hosts.
4. Upgrade is dry-run by default, provenance-gated, journaled, verified, and
   rollback-safe under tested interruption paths.
5. New code obeys complexity 10, function 50, and module 400 limits; recorded
   legacy debt does not grow.
6. Scorecard, dependency review, CodeQL, SBOM, checksum, and artifact provenance
   are present with least permissions and immutable action pins.
7. `main` is protected by a recorded ruleset requiring the actual validation
   check names.
8. Support, contribution, installation, README, Wiki, and Pages routes are
   synchronized in Turkish and English where they are critical to first use.
9. The repository homepage points to Pages and the social preview is verified.
10. The full local and remote validation chain passes, v0.13.0 is installed and
    discovered in Claude and Codex, unrelated extensions remain unchanged, and
    the v1 independent-adoption gate remains honestly pending.
