---
description: Inspect a project, apply the Divan Governance Model, and select the smallest qualified delivery path.
argument-hint: <natural-language mandate>
allowed-tools: Read, Glob, Grep, Bash
---

Treat `$ARGUMENTS` as the Hükümdar's natural-language mandate. Do not ask the
user to select a package, skill, module, provider, or quality gate.

1. Resolve the project root without executing project code.
2. Resolve `${CLAUDE_PLUGIN_ROOT}` or the equivalent loaded-plugin root from
   host metadata; never resolve relative to the user project.
3. Run
   `python "${CLAUDE_PLUGIN_ROOT}/divan_runtime/cli.py" architecture --json`.
4. Run
   `python "${CLAUDE_PLUGIN_ROOT}/divan_runtime/cli.py" inspect --project <project> --json`.
5. Run
   `python "${CLAUDE_PLUGIN_ROOT}/divan_runtime/cli.py" plan --project <project> --intent "$ARGUMENTS" --json`.
6. Present detected frameworks, selected workflows, the smallest qualified
   team, skills, and evidence gates. Keep every delegated action within the
   mandate; only `owner/Hükümdar` may expand scope.
7. If changed paths exist, run
   `python "${CLAUDE_PLUGIN_ROOT}/divan_runtime/cli.py" impact <relative-paths> --json`
   and close the transitive checks.

This is an expert inspection surface. Normal users can state the same mandate
directly; Sadrazam performs the routing automatically.
