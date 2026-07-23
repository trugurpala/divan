# Persistent Project Memory

Divan stores project state inside the user's repository. Claude Code, Codex, terminals, restarts and context compaction are replaceable clients; `.divan/` is the source of truth.

## Durable layout

- `project.json`: project identity, goal, source and lifecycle.
- `tasks.json`: vertical-slice tasks, dependencies, status and evidence.
- `current-state.json`: exact active task, branch, commit, last gate, blocker and next action.
- `progress.md`: regenerated human-readable summary.
- `decisions/`: architecture decision records.
- `evidence/`: test, build, migration and review proof.
- `handoffs/`: session-to-session transfer notes.
- `history/`: event log and checkpoint snapshots.
- `lessons/`: verified project-specific learnings.
- `spec/`: specifications and plans.

## Guarantees

Mutations are dry-run first and require explicit execution. Existing memory is never overwritten. Initialization and file updates are atomic. A fail-closed lock permits one writer. Only one task may be active. Dependencies must complete before a task starts. Completed tasks require existing evidence inside the project. Lifecycle transitions are adjacent and evidence-backed. Shipping requires explicit confirmation.

## Canonical commands

Use `python scripts/divan.py memory init` to create memory, `task-add` and `task-start` to select work, `checkpoint` at every durable stopping point, `task-complete` with evidence, `transition` for project lifecycle, and `continue` in every new Claude or Codex session.

Claude auto-memory, agent memory, Codex session history and chat transcripts are caches. They never override `.divan/`. Forge, Serena and reviewer adapters must share this contract rather than create competing private state.
