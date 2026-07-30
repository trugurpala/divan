# Divan v0.18.2 Local Seyir and Stabilization Design

**Status:** Written design for Hükümdar review  
**Release target:** v0.18.2  
**Companion specification:** `2026-07-30-v0182-truth-timeout-design.md`

## 1. Outcome

Divan v0.18.2 makes the existing modular, Python-standard-library runtime easier
to install, easier to understand, and harder to misreport. A user gives Divan a
goal in Codex or another supported host. Divan continues doing the technical work
in the background while a local, read-only **Seyir** page explains progress in
plain Turkish or English.

The product remains **Divan**. `Company OS` and `Project OS` remain compatibility
terms only. The product is not renamed, split into a second repository, or made
dependent on a hosted control plane.

The user journey is:

```text
Hükümdar gives a goal
→ Ferman records the intended outcome
→ Divan plans and routes the work
→ İcra performs the authorized changes
→ Teftiş checks evidence
→ Yayın verifies the release
→ Seyir explains the current truth locally
```

## 2. Product boundaries

### Included

- a real first-run bootstrap path that starts from a release asset;
- prerequisite diagnosis for Python, Git, the selected host, and `PATH`;
- a deterministic status snapshot assembled from Divan state and local Git;
- a temporary local HTTP server bound only to `127.0.0.1`;
- a bilingual, vibe-coder-friendly Seyir page;
- smart timeouts based on measured command families;
- a retry budget for repeated CI failure fingerprints;
- current README, Wiki, Pages, release, and installer copy;
- one repository and one versioned release train.

### Not included

- a cloud dashboard, account system, database, telemetry service, or daemon;
- React, Node.js, npm, or an external web framework for Seyir;
- commit, push, merge, deploy, or release buttons in Seyir;
- arbitrary shell execution through HTTP;
- silent installation of Node, Codex, Claude Code, or another host;
- a promise that every agent host has identical capabilities.

Seyir is an optional view over the existing runtime. It is not a tenth brain
module and it is not allowed to become Divan's source of truth.

## 3. Modular architecture

The existing nine runtime modules remain authoritative:

```text
kernel      deterministic routing and policy
governance  authority and approval boundaries
council     role and capability selection
project     project discovery and state
evidence    verification facts
records     durable receipts and memory
providers   optional external capabilities
release     publication contracts
api         CLI and local presentation adapters
```

v0.18.2 adds presentation components under the existing `api` boundary:

```text
divan_runtime/status.py          read-only status snapshot builder
divan_runtime/local_server.py    loopback-only HTTP adapter
divan_runtime/locales.py         message catalog loader and validator
divan_runtime/studio/            static HTML, CSS, and JavaScript
```

`status.py` reads existing state; it does not create a parallel state machine.
`local_server.py` serves only static assets and a status JSON endpoint. The
browser never reads project files directly.

## 4. Command and lifecycle

The canonical machine-facing command is English and ASCII:

```bash
python scripts/divan.py status --project . --open --lang auto
```

The reader-facing name is **Seyir · Local Progress**.

Command behavior:

1. validate the project path and Divan state;
2. build the first status snapshot;
3. bind to `127.0.0.1` on an operating-system-selected free port;
4. create a cryptographically random session capability;
5. open the exact generated URL in the default browser when `--open` is used;
6. print the same URL and an explicit stop instruction;
7. serve until `Ctrl+C`, parent-process exit, or 30 minutes of inactivity.

The displayed URL is never hard-coded. Example ports in documentation must be
marked as examples and must never be described as live.

## 5. Status data contract

The JSON response is versioned and intentionally small:

```json
{
  "schema_version": 1,
  "product": {"name": "Divan", "version": "0.18.2"},
  "locale": "tr",
  "project": {
    "name": "example",
    "branch": "feat/example",
    "head": "abc1234",
    "dirty": true
  },
  "goal": {
    "id": "goal-123",
    "title": "Kullanıcı dostu kurulumu tamamla",
    "status": "RUNNING"
  },
  "current": {
    "phase": "TEFTIS",
    "task": "Kurulum testlerini doğrula"
  },
  "tasks": [],
  "checks": [],
  "evidence": [],
  "blocker": null,
  "next_action": "Windows temiz kurulum testini çalıştır",
  "generated_at": "2026-07-30T12:00:00Z"
}
```

Rules:

- absolute paths, tokens, environment values, prompts, and command output are
  excluded by default;
- project-relative changed paths may be shown after secret redaction;
- no field is called complete without evidence;
- missing state is a valid `NO_ACTIVE_GOAL` view, not a server error;
- optional GitHub data is summarized and linked, never copied into a second
  issue/PR system;
- the browser polls every two seconds and uses `ETag` to avoid unchanged payloads.

## 6. Local security contract

The local page is safe by construction:

- bind only to IPv4 loopback `127.0.0.1`;
- reject unexpected `Host` headers to resist DNS rebinding;
- generate the session secret with `secrets.token_urlsafe(32)`;
- put the secret in the URL fragment, not the request path or query string;
- require the secret in `X-Divan-Session` for the JSON endpoint;
- never persist or log the secret;
- disable CORS and accept no cross-origin requests;
- expose only `GET` and `HEAD`; reject mutation methods;
- use `Cache-Control: no-store`;
- use a restrictive Content Security Policy, `nosniff`, `no-referrer`, and
  `frame-ancestors 'none'`;
- render user-controlled values with `textContent`, never `innerHTML`;
- escape fallback HTML with the standard library;
- shut down cleanly on `Ctrl+C` and parent exit.

No HTTP endpoint can invoke a shell command or alter a repository in v0.18.2.

## 7. Bilingual identity

Code, JSON keys, CLI commands, and file names remain canonical English. Public
meaning is first-class Turkish and English.

