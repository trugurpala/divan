# Divan Desktop product direction

## Product identity

- Product name: **Divan Desktop**
- Window title / primary wordmark: **DİVAN**
- Positioning: **AI Yazılım Kumanda Merkezi** / **Agent Command Center**
- Windows installer target: `Divan-Setup-x64.exe`
- User-facing identity is Divan. Orca is presented only in advanced engine settings and diagnostics.

The visual language should feel like a serious developer tool, not an Ottoman-themed novelty UI. Historical naming may remain in internal domain concepts where it is useful, but the everyday interface uses clear product language.

## Visual system

Default theme: **Divan Obsidian** (dark).

Initial design tokens:

| Token | Value | Use |
| --- | --- | --- |
| `surface.root` | `#0E1116` | main background |
| `surface.panel` | `#151A22` | panels and cards |
| `surface.raised` | `#1B2230` | dialogs / selected surfaces |
| `text.primary` | `#E6EDF3` | primary text |
| `text.muted` | `#8B949E` | secondary text |
| `accent.divan` | `#D9A441` | Divan amber/copper accent |
| `status.pass` | `#3FB950` | PASS / healthy |
| `status.blocked` | `#F85149` | blocked / destructive |
| `status.review` | `#58A6FF` | review / information |

Avoid decorative gradients, fake gold textures, heavy shadows, and ornamental palace motifs. Use crisp borders, compact density, readable monospace/code surfaces, and restrained motion.

## Logo direction

A simple geometric **D / council-seal monogram** with four connected nodes representing:

`PLAN -> EXECUTE -> REVIEW -> GATE`

It must remain legible as a 16px tray/taskbar icon and as a monochrome mark. Do not copy Orca branding.

## Main window

```text
+--------------------------------------------------------------------------------+
| DİVAN   Project: fibercore-api       branch: main             Engine: Orca ●    |
+------------------+------------------------------------------+-------------------+
| Projects         | TASK / WORKSPACE                         | INSPECTOR         |
| Tasks            |                                          | Agent             |
| Agents           |  Fix login regression                    | Codex             |
| Evidence         |  --------------------------------------  | Worktree          |
| Releases         |  PLAN  -> WORKING -> REVIEW -> PASS      | fix-login         |
|                  |                                          | Authority         |
|                  |  Agent cards / terminal / diff / tests   | mandate-123       |
|                  |                                          | Risk              |
|                  |                                          | Evidence          |
+------------------+------------------------------------------+-------------------+
| Codex ●  Claude ●  OpenCode ○ | Tests PASS | 3 changed | Divan Core healthy    |
+--------------------------------------------------------------------------------+
```

### Left navigation

- Projects
- Tasks
- Agents
- Evidence
- Releases
- Settings

### Center workspace

The center is task-first, not terminal-first. A task shows:

- user request
- Divan plan and bounded steps
- active agent/worktree cards
- terminal output when needed
- changed files and diff
- tests / browser verification
- reviewer verdict

### Right inspector

The selected task/agent inspector shows:

- worker and model/provider
- engine and environment (Local / WSL / SSH)
- branch and worktree
- authority / mandate
- changed files
- risk summary
- evidence and receipt links
- retry count / budget

### Bottom status bar

Show operational truth at a glance:

- Codex / Claude / OpenCode availability
- selected execution engine
- Git branch / worktree
- test state
- Divan Core health

## Task states

Use a small stable vocabulary:

- `PLAN`
- `WORKING`
- `REVIEW`
- `BLOCKED`
- `RETRY`
- `PASS`
- `MERGED`
- `RELEASED`

The UI should make it obvious whether a statement is an agent claim or verified evidence.

## Approval UX

User-facing name: **Onay Kapısı**.

Before a high-impact mutation the dialog shows:

- what will happen
- repository and branch/worktree
- affected scope/files when known
- engine/agent performing the action
- risk reason
- evidence available so far

Primary actions:

- **Bir kez onayla**
- **Reddet**

Internal governance roles may keep historical domain names, but users should not need to understand them to operate the product.

## First-run experience

1. Detect Git.
2. Detect available agent CLIs: Codex, Claude Code, OpenCode, and custom CLIs.
3. Detect Orca CLI/runtime when installed.
4. Offer execution profile: Local, WSL, or SSH/remote when supported.
5. Open or clone a repository.
6. Run a read-only health check.
7. Do **not** enable mutation until the user explicitly starts a task and Divan issues an authority mandate.

Missing optional engines must degrade cleanly; the application should still open and explain what capability is unavailable.

## Normal task flow

1. User selects **Yeni Görev** and describes the outcome in Turkish or English.
2. Divan creates a bounded plan and selects worker/reviewer roles.
3. Onay Kapısı authorizes the required mutation scope.
4. OrcaEngine creates isolated worktrees and launches selected CLI agents.
5. Divan reads progress, diff, test and browser evidence.
6. An independent reviewer returns `PASS`, `RETRY`, or `BLOCKED`.
7. Merge and release remain separate authority gates.
8. Divan writes the final receipt/evidence trail.

## Packaging strategy

### Phase A — sidecar

Ship Divan Desktop while keeping Orca as an optional replaceable runtime. This is the first product target because it minimizes vendor lock-in and keeps Divan's governance boundary testable.

### Phase B — managed runtime

If the sidecar PoC proves the dependency is necessary, add guided installation/version checks and a supported Orca compatibility matrix.

### Phase C — bundled/forked runtime, only if justified

A branded fork or bundled Orca runtime is a packaging decision, not a Divan architecture decision. Before doing it, complete dependency/license/trademark review, updater ownership, security maintenance, and migration/escape testing.

## Release target

The first Windows installer is not considered production-ready until it passes:

- clean Windows VM install/uninstall
- first-run detection with and without Orca
- Codex/Claude availability checks
- authority-gate negative tests
- isolated-worktree execution test
- reviewer/evidence flow
- crash/restart recovery
- signed artifact verification when signing is enabled
- upgrade and rollback test
