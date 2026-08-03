# Changelog

All notable changes to Divan are recorded here. The project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses Semantic
Versioning.

## [Unreleased]

## [1.3.6] - 2026-08-03

### Added

- Added a deterministic host-state layer for install lifecycle evidence with explicit
  fallback behavior and fail-closed validation gates.
- Added a source-line alignment path for new public hosts and fallback installers with
  safer evidence checks.

### Changed

- Updated release-facing and onboarding surfaces for `v1.3.6` by design, including
  wiki/community pages, install references, marketplace metadata and install scripts.
- Improved local runtime checks around host installation and recovery command paths to keep
  clean-room behavior deterministic.

### Fixed

- Hardened `scripts/host_state.py` to fail safely when evidence checkout is not exact.
- Prevented verification false-positives in environments with strict cache directories by
  keeping release checks and install defaults deterministic.

### Verification

- `VERSION`, `scripts/release.py --check`, `python scripts/prose.py --check --json`,
  and full `python scripts/verify.py` pass for this release preparation branch.
- `python scripts/divan.py doctor --host codex --ref v1.3.6` returned `healthy`
  after the runtime and host cleanup.

## [1.3.5] - 2026-08-02

### Changed

- Synchronized release surfaces to source line 1.3.5 for runtime references,
  install targets, README/Wiki/site pages, marketplace metadata, and installer
  defaults that previously still pointed to v1.3.4.
- Hardened remote script handling in tests and docs to avoid parsing regressions
  while preserving backwards-compatible fallback behavior.

### Fixed

- Made Windows native checksum verification independent from PowerShell module path
  side effects.
- Tightened site release CTA and install entrypoints to always resolve the
  immutable latest release as authoritative source.

### Verification

- Existing release evidence for v1.3.4 remains immutable; v1.3.5 was prepared as a
  source-line update and documentation/evidence-surface alignment pass.
- `python scripts/release.py --check`, `python scripts/prose.py --check --json`,
  and full `python scripts/verify.py` passed on this branch after v1.3.5 surface
  updates.

## [1.3.4] - 2026-08-02

### Fixed

- Made the Windows legacy-host checksum path independent of the PowerShell
  `Get-FileHash` cmdlet. The installer now uses the .NET SHA-256 API, so it
  remains available when Windows PowerShell 5.1 inherits a PowerShell 7 module
  path.
- Kept the risk-hardening checks from the preceding `main` changes in the
  published source line: distributed skill provenance, public-command
  validation, dependency observation, and duplicate verification work remain
  covered by the bounded checks that introduced them.

### Verification

- Added a Windows regression that clears `PSModulePath` before exercising the
  checksum helper, the environment that exposed the portability failure.
- No runtime dependency, external repository fork, or unmeasured quality or
  speed claim was added.

## [1.3.3] - 2026-08-02

### Fixed

- Raised the verified test timeout policy from 600 to 720 seconds so the full
  repository verifier is not cut off before completion.
- Prevented post-install doctor from scanning the same transaction journal a
  second time, allowing native Codex and Claude installation checks to finish
  with a truthful `READY` result.

### Verification

- GitHub CI passed native Claude and Codex installation checks on Windows,
  macOS, and Linux, plus CodeQL, Playwright, and full validation.
- No runtime dependency or external repository fork was added.

## [1.3.2] - 2026-08-02

### Fixed

- Corrected the Turkish README release badge so every current-language badge
  points at the published source line.
- Extended the prose gate to check English and Turkish source lines and release
  badges against `VERSION`, preventing silent onboarding drift.

### Verification

- Added a regression test for bilingual release-line and badge drift.
- Stabilized the waiver evidence test so it remains valid as calendar time
  advances.
- The change adds no runtime dependency and does not vendor or fork another
  repository.

## [1.3.1] - 2026-08-01

### Fixed

- Synchronized README, quick-start, installation, status, Blueprint, Pages,
  and Wiki copy with the latest published release instead of leaving the
  previous release marked as current or the new release marked as a candidate.
- Recorded the release evidence path used by the current installation source.

### Verification

- Added a release-publication truth check so public onboarding text cannot
  point at an older release after `VERSION` advances.
- Kept the release process stdlib-only and preserved the existing five-pack,
  42-skill distribution.

## [1.3.0] - 2026-08-01

### Added

- Added a deterministic `musavir` capability scorer that validates an explicit
  task requirement ledger and reports coverage, gap, and evidence confidence
  without assigning fake intelligence or quality percentages.
- Added `musavir` audit, toolkit, and behavior-eval references for evidence
  levels, technology decisions, autonomy boundaries, and state-separated
  reporting.

### Changed

- Reframed `musavir` as an evidence-based technology and capability advisor. It
  now separates `KEEP`, `ADD`, `LATER`, `REPLACE`, and `REJECT` decisions from
  installation, commit, push, release, and live-state claims.
- Updated the public skill catalog and Blueprint so capability-audit behavior is
  part of Divan's documented product contract.

### Verification

- Added scorer unit tests for valid ledgers, malformed JSON, duplicate IDs,
  unsupported statuses, invalid IDs, invalid evidence, and traceback-free
  failures.
- Added three `musavir` contract evals. They protect against fake AI-IQ scores,
  conflicting stack dumps, and over-broad autonomous installation or publishing.

## [1.2.0] - 2026-08-01

### Added

- Added a permanent Turkish/English writing and style contract, a stdlib prose
  gate, and structured GitHub forms for bugs, features, documentation, skills,
  source candidates, and clean-room evidence.
- Added the editable `Divan — Nizamlı Müşterek` Figma source with semantic
  variables, type styles, reusable component variants, desktop/mobile layouts,
  and six tracked production assets.
- Added governance, maintainer, roadmap, release, security, and support routes
  written for first-time community contributors.

### Changed

- Rebuilt README information architecture around the questions a new user asks:
  what Divan does, what it costs, which hosts work, how to install, what to type,
  and which evidence proves completion.
- Replaced the monthly Nöbet drift alarm with text, Markdown, and JSON reports
  that record source, commits, files, category, license, local counterpart,
  decision, rationale, and evidence. The workflow reuses one issue and closes it
  when no review debt remains.
- Replaced the previous social preview and Mühürdar illustration after every
  public reference moved to the new canonical asset paths.

### Verification

- Added prose, TDK-safe spelling, README ordering, issue-form, Nöbet report,
  single-issue workflow, Figma export dimension, SVG safety, social metadata,
  and desktop/mobile public-surface tests.
