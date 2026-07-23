---
description: Inspect a project, select the qualified Divan team, and show change impact.
argument-hint: <natural-language intent>
allowed-tools: Read, Glob, Grep, Bash
---

Treat `$ARGUMENTS` as natural-language intent. Do not ask the user to select a
package or skill.

1. Resolve the current project root without executing project code.
2. Resolve `${CLAUDE_PLUGIN_ROOT}` or the equivalent root from this loaded
   command's host metadata; never resolve relative to the user project.
3. Run `python "${CLAUDE_PLUGIN_ROOT}/company/cli.py" inspect --project <project> --json`.
4. Run `python "${CLAUDE_PLUGIN_ROOT}/company/cli.py" plan --project <project> --intent "$ARGUMENTS" --json`.
5. Present the detected frameworks, selected workflow, smallest qualified
   team, skills, and quality checks.
6. If changed paths already exist, run
   `python "${CLAUDE_PLUGIN_ROOT}/company/cli.py" impact <relative-paths> --json` and include the
   transitive surfaces.

This command is an expert inspection surface. Normal users can state the same
intent directly; Sadrazam performs this routing automatically.