A single message catalog owns user-facing text:

```json
{
  "progress.current_task": {
    "en": "Current task",
    "tr": "Şu an yapılan"
  }
}
```

Validation fails when:

- an English or Turkish key is missing;
- placeholder names differ between languages;
- raw machine states leak into reader-facing copy;
- obsolete `Company OS` or `Project OS` branding appears outside compatibility
  documentation;
- README, Wiki, Pages, installer, and CLI disagree about the current release.

Ottoman terms are used where they make the workflow clearer, always paired with
plain modern meaning. **Devşirme** is not used as a friendly public feature name
because its historical meaning is coercive. External capability evaluation is
named **Kaynak Meclisi · Source Intake**; adaptation is an `INTIBAK` lifecycle
state, not a separate product.

## 8. Vibe-coder presentation

The page answers six questions without engineering jargon:

1. Ne istedin? / What did you ask for?
2. Şu an ne yapılıyor? / What is happening now?
3. Neler bitti? / What is complete?
4. Hangi kontrol geçti veya kaldı? / Which check passed or failed?
5. Bir engel var mı? / Is anything blocked?
6. Sıradaki adım ne? / What happens next?

The first screen contains:

- goal and one-sentence status;
- a step rail: Ferman, Plan, İcra, Teftiş, Yayın;
- current task;
- strongest evidence or blocker;
- next action.

Technical details are collapsed beneath a clearly labelled section. Red is
reserved for an actual failure or blocker. Empty, loading, disconnected,
completed, and stale-snapshot states all have explicit copy.

## 9. First-run bootstrap

The current repository-dependent instruction is insufficient for a new user.
v0.18.2 publishes a portable standard-library CLI asset:

```text
divan.pyz
```

The first-run path becomes:

```bash
python divan.pyz doctor --host codex
python divan.pyz install --host codex --profile auto --execute
```

The bootstrap:

- requires a supported Python version and explains how it was detected;
- detects Git and the selected host without assuming `PATH` is refreshed;
- on Windows, prefers `.cmd` host shims when PowerShell execution policy blocks
  `.ps1` wrappers;
- never changes PowerShell execution policy;
- downloads only a pinned release selected by the user or the bundled version;
- verifies the release checksum before installation;
- performs a dry run before an authorized write;
- rolls back a failed native installation;
- ends with `doctor` and a plain success/failure summary.

Divan diagnoses missing third-party prerequisites but does not silently install
them. Official host installation links are shown only when needed.

## 10. CI circuit breaker and stale work

Repeated red pipelines must not create an endless stream of speculative commits.
Divan fingerprints a failure using workflow, job, test/check name, and normalized
error signature.

Policy:

- first occurrence: diagnose and reproduce locally;
- first remediation push: allowed with focused local evidence;
- second remediation push for the same fingerprint: allowed only with a changed
  root-cause hypothesis and focused evidence;
- third occurrence: stop mutation, mark `BLOCKED`, and report the remaining root
  cause and owner action.

GitHub Actions use concurrency cancellation for obsolete branch runs where safe.
Content-contract failures must run their exact focused test before another push.

Stale PRs are handled deliberately:

- salvage useful human-facing copy from PR #51, but do not merge its stale
  contract changes;
- re-evaluate PR #28 and PR #29 against the current runtime module by module;
- supersede only after equivalent behavior and tests exist on the v0.18.2 branch;
- comment with the replacement commit before closing;
- rebase or group Dependabot updates after the release branch is stable.

## 11. Delivery slices

v0.18.2 is one release delivered through four independently verifiable slices:

### Slice A — Truth and stabilization

- implement the companion truth/timeout design;
- repair worktree discovery;
- add timeout benchmarks and failure receipts;
- add the CI circuit breaker;
- reconcile stale PR value without merging stale branches.

### Slice B — Installation

- build and verify `divan.pyz`;
- add prerequisite diagnosis and Windows shim handling;
- test clean install, update, rollback, and doctor on Windows, Linux, and macOS.

### Slice C — Seyir

- implement the status schema and redaction;
- implement the loopback server and security headers;
- build the bilingual static interface;
- add browser, accessibility, empty-state, and shutdown tests.

### Slice D — Publication

- synchronize README, Turkish README, Wiki, Pages, examples, and release assets;
- run the complete verification and compatibility matrix;
- publish a release candidate;
- perform an independent clean-machine acceptance run;
- merge, tag `v0.18.2`, publish, and read back every public surface and checksum.

## 12. Acceptance gates

The release is blocked unless all of the following are true:

1. `python divan.pyz doctor --host codex` gives an actionable result on a clean
   Windows account without requiring PowerShell policy changes.
2. A native install and update complete transactionally on supported hosts.
3. `status --open` prints and opens the same reachable local URL.
4. The server binds only to `127.0.0.1` and rejects missing/incorrect capability,
   hostile Host headers, mutation methods, traversal, and injected markup.
5. The page explains active, blocked, failed, complete, empty, and stale states in
   both Turkish and English.
6. Status claims match durable state, Git, receipts, and check evidence.
7. Timeout defaults are supported by committed benchmark evidence.
8. A repeated CI failure fingerprint stops after the retry budget.
9. All release assets match checksums and attestations.
10. README, Wiki, Pages, CLI, package manifests, and GitHub Release report the
    same version, install path, host support, and limitations.
11. An independent user completes one real task and produces a privacy-filtered
    acceptance receipt.

Only after these gates pass may Divan call v0.18.2 released.

## 13. Hükümdar authority

The Hükümdar defines the product goal and may expand scope. Divan may choose
implementation details inside the approved design, but it may not silently
broaden authority, weaken evidence, publish, merge, or release beyond the
approved gates. A missing permission or external dependency becomes a visible
blocker, never a fabricated success.