- Upstream review pins 31 distributed skill counterparts at current immutable
  commits. No external repository or runtime was installed or forked.

## [1.1.0] - 2026-08-01

### Added

- Added `product-design-audit`, one evidence-based UI/UX entry point for vibe
  coders. It inspects real desktop and mobile behavior, prioritizes at most ten
  findings, and separates defects from taste.
- Reviewed eleven current UI/UX skill repositories in the Candidate Council
  with immutable commits, license evidence, overlap decisions, and no automatic
  installation. Two are clean-room adaptation candidates, eight remain
  references, and one was rejected because no redistribution license exists.

### Changed

- Explicit, bounded, reversible pre-authorization can satisfy the brainstorming
  approval gate after a compact design. Publication, release, destructive work,
  secrets, payments, messaging, and account or security changes still require
  fresh approval.
- The v1.0.3 friendly control plane remains the onboarding baseline. The
  canonical distribution now contains five packs and 42 skills; UI Pack is
  version 0.2.0.

### Verification

- Added skill-contract, license-provenance, Candidate Council, workflow, site,
  and behavior regression tests. Comparative quality is not claimed without a
  real blinded agent evaluation.

## [1.0.3] - 2026-08-01

### Fixed

- A healthy host doctor no longer recommends installing Divan again. Machine
  output keeps the public string type with `next_command: ""`; human output
  ends with a plain `READY` instruction. Attention, unavailable, invalid-JSON,
  and unfinished-transaction paths keep their exact recovery or remediation
  command.

### Changed

- Host compatibility claims now name the exact product surfaces they cover.
  Verified Codex lifecycle support applies to CLI; Desktop, the IDE extension,
  and mobile clients remain outside that claim pending separate canaries.
- README, installation guidance, and Pages now separate one-time setup,
  natural-language daily use, and maintenance/recovery. The no-checkout hero
  path uses the release bootstrap instead of assuming a repository checkout.
- Divan remains one repository with five progressive packs. No global PATH
  mutation, bulk connector authorization, external agent runtime, or copied
  skill catalog was added.

### Verification

- Added regression coverage for healthy doctor semantics, terminal-journal
  recovery, malformed host-surface data, claim boundaries, and the three-moment
  onboarding journey on both site sources.
- Canonical local verification passed 715 tests with 14 expected
  platform-specific skips on Windows 11.

## [1.0.2] - 2026-07-31

### Fixed

- Project inspection now ignores Divan-owned `.worktrees`, dependency/build
  caches, fixture trees, and skill-internal helper folders while traversing a
  parent project. Old agent branches, test fixtures, and packaged skill helper
  files no longer appear as duplicate user workspaces or extra test targets.

### Changed

- README, Pages, Wiki, and Divan Engine guidance now explain that discovery
  stays focused on the explicit project root. This keeps onboarding and Seyir
  status calmer for vibe coders without adding an external runtime, a second
  repository, or a forked dependency.

### Verification

- Added a regression test that first reproduced `.worktrees`/fixture/skill
  discovery noise as an unwanted `python` framework signal, then passed after
  the traversal contract was narrowed.
- The current repository inspection now reports one root workspace and one root
  test command for Divan instead of stale worktree or fixture-derived targets.

## [1.0.1] - 2026-07-31

### Fixed

- Standalone `divan.pyz update --execute` now uses its embedded immutable
  release identity, commit, and marketplace digest instead of treating the
  extracted bootstrap directory as a Git checkout. This repairs the real
  Windows upgrade path from an older native Codex installation while keeping
  source/ref proof, transactional rollback, and unrelated plugins intact.

### Changed

- Synchronized README, Pages, Wiki, roadmap, and project handoff with the
  verified immutable v1.0.1 Release and recorded downloaded-asset, checksum,
  SBOM, runner-identity, strict-attestation, and real Windows/Codex update
  evidence.

### Verification

- The released v1.0.0 runner reproduced the failure before any host mutation:
  its dry-run produced the correct replacement plan, while execute stopped at
  `git status` against the extracted non-Git bootstrap directory. A regression
  test now fails on that exact boundary and the related 64 upgrade, rollback,
  authority, security, and bootstrap tests pass after the fix.
- The candidate passed 698 tests with 14 expected platform skips and both PR
  quality runs. The immutable v1.0.1 Release then passed every main/publication
  workflow, seven downloaded SHA-256 checks, strict attestation verification,
  and a real update of the existing native Windows/Codex installation. Final
  doctor was healthy and a second execute was a no-op.

## [1.0.0] - 2026-07-30

Divan's first stable release freezes the tested public product contract:
one repository, five modular packages, 41 skills, Claude Code and Codex host
lifecycles, the stdlib-only Divan Engine, owner-first Divan Nizamı governance,
the installed Divan Project Contract, evidence-backed goals, and local Seyir.

### Added

- A privacy-reviewed schema-2 receipt produced by immutable v0.18.5 on Windows
  11, Codex `0.146.0`, and a real project distinct from Divan. JSON and Markdown
  both re-verify offline as `valid-clean-room-adoption`.
- The machine-backed v1 readiness score now records 8/8 completed gates while
  keeping the bounded claim separate from independent-user, endorsement,
  market-adoption, speed, or quality-improvement claims.

### Fixed

- README, Pages, Wiki, roadmap, and progress copy now names v0.18.5 as the
  latest published release instead of retaining the previous release label.

## [0.18.5] - 2026-07-30

### Fixed

- The clean-room Codex/Claude version probe now resolves the runnable Windows
  `.cmd` or `.exe` launcher before falling back to the portable command name.
  This avoids an access-denied failure when npm places an extensionless shim
  before its working `.cmd` launcher on `PATH`.

### Added

- Immutable v0.18.4 publication evidence with workflow, asset, checksum,
  attestation, Pages, Wiki, and live-readback identifiers.
- A regression test for the exact Windows launcher ordering reproduced by the
  released v0.18.4 runner on Codex Desktop.

### Verification

- The released v0.18.4 runner reached the real VERIFIED clean-room goal and
  bounded native test plan, then failed closed at the host probe. Direct
  process execution reproduced access denied for `codex` and success for
  `codex.cmd --version`; the fix selects the latter without using a shell.

## [0.18.4] - 2026-07-30

### Added

- `goal advance --evidence`, a dry-run-first way to bind new implementation,
  regression-test, or verification files to the goal receipt in the same
  atomic write as the state transition.
