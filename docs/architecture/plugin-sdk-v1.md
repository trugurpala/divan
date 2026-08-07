# Divan Plugin SDK v1

## Goal

Divan may gain external execution engines, reviewers, evidence producers and providers without allowing those extensions to become Divan Core authority.

The v1 lifecycle is deliberately fail-closed:

`DISCOVER -> VALIDATE -> APPROVE -> ENABLE`

Discovery never imports third-party Python code. A plugin is represented by a static JSON manifest plus a separately installed executable sidecar.

## Trust boundary

- Divan Core remains authoritative for mandate, task state, evidence truth, review gate, approval, merge and release.
- External plugins are sidecars. They are replaceable and never become a required Core runtime dependency.
- Plugin manifests may request bounded capabilities, but may never request `authority.expand`, `approval.grant`, `evidence.rewrite`, `merge.commit` or `release.promote`.
- Reviewer, provider and evidence plugins are read-only with respect to project/git mutation.
- A mutating execution-engine plugin must declare `requires_mandate=true`; Divan still owns and issues the mandate.
- Approval is bound to SHA-256 of both the manifest and the resolved executable. Any post-approval drift requires a new approval.
- Discovery scans only explicitly supplied directories and their direct JSON children. It never recursively scans the user disk.
- Manifest capabilities are Divan policy declarations, not an operating-system sandbox. Third-party binaries still require source/license review, immutable release provenance and explicit owner approval.

## Manifest v1

```json
{
  "schema_version": 1,
  "id": "playwright-evidence",
  "display_name": "Playwright Evidence",
  "version": "1.0.0",
  "api_version": 1,
  "kind": "evidence",
  "transport": "sidecar-json-v1",
  "executable": "divan-playwright-evidence",
  "capabilities": ["project.read", "evidence.emit"],
  "source": {"url": "https://github.com/microsoft/playwright"},
  "license": {
    "spdx_expression": "Apache-2.0",
    "evidence": "https://github.com/microsoft/playwright/blob/main/LICENSE"
  },
  "requires_mandate": false
}
```

The executable is a bare command name, never a shell string or arbitrary manifest-supplied path.

## Desktop trust inspection

The first Desktop integration is deliberately read-only.

`plugin.inspect` accepts only an explicitly selected manifest path and returns a privacy-bounded trust report. It:

- reads and validates static UTF-8 JSON;
- resolves the declared bare executable through Divan's bounded executable locator;
- hashes the manifest and resolved executable with SHA-256;
- returns only local basenames, never absolute manifest or executable paths;
- never imports or executes third-party plugin code;
- never persists approval;
- never claims that a valid plugin is enabled or trusted.

The Desktop Trust Center has three current terminal display states:

- `invalid` — the manifest contract failed;
- `executable-missing` — the manifest is valid, but exact executable identity is unavailable;
- `approval-required` — manifest and executable identity are known, but no activation claim exists.

The product-level information architecture, accessibility rules and practical capability language are defined in `docs/product/plugin-trust-center.md`.

## Open-source adoption map

| Upstream | Decision | Intended Divan use | Integration rule |
| --- | --- | --- | --- |
| https://github.com/tauri-apps/plugins-workspace | ADOPT selectively | Desktop single-instance, privacy-minimal logging, window-state, notifications | Add only official plugins with minimum Tauri capabilities; do not expose broad fs/http/store access by default |
| https://github.com/pytest-dev/pluggy | REFERENCE | Hook/API design lessons | Do not load untrusted plugins in-process; SDK v1 remains dependency-free and sidecar-first |
| https://github.com/microsoft/playwright | ADAPT | Browser/E2E evidence adapter | External sidecar emits bounded evidence; browser output is never treated as automatic PASS |
| https://github.com/semgrep/semgrep | ADAPT | Read-only static-analysis reviewer/evidence | External CLI adapter; no vendoring into Core; findings remain evidence, not release authority |
| https://github.com/anchore/syft | ADAPT | SBOM evidence for release candidates | External CLI adapter; produce SPDX/CycloneDX evidence without becoming release authority |
| https://github.com/aquasecurity/trivy | REFERENCE / later ADAPT | Vulnerability/misconfiguration evidence | Add only after offline/cache/network behavior is explicitly bounded and evidenced |
| https://github.com/gitleaks/gitleaks | REFERENCE / later ADAPT | Secret-leak evidence | Redacted findings only; never persist discovered secret values into Divan evidence |
| https://github.com/modelcontextprotocol/python-sdk | REFERENCE | Optional MCP provider bridge | MCP is a provider protocol, not Divan authority; pin a compatible protocol/SDK version before adoption |

## Desktop plugin roadmap

The current stable-release source identity must not be disturbed for convenience features. After the current stable Windows release gates are complete, the preferred first Desktop additions are:

1. `single-instance` — prevent two Desktop instances racing the same local Core state.
2. `log` — privacy-minimal local diagnostics with prompt/secret/source-content redaction.
3. `window-state` — restore window position/size only.
4. `notification` — task/review completion notification after explicit permission.
5. `opener` — narrowly open evidence folders or approved URLs.

Tauri 2 plugin commands remain denied unless explicitly granted through capabilities/permissions. `single-instance`, when introduced, must be registered first in the desktop builder. The Trust Center inspection path itself adds no new Tauri permission and reuses the existing native dialog capability.

`fs`, `http`, `store`, `sql`, `websocket` and clipboard-read are not default SDK requirements. They should remain absent until a concrete feature has a reviewed minimum-permission contract.

## Implemented in this slice

- static manifest contract and fail-closed validation;
- bounded plugin discovery;
- bounded Windows-aware executable resolution shared with Divan's existing local-tool resolver;
- SHA-256 manifest and executable identity;
- hash-bound approval model and drift invalidation primitives;
- privacy-bounded Desktop trust report;
- read-only `plugin.inspect` Core protocol command;
- first-class Desktop `Eklentiler` / Plugin Trust Center destination;
- explicit native JSON manifest picker;
- plain-language capability, mutation, provenance and activation-boundary UI;
- context-aware Plugin Trust inspector rail;
- focused Core/protocol/UI contract tests.

## Not yet implemented

SDK v1 intentionally does **not** yet:

- spawn third-party plugins;
- persist approvals;
- add a Marketplace;
- grant additional webview permissions;
- auto-install plugin binaries;
- auto-update third-party plugins;
- route a plugin into execution/review/evidence without a separate adapter.

Those are later slices and must reuse Divan mandate/evidence/release gates rather than bypass them.
