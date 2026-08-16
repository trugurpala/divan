"""Run a child process under a bound and observe whether it is still working.

A process that exists is not a process that is doing something, so liveness and
progress are reported separately: the first says the worker is still there, the
second says it produced output since the last look.

Output is drained on its own threads rather than after the wait. A worker that
talks more than a pipe buffer holds would otherwise block forever on a write
nobody is reading, and Divan would record that deadlock as a stall. The
instructions are written on a thread for the same reason in reverse: a worker
that never reads its stdin must not be able to block the caller.

When the bound expires the whole process tree is stopped, not just the child
Divan started. A coding agent spawns compilers and test runners, and a
descendant left alive can still change the worktree after the attempt has been
recorded failed, which would put another attempt's work under this one's name.
"""
from __future__ import annotations

import os
import signal
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
    #: Set when the instructions could not be delivered in full.
    stdin_error: str | None = None


class _Drain:
    """Collect one stream on its own thread, counting what has arrived.

    A count rather than a flag: clearing a flag races with the thread setting
    it, and the lost signal would silently under-report a worker's progress.
    """

    def __init__(self) -> None:
        self._chunks: list[str] = []
        self._lock = threading.Lock()
        self._count = 0

    def pump(self, stream: IO[str]) -> None:
        with stream:
            for line in stream:
                with self._lock:
                    self._chunks.append(line)
                    self._count += 1

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    @property
    def text(self) -> str:
        with self._lock:
            return "".join(self._chunks)


def _require(stream: IO[str] | None, name: str) -> IO[str]:
    if stream is None:
        raise RuntimeError(f"the worker process has no {name} to read")
    return stream


def _start(target: Callable[..., None], *args: object) -> threading.Thread:
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()
    return thread


class _Feeder:
    """Deliver the instructions without letting the worker block the caller."""

    def __init__(self, stream: IO[str], text: str) -> None:
        self._stream = stream
        self._text = text
        self.error: str | None = None

    def write(self) -> None:
        try:
            with self._stream:
                self._stream.write(self._text)
        except (BrokenPipeError, OSError) as problem:
            # The worker closed its input or died mid-write. That is a fact
            # about the attempt, not an exception for the caller to handle.
            self.error = f"the worker did not take its instructions: {problem}"


def _kill_process_group(pid: int) -> None:
    """Stop a POSIX process group. Absent on Windows, hence the lookups."""
    kill_group = getattr(os, "killpg", None)
    group_of = getattr(os, "getpgid", None)
    if kill_group is None or group_of is None:
        return
    try:
        kill_group(group_of(pid), getattr(signal, "SIGKILL", signal.SIGTERM))
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _kill_tree(process: subprocess.Popen[str]) -> None:
    """Stop the worker and everything it started."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            check=False,
        )
    else:
        _kill_process_group(process.pid)
    process.kill()


def _wait(
    process: subprocess.Popen[str],
    *,
    deadline: float,
    poll_seconds: float,
    drains: Sequence[_Drain],
    on_alive: Callable[[], None] | None,
    on_progress: Callable[[], None] | None,
) -> bool:
    """Wait for the process. Returns True when the bound expired first."""
    seen = [drain.count for drain in drains]
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return True
        # Never sleep past the bound: a worker that finishes late would
        # otherwise be waved through simply because the poll was longer.
        try:
            process.wait(timeout=min(poll_seconds, remaining))
            return False
        except subprocess.TimeoutExpired:
            pass
        if on_alive is not None:
            on_alive()
        counts = [drain.count for drain in drains]
        if counts != seen:
            seen = counts
            if on_progress is not None:
                on_progress()


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
    deadline = time.monotonic() + timeout_seconds
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
        # So the bound can reach the whole tree the worker builds under itself.
        start_new_session=os.name != "nt",
    )
    if on_start is not None:
        on_start(process)

    out, err = _Drain(), _Drain()
    feeder = _Feeder(_require(process.stdin, "stdin"), stdin_text)
    threads = [
        _start(out.pump, _require(process.stdout, "stdout")),
        _start(err.pump, _require(process.stderr, "stderr")),
        _start(feeder.write),
    ]

    timed_out = _wait(
        process,
        deadline=deadline,
        poll_seconds=poll_seconds,
        drains=(out, err),
        on_alive=on_alive,
        on_progress=on_progress,
    )
    if timed_out:
        _kill_tree(process)
        process.wait()
    for thread in threads:
        thread.join(timeout=poll_seconds)

    return ProcessOutcome(
        exit_code=process.returncode,
        stdout=out.text,
        stderr=err.text,
        timed_out=timed_out,
        stdin_error=feeder.error,
    )