- Clean-room proof extraction from the actual VERIFIED transition rather than
  from all files that happened to exist in the original goal plan.
- Immutable v0.18.3 publication evidence with workflow, asset, checksum,
  attestation, Pages, Wiki, and live-readback identifiers.

### Changed

- A bug-fix intent now uses the focused six-step bug-fix workflow instead of
  also expanding generic testing and feature workflows into an 18-task graph.
- A conventional project-level `VERSION` file or an unrelated plugin
  marketplace no longer makes a distinct project look like a Divan checkout.
  Divan-owned marketplace/module signatures continue to fail closed.
- English and Turkish README, Project Contract, Wiki, Pages, Blueprint,
  progress, and release surfaces now describe the same real-evidence boundary
  and distinguish current source v0.18.4 from published v0.18.3.

### Safety

- VERIFIED rejects absolute or backslash paths, traversal, missing files,
  symlinks/reparse points, secrets, and files larger than 4 MiB before writing.
- A goal backed only by generated specification or plan artifacts cannot
  become VERIFIED. `adoption prove` independently refuses a VERIFIED goal
  without real evidence recorded on the terminal transition.
- Existing bound artifacts are preserved and new artifacts are merged
  deterministically without an intermediate partially updated receipt.

### Verification

- The canonical local verifier passes 695 tests with 14 expected
  Windows-only symlink/permission skips, plus the five-package/41-skill
  catalog, v1 registry, 230 release surfaces, Wiki, Ruff, mypy, Clean Code,
  and final repository hygiene.
- A separate Git repository reproduced a label-normalization bug, observed the
  regression test fail, applied the smallest fix, observed two tests pass, and
  reached VERIFIED only after the implementation, test, and verification
  files were hash-bound. This is local pre-release evidence, not yet the v1
  clean-room receipt.

## [0.18.3] - 2026-07-30

### Added

- `adoption prove`, a dry-run-first command that plans and executes bounded
  clean-room evidence for an existing verified goal.
- Schema-2 JSON and Markdown adoption receipts that bind an immutable Divan
  release, a project distinct from Divan, observed Claude Code or Codex
  version, test-backed checks, source stability, privacy limits, and an offline
  integrity digest.
- A machine-backed v1 gate that accepts only one repository-contained,
  privacy-reviewed `valid-clean-room-adoption` receipt whose release identity
  matches the gate registry.

### Changed

- The eighth v1 gate now measures verifiable technical evidence rather than an
  unprovable declaration that the operator is outside the maintainer group.
- Maintainer and external operator roles are retained as provenance but pass
  the same technical eligibility contract.
- GitHub intake, README, Project Contract, Wiki, Pages, progress, and impact
  rules now lead with `adoption prove` and keep v1 honestly at 7/8 until a real
  receipt from the released mechanism is committed and re-verified.
- Historical schema-1 receipts remain readable and now return explicit
  `valid-schema-1-owner-canary` or
  `valid-schema-1-independent-declaration` compatibility statuses; neither is
  eligible for v1.

### Safety

- Preview performs no writes and starts no subprocess.
- Execute uses only fixed host-version probes and allowlisted native project
  checks; it never evaluates caller-supplied shell strings, retries failed
  checks, or continues after timeout, cancellation, or source drift.
- The project runner must match its adjacent checksum, embedded source identity,
  and the digest read independently from the immutable GitHub Release API
  before planning; execution rebuilds the private plan before launch and
  rejects worktree, index, or HEAD drift.
- Goal-bound checks receive priority inside the eight-check ceiling, and
  missing native goal checks now fail closed. Canonical verification also
  reserves the complete test-class timeout instead of truncating it with a
  shorter overall workflow budget.
- Markdown verification requires the visible summary to be the canonical
  rendering of its embedded JSON envelope.
- A durable staging journal records pending state before each check. Receipt
  files are promoted atomically only after both JSON and Markdown verify
  offline.
- Receipts reject usernames, e-mail addresses, absolute paths, remote URLs,
  secrets, raw argv, command-output bodies, unrelated plugin inventory, unknown
  keys, boolean integers, and recomputed-digest schema tampering.

### Verification

- Schema-1 compatibility, schema-2 validation, proof planning/execution, CLI
  presentation, v1 registry, impact graph, bilingual public-copy, and release
  surface tests cover the new contract.
- The runtime remains nine-module and Python-standard-library-only; internal
  receipt, runner, proof-execution, and CLI dispatch helpers keep each new
  source below the clean-code ceiling. No daemon,
  database, telemetry service, external agent runtime, or second repository was
  added.
- The publication manifest tracks 229 synchronized surfaces before final
  release verification.

## [0.18.2] - 2026-07-30

### Added

- Seyir, a bilingual read-only local progress page backed by the active Divan
  goal, task graph, Git state, checks, and receipt evidence.
- A separate deterministic `divan.pyz` clean-host bootstrap that can diagnose
  Claude Code and Codex without a repository checkout or a manually supplied
  release ref.
- Evidence-backed timeout classes, packaged benchmark data, one-shot command
  execution, and a CI circuit breaker that blocks after two distinct
  evidence-backed fixes repeat the same failure fingerprint.

### Changed

- Goal execution records the active, completed, and next task so a new session
  and Seyir can resume from verified state rather than chat history.
- Windows host discovery prefers safe `.cmd`/`.exe` shims, searches the npm
  profile directory, and never selects a PowerShell `.ps1` shim.
- English and Turkish public surfaces now explain the same product identity,
  local progress path, installation boundary, and lifecycle.
- The immutable release workflow now builds, checksums, describes in SPDX,
  attests, publishes, downloads, and byte-compares seven assets, including the
  clean-host bootstrap and its checksum.

### Safety

- Seyir binds only to loopback, uses an unguessable session capability, removes
  the capability from the visible URL, performs no mutation, and fails closed
  on stale or ambiguous evidence.
- The bootstrap is locked to its canonical source, exact release tag, exact
  source commit, five-package catalog digest, and 41-skill inventory.
- Bootstrap recovery commands retain the original `.pyz` path after temporary
  extraction ends; alternate remote or local sources are rejected before host
  mutation.
- Timeout expiry never retries mutation automatically, and raw failure text or
  secrets are not persisted in the CI retry ledger.

### Verification

- The clean Windows candidate passed 642 tests with 14 expected
  platform-specific skips.
- Bootstrap builds are byte-identical with a sorted, fixed-timestamp,
  allowlisted inventory; repo-free doctor, bundled authority, durable recovery,
  Windows shim resolution, timeout policy, and circuit-breaker tests pass.
