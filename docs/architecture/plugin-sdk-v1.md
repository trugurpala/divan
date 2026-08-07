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

`fs`, `http`, `store`, `sql`, `websocket` and clipboard-read are not default SDK requirements. They should remain absent until a concrete feature has a reviewed minimum-permission contract.

## Not yet implemented

SDK v1 in this slice defines manifest validation, bounded discovery and hash-bound approval/activation only. It intentionally does **not** yet:

- spawn third-party plugins,
- persist approvals,
- add a Marketplace,
- grant webview permissions,
- auto-install plugin binaries,
- auto-update third-party plugins,
- route a plugin into execution/review/evidence without a separate adapter.

Those are later slices and must reuse Divan mandate/evidence/release gates rather than bypass them.
