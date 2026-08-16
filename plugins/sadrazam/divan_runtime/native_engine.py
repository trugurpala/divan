from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .desktop_state import worktree_root
from .executable_locator import locate_executable
from .execution_contract import ExecutionAction, ExecutionReceipt, ExecutionRequest

ENGINE_ID = "native"
_SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")
AgentRunner = Callable[
    [Sequence[str], Path, float, str | None], tuple[int, str, str]
]
GitRunner = Callable[[Sequence[str], Path | None, float], tuple[int, str, str]]


@dataclass(frozen=True)
class AgentProfile:
    id: str
    aliases: tuple[str, ...]
    subscription_supported: bool
    timeout_seconds: float = 3600.0

    def invocation(self, binary: str, prompt: str) -> tuple[tuple[str, ...], str | None]:
        if self.id == "codex":
            return (binary, "exec", "--json", "--ephemeral", "-"), prompt
        if self.id == "claude":
            return (
                binary,
                "-p",
                "--output-format",
                "json",
                "--max-turns",
                "50",
            ), prompt
        if self.id == "opencode":
            return (binary, "run", prompt), None
        if self.id == "cursor-agent":
            return (binary, "-p", prompt, "--output-format", "json"), None
        raise ValueError(f"unsupported native agent: {self.id}")


AGENT_PROFILES = (
    AgentProfile("codex", ("codex",), True),
    AgentProfile("claude", ("claude",), True),
    AgentProfile("opencode", ("opencode",), False),
    AgentProfile("cursor-agent", ("cursor-agent",), True),
)


class NativeExecutionEngine:
    """Git-worktree execution engine for already installed local coding agents.

    Divan owns the mandate and the Git isolation boundary. The selected agent
    keeps its own account/subscription authentication; Divan never copies tokens.
    """

    engine_id = ENGINE_ID

    def __init__(
        self,
        *,
        agent_binaries: Mapping[str, str] | None = None,
        which: Callable[[str], str | None] = shutil.which,
        git_runner: GitRunner | None = None,
        agent_runner: AgentRunner | None = None,
    ) -> None:
        self.git_runner = git_runner or _run
        self.agent_runner = agent_runner or _run_in_directory
        self._which = which
        self._requires_current_probe = agent_binaries is None
        self.agent_binaries = dict(agent_binaries or _discover_agents(which))

    def execute(self, request: ExecutionRequest) -> ExecutionReceipt:
        if request.action is ExecutionAction.STATUS:
            return self._status(request)
        if request.action is ExecutionAction.WORKTREE_LIST:
            return self._worktree_list(request)
        if request.action is ExecutionAction.WORKTREE_CREATE:
            return self._worktree_create(request)
        if request.action is ExecutionAction.FILE_DIFF:
            return self._file_diff(request)
        raise ValueError(f"native engine does not support {request.action.value}")

    def _status(self, request: ExecutionRequest) -> ExecutionReceipt:
        payload = {
            "ready": bool(self.agent_binaries),
            "agents": [
                {
                    "id": profile.id,
                    "available": profile.id in self.agent_binaries,
                    "path": self.agent_binaries.get(profile.id),
                    "subscription_supported": profile.subscription_supported,
                }
                for profile in AGENT_PROFILES
            ],
        }
        return _receipt(request, True, 0, payload, (), None)

    def _worktree_list(self, request: ExecutionRequest) -> ExecutionReceipt:
        root = _project_root(request.project_root)
        code, stdout, stderr = self.git_runner(
            ("git", "-C", str(root), "worktree", "list", "--porcelain"),
            None,
            15.0,
        )
        payload = {"worktrees": _parse_worktrees(stdout)} if code == 0 else None
        return _receipt(
            request,
            code == 0,
            code,
            payload,
            ("git", "-C", str(root), "worktree", "list", "--porcelain"),
            request.mandate_id,
            stdout,
            stderr,
        )

    def _worktree_create(self, request: ExecutionRequest) -> ExecutionReceipt:
        root = _project_root(request.project_root)
        name = _required(request.args, "name")
        prompt = _required(request.args, "prompt")
        agent = _select_agent(request.args.get("agent"), self.agent_binaries)
        binary = self.agent_binaries[agent]
        if self._requires_current_probe and _discover_agents(self._which).get(agent) != binary:
            return _receipt(
                request,
                False,
                3,
                {"agent": agent},
                ("<agent-capability-probe>", agent),
                request.mandate_id,
                "",
                "agent capability changed since the engine was initialized",
            )
        slug = _slug(name)
        branch = f"divan/{slug}"
        destination = worktree_root() / slug
        if destination.exists():
            return _receipt(
                request,
                False,
                2,
                {"worktree": str(destination), "branch": branch, "agent": agent},
                ("git", "worktree", "add", "<existing>"),
                request.mandate_id,
                "",
                "worktree destination already exists",
            )
        destination.parent.mkdir(parents=True, exist_ok=True)

        git_argv = (
            "git",
            "-C",
            str(root),
            "worktree",
            "add",
            "-b",
            branch,
            str(destination),
            "HEAD",
        )
        code, stdout, stderr = self.git_runner(git_argv, None, 60.0)
        if code != 0:
            return _receipt(
                request,
                False,
                code,
                {"worktree": str(destination), "branch": branch, "agent": agent},
                git_argv,
                request.mandate_id,
                stdout,
                stderr,
            )

        profile = _profile(agent)
        agent_argv, stdin_text = profile.invocation(binary, prompt)
        agent_code, agent_stdout, agent_stderr = self.agent_runner(
            agent_argv,
            destination,
            profile.timeout_seconds,
            stdin_text,
        )
        evidence_argv = tuple(
            "<redacted-prompt>" if part == prompt else part for part in agent_argv
        )
        payload: dict[str, Any] = {
            "worktree": str(destination),
            "branch": branch,
            "agent": agent,
            "agent_exit_code": agent_code,
            "output": _structured_output(agent, agent_stdout),
        }
        return _receipt(
            request,
            agent_code == 0,
            agent_code,
            payload,
            evidence_argv,
            request.mandate_id,
            agent_stdout,
            agent_stderr,
        )

    def _file_diff(self, request: ExecutionRequest) -> ExecutionReceipt:
        worktree = request.args.get("worktree")
        if not isinstance(worktree, str) or not worktree.strip():
            raise ValueError("worktree is required")
        path = request.args.get("path")
        staged = request.args.get("staged") is True
        argv = ["git", "-C", worktree, "diff", "--no-ext-diff"]
        if staged:
            argv.append("--cached")
        argv.append("--")
        if isinstance(path, str) and path.strip() and path != "*":
            argv.append(path)
        code, stdout, stderr = self.git_runner(tuple(argv), None, 30.0)
        return _receipt(
            request,
            code == 0,
            code,
            {"diff": stdout, "staged": staged} if code == 0 else None,
            tuple(argv),
            request.mandate_id,
            stdout,
            stderr,
        )


