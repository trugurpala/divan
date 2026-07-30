# Divan v0.18.2 Public Truth and Smart Timeout Design

**Status:** Approved direction; implementation plan pending written-spec review  
**Release target:** v0.18.2  
**Owner:** Hükümdar  
**Product boundary:** One Divan repository, modular stdlib-only engine

## Purpose

Divan v0.18.2 makes two promises enforceable:

1. public product claims must be derived from repository and release evidence;
2. work launched by Divan must receive a timeout suited to its command class and
   observed duration instead of one arbitrary global limit.

The user experience requires one natural-language goal. Divan keeps benchmarks,
command classes, evidence identifiers, and validation details behind the
interface. It reports what happened, why it matters, and the next meaningful
result.

## Problem

The published v0.18.1 repository is healthy, but its public and execution
contracts still allow avoidable ambiguity:

- prose can retain an old version, PR, host-support statement, or release state
  after the underlying evidence changes;
- an independent technical inspection can be confused with the still-open
  independent-user adoption gate;
- elapsed-time language can become a product promise without a reproducible
  benchmark;
- local verification, CI, release, browser, and provider operations do not have
  the same duration or failure semantics;
- a single short timeout can terminate healthy work, while a single long timeout
  can conceal a hung command;
- repository discovery currently treats stale linked worktrees as product
  workspaces, creating noisy plans.

## Evidence Baseline

The design begins from the published v0.18.1 state and the latest 100 GitHub
Actions records read on 2026-07-30. Representative successful runs show:

| Workflow class | Observed recent range |
|---|---:|
| candidate review | about 8–19 seconds |
| wiki sync | about 9–29 seconds |
| site tests | about 36–55 seconds |
| compatibility | about 65–80 seconds |
| CodeQL | about 93–170 seconds |
| quality gate | about 190–264 seconds |
| release | about 123–570 seconds |

These are design inputs, not permanent performance claims. The implementation
must record sample count, run identifiers, event, conclusion, collection time,
and source repository before deriving a policy.

## User Contract

The primary interface is natural language:

> Divan, this repository's installation and version truth, then develop v0.18.2
> and prepare it for release.

Divan answers in short semantic updates:

```text
Ferman alındı — hedef ve sınırlar doğrulanıyor.
Kurulum sağlıklı — 5 Divan paketi etkin, kaynak v0.18.1.
Plan hazır — public truth, smart timeout, verification.
Kod hazırlanıyor — teknik ayrıntılar arkada tutuluyor.
Doğrulama geçti — test and evidence summary follows.
GitHub hazır — branch/PR/CI state is explicit.
Yayın doğrulandı — tag, assets, Pages, and Wiki were read back.
```

The words `planned`, `implemented`, `tested`, `pushed`, `merged`, `published`,
and `live` remain distinct claims. Divan never collapses them into “done.”

Optional expert commands may expose the same information without becoming
required for normal use:

```text
divan benchmark collect
divan timeout explain verify
divan truth check
```

Names are illustrative until the implementation plan confirms existing CLI
conventions and backward compatibility.

## Architecture

### 1. Public Truth Contract

Public facts are checked against existing canonical sources rather than copied
into another manually maintained registry:

- `VERSION` and the package marketplace define product/package versions;
- `registry/host-compatibility.json` defines host support levels and evidence;
- `registry/v1-gates.json` defines adoption readiness;
- `release-manifest.json`, CHANGELOG, and publication evidence define release
  status;
- GitHub run and release identifiers remain evidence, not marketing copy.

A stdlib-only checker maps public claim classes to these sources and fails on:

- stale version or release references;
- unsupported host-support wording;
- “independent user” wording without the adoption receipt;
- duration promises without benchmark provenance;
- contradictory README, Turkish README, Wiki source, Pages, or CHANGELOG text.

The checker validates authored prose; it does not replace the README with a
generated wall of metadata.

### 2. Benchmark Evidence

Benchmark collection is a maintainer operation, not an implicit runtime network
dependency. An optional collector reads bounded GitHub Actions history through
the authenticated GitHub CLI and writes a redacted, deterministic evidence
snapshot.

The snapshot contains only:

- repository and workflow identifiers;
- run database identifier;
- event and successful conclusion;
- start/end timestamps and derived duration;
- collection timestamp and schema version.

It contains no token, raw environment, log body, actor email, or secret. Samples
from untrusted pull requests are not allowed to change runtime policy
automatically. A policy change remains a reviewed Git diff.

### 3. Timeout Policy

The stdlib-only runtime resolves a timeout from:

```text
command → command class → trusted samples → percentile → safety margin → caps
```

Initial command classes:

- `fast-check`: metadata, catalog, Wiki, and link checks;
- `test`: focused or complete project test commands;
- `verify`: canonical local verification;
- `browser`: bounded user-flow checks;
- `security`: CodeQL and dependency/security analysis;
- `release`: packaging, attestations, and publication verification;
- `provider`: external host, model, API, or MCP work.

Policy rules:

1. use a conservative default until the minimum trusted sample count is met;
2. after the threshold, derive from p95 plus a documented safety margin;
3. apply per-class minimum and maximum caps;
4. record the selected class, source, sample count, and final timeout in the
   plan or receipt;
