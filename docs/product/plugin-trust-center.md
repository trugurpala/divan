# Divan Plugin Trust Center — Product Contract

## Product promise

Divan should make third-party extensibility understandable without turning trust into a marketing badge.

The Plugin Trust Center answers five questions before any future activation path exists:

1. What is this plugin?
2. Where did it come from and under which license?
3. What capabilities does it request?
4. Is the exact manifest and executable identity known?
5. What still prevents activation?

The UI must never collapse `valid`, `available`, `approved`, `enabled`, and `trusted` into one state.

## Primary user

The first-release user is a local Windows operator who may be comfortable asking Codex or Claude to change code but should not need to understand Python package internals, Rust plugin wiring, or operating-system sandbox terminology.

Advanced provenance remains visible, but the first sentence on every state must explain the practical consequence in plain language.

## Core lifecycle

The canonical trust lifecycle is:

`DISCOVER -> VALIDATE -> APPROVE -> ENABLE`

The current SDK slice implements static inspection only. Desktop may display:

- `invalid` — manifest contract failed; do not offer approval.
- `executable-missing` — manifest is valid but the declared sidecar cannot be resolved or hashed.
- `approval-required` — manifest and executable are known; no activation claim is allowed yet.

Future persisted approval and activation states must be introduced only with separate reviewed contracts.

## Information architecture

### Navigation

Use one first-class `Plugins / Eklentiler` destination. Do not bury plugin safety inside generic Settings.

The destination is a trust center, not a marketplace. Discovery and provenance come before installation or promotion.

### Empty state

Show three steps:

1. Choose a manifest.
2. Divan validates it without executing plugin code.
3. Review source, license, capabilities and hashes.

Primary action: `Manifest incele`.

Do not show `Install`, `Enable`, `Approve`, `Run`, or marketplace language before those operations exist safely.

### Inspection summary

The first viewport should contain:

- status label with text, never color alone;
- plugin display name, id, version and kind;
- mutation classification;
- executable availability;
- manifest and executable SHA-256 presence;
- activation blocker.

### Capability disclosure

Capabilities are grouped by practical effect:

- Read project: `project.read`, `git.read`.
- Change project: `project.mutate`, `git.mutate`.
- Start process: `process.spawn`.
- Use network: `network.outbound`.
- Read/emit evidence: `evidence.read`, `evidence.emit`.
- Review/provider read access: `review.read`, `provider.read`.

Mutation capabilities must carry explicit `Değişiklik yapabilir` text and must never be represented only by a warning color.

Reserved Divan authority is never presented as grantable:

- `authority.expand`
- `approval.grant`
- `evidence.rewrite`
- `merge.commit`
- `release.promote`

If a manifest requests one, the product state is invalid rather than `high risk` or `needs confirmation`.

## Provenance presentation

Show source URL, SPDX license expression and license evidence as copyable text in the future. Do not automatically open remote URLs during inspection.

The first SDK inspection response intentionally returns only local file basenames plus SHA-256 digests. Absolute local manifest/executable paths are not part of the report contract.

The UI may disclose the exact local path later only behind an explicit local diagnostics affordance; it must not enter task evidence or telemetry by default.

## Visual hierarchy

Divan already uses a dark command-center visual language. Plugin Trust Center should extend it rather than invent a marketplace aesthetic.

Use:

- one primary gold/accent action per screen;
- neutral bordered surfaces for provenance and capability groups;
- status text + icon/shape + color redundancy;
- monospace only for ids, capabilities and hashes;
- no gradients, animated glow, trust scores or gamified safety meters;
- no green `Trusted` badge based only on schema validation.

Hash values should be readable in grouped form, with the full value available without forcing horizontal page scroll.

## Interaction rules

### Manifest selection

Desktop uses the existing native Tauri dialog capability. The user selects one JSON file explicitly.

Divan must not recursively scan the user disk from this interaction.

### Inspection

Inspection calls Divan Core `plugin.inspect`.

The command:

- reads static UTF-8 JSON;
- validates the SDK manifest contract;
- resolves a bare executable command with Divan's bounded executable locator;
- hashes manifest and resolved executable;
- never imports third-party Python;
- never executes the plugin;
- never persists approval;
- returns a privacy-bounded report.

### Errors

Validation errors are shown as stable error code + plain-language explanation.

Examples:

- `PLUGIN_CAPABILITY_RESERVED` — “Bu yetki Divan'a aittir ve eklentiye devredilemez.”
- `PLUGIN_READ_ONLY_KIND_MUTATES` — “Reviewer/provider/evidence eklentileri projeyi değiştiremez.”
- `PLUGIN_MUTATION_REQUIRES_MANDATE` — “Değişiklik yapan engine, Divan mandate zorunluluğunu açıkça kabul etmelidir.”

Unknown failures must never convert into an approval-ready state.

## Accessibility contract

The production component must:

- use semantic heading order;
- expose inspection result changes through a polite live region;
- keep native button focus behavior;
- never rely on color alone;
- preserve readable text at 200% zoom;
- avoid horizontal page scrolling for hashes and capabilities;
- provide a visible label for the manifest-selection control/action;
- keep disabled future actions out of the primary task path rather than presenting an unexplained dead button.

The Desktop shell keeps its native Tauri window floor, while CSS reflows at narrower CSS viewports so Windows display scaling and browser zoom do not force the three-column layout indefinitely.

## Tauri least-privilege rule

Tauri 2 plugin commands remain blocked until granted through capabilities/permissions. Divan will add official Desktop plugins only with the minimum permission set needed by the feature.

The preferred post-stable order remains:

1. `single-instance`;
2. privacy-minimal `log`;
3. `window-state`;
4. `notification` after explicit permission;
5. narrowly scoped `opener`.

Broad `fs`, `http`, `sql`, `store`, `websocket` and clipboard-read permissions are not baseline Plugin Trust Center requirements.

Single-instance must be registered first when introduced, matching Tauri's desktop plugin ordering requirement.

## World-class quality gates

A Plugin Trust Center change is not complete unless all applicable gates pass:

- manifest/runtime architecture validation;
- Ruff and clean-code;
- Mypy;
- canonical unit suite + coverage;
- Desktop TypeScript build;
- Windows Desktop Build;
- CodeQL and dependency review;
- accessibility/source-contract tests for new UI states;
- no new Tauri permission without an explicit feature reason.

## Current implementation slice

Implemented on `feat/plugin-sdk-v1`:

- fail-closed manifest contract;
- bounded Windows-aware executable resolution;
- manifest + executable SHA-256 binding;
- privacy-bounded Desktop trust report;
- read-only `plugin.inspect` Core command;
- first-class Desktop `Eklentiler` destination;
- native JSON-only manifest selection;
- plain-language identity, provenance, capability and mutation disclosure;
- context-aware Plugin Trust inspector rail;
- stable Core/protocol/UI permission-boundary tests;
- zoom-safe responsive Desktop reflow;
- no activation, installation, marketplace, auto-update or webview-permission expansion.

## Next reviewed slices

### Slice 3 — Persistent owner approval

Add identifier-scoped local approval persistence that binds plugin id, decision, approved capabilities, manifest hash and executable hash. Any drift invalidates the approval.

### Slice 4 — Sidecar protocol execution

Define request/response framing, timeout, cancellation, stdout/stderr redaction, mandate propagation and evidence binding before the first third-party plugin can run.

### Slice 5 — First adapters

Prefer evidence-first adapters:

- Playwright evidence — https://github.com/microsoft/playwright
- Semgrep read-only reviewer/evidence — https://github.com/semgrep/semgrep
- Syft SBOM evidence — https://github.com/anchore/syft
- OSV vulnerability evidence — https://github.com/google/osv-scanner
- cargo-deny Rust dependency policy — https://github.com/EmbarkStudios/cargo-deny

Only after those contracts are mature should Divan consider a remote catalog or marketplace experience.
