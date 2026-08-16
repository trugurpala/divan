# Teftiş — worker discovery stops depending on the machine it runs on

Date: 2026-08-16
Branch: `feat/agency-os-turnkey-v1`
Scope: `plugins/sadrazam/divan_runtime/worker_discovery.py`

## The regression

Exact-head CI failed at `validate`, step 18, "Local quality gates (canonical
verification with coverage)". Two discovery tests failed on the Ubuntu runner
and passed on Windows:

- `test_a_winget_package_is_found_when_path_is_stale`
- `test_a_worker_outside_path_is_found_and_named_as_such`

Both build a Windows install layout in a temporary directory and expect the
probe to resolve it. The search chose its launcher suffixes at call time from
`os.name`, so on Linux it looked for an extensionless `codex` and could never
find the `codex.cmd` and `claude.exe` the fixtures had written. The finding
came back ABSENT where the fixture said RESOLVED.

The tests were not wrong. The module was asking the operating system a question
it should have been told the answer to.

## The change

The platform is now stated rather than inferred. `LauncherPlatform` is an
explicit value with `current()` as its default, threaded through
`probe_worker`, `probe_all`, the root selection and the suffix choice.

Windows and POSIX roots are separate functions instead of one body gated by
environment variables, so each platform's documented install locations can be
read on their own. Launcher suffixes come from a table keyed by platform.

Nothing about the Windows behaviour changed: winget package discovery still
walks one level into each package directory, `.cmd` `.exe` `.bat` are still the
only eligible launchers in that order, the extensionless script and the `.ps1`
shim are still never selected, and the credential-directory guard is untouched.

## What this buys beyond the fix

A third test, `test_a_windows_script_shim_is_never_preferred_over_a_launcher`,
called `skipTest` on any non-Windows host. It was therefore proving nothing on
the runner where the regression happened. Stating the platform lets it run
everywhere, and it is now one of the tests that catches this class.

Two tests were added for the other direction: a POSIX launcher resolves from
`~/.local/bin`, and a `.cmd` file found on POSIX is ABSENT rather than
RESOLVED, because reporting an unrunnable file as a worker would send an owner
after a phantom.

## Verification

Run on this Windows host and again with the module's view of `os.name`
replaced by the value Ubuntu reports, so the CI platform is exercised here.

| Run | Result |
|---|---|
| Windows host | 10 tests, pass, 0 skipped |
| Simulated Ubuntu | 10 tests, pass, 0 skipped |
| Simulated Ubuntu, fix reverted | 3 failures |

The three red tests without the fix are the two CI named and the one that used
to be skipped.

Dependants pass unchanged: `test_worker_certification`, `test_worker_execution`,
`test_attempt_recovery` — 51 tests.

Gates: ruff, mypy, clean-code, naming, prose, standards, wiki, candidate-review
all clean.
