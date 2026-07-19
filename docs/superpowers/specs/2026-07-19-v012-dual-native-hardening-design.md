# Divan v0.12 Dual-Native Hardening Design

**Date:** 2026-07-19
**Status:** Approved in conversation; written-spec review pending
**Target release:** v0.12.0

## Goal

Make Divan a native, globally installable marketplace for both Claude Code
Desktop and Codex while preserving the portable Agent Skills source, hardening
the public supply chain, and producing honest cross-provider behavioral
evidence. The release must keep existing third-party plugins and loose skills
recoverable and must not claim v1 until an independent user submits adoption
evidence.

## Current State

- Claude Code 2.1.209 is installed, authenticated, and exposed through the
  Claude desktop Code surface. Divan is not configured in its user-scoped
  marketplace list.
- Codex CLI 0.144.4 and the Codex desktop app are installed and authenticated.
  Forty-one Divan skills are installed as loose global skills. Twenty-two other
  loose skills remain present. The current Codex release also supports native
  `.agents/plugins/marketplace.json` catalogs and `.codex-plugin/plugin.json`
  manifests.
- Divan already publishes five Claude plugins from one repository and validates
  41 portable Agent Skills.
- Local and main-branch validation pass, but branch protection, CodeQL,
  vulnerability alerts, immutable Action pins, type/lint/coverage gates, and
  full accessibility checks are incomplete.
- Four skills have 13 contract eval cases. No declared real-agent and judge run
  has been published. Independent adoption evidence is still absent.

## Selected Approach

Use a dual-native marketplace with a shared content tree. Claude and Codex get
host-specific metadata, but both resolve the same five plugin directories and
the same skill files.

Rejected alternatives:

1. **Continue loose Codex skill copying only.** It works but bypasses Codex's
   native plugin lifecycle, lacks namespaced package identity, and makes updates
   and provenance harder to reason about.
2. **Publish one monolithic Divan plugin.** Installation is simpler but removes
   the existing package-selection model and increases prompt/context exposure.
3. **Duplicate Claude and Codex content trees.** Host metadata would be simple,
   but every skill change would create drift and license-maintenance risk.

## Architecture

### 1. Shared package source, two native catalogs

The existing `plugins/{sadrazam,core-pack,ui-pack,react-pack,zanaat-pack}`
directories remain the only content source.

- Claude continues to use `.claude-plugin/marketplace.json` and each package's
  `.claude-plugin/plugin.json`.
- Codex gains `.agents/plugins/marketplace.json` at the repository root and a
  `.codex-plugin/plugin.json` inside each package.
- Codex plugin metadata points `skills` at `./skills/`; no skill content is
  copied.
- Package names and versions must agree across both host catalogs. The local
  validator and release gate reject drift.
- The existing direct-copy Codex installers remain as an explicitly documented
  legacy/fallback path for older Codex releases without native plugins.

### 2. Transactional global installation

Host installers operate in two phases: prepare and activate.

**Claude:**

1. Add the tagged `trugurpala/divan` marketplace at user scope.
2. Install all five packages at user scope.
3. Validate the installed inventory and enabled state.
4. Preserve GitKraken, prompts.chat, and any other existing marketplace/plugin
   state.

**Codex:**

1. Add the tagged marketplace with `codex plugin marketplace add ... --ref`.
2. Install all five native packages.
3. Validate installed marketplace, package versions, and discoverable skills.
4. Only after native verification, migrate the 41 legacy loose Divan skills out
   of `~/.codex/skills` using their existing install manifest.
5. Restore any pre-Divan collision backup, including the prior
   `ui-ux-pro-max`, when the old loose installation is retired.

Migration records include host, Divan version, requested ref, resolved commit,
archive or catalog digest, target paths, replaced paths, backup paths, and UTC
timestamp. Failure before activation leaves the old installation untouched;
failure after activation triggers rollback from the recorded manifest.

### 3. Pinned release and installer trust

- Public one-liners fetch installer scripts from the version tag, never
  `main`.
- The default embedded installer ref is the release tag, not a moving branch.
- Release automation emits deterministic install artifacts plus SHA-256 files.
- Installers verify SHA-256 before extraction or activation and fail closed on
  mismatch.
- Git tags are never moved. Updating an installer requires a new release.
- Documentation distinguishes native installation, legacy fallback, update,
  uninstall, rollback, and host restart/reload behavior.

### 4. Repository and CI hardening

- Pin every third-party GitHub Action to an immutable reviewed commit SHA while
  retaining the human-readable release tag in a comment.
- Add CodeQL for the repository's Python and JavaScript surfaces.
- Enable GitHub vulnerability alerts, Dependabot security updates, secret
  scanning, push protection, and a `main` ruleset with required pull request and
  required status checks.
- Keep default workflow permissions read-only; only Release and Wiki publishing
  jobs receive narrowly scoped write permission.
- Add pinned lint, type-check, and coverage gates. New thresholds are based on
  an observed baseline and must not be achieved by excluding relevant code.
- Keep the existing official Agent Skills and Claude Code validators.

