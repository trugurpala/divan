# Keep useful project memory

Read the host's applicable project instructions, README, and linked project documents before adding files. Preserve the repository's language, names, and existing equivalents, such as `AGENTS.md`, `CLAUDE.md`, or an established editor rules file. Update the owning document rather than creating a second source of truth.

Use a short `AGENTS.md` as an instruction entry point when the repository uses one: durable engineering rules, canonical checks, and links to details needed for particular tasks. Keep task logs and deployment inventories out of this entry point.

If the project needs separate documents and has no suitable equivalents, these are optional repository conventions, not files that every host automatically loads:

| Document | Keep here |
| --- | --- |
| `docs/project.md` | Product purpose, boundaries, requested outcome and acceptance criteria, current state, and the next open step. |
| `docs/decisions.md` | Durable decisions, their reasons and consequences, and relevant sources or superseding decisions. |
| `docs/operations.md` | How to run and verify the project, non-secret environment assumptions, and observed operational state. |

Create only documents that solve an actual continuity gap and link them from the existing entry point. A small project may need only a README section. Do not add empty templates or copy chat transcripts.

## Leave a usable continuation point

At a meaningful handoff or when the user requests durable memory, update the relevant document with:

- the requested outcome and accepted constraints, including language and any authorization whose scope matters to continuation;
- what changed and the current evidence: command or action, observed result, date, and the revision or working-tree state it covers;
- unresolved questions or limits and the next concrete step.

Keep one concise current-state summary. Preserve durable decision history; replace stale status instead of accumulating contradictory status logs. Distinguish facts from assumptions and planned actions. Record permission scope without storing credentials or implying that a past authorization grants unrelated future access.

## Resume from evidence

On continuation, read the current request, applicable instructions, and linked state. Compare them with Git changes and the actual environment needed for this task. Retain earlier decisions and authorization unless the user changes them; ask only when a material conflict cannot be resolved from evidence.

Previous checks explain history. Rerun applicable checks for the current tree or live environment before a new completion claim. When a check cannot run, record it as unavailable or not run and retain the open next step. A saved `passed` line is not current verification.

Keep secrets, tokens, private machine addresses, and sensitive personal details out of public project memory. Use the project's existing private configuration or documentation mechanism when needed; portable instructions should name a configuration variable or role, not a developer's absolute local path.