- The nine-module stdlib-only runtime remains intact and the publication
  manifest tracks 212 synchronized surfaces before final release preparation.

## [0.18.1] - 2026-07-30

### Added

- An explicit Codex Desktop `--profile auto` install path that distinguishes
  healthy, missing, non-executable, access-denied, and invalid-JSON CLI states.
- A machine-readable native-versus-skill-fallback capability contract.

### Changed

- Eligible Codex launch failures now reuse the canonical checksum-backed
  41-skill installer instead of ending at a manual troubleshooting step.
- The fallback receives the running Divan Python interpreter, so Codex Desktop
  does not depend on a separate `python` command being present on `PATH`.

### Safety

- Plain install remains native; fallback requires explicit user selection and
  dry-run remains the default.
- Invalid host JSON blocks instead of hiding a protocol incompatibility.
- Fallback completion verifies immutable ref, source commit, release archive
  SHA-256, exactly 41 skills, and every installed tree SHA-256.
- Skill fallback never claims native commands, agents, hooks, MCP
  configuration, or native lifecycle support.

### Verification

- The clean Windows candidate passed 580 tests with 13 expected
  platform-specific skips and 77% branch coverage.
- Ruff, the Clean Code debt ratchet, and mypy across 90 first-party source
  files passed. The install function's previous complexity and function-length
  debt was removed by separating host options and human output from execution.
- The isolated Windows install/remove canary produced 41 verified Divan skills,
  preserved an unrelated skill, and restored a quarantined collision.
- All nine main/publication workflows passed. The immutable Release, five
  downloaded assets, checksum manifests, SPDX 2.3 SBOM, and strict SLSA
  verification were read back successfully.
- A checksum-backed remote Windows auto-install canary discovered all 41
  skills in a fresh process, preserved an unrelated skill, and removed only
  Divan-owned files during rollback. Pages/Wiki publication truth is recorded
  in the immutable release evidence.

## [0.18.0] - 2026-07-29

### Added

- Nizam-i Sefer planning intelligence: deterministic complexity, host/context
  uncertainty, bounded parallel workstreams, sefer handoffs, stage task graphs,
  model capability classes, and public-surface obligations.
- `--host-profile`, `--context-window`, and `--target` planning controls.
- Goal-local `route.json`, bound into the existing evidence receipt.
- Explicit dependency-graph workstream lanes that join at integrated
  verification, while sefers remain sequential context/handoff windows.
- A mandatory independent-review gate for every workflow that declares the
  independent reviewer role.

### Changed

- The Sadrazam package advances to `0.10.0`, so host caches and upgrade
  evidence cannot confuse this planning-capability release with v0.17.1.
- A sefer is a sequential context and handoff window; independent workstreams
  are explicit dependency-graph lanes that converge at integrated
  verification. Public language no longer presents the two concepts as the
  same thing.
- The existing nine-module Divan Engine remains the canonical stdlib-only
  runtime. Planning policy belongs to the council module and does not create a
  tenth module, external agent runtime, second repository, or mandatory MCP
  dependency.

### Safety

- Context fallback numbers are explicit planning assumptions, never
  vendor-verified product limits.
- Codex GPT-5.6 Luna/Terra/Sol values are candidates chosen by risk class; the
  host must confirm availability before execution.
- Security, production, release, credential, package-manager conflict,
  financial, and destructive/production-data signals cannot fall through to
  the economy model class.
- Planning performs no model call, target-project command, dependency install,
  daemon startup, or external harness activation.

### Verification

- The implementation pull request passed 562 tests with 11 expected
  platform-specific skips and 75% coverage. Quality Gate, CodeQL, dependency
  review, Pages/Wiki checks, Playwright, and the Claude/Codex compatibility
  matrix were green before merge.
- Two independent read-only reviews were completed. Their task-ownership,
  monorepo-command, legacy-goal, impact-graph, risk-floor, independent-review,
  and parallel-semantics findings were addressed before the protected squash
  merge.
- Planning remains deterministic and side-effect free. Exact model
  availability, native host execution, independent adoption, and measured
  productivity improvement are not claimed by this release.

## [0.17.1] - 2026-07-29

### Added

- One canonical Vibe Progress Protocol for substantial Divan work, with calm
  phase language, meaningful update cadence, real-blocker handling, and short
  `Şu anda` / `Ne öğrendim` / `Sırada` guidance.
- Focused regression coverage for the Sadrazam contract, all seven public chat
  entry commands, synchronized public documentation, and Pages source.

### Changed

- Sadrazam and all seven public chat commands now share one progress contract
  instead of exposing command-by-command activity. Each command resolves the
  contract from the loaded-plugin root rather than the user working directory.
- Public English and Turkish surfaces explain that Divan keeps engineering
  detail in the background while reporting what is happening, why it matters,
  and what comes next.
- The Sadrazam package advances to `0.9.2`; the Divan Engine, nine-module graph,
  authority order, runtime APIs, and bounded v1 compatibility paths are
  unchanged.

### Trust and accessibility

- Planning, implementation, testing, GitHub delivery, merge, publication, and
  live verification remain separate evidence claims.
- Status does not depend only on color, emoji, Ottoman metaphor, or an invented
  percentage. Secrets, hidden reasoning, raw logs, and private scratch work are
  excluded from routine progress updates.
- Semantic progress states have English and Turkish labels and follow the
  user's language instead of forcing Turkish labels into English conversations.
- This skill-level communication contract does not claim control over the
  native Codex or Claude Code interface and adds no runtime, MCP, external
  repository, hosted service, or third-party dependency.
- Repository tests prove the contract and publication surfaces, not a new
  real-agent A/B result; real-host transcript evaluation remains separate.

### Verification

- The clean Windows candidate passed the canonical verifier: 544 tests passed,
  14 platform-specific tests skipped, and final hygiene remained clean.
- Five packages, 41 skills, 151 release surfaces, the handoff contract, v1
  scorecard, release consistency, and eval contract passed.
- Independent whole-change review reported no open P0-P3 findings and approved
  the local release gate. GitHub PR, protected merge, immutable Release, Pages,
  and Wiki remain separate delivery states until their identifiers are bound.

## [0.17.0] - 2026-07-29

### Added

- A canonical stdlib-only `divan_runtime` package with a machine-readable
  nine-module graph covering kernel, governance, council, evidence, project,
  records, providers, release, and API/compatibility responsibilities.