### 5. Vitrine accessibility and metadata

- Wrap primary page content in a semantic `<main id="main-content">`.
- Add a keyboard-visible skip link.
- Raise the small coral-label contrast to at least WCAG AA 4.5:1.
- Extend the browser test with keyboard focus, landmark, accessible-name, and
  reduced-motion assertions. Add an automated accessibility scan if it can be
  pinned without making a heavyweight runtime dependency part of Divan itself.
- Preserve the current Ottoman visual direction and responsive behavior.
- Restore exact MIT license recognition by keeping the root license text
  canonical and moving the third-party notice to a separate notice file.

### 6. Real cross-provider eval evidence

Use declared local adapters in a trusted temporary workspace:

- **Agent:** authenticated Claude Code, run once without the target plugin and
  once with the exact tagged Divan plugin/package.
- **Judge:** authenticated Codex CLI in read-only/no-approval mode, receiving
  blinded A/B outputs and returning the existing judgement schema.
- **Runner:** the existing provider-independent `evals/run.py`, extended only as
  needed for declared adapter commands, bounded cost/timeout, redacted
  provenance, and deterministic artifact paths.

The public result records tool versions, model identifiers, source commit,
environment, case count, threshold, timestamps, and redacted output. The blind
mapping remains separate. A failed or incomplete run stays
`review_required`; no win-rate claim is made without a completed judged run.

The `real-agent-comparison` v1 gate may pass only if the result is reproducible,
reviewed, and linked from the gate registry. The `independent-adoption` gate
remains pending until a person other than the repository owner submits the
existing acceptance form against a fixed release.

### 7. Upstream curation

The current 15-skill upstream drift report is a review queue, not an automatic
upgrade list.

- Record current source commits and compare each changed skill against the
  vendored version.
- For each source, choose KEEP, ADAPT, ADOPT, REFERENCE, or REJECT with license
  evidence and product rationale.
- ADAPT/ADOPT changes require their own tests/evals and updates to `UPSTREAM.md`
  and `THIRD_PARTY_LICENSES.md`.
- The monthly watcher must distinguish a known local patch from new upstream
  movement by pinning the reviewed upstream baseline.

## Data and Failure Boundaries

- Installers never merge same-named skill directories.
- All migration writes are preceded by target resolution and backup creation.
- Host configuration is mutated through the host's supported CLI, not by
  hand-editing opaque caches.
- Existing non-Divan plugins and skills are outside deletion scope.
- Credentials, auth files, prompts, and session histories are never copied into
  repository evidence.
- A host install is successful only when its native CLI lists all five packages
  at the expected version and a fresh session can discover the package skills.
- Claude's currently running task is not interrupted; plugin activation occurs
  through a safe reload or a user-visible restart after installation.

## Testing Strategy

Implementation follows red-green-refactor cycles.

1. Catalog tests fail when Claude/Codex package names or versions drift.
2. Installer tests use temporary homes and fixture artifacts to prove checksum
   failure, collision backup, migration, rollback, and unrelated-skill
   preservation.
3. Workflow tests/actionlint validate immutable pins and permission boundaries.
4. Security configuration is verified by GitHub API readback.
5. Static and Playwright tests cover semantic landmarks, keyboard navigation,
   interaction, mobile viewport, console errors, and the release version.
6. Eval runner tests cover adapters, timeouts, redaction, incomplete runs, and
   judged evidence before a bounded real run is executed.
7. Full repository, official schema, clean-host matrix, live Pages/Wiki, tag,
   Release, and both global host inventories form the final evidence set.

## Release and Rollback

- Prepare v0.12.0 only after all code and documentation surfaces agree.
- Merge through a protected pull request after required checks pass.
- Publish a new immutable tag and GitHub Release; do not move v0.11.1.
- Install the tagged release globally into Claude and Codex, then verify in
  fresh sessions.
- If native migration fails, remove only the new Divan plugin entries and
  restore the old loose-skill manifest and collision backups.
- Record test output, CI URLs, settings readback, install manifests, live-site
  readback, and honest remaining blockers under `.divan/evidence/`.

## Acceptance Criteria

1. Five Claude packages and five Codex packages resolve the same 41 skills with
   matching versions and pass official/local validators.
2. Tagged, checksum-verified install and rollback pass on Windows plus the
   existing Linux/macOS clean-host matrix.
3. Claude and Codex global inventories show all five Divan packages enabled;
   unrelated extensions remain intact.
4. `main` is protected, required checks are enforced, CodeQL and dependency
   security are enabled, and workflow actions are SHA-pinned.
5. Lint, type-check, coverage, unit, integration, browser, schema, publication,
   and secret checks have fresh passing evidence.
6. The live Pages, Wiki, README, catalog, installation guide, changelog,
   blueprint, version, tag, and Release agree on v0.12.0.
7. A declared Claude-agent/Codex-judge A/B artifact exists and is linked from
   the v1 gate registry if it satisfies the published threshold.
8. Independent adoption remains visibly pending unless a genuine external
   submission is received; v1.0 is not tagged prematurely.
