"""One-shot, timeout-aware execution for Divan-owned subprocesses."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from . import receipts, timeouts

Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float
    timeout: dict[str, Any]
    mutating: bool
    retry_allowed: bool
    next_action: str


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return receipts.redact_text(value)


def _result(
    *,
    status: str,
    returncode: int | None,
    stdout: str | bytes | None,
    stderr: str | bytes | None,
    started: float,
    decision: timeouts.TimeoutDecision,
    mutating: bool,
    retry_allowed: bool,
    next_action: str,
) -> ExecutionResult:
    return ExecutionResult(
        status=status,
        returncode=returncode,
        stdout=_text(stdout),
        stderr=_text(stderr),
        elapsed_seconds=round(max(0.0, time.monotonic() - started), 3),
        timeout=asdict(decision),
        mutating=mutating,
        retry_allowed=retry_allowed,
        next_action=next_action,
    )


def run(
    command: Sequence[str],
    decision: timeouts.TimeoutDecision,
    *,
    mutating: bool = False,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    input_text: str | None = None,
    runner: Runner = subprocess.run,
) -> ExecutionResult:
    """Launch exactly once and preserve timeout, failure, and cancellation meaning."""
    if (
        isinstance(command, (str, bytes))
        or not isinstance(command, Sequence)
        or not command
        or any(not isinstance(item, str) or not item for item in command)
    ):
        raise ValueError("command must be a non-empty argument list")
    started = time.monotonic()
    arguments = list(command)
    try:
        completed = runner(
            arguments,
            cwd=cwd,
            env=env,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=decision.configured_seconds,
        )
    except subprocess.TimeoutExpired as error:
        retry_allowed = not mutating
        next_action = (
            "Retry once with a reviewed controlled timeout."
            if retry_allowed
            else "Inspect evidence before authorizing a new mutation."
        )
        return _result(
            status="TIMEOUT",
            returncode=None,
            stdout=error.output,
            stderr=error.stderr,
            started=started,
            decision=decision,
            mutating=mutating,
            retry_allowed=retry_allowed,
            next_action=next_action,
        )
    except KeyboardInterrupt:
        return _result(
            status="CANCELLED",
            returncode=None,
            stdout="",
            stderr="",
            started=started,
            decision=decision,
            mutating=mutating,
            retry_allowed=False,
            next_action="The user cancelled the command; no automatic retry was attempted.",
        )
    except OSError as error:
        return _result(
            status="FAILED",
            returncode=None,
            stdout="",
            stderr=str(error),
            started=started,
            decision=decision,
            mutating=mutating,
            retry_allowed=False,
            next_action="Fix the command launch failure before retrying.",
        )
    status = "PASS" if completed.returncode == 0 else "FAILED"
    return _result(
        status=status,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        started=started,
        decision=decision,
        mutating=mutating,
        retry_allowed=False,
        next_action=(
            "Continue with the verified result."
            if status == "PASS"
            else "Diagnose the command failure before retrying."
        ),
    )


def run_completed(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Adapt bounded execution to the provider runner compatibility contract."""
    observed = run(command, timeouts.resolve_default("provider"), mutating=False)
    return_codes = {"TIMEOUT": 124, "CANCELLED": 130}
    returncode = observed.returncode
    if returncode is None:
        returncode = return_codes.get(observed.status, 125)
    stderr = observed.stderr
    if observed.status == "TIMEOUT":
        stderr = f"divan-timeout: {observed.next_action}"
    elif observed.status == "CANCELLED":
        stderr = f"divan-cancelled: {observed.next_action}"
    return subprocess.CompletedProcess(
        list(command),
        returncode,
        observed.stdout,
        stderr,
    )