- A bilingual Divan Nizamı authority contract ordered as
  `owner/Hükümdar → mandate/Ferman → orchestrator/Sadrazam → council/Divan →
  specialist/Uzman → provider/Sağlayıcı`.
- `python scripts/divan.py architecture --json` for deterministic inspection
  of the product, module dependencies, authority chain, and no-external-runtime
  invariant.
- A deterministic mutation envelope that binds public CLI arguments to a
  Ferman id, records the local authority source, and rejects delegated actors
  attempting `--execute`.
- Canonical Divan Engine and Divan Project Contract / Divan Proje Sözleşmesi
  guides plus ADR 0007 for the one-product architecture.

### Changed

- Divan is presented as one product in one repository. Divan Engine names its
  execution core, Divan Nizamı its governance model, and Divan Project Contract
  the supervised layer installed into a target repository.
- Hükümdar is the final authority. Only `owner` may expand scope; every
  delegated layer receives narrower authority and tool availability never
  grants permission by itself.
- Canonical CLI, project runner, quality, Wiki, and public documentation
  surfaces use `divan_runtime`, `validate`, Divan Engine, and Divan Project
  Contract terminology.

### Compatibility

- Existing `plugins/sadrazam/company/` Python and JSON paths, `/company`,
  `company-validate`, Company OS, and Project OS remain bounded compatibility
  surfaces through v1 and will not be removed before v2.
- Existing `.divan/` data, DCS/DPS identifiers, generic CLI commands, project
  ownership records, receipts, hashes, and provider identifiers remain stable.

### Security

- The engine contract rejects missing, duplicate, or cyclic modules and
  authority rows that let a delegated layer expand scope. Runtime inventory
  and AST import edges must match the declared graph; undeclared, symlinked,
  out-of-root, or third-party runtime modules fail closed.
- Canonical runtime loading is source-bound and isolated from ambient Python
  module caches, including legacy compatibility and repository validation.
- Divan Nizamı is local workflow governance, not identity authentication. Host
  operating-system and repository permissions remain the security boundary.
- The core remains in the Divan repository and adds no third-party agent
  runtime or external-repository dependency. Connected providers remain
  bounded capabilities rather than sources of authority.

### Published evidence

- Local verification passed 538 tests with 7 platform skips and 76% coverage,
  plus Ruff, mypy, Clean Code, 41 Agent Skills, strict Claude validation, and
  deterministic runner checks. Final independent re-review reported no open
  P0-P3 findings.
- PR #49 passed all seven required pull-request workflows and merged as
  `8b711b6f0ebb696ce971d83c90833bb59acf3c34`. The immutable `v0.17.0`
  tag/Release, five checksummed assets, SPDX 2.3 SBOM, two attestations per
  asset, Pages, and Wiki were independently read back. Exact identities and
  digests are recorded in
  `.divan/evidence/teftis-20260729-v017-release.md`.
- Publication does not close independent-adoption issue #34; v1 readiness
  remains 7/8 until reproducible, privacy-bounded evidence arrives from a
  non-owner.

## [0.16.0] - 2026-07-24

### Added

- Schema 2 installed-project ownership with immutable Divan source identity,
  project identity, and hashes for every managed whole file or marked block.
- Read-only `project status`, dry-run-first transactional `project update`, and
  intentionally narrow `project repair` commands with fail-closed drift,
  marker, symlink/reparse, stale-plan, and unowned-path handling.
- Verified goal archival with receipt/artifact hash binding, collision checks,
  controlled source removal, and rollback on interrupted application.
- Privacy-bounded JSON and Markdown adoption receipts with explicit
  maintainer/independent declarations and offline verification.

### Changed

- `divan-project.pyz` now carries source metadata schema 2 and the complete
  ownership, lifecycle, archive, and adoption engine while retaining
  deterministic byte-identical builds.
- DCS-007 and the impact graph now cover host lifecycle and installed-project
  lifecycle together. English/Turkish README, Project OS, install, Wiki, and
  publication surfaces distinguish host update, project update, audit, and
  lifecycle status.
- Ruff, mypy, coverage, and the Clean Code debt ratchet now include the
  first-party Company OS runtime instead of measuring only `scripts/` and
  `evals/`. Existing exact-symbol debt is pinned and cannot grow silently.

### Security

- Project updates run only from the immutable code already executing; they do
  not fetch remote refs or execute target-project code. Install state is written
  last inside the proven locked, journaled, authority-bound transaction.
- Repair never force-overwrites user changes. Adoption exports reject secrets,
  email addresses, usernames, absolute paths, remotes, unrelated plugin
  inventory, and command-output bodies.

### Verified

- The release candidate passed the full local unit suite with 10
  platform-specific skips plus focused lifecycle, archive, adoption,
  reproducible-runner, Unicode, and fail-closed impact tests.
- Five packages and 41 discoverable skills remain unchanged. Owner-operated
  canary evidence is classified separately and cannot close the independent
  adoption gate; v1 readiness remains 7/8.
- PR #31 and all required checks completed; immutable `main`/tag
  `5513e73d5faa8657a22d813ecfec763a6089bea0`, GitHub Release, five recomputed
  assets and checksum manifests, SPDX SBOM, release/SLSA attestations, Pages,
  and Wiki are bound in tracked post-merge evidence. Owner canary, dual-host
  global update, and independent adoption remain separate unverified states.

## [0.15.0] - 2026-07-24

### Added

- A portable Project OS contract with deterministic `init`, `inspect`, `audit`,
  `plan`, `impact`, `goal`, `verify`, `release`, and receipt-verification
  routes. Installed projects receive bounded `.divan/` rules, specs, plans,
  tasks, waivers, and append-only evidence without losing existing host text.
- Twelve `DPS-*` installed-project standards, scoped by project type, alongside
  Divan's existing `DCS-*` repository-maintenance standards.
- Unicode-aware English/Turkish intent routing, recursive bounded workspace
  discovery, native package-manager command detection, multi-workflow
  composition, and fail-closed impact classification.
- Provider capability contracts for local, GitHub, Context7, and Vercel
  delivery; a read-only composite action; and a reproducible standalone
  `divan-project.pyz` runner.
- Static public-web SEO contracts covering canonical metadata, robots,
  sitemap, hreflang, social cards, structured data, internal links, and pinned
  Lighthouse CI/Lychee evidence.

### Changed

- Sadrazam can carry a supervised goal from intent through specification,
  planning, verified evidence, preview, release, and live observation while
  keeping provider mutations behind explicit authority.
- English machine interfaces and public technical documentation are canonical;
  Turkish localization remains synchronized and first-class. Existing Turkish
  script names remain bounded compatibility wrappers throughout `0.x`.
- README, Project OS and Company OS guides, Community Standards, Wiki sources,
  Pages/site metadata, install references, and release manifests now share one
  change-impact and publication contract.

### Security

- Project discovery never executes target code, rejects symlink/path escape,
  bounds traversal and input sizes, and reports every unknown changed path as
  `unclassified`.
- Project initialization is dry-run-first, idempotent, transactionally locked,
  atomic, and fail-closed on malformed managed blocks or untrusted recovery
  state.
- Release completion requires provider-native, source-bound evidence and live
  readback. Missing capabilities remain `BLOCKED`; ambient executables,
  environment variables, local JSON, secrets, and hidden reasoning cannot
  establish release authority.

### Verified

- The approved release candidate passed 452 repository tests with 10
  platform-specific skips, Ruff, mypy, the Clean Code debt ratchet, and 71%
  branch coverage against the 64% floor.
- Five packages and 41 discoverable skills remain unchanged. The independent
  adoption gate remains open, so v1 readiness honestly stays 7/8.
- This section records local release preparation only. PR checks, immutable
  `main`, tag, GitHub Release, Pages, Wiki, attestations, and dual-host global
  installation require separate post-merge evidence.

## [0.14.1] - 2026-07-23

### Fixed

- Codex marketplace snapshots now accept Codex's validated, isolated
  `.codex-marketplace-install.json` metadata file even when the CLI reports an
  explicit marketplace ref. Other untracked files, malformed metadata, source
  drift, and ref drift remain fail-closed.

## [0.14.0] - 2026-07-23

### Added

- Company OS contracts for 12 functional roles, 8 delivery workflows,
  evidence-based framework detection, and transitive change-impact analysis.
- A portable `scripts/divan.py` CLI for project inspection, planning, impact
  analysis, contract validation, install, update, doctor, and recovery.
- DCS-011 and a machine-readable naming policy enforcing English canonical
  technical entrypoints with Turkish localization and bounded legacy aliases.
- English and Turkish Company OS guides plus synchronized Pages and Wiki entry.

### Changed

- Sadrazam now routes natural-language intent through Company OS and selects the
  smallest justified combination of Core, UI, React, and Zanaat packs.
- English is the canonical README and contributor surface; Turkish remains
  first-class through `README.tr.md` and `CONTRIBUTING.tr.md`.
- Workflows and maintainer scripts use English canonical names. Pre-v1 Turkish
  script names remain narrow deprecated wrappers to avoid breaking users.

### Security

- Project inspection is bounded, read-only, path-safe, and never executes
  project code.
- Framework packs are selected from manifest evidence; integrations and
  creative tooling are not activated for unrelated tasks.

## [0.13.0] - 2026-07-21

### Added

- A machine-readable registry for DCS-001..DCS-010, narrow expiring
  exceptions, deterministic documentation, and a CI enforcement gate.
- Read-only `--doctor`, dry-run-first `--upgrade`, and ownership-checked
  interrupted-transaction recovery for Claude Code/Desktop Code and Codex.
- Deterministic SPDX 2.3 SBOM generation, OpenSSF Scorecard, pull-request
  dependency review, and release provenance for both ZIP and SBOM assets.
- Bilingual contribution guidance, request-specific support routes, and a
  version-controlled 1280x640 Mühürdar social preview under 1 MB.

### Changed

- New code is ratcheted at McCabe 10, 50 lines per function, and 400 lines per
  module. The enforced branch-coverage floor is the recorded 64% baseline.
- The legacy-debt registry must exactly match current violations; growth is
  rejected and shrinkage/removal requires the same reviewed baseline refresh.
- Host adapters, transaction journals, lock/transition validation, eval
  provenance, and result contracts moved into smaller stdlib modules.
- README, Wiki sources, Pages, install, upgrade, rollback, uninstall, and
  contribution surfaces now share one five-minute first-success path.

### Security

- Upgrade refuses host mutation until it proves a clean pinned source commit,
  catalog digest, full package fingerprints, and a single active transaction.
- Durable intent is written before every external mutation. Verification and
  rollback touch only transaction-owned Divan rows and reject foreign state.
- GitHub Actions remain full-SHA pinned, narrowly permissioned, and release
  assets are never overwritten.
- Social-preview validation traverses every PNG chunk and requires valid CRCs,
  one exact IHDR, at least one IDAT, and a terminal empty IEND.

### Verified

- Local pre-release integration passed 223 tests (2 platform-specific Windows
  skips), Ruff, mypy, Clean Code, actionlint 1.7.10, skills-ref 0.1.1 for all
  41 skills, and Claude Code 2.1.212 for the marketplace and five packages.
- This is local release-candidate evidence. PR/main, repository rules, Pages,
  Wiki, tag, GitHub Release, attestations, and global v0.13.0 host upgrade are
  separate delivery states that remain pending.
- v1 remains 7/8 because no independent non-owner acceptance evidence exists.

## [0.12.2] - 2026-07-20

### Fixed

- `scripts/hijyen.py --clean` artık Windows'ta salt-okunur özniteliği taşıyan
  allowlist cache ağaçlarını, silme sınırını genişletmeden yazılabilir yapıp
  kalıcı kaldırır.
- Windows salt-okunur `__pycache__` regresyonu birim testine bağlandı.

## [0.12.1] - 2026-07-19

### Added

- `scripts/hijyen.py --check/--clean`: UTF-8/BOM/mojibake denetimi, açık
  subprocess kodlaması kuralı ve yalnız yeniden üretilebilir cache'leri silen
  fail-closed repo temizliği.
- UTF-8/LF editor ve Git sözleşmesi ile Ruff C90 McCabe 25 karmaşıklık bütçesi.

### Changed

- Pazar, skill, belge, ajan ve vitrin denetimleri isimli tek-sorumluluk
  fonksiyonlarına ayrıldı; kurulum rollback'i ile v1 kanıt doğrulaması aynı
  public davranışı koruyan aşamalara bölündü.
- Windows sistem locale'ine bırakılan host CLI ve Git metin çıktıları açık
  `encoding="utf-8"` sözleşmesine geçirildi.

### Security

- Temizlik allowlist dışındaki yedek, manifest, kanıt ve kullanıcı dosyalarını
  silmez. Aktif rollback yedekleri korunur; yalnız üretilebilir cache içeriği
  kalıcı kaldırılabilir.

