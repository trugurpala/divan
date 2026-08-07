#!/usr/bin/env python3
"""Typed, stdlib-only adapter for the Orca CLI execution engine."""
from __future__ import annotations

import json
import pathlib
import subprocess
from dataclasses import dataclass
from typing import Any, Callable, Sequence

ENGINE_ID = "orca"
CONTRACT_VERSION = 1


class OrcaExecutionDenied(PermissionError):
    """Raised when a mutating Orca action has no explicit Divan mandate."""


@dataclass(frozen=True)
class ExecutionAuthority:
    execute: bool = False
    mandate_id: str | None = None

    def require_mutation(self, action: str) -> None:
        if not self.execute or not self.mandate_id or not self.mandate_id.strip():
            raise OrcaExecutionDenied(
                f"mutating Orca action requires execute authority and mandate_id: {action}"
            )


@dataclass(frozen=True)
class RunnerResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class OrcaCommand:
    action: str
    argv: tuple[str, ...]
    mutating: bool = False
    evidence_argv: tuple[str, ...] | None = None


@dataclass(frozen=True)
class OrcaResult:
    action: str
    argv: tuple[str, ...]
    mutating: bool
    mandate_id: str | None
    exit_code: int
    payload: Any
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": ENGINE_ID,
            "contract_version": CONTRACT_VERSION,
            "action": self.action,
            "argv": list(self.argv),
            "mutating": self.mutating,
            "mandate_id": self.mandate_id,
            "exit_code": self.exit_code,
            "ok": self.ok,
            "payload": self.payload,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


Runner = Callable[[Sequence[str], pathlib.Path | None, float], RunnerResult]


class OrcaEngine:
    """Minimal Orca sidecar adapter with an explicit authority boundary."""

    def __init__(
        self,
        binary: str = "orca",
        runner: Runner | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not binary.strip():
            raise ValueError("Orca binary must not be empty")
        self.binary = binary
        self.runner = runner or _default_runner
        self.timeout_seconds = timeout_seconds

    def status(self) -> OrcaResult:
        return self.run(self._command("status", "status"))

    def worktree_list(self, repo_selector: str) -> OrcaResult:
        _require_value("repo_selector", repo_selector)
        return self.run(
            self._command(
                "worktree.list",
                "worktree",
                "list",
                "--repo",
                repo_selector,
            )
        )

    def worktree_ps(self) -> OrcaResult:
        return self.run(self._command("worktree.ps", "worktree", "ps"))

    def worktree_create(
        self,
        *,
        name: str,
        authority: ExecutionAuthority,
        repo_selector: str | None = None,
        agent: str | None = None,
        prompt: str | None = None,
        setup: str = "inherit",
    ) -> OrcaResult:
        _require_value("name", name)
        if setup not in {"run", "skip", "inherit"}:
            raise ValueError("setup must be run, skip, or inherit")
        args = ["worktree", "create"]
        evidence = [self.binary, *args]
        if repo_selector:
            args.extend(["--repo", repo_selector])
            evidence.extend(["--repo", repo_selector])
        args.extend(["--name", name])
        evidence.extend(["--name", name])
        if agent:
            args.extend(["--agent", agent])
            evidence.extend(["--agent", agent])
        if prompt is not None:
            args.extend(["--prompt", prompt])
            evidence.extend(["--prompt", "<redacted-prompt>"])
        args.extend(["--setup", setup])
        evidence.extend(["--setup", setup, "--json"])
        command = OrcaCommand(
            action="worktree.create",
            argv=(self.binary, *args, "--json"),
            evidence_argv=tuple(evidence),
            mutating=True,
        )
        return self.run(command, authority=authority)

    def terminal_read(self, terminal: str) -> OrcaResult:
        _require_value("terminal", terminal)
        return self.run(
            self._command("terminal.read", "terminal", "read", "--terminal", terminal)
        )

    def terminal_wait(self, terminal: str, timeout_ms: int = 300_000) -> OrcaResult:
        _require_value("terminal", terminal)
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        command = self._command(
            "terminal.wait",
            "terminal",
            "wait",
            "--terminal",
            terminal,
            "--for",
            "tui-idle",
            "--timeout-ms",
            str(timeout_ms),
        )
        return self.run(command)

    def file_diff(self, path: str, worktree: str = "active", staged: bool = False) -> OrcaResult:
        _require_value("path", path)
        _require_value("worktree", worktree)
        args = ["file", "diff", path]
        if staged:
            args.append("--staged")
        args.extend(["--worktree", worktree])
        return self.run(self._command("file.diff", *args))

    def snapshot(self, worktree: str = "active") -> OrcaResult:
        _require_value("worktree", worktree)
        return self.run(self._command("browser.snapshot", "snapshot", "--worktree", worktree))

    def run(
        self,
        command: OrcaCommand,
        *,
        authority: ExecutionAuthority | None = None,
        cwd: pathlib.Path | None = None,
    ) -> OrcaResult:
        authority = authority or ExecutionAuthority()
        if command.mutating:
            authority.require_mutation(command.action)
        raw = self.runner(command.argv, cwd, self.timeout_seconds)
        payload = _parse_json(raw.stdout)
        return OrcaResult(
            action=command.action,
            argv=command.evidence_argv or command.argv,
            mutating=command.mutating,
            mandate_id=authority.mandate_id if command.mutating else None,
            exit_code=raw.returncode,
            payload=payload,
            stdout=raw.stdout,
            stderr=raw.stderr,
        )

    def _command(self, action: str, *args: str, mutating: bool = False) -> OrcaCommand:
        return OrcaCommand(action=action, argv=(self.binary, *args, "--json"), mutating=mutating)


def _parse_json(stdout: str) -> Any:
    if not stdout.strip():
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def _require_value(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _default_runner(argv: Sequence[str], cwd: pathlib.Path | None, timeout: float) -> RunnerResult:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        check=False,
        shell=False,
    )
    return RunnerResult(completed.returncode, completed.stdout, completed.stderr)
