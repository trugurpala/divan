# Persistent Memory Current-Main Integration Plan

**Goal:** Turn draft PR #29 into a current, release-tracked, cross-platform
persistent-memory candidate without weakening Divan's Project OS or claiming
independent-user adoption.

## Tasks

- [x] Merge current `main` into the persistent-memory branch without rewriting
  its historical commits.
- [x] Run the memory, canonical CLI, Company OS, and full canonical test suites.
- [x] Add red regressions for stale-state overwrite and symlink path escape.
- [x] Reload state only after the single-writer lock is acquired and reject
  symlinked memory/evidence paths.
- [x] Track the public memory runtime, contract, and guide in the release
  manifest.
- [x] Add a Linux/macOS/Windows memory smoke job and its workflow contract test.
- [ ] Publish the integration commit to PR #29 and require all applicable
  GitHub checks.
- [ ] Merge only after an independent review finds no blocking issue.

## Non-claims

- The existing Markdown-only `.divan/` directory is not migrated automatically.
- Host-specific private memory and chat history are not canonical state.
- Issue #34 remains open and v1 readiness remains 7/8.