## [0.12.0] - 2026-07-19

### Added

- Native Codex marketplace manifests for the same five packages and 41 skills
  already published through Claude Code, with a cross-host drift validator.
- Dry-run-first transactional installer for Claude Code/Desktop Code and Codex;
  it records pre-state, preserves unrelated plugins, verifies all packages, and
  rolls back only entries created by the failed transaction.
- First-party real-provider evaluation adapters: Claude Code as the bounded
  agent and an ephemeral read-only Codex process as the blinded JSON judge.
- CodeQL, Ruff, mypy, Coverage, actionlint, and immutable GitHub Action pins.

### Changed

- The legacy loose-skill installer is now a compatibility fallback. Release
  archives are SHA-256 verified before extraction and manifests record version,
  ref, source commit, archive hash, per-skill installed hash, install time,
  target, and backup. Migration preflights every row, quarantines owned content,
  preserves changed targets, and reverses every move on failure.
- Site navigation now has a keyboard-visible skip link, one main landmark,
  WCAG AA coral contrast, reduced-motion verification, and mobile/landscape
  overflow checks in real Chromium.
- Root licensing is canonical MIT with separate notices; 15 current upstream
  differences were reviewed and pinned without automatically copying content.

### Security

- Release workflows publish a versioned fallback archive and checksum with its
  source commit; mutable `main` downloads, mutable Action tags, moved release
  tags, and release-asset overwrite attempts are rejected.
- Host mutations are atomically journaled before execution and interrupted
  transactions have an ownership-checked, resumable recovery command. Legacy
  migration and fallback copying use their own durable, reversible journals;
  parent rollback restores even a completed legacy migration before removing
  native packages and fails closed if the recorded legacy journal is missing.
- Eval subprocesses are bounded, do not use dangerous bypass flags, redact
  secrets/PII/home paths, keep per-case A/B outcomes private, and bind publishable
  provenance to a clean Git HEAD plus provider-derived versions. Windows
  provider `.cmd` wrappers are resolved without invoking a shell for other
  commands, adapter JSON I/O is explicitly UTF-8 across platforms, and the
  Codex judge disables plugins while using a strict static score-array schema.

### Verified

- Fixture and repository tests prove host preservation/rollback, checksum
  fail-closed behavior, transactional legacy quarantine, marketplace parity,
  blind judging, and accessibility.
- A publishable first-party comparison ran three `baglam-muhafizi` cases with
  Claude Code 2.1.209 / `claude-sonnet-5` as the bounded agent and Codex CLI
  0.144.4 / `gpt-5.6-terra` as the blinded judge. The skill condition won zero
  cases, baseline won one, and two tied; no release threshold was predeclared,
  so this is auditable run evidence rather than a quality-improvement claim. Independent
  adoption remains pending for v1.
- Public eval evidence uses a commit-reveal boundary with a runner-generated
  256-bit OS-random seed: the raw blinding seed, condition mapping, per-case
  winner, and judge reasons remain in the private
  key while the public provenance records only the seed's SHA-256 commitment.

## [0.11.1] - 2026-07-18

### Added

- Repository-root `CLAUDE.md`, giving Claude Code a native durable handoff
  contract instead of relying on prior chat context.
- `scripts/devral.py --check` and regression tests that reject a missing
  handoff chain or a progress journal without an exact next action.
- GitHub Actions Dependabot configuration and CODEOWNERS coverage for policy,
  automation, release, registry, and project-memory surfaces.

### Changed

- Sadrazam advanced to 0.9.1; SessionStart now surfaces the Claude handoff
  contract before the current progress journal.
- Publication and local audit gates now cover Claude handoff and dependency
  maintenance as release-controlled surfaces.

### Security

- Guidance distinguishes controls stored in Git from GitHub settings requiring
  platform verification: rulesets, required reviews, secret scanning, push
  protection, Dependabot alerts, and CodeQL.

## [0.11.0] - 2026-07-18

### Added

- Publication control plane with a machine-readable surface manifest,
  deterministic version preparation, drift checks, and changelog-derived
  GitHub Release notes.
- Idempotent `main` workflow that waits for matching Pages and Wiki versions,
  then creates the immutable tag/Release or updates notes without moving a tag.
- Clean-host compatibility matrix: official Claude Code marketplace validation
  plus Codex install/discovery/removal on Ubuntu, macOS, and Windows.
- Manifest-driven Codex removal/rollback scripts, independent adoption evidence
  issue form, and a generated machine-readable v1 readiness scorecard.
- `/yayin` command and Sadrazam publication-surface law so future agents do not
  rely on the user to remind them about README, Wiki, site, or Release pages.

### Changed

- Sadrazam advanced to 0.9.0 and the public publication contract now treats
  README, marketplace, Pages, Wiki, changelog, tag, and GitHub Release as one
  ordered but separately verified delivery chain.
- v1 claims are gated by eight explicit evidence records; real-agent comparison
  and independent adoption remain pending instead of being inferred.

### Verified

- Unit coverage rejects stale public surfaces, validates release-note sourcing,
  checks the generated v1 scorecard, and rehearses installer rollback.
- GitHub's official documentation was used for least-privilege
  `contents: write`, non-recursive `GITHUB_TOKEN` behavior, and workflow
  concurrency design.
- PR #12 and all seven post-merge workflows passed. The release workflow
  verified Linux/macOS/Windows rollback, live Pages and Wiki markers, and the
  interactive site in Chromium before publishing tag/Release v0.11.0 at
  commit `5680337a`.

## [0.10.3] - 2026-07-18

### Added

- Deterministic Vezir Catalog generator and exact drift tests over all 41 skill
  frontmatter records.
- Explicit Wiki initialization preflight with the one required `Save Page`
  recovery action instead of an opaque clone failure.

### Changed

- GitHub Actions moved to the current major releases observed from their
  official repositories: checkout v7, setup-python v6, setup-node v7, and
  github-script v9.
- Repository guidance and contribution checks now require catalog validation.

### Fixed

- Multi-line YAML descriptions are rendered correctly; `claude-api` no longer
  appears as the broken `/-…` text in the public catalog and Wiki source.

### Verified

- GitHub repository and workflow state, the live Wiki HTTP 404, failed publish
  job steps, Context7's GitHub Docs result, current Codex manual, and active
  Mühürdar pet were inspected independently.
