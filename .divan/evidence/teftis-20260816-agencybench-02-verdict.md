# AgencyBench-02 — verdict

Date: 2026-08-16
Application head: `9fc2d67`, 2365 lines, 15 test files
Project: a disposable local project outside the Divan repository

## Verdict

**TURNKEY_BLOCKED.**

Eight of nine required gates pass, measured by running the application rather
than by reading its test names. The ninth, independent review, does not.

| Gate | Result |
|---|---|
| clean-start | PASS, 3/3 |
| database-init | PASS, 3/3 |
| restart-persistence | PASS, 3/3 |
| ledger and commission correctness | PASS, 23/23 |
| browser acceptance in real Chromium | PASS, 11/11 |
| security | PASS, 15/15 |
| backup and restore | PASS, 14/14 |
| worker kill and recovery | PASS, 12/12 |
| **independent review** | **FAIL, 4/5** |

The project's own suite: 57 tests, all pass.

## Why it is blocked

### One finding that cannot be closed in scope

The ledger can be forged by anyone who can write to `operations.db`. Alter a
row, recompute the public SHA-256 chain, update the head anchor which lives in
the same database, and verification accepts it.

Two rounds of work went into this. The chain was anchored so truncation is
caught, and verification was extended to recompute payload hashes from the
business rows so a change made directly in SQLite is detected. Both were real
improvements. Neither closes the finding, because an unkeyed hash cannot
defend against an attacker who rewrites the hash too, and this application is
deliberately local and offline with nowhere to hold a key.

The README states the limit in plain words: a corruption detector, not a tamper
seal. The reviewer's judgement stands anyway, and it is the right judgement:
"the README discloses this limitation, but it remains a failure of the required
audit and immutable-ledger property." Disclosing a limit does not remove it.

### Four findings that are open, three of them caused by the repairs

The fifth review found four P1s. Three are regressions introduced by the fourth
repair round, which is the more important fact.

- **Ordinary recovery makes the ledger report tampering.** Two claims whose
  leases expire in the same recovery request record two events with identical
  tenant, actor, action and millisecond timestamp. Verification matches the
  first payload for both, so the second hash mismatches. The lease recovery and
  the payload verification were each asked for separately; together they make a
  healthy system accuse itself. This is worse than not verifying at all.
- **An expired lease still grants authority** until another worker happens to
  claim. The lease was added; the authorization queries were not taught to read
  it.
- **Restore leaves an invalid manifest.** The staged copy is verified, then
  document paths are rewritten in the database, and nothing verifies again. The
  restore succeeds and `verifyBackupIntegrity` on its output then fails.
- **Attempts and document uploads are not idempotent.** The identity rule that
  was applied to commission was not applied to them.

## What the repair loop actually did

Four rounds, ten repair attempts, every one a real Codex process working from
the reviewer's own words. No fabricated findings.

| Round | Closed |
|---|---|
| 1 | doubled money on retry; four denial-of-service paths; work belonging to whoever claimed it; a queue that could lose work permanently |
| 2 | identity reuse across cases; a document readable by the wrong worker; a legitimate retry wrongly refused |
| 3 | a case that could never be closed; reassignment breaking single ownership; restore destroying the previous copy before writing |
| 4 | two JSON routes leaking owner-only data; a permitted filename crashing the server; verification that never checked the business rows; a published administrator password |

Rounds one to three converged. Round four closed four P0 findings and
introduced at least two new P1s. That is the honest reading of the trajectory,
and it is why this stops here rather than running a fifth round: a loop that
introduces defects as fast as it closes them is not converging, and the budget
was set finite for exactly this reason.

## What was proved along the way

Independent of the verdict, these were measured and hold:

- The application was written entirely by workers Divan drove. No application
  code was written by hand at any point, including the plan.
- Four roles, tenant isolation with no cross-tenant path found by any of the
  five reviews, a queue with an atomic claim proved concurrent by four
  simultaneous requests producing one winner.
- Money is deterministic, bounded, refuses impossible dates, and a retry under
  one identity has one economic effect, enforced by a database constraint
  rather than a check in a handler.
- Backup and restore proved by destroying the disposable store, confirming the
  application could no longer see the data, restoring, and matching the digest
  exactly.
- A real Codex worker killed mid-task, classified orphaned, replaced under the
  same task contract by a fresh process, with the dead attempt's record intact.

## Corrections made to the harness, recorded because they were mine

Nine times a gate failed and the cause was this harness rather than the
application: driving routes that do not exist as pages, using the wrong role,
probes that could not set up their own subject, a secret scanner that flagged a
session variable and then thirty-five synthetic passwords, a check that counted
a sign-out form as a mutating control, a kill that let the supervisor write a
verdict before the orphan path could run, and a registration check that treated
data files as Python modules.

Each was found by looking at what the application actually returned before
calling anything a defect. One check that always passed was deleted rather than
kept: a test that cannot fail inflates a matrix and proves nothing.

The last adaptation is worth naming. When the fourth round replaced the
published administrator password with one generated at first run, every probe
lost its login. The easy repair was to the application. The correct one was to
the harness, which now provisions its own users through the application's
factory exactly as the README tells deployments to.
