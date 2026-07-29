---
description: Compatibility alias for /divan; retained through v1.
argument-hint: <natural-language mandate>
allowed-tools: Read, Glob, Grep, Bash
---

This is the pre-v0.17 compatibility alias. Follow the canonical `/divan`
contract with the same `$ARGUMENTS`.

Use `${CLAUDE_PLUGIN_ROOT}/divan_runtime/cli.py` as the primary CLI. If a pinned
pre-v0.17 installation lacks that path, fall back to
`${CLAUDE_PLUGIN_ROOT}/company/cli.py`. Do not treat `Company OS` as a separate
product and do not expand the Hükümdar's mandate.
