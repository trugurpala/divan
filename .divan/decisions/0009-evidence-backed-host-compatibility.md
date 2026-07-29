# ADR 0009: Evidence-backed host compatibility

## Decision

Divan remains one repository and one modular product. Host differences are
implemented through small adapters generated from one canonical capability
registry. Compatibility is never a boolean marketing claim.

The public levels are `experimental`, `skill-compatible`, `native`, and
`verified`. Only a clean-host lifecycle canary may produce `verified`. Missing
capabilities remain visible as degraded or unsupported; they are not silently
reported as installed.

## Consequences

- Claude Code and Codex retain their verified native paths.
- New hosts may enter as experimental or skill-compatible without overstating
  lifecycle, hook, agent, or MCP parity.
- Host forks and separately maintained source repositories are forbidden.
- External apps and MCP servers remain optional capabilities, not core runtime
  dependencies.
- Documentation is generated or checked against the registry so host claims
  cannot drift independently.
