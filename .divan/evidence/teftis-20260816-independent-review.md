# Teftiş — an independent reviewer took the execution chain apart

Date: 2026-08-16
Branch: `feat/agency-os-turnkey-v1`
Reviewer: Codex 0.147.0, fresh process, read-only sandbox

## How the review was obtained

A second worker process was started with no history of the session that wrote
the code and with a sandbox that denies writing. Both claims were checked
rather than trusted: the reviewer's pid was recorded, and the worktree was
fingerprinted before and after so a reviewer that had changed something could
not be described as read-only.

```
reviewer pid          : 44232
exit code             : 0
duration              : 383.3 s
provider independence : unavailable
process independence  : proven
write access          : denied
```

Provider independence is recorded as unavailable, not glossed over: the only
authenticated vendor on this machine is Codex, so a Codex process reviewed
Codex-assisted work. That is a stated limitation of this review, not a claim
of vendor independence.

It found seven defects. Every one was real.

## Findings, and the proof each is closed

Each fix was reverted on its own and the named test re-run. A test that still
passes with the defect back in place proves nothing, so `without fix` is the
column that matters.

| # | Finding | Risk | Closed by | with fix | without fix |
|---|---|---|---|---|---|
| P0-1 | The bound was only checked after a full poll had elapsed | A worker that ran past its limit was recorded completed | `_wait` never sleeps past the deadline | PASS | FAIL |
| P0-2 | Work left behind by a rejected attempt counted as the next attempt's | A retry that changed nothing was recorded completed and committed the rejected work under its own name | The tree is fingerprinted before and after; only change during the attempt counts | PASS | FAIL |
| P0-3 | A reviewer that crashed or timed out still counted as a review | An authentication error became "findings" and certified the work | A review counts only if it exited cleanly and inside its bound | PASS | FAIL |
| P1-1 | Instructions were written on the calling thread with no guard | A worker that never reads stdin blocked the caller; a closed pipe raised out of the run and left the attempt recorded running | The prompt is delivered on its own thread and a refused write becomes a recorded fact | PASS | FAIL |
| P1-2 | Only the started process was killed, not what it had spawned | A surviving descendant could still write into the worktree after the attempt was recorded failed, contaminating the next attempt | The whole process tree is stopped | PASS | FAIL |
| P1-3 | A tree that could not be read looked identical to one that had not changed | A reviewer was reported unable to write when nothing had been observed at all | Both git calls are checked; an unreadable tree is `unobserved`, and unobserved is not usable | PASS | FAIL |
| P2-1 | Reading the progress signal cleared it, losing concurrent output | Real worker progress was under-recorded, moving an active worker toward the stall verdict | Arrivals are counted rather than flagged, and a count only moves forward | PASS | FAIL |

Seven of seven proven.

## Execution invariants, each held by a named test

| Invariant | Tests |
|---|---|
| Work a rejected attempt left behind is not the next attempt's success | 3 |
| A run that changed nothing cannot be completed | 1 |
| Output the host cannot read or stage is not produced work | 3 |
| The prompt never reaches the command line; stdin carries it | 3 |
| Talkative output cannot deadlock the run | 2 |
| Heartbeat is not progress | 2 |
| Accepted work is bound to an immutable commit | 2 |
| The writer is not its own reviewer | 4 |

The command-line invariant is asserted against the argv actually built by
`build_argv`, which both the worker path and the review path now share, rather
than against a promise made elsewhere.

## One thing the reviewer could not do

It reported: focused tests were not run, because no Python interpreter was on
its shell's PATH. The review is therefore a reading of the code, not an
execution of it. Recorded as a limit of this review rather than left implied.

## Structural change made while closing the findings

`worker_execution` reached 426 lines against a 400 line ceiling. Rather than
raise the ceiling, the worktree questions moved to `worktree_reading`: what
changed, whether this host may read it, and what the accepted work is called.
Starting a process and judging a diff are different jobs.

## Verification

| Gate | Result |
|---|---|
| worker suites (execution, process, review, discovery) | 65 tests, pass |
| ruff, mypy | clean |
| clean-code | valid, 315 lines |
| naming, prose, standards, wiki, candidate-review | clean |
| frontend (vitest) | 20 tests, pass |