- The first Wiki page was initialized by the repository owner; raw `Home.md`
  returned HTTP 200 before the full 16-page source sync was triggered.

## [0.10.2] - 2026-07-18

### Added

- **Aday Meclisi:** machine-readable candidate registry with a deterministic
  human catalog and an explicit `never-auto-install` autonomy boundary.
- Structured GitHub source-candidate issue form for user gap, exact license,
  execution surface, and evidence—not popularity alone.
- Weekly read-only GitHub discovery workflow that opens a bounded triage issue,
  excludes known/upstream repositories, and never downloads candidate code.
- Candidate validation for canonical identity, duplicate IDs/URLs, lifecycle
  state, license evidence, decision consistency, review dates, and proof count.

### Changed

- `kaynak-kuratori` now persists discovery into the Meclis lifecycle and keeps
  ADOPT/ADAPT decisions separate from actual installation or vendoring.
- Core pack advanced to 0.5.1; public documentation now exposes how Divan grows
  continuously without turning an “awesome list” into trusted executable code.

### Verified

- The reference audit of `punkpeye/awesome-mcp-servers` records it as a
  MIT-licensed registry/index and explicitly re-audits every downstream item.
- Tests reject duplicate URLs and license-unknown ADOPT decisions and require
  the generated catalog to match the registry exactly.

## [0.10.1] - 2026-07-18

### Added

- Versioned GitHub Wiki manifest, deterministic builder, link/version checks,
  and a generated navigation sidebar.
- Fourteen intent-first Wiki pages covering quick start, current status,
  roadmap, OpenAI/Codex boundaries, and the Mühürdar verification mascot.
- `wiki-sync` Actions workflow: validates Wiki sources on pull requests,
  publishes them to the separate Wiki Git repository after `main`, and reads
  the live `Home.md` back before succeeding.

### Changed

- Sadrazam 0.8.1 now treats enabled Wikis, docs sites, and help centers as
  product surfaces with a canonical source, automated synchronization, and
  explicit live-publication evidence.
- README, English README, landing, roadmap, pull request template, and agent
  guidance now include the Wiki in the same publication contract.
- OpenAI/Codex documentation now distinguishes portable Agent Skills from the
  OpenAI Agents SDK application runtime and links to current official guides.

### Verified

- Wiki compilation is deterministic and rejects missing sources, duplicate
  slugs, broken internal links, and version drift.
- Unit coverage exercises manifest integrity, generated pages/sidebar, and
  version/link consistency.

## [0.10.0] - 2026-07-18

### Added

- Provider-neutral skill-vs-baseline eval runner with 12 cases across four
  original skills.
- JSON stdin/stdout adapter protocol for real agents and optional blind judges.
- A/B blinding, separate reveal keys, timeouts, zero-case failure, and optional
  minimum skill win-rate gates.
- Interactive five-intent decree selector for vibe coders.
- Persistent v0.10 product plan grounded in the official OpenAI agent-evals
  progression from traces to repeatable datasets and eval runs.

### Changed

- Pull-request site CI now tests the proposed `docs/` build locally instead of
  testing the old production page. Every `main` push now waits for the matching
  Pages version and repeats the browser test live; scheduled runs keep watch.
- Product pages now lead from user intent to the smallest pack, a copyable
  decree, and an observable delivery path.
- Marketplace advanced to 0.10.0 and Sadrazam to 0.8.0 with persistent
  intent-first routing and honest eval-evidence rules.

### Verified

- Eval contract discovery reports four skills and 12 non-empty cases.
- Unit tests cover discovery, zero-case failure, A/B blinding, judge mapping,
  threshold behavior, and review-required results.
- Static site JavaScript passes syntax validation; GitHub Actions browser proof
  is recorded with the publication evidence.

## [0.9.0] - 2026-07-18

### Added

- Native-first `ordu-nizami` orchestration and `/sefer` command.
- Evidence-first `arama-ustasi` codebase search.
- `baglam-muhafizi` context-budget and handoff discipline.
- `kaynak-kuratori` repository/license/provenance curation with three eval cases.
- English product README and persistent `.divan/` delivery records.
- Publication Law: a draft PR is not considered a public delivery.
- Version, changelog, roadmap, and public-surface consistency gates.

### Changed

- Marketplace version advanced to 0.9.0 because this release adds public,
  backward-compatible capabilities rather than a patch-only fix.
- Core pack advanced to 0.5.0 and Sadrazam to 0.7.0.
- README now explains why the project exists, how it improves itself, and which
  v1.0 claims are intentionally not made yet.
- Upstream audit now recognizes the original `kaynak-kuratori` workflow instead
  of looking for a nonexistent vendored copy.

### Verified

- Repository unit tests and local audit.
- Official Agent Skills validation for all 41 skills.
- Claude Code strict marketplace and plugin validation.
- GitHub Actions repository audit and Playwright site test.

## [0.7.0] - 2026-07-17

### Added

- 37-skill, five-pack marketplace baseline.
- Curated CC0 rule treasury and original `temkin` engineering prudence.
- Monthly upstream monitoring, community files, GitHub Pages, and local audits.

[Unreleased]: https://github.com/trugurpala/divan/issues
[1.0.2]: https://github.com/trugurpala/divan/releases/tag/v1.0.2
[1.0.1]: https://github.com/trugurpala/divan/releases/tag/v1.0.1
[1.0.0]: https://github.com/trugurpala/divan/releases/tag/v1.0.0
[0.18.0]: https://github.com/trugurpala/divan/releases/tag/v0.18.0
[0.17.1]: https://github.com/trugurpala/divan/releases/tag/v0.17.1
[0.17.0]: https://github.com/trugurpala/divan/releases/tag/v0.17.0
[0.16.0]: https://github.com/trugurpala/divan/releases/tag/v0.16.0
[0.15.0]: https://github.com/trugurpala/divan/releases/tag/v0.15.0
[0.13.0]: https://github.com/trugurpala/divan/releases/tag/v0.13.0
[0.11.0]: https://github.com/trugurpala/divan/releases/tag/v0.11.0
[0.10.3]: https://github.com/trugurpala/divan/tree/main
[0.10.2]: https://github.com/trugurpala/divan/tree/main
[0.10.1]: https://github.com/trugurpala/divan/tree/main
[0.10.0]: https://github.com/trugurpala/divan/tree/main
[0.9.0]: https://github.com/trugurpala/divan/tree/main
[0.7.0]: https://github.com/trugurpala/divan/releases/tag/v0.7.0