def _discover_agents(which: Callable[[str], str | None]) -> dict[str, str]:
    found: dict[str, str] = {}
    for profile in AGENT_PROFILES:
        path = locate_executable(profile.aliases, which=which)
        if path:
            found[profile.id] = path
    return found


def _select_agent(value: object, binaries: Mapping[str, str]) -> str:
    if isinstance(value, str) and value.strip():
        agent = value.strip()
        if agent not in binaries:
            raise ValueError(f"agent is not available: {agent}")
        return agent
    for profile in AGENT_PROFILES:
        if profile.id in binaries:
            return profile.id
    raise ValueError("no supported local coding agent is available")


def _profile(agent: str) -> AgentProfile:
    for profile in AGENT_PROFILES:
        if profile.id == agent:
            return profile
    raise ValueError(f"unknown agent profile: {agent}")


def _project_root(value: str | None) -> Path:
    if not value or not value.strip():
        raise ValueError("project_root is required")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project_root must be an existing directory")
    return root


def _required(args: Mapping[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def _slug(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.strip()).strip("-._").lower()
    if not slug:
        raise ValueError("worktree name is not usable")
    return slug[:80]


def _parse_worktrees(stdout: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            if current:
                rows.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key in {"worktree", "HEAD", "branch"}:
            current[key.lower()] = value
    if current:
        rows.append(current)
    return rows


def _structured_output(agent: str, stdout: str) -> Any:
    if agent not in {"codex", "claude", "cursor-agent"}:
        return None
    text = stdout.strip()
    if not text:
        return None
    if agent == "codex":
        events: list[Any] = []
        for line in text.splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events[-20:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _receipt(
    request: ExecutionRequest,
    ok: bool,
    exit_code: int,
    payload: Any,
    argv: Sequence[str],
    mandate_id: str | None,
    stdout: str = "",
    stderr: str = "",
) -> ExecutionReceipt:
    return ExecutionReceipt(
        engine=ENGINE_ID,
        action=request.action,
        ok=ok,
        exit_code=exit_code,
        payload=payload,
        stdout=stdout,
        stderr=stderr,
        argv=tuple(argv),
        mandate_id=mandate_id,
    )


def _timeout_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _run(
    argv: Sequence[str],
    cwd: Path | None,
    timeout: float,
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            list(argv),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        stdout = _timeout_text(error.stdout)
        stderr = _timeout_text(error.stderr) or "command timed out"
        return 124, stdout, stderr
    except OSError as error:
        return 127, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr


def _run_in_directory(
    argv: Sequence[str],
    cwd: Path,
    timeout: float,
    stdin_text: str | None,
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            list(argv),
            cwd=cwd,
            input=stdin_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        stdout = _timeout_text(error.stdout)
        stderr = _timeout_text(error.stderr) or "command timed out"
        return 124, stdout, stderr
    except OSError as error:
        return 127, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr
