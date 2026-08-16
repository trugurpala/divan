# Teftiş — the execution chain stops depending on luck

Date: 2026-08-16
Branch: `feat/agency-os-turnkey-v1`
Scope: `worker_process.py`, `worker_execution.py`, `attempt_contract.py`

## What was missing

Divan could start a worker and judge its result, but three parts of the
execution contract were still unmet.

**The prompt travelled in argv.** A command line is readable by every other
process on the machine and has a hard length limit that real compiled task
context will exceed. Codex reads instructions from stdin when given `-`, so it
is given `-` and the prompt is written to the pipe.

**Progress was recorded once and never again.** `AttemptRecord` separates
`heartbeat_at` from `last_progress_at` on purpose, and `classify_quiet_attempt`
prefers the second, because a process can be alive and stuck. Both were stamped
at launch and left there, so a worker that hung after one second and a worker
that worked for ten minutes looked identical to stall detection. The stall
policy was real code answering a question nobody was feeding.

**Output was drained only after the wait.** A worker that writes more than a
pipe buffer holds blocks on the write, nobody reads, and the run deadlocks. On
a 160-second Codex attempt this had not bitten yet; it would have.

## What changed

`worker_process.run_bounded` owns the process: it starts the child, hands the
caller the process so the attempt can be recorded with a real pid, drains
stdout and stderr on their own threads, writes the instructions only once the
readers are running, and polls until the bound expires.

Liveness and progress are reported separately. Every poll says the process is
still there; only a poll that found new output says the worker did something.
`_AttemptTracker` writes those into the attempt record as they happen, so the
existing stall and orphan policy now runs on observed facts.

Accepted work is committed in the worktree and the commit recorded on the
attempt, so a result has an immutable name rather than a description. Divan
commits under its own identity: the work was produced by a worker under Divan's
control rather than typed by the owner, and a disposable benchmark project may
have no git identity configured at all.

`next_attempt_id` from the attempt store replaced a second hand-written
copy of the same numbering, so attempt identity has one owner.

## A defect found while reviewing the result

The note "the accepted work could not be committed" fired whenever a rejected
attempt had left readable changes behind. No commit is attempted for a rejected
attempt, so the note accused the run of failing at something it never tried.
Committing is now stated explicitly and the note only speaks when it applies.

## Verification

| Suite | Result |
|---|---|
| `test_worker_process.py` | 7 tests, pass |
| `test_worker_execution.py` | 24 tests, pass |
| `test_worker_discovery.py`, `test_worker_certification.py`, `test_attempt_recovery.py` | 51 tests, pass |

`test_worker_process` covers the cases that used to be assumed: a talkative
child producing 200000 characters returns instead of deadlocking, a child that
never finishes is stopped and named as timed out, a silent child is reported
alive without being credited with progress, and instructions arrive on stdin.

Real contract run through Divan against Codex 0.147.0, with the prompt on
stdin:

```
attempt state : completed      changed files : jsoncheck.py, test_jsoncheck.py
exit code     : 0              diff lines    : 86
duration      : 76.5 s         produced work : True
the three tests the worker wrote, run by Divan: exit 0, OK
```

Gates: ruff, mypy, clean-code, naming, prose, standards, wiki, candidate-review
all clean.
