"""Run a child process under a bound and observe whether it is still working.

A process that exists is not a process that is doing something, so liveness and
progress are reported separately: the first says the worker is still there, the
second says it produced output since the last look.

Output is drained on its own threads rather than after the wait. A worker that
talks more than a pipe buffer holds would otherwise block forever on a write
nobody is reading, and Divan would record that deadlock as a stall.
"""
from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Callable, Sequence

#: How often the caller is told the process is still there.
DEFAULT_POLL_SECONDS = 5.0


@dataclass(frozen=True)
class ProcessOutcome:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


class _Drain:
    """Collect one stream on its own thread, noting when anything arrives."""

    def __init__(self) -> None:
        self._chunks: list[str] = []
        self.arrived = threading.Event()

    def pump(self, stream: IO[str]) -> None:
        with stream:
            for line in stream:
                self._chunks.append(line)
                self.arrived.set()

    @property
    def text(self) -> str:
        return "".join(self._chunks)


def _require(stream: IO[str] | None, name: str) -> IO[str]:
    if stream is None:
        raise RuntimeError(f"the worker process has no {name} to read")
    return stream


def _start_drain(stream: IO[str], drain: _Drain) -> threading.Thread:
    thread = threading.Thread(target=drain.pump, args=(stream,), daemon=True)
    thread.start()
    return thread


def _wait(
    process: subprocess.Popen[str],
    *,
    deadline: float,
    poll_seconds: float,
    drains: Sequence[_Drain],
    on_alive: Callable[[], None] | None,
    on_progress: Callable[[], None] | None,
) -> bool:
    """Wait for the process. Returns True when it had to be stopped."""
    while True:
        try:
            process.wait(timeout=poll_seconds)
            return False
        except subprocess.TimeoutExpired:
            pass
        if on_alive is not None:
            on_alive()
        if any(drain.arrived.is_set() for drain in drains):
            for drain in drains:
                drain.arrived.clear()
            if on_progress is not None:
                on_progress()
        if time.monotonic() >= deadline:
            return True


def run_bounded(
    argv: Sequence[str],
    *,
    cwd: Path,
    stdin_text: str,
    timeout_seconds: float,
    on_start: Callable[[subprocess.Popen[str]], None] | None = None,
    on_alive: Callable[[], None] | None = None,
    on_progress: Callable[[], None] | None = None,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
) -> ProcessOutcome:
    """Start a process, feed it its instructions, and bound how long it may run."""
    process = subprocess.Popen(
        list(argv),
        cwd=str(cwd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    if on_start is not None:
        on_start(process)

    out, err = _Drain(), _Drain()
    threads = [
        _start_drain(_require(process.stdout, "stdout"), out),
        _start_drain(_require(process.stderr, "stderr"), err),
    ]
    # Written only once the readers are running, so a worker that answers
    # immediately cannot fill a pipe nobody is draining.
    with _require(process.stdin, "stdin") as stdin:
        stdin.write(stdin_text)

    timed_out = _wait(
        process,
        deadline=time.monotonic() + timeout_seconds,
        poll_seconds=poll_seconds,
        drains=(out, err),
        on_alive=on_alive,
        on_progress=on_progress,
    )
    if timed_out:
        process.kill()
        process.wait()
    for thread in threads:
        thread.join(timeout=poll_seconds)

    return ProcessOutcome(
        exit_code=process.returncode,
        stdout=out.text,
        stderr=err.text,
        timed_out=timed_out,
    )