5. allow an explicit user override within safety bounds;
6. distinguish timeout from command failure and user cancellation;
7. never silently retry a mutating command;
8. show a vibe-friendly explanation and exact next action on timeout.

For v0.18.2, automatic enforcement is limited to subprocesses Divan itself
launches. GitHub workflow ceilings may be checked against recommendations but
are not rewritten from untrusted telemetry.

### 4. Host and Provider Boundary

Codex, Claude Code, Cursor, Gemini CLI, and other hosts control their own model
turn, tool, and approval lifecycles. Divan must not claim it can override those
limits.

Therefore v0.18.2:

- applies adaptive enforcement to local commands launched by Divan;
- explains externally controlled timeouts when detected;
- records provider operations as a separate class;
- does not add an MCP server, model SDK, telemetry service, or second repository.

Full model/API/MCP timeout adaptation is a later release only after cost,
privacy, retry, idempotency, and host capability contracts exist.

### 5. Discovery Hygiene

Project inspection must ignore linked worktree administration paths unless a
worktree is the explicit project root. This prevents old release branches under
`.worktrees/` from appearing as monorepo workspaces or duplicate test targets.

The rule must remain path-safe and platform-neutral. It cannot exclude a real
workspace merely because its name contains the word “worktree.”

## Timeout Result Experience

A timeout is reported like this:

```text
Doğrulama durdu — bu komut için 8 dakikalık güvenli sınır doldu.
Son kanıt: 580 testin 431'i tamamlandı; süreç yanıt vermeye devam ediyordu.
Sıradaki adım: aynı doğrulamayı 12 dakikalık kontrollü sınırla sürdür.
```

When partial progress cannot be proven, Divan says so. It does not invent a test
count or present a timeout as a code defect.

Machine-readable output additionally includes:

- command class;
- elapsed and configured seconds;
- policy source and sample count;
- termination result;
- safe retry recommendation;
- whether the command was read-only or mutating.

## Documentation Changes

The implementation synchronizes:

- English and Turkish README first-run and honest-status sections;
- installation and host compatibility guidance;
- Wiki source and Pages copy;
- CHANGELOG and BLUEPRINT;
- public claim and link checks.

The README must say plainly:

- Divan is one modular product, not a bundle of forked runtimes;
- Codex native plugin support and skill fallback are different capability modes;
- v0.18.1 is the published base until v0.18.2 is actually tagged;
- independent technical review does not satisfy issue #34;
- timing examples are observations with a date/sample source, not guarantees.

Useful human wording from historical PR #51 may be adapted, but its stale branch
must not be merged as-is.

## Verification Contract

Test-first implementation must prove:

1. stale public version, PR, release, host, adoption, and timing claims fail;
2. valid evidence-backed wording passes in both languages;
3. benchmark snapshots are deterministic, bounded, redacted, and schema-checked;
4. failed, cancelled, skipped, or untrusted runs cannot train the policy;
5. insufficient samples use the conservative default;
6. p95, margin, minimum, maximum, and override calculations are deterministic;
7. read-only timeout, mutating timeout, failure, and cancellation remain distinct;
8. external host/provider limits are reported but not falsely controlled;
9. stale linked worktrees do not become project workspaces;
10. Windows, Linux, and macOS behavior remains equivalent;
11. canonical verification, release, Wiki, site, compatibility, and security
    checks pass;
12. release claims are made only after tag, Release assets, attestations, Pages,
    and Wiki are independently read back.

## Security and Failure Policy

- No shell string construction for collected commands.
- No secrets or raw logs in benchmark evidence.
- No telemetry upload and no always-on monitoring.
- No auto-learning from fork or pull-request timing.
- No automatic retry for release, push, merge, install, update, or other
  mutating commands.
- Benchmark corruption, unknown command class, or invalid policy fails to a
  conservative timeout, not unlimited execution.
- Existing dry-run-first and explicit-execute rules remain intact.

## Deliberate Non-Goals

- A hosted control plane or separate Divan repository.
- Replacing host-native approvals, scheduling, or model selection.
- Automatic installation of GitHub, Context7, Figma, Gmail, Slack, or MCP tools.
- Claiming a benchmark proves faster or better agent behavior.
- Closing the independent-user v1 gate without a real external acceptance
  receipt.
- Publishing v0.18.2 before implementation, review, CI, merge, tag, assets,
  attestations, Pages, Wiki, and live readback are separately proven.

## Delivery Sequence

1. lock public-claim and timeout-policy schemas with failing tests;
2. fix worktree discovery noise;
3. implement deterministic truth checking;
4. implement trusted benchmark snapshot and timeout resolution;
5. integrate only Divan-owned subprocess execution points;
6. add vibe-friendly timeout and progress messages;
7. synchronize all public surfaces;
8. run canonical local and cross-platform verification;
9. obtain independent code and documentation review;
10. open the release PR, wait for all required CI, merge, and read back `main`;
11. prepare and publish v0.18.2 through the canonical release path;
12. verify immutable tag, assets, checksums, attestations, SBOM, Pages, and Wiki.

## Success Definition

v0.18.2 succeeds when a vibe coder can state one goal, see short truthful
progress, survive legitimately long verification without arbitrary termination,
understand a real timeout without reading logs, and verify every public claim
from repository or release evidence.
