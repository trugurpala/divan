# Teftiş — Divan starts a real worker and reads a real result

Date: 2026-08-16
Branch: `feat/agency-os-turnkey-v1`
Scope: `plugins/sadrazam/divan_runtime/worker_execution.py`

## What was being proved

That Divan can start a certified coding worker itself, own the attempt record,
and accept the result **only** on file, diff and test evidence. A worker saying
it finished is not a result.

## Contract run

Divan started Codex 0.147.0 in a fresh git worktree and asked for a JSON
validation CLI plus unit tests.

```
attempt id     : CONTRACT-1-A001
attempt state  : completed
exit code      : 0
duration       : 162.0 s
changed files  : ('jsoncheck.py', 'test_jsoncheck.py')
unreadable     : ()
diff lines     : 90
produced work  : True

running the tests the worker wrote...
test exit      : 0
Ran 3 tests in 0.137s — OK
```

`jsoncheck.py` 25 lines, `test_jsoncheck.py` 53 lines, 78 insertions. The three
tests the worker wrote were executed by Divan, not by the worker, and passed.

## Defects this run exposed, and what was done about them

### 1. A clean exit was accepted as a result

`_classify` returned "no failure" whenever the process exited 0, so the first
contract run — where the worker changed nothing at all — was recorded as
COMPLETED. That is precisely the fake pass this system exists to prevent.

A clean exit with an empty change set is now `WORK_REJECTED`.

### 2. Work the host cannot read was counted as work

`worktree_changes` ran `git add -A` and ignored its exit code. When staging
failed the diff came back empty while the changed-file list stayed full, so an
attempt reported `produced_work: True` alongside `diff lines: 0`.

The staging result is now read. Files git was refused access to are named, and
an attempt whose output cannot be read back is `ENVIRONMENT`, never completed.

### 3. The worker had no way to write

Codex defaults to a read-only sandbox, so the first run could not have produced
anything. It is now given `--sandbox workspace-write`: it may write inside the
worktree it was handed and nowhere else. `danger-full-access` and
`--dangerously-bypass-approvals-and-sandbox` are deliberately not used, and a
test pins that they never appear.

All three defects are covered by `tests/test_worker_execution.py` (18 tests).
Reverting the three fixes turns 5 of them red.

## Two environment causes found on the way

Both produced the same symptom — a worker that ran and delivered nothing
readable — and neither was a Divan defect.

**Codex could not write from its installed location.** The npm global prefix on
this machine sits inside the winget Node.js package directory, which put Codex's
own sandbox helper at 270 characters — past the Windows 260-character limit.
Every sandbox launch failed with `os error 3`, so `apply_patch` was denied and
the worker fell back to a shell that also could not start. Codex was installed
to `C:\divan-tools` (helper path 156 characters) and that install placed first
on the user PATH. The helper then launched and the worker wrote normally.

**The probe harness created a worktree the sandbox could poison.** The contract
script built its workspace with `tempfile.mkdtemp`, which protects the directory
against inheritance: SYSTEM, Administrators and OWNER RIGHTS only, with no ACE
for the user. Files the sandboxed worker created were owned by the sandbox
account, so the user had no access to them at all and `git add` failed with
permission denied. A directory created the ordinary way inherits
the owner account's full-control entry from the project tree, and the same run
succeeds.

No ACL was modified and no security setting was changed to reach this result.
Codex adds its own sandbox ACEs to the write root but leaves inheritance intact,
which was verified with a before/after reading of the same directory.

## Verification

- `tests/test_worker_execution.py` — 18 tests, pass
- red-proof: fixes reverted → 5 failures
- `worker_execution` registered in `modules.json` (providers) and in
  `RUNTIME_FILES`; ruff clean
