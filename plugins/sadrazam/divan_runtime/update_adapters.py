"""Real adapters for the tools the update governor manages.

The governor decides; these adapters observe. Each one answers three questions
about a real installation on this host: which version is present, which version
the source offers, and does the present one actually satisfy the contract Divan
depends on.

Nothing here installs, upgrades, replaces or removes anything. Discovery reads a
registry, certification runs the tool that is already there, and promotion
remains the governor's decision on the governor's evidence. A blind `npm update`
is exactly what this module exists to make unnecessary.

One certification check deserves its name. Asking a worker for its version tells
you a binary answers; it does not tell you the worker can start the sandbox it
needs to do work. A campaign attempt failed for precisely that reason while
version reporting stayed healthy, so the contract smoke asks the worker to
complete a trivial real task in a real directory.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .quality_factory import GateState
from .update_pipeline import CONTRACT_SMOKE_CHECKS

#: How long any single observation may take before it is reported as unknown.
PROBE_TIMEOUT_SECONDS = 120

#: Where each managed tool's candidate version is published, and how to read the
#: installed one. Registry names only; no download and no execution of anything
#: the source hands back.
_REGISTRY: dict[str, str] = {
    "codex": "@openai/codex",
    "claude": "@anthropic-ai/claude-code",
    "playwright": "playwright",
}


@dataclass(frozen=True)
class Observation:
    """What was actually seen, including nothing."""

    tool_id: str
    installed_version: str | None
    candidate_version: str | None
    source: str
    detail: str

    @property
    def known(self) -> bool:
        return self.installed_version is not None

    @property
    def has_candidate(self) -> bool:
        return (
            self.candidate_version is not None
            and self.installed_version is not None
            and self.candidate_version != self.installed_version
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "tool_id": self.tool_id,
            "installed_version": self.installed_version,
            "candidate_version": self.candidate_version,
            "source": self.source,
            "detail": self.detail,
        }


def _run(argv: Sequence[str], *, cwd: Path | None = None) -> tuple[int | None, str]:
    """Run a bounded observation, reporting failure rather than raising."""
    try:
        finished = subprocess.run(
            list(argv),
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PROBE_TIMEOUT_SECONDS,
            shell=os.name == "nt",
        )
    except (OSError, subprocess.SubprocessError) as problem:
        return None, f"{type(problem).__name__}: {problem}"
    return finished.returncode, (finished.stdout + finished.stderr).strip()


def _first_version(text: str) -> str | None:
    for piece in text.replace("(", " ").replace(")", " ").split():
        head = piece.lstrip("v")
        if head[:1].isdigit() and head.count(".") >= 1:
            return head
    return None


def installed_version(tool_id: str) -> tuple[str | None, str]:
    """The version of the tool actually on this host."""
    if tool_id == "chromium":
        return _installed_chromium()
    launcher = shutil.which(tool_id if tool_id != "playwright" else "npx")
    if launcher is None:
        return None, f"{tool_id} is not on the path"
    argv = [launcher, "--version"] if tool_id != "playwright" else [
        launcher, "--no-install", "playwright", "--version"
    ]
    code, text = _run(argv)
    if code != 0:
        return None, f"exit {code}: {text[:160]}"
    return _first_version(text), text[:160]


def _installed_chromium() -> tuple[str | None, str]:
    """Chromium is not a command; it is a directory Playwright manages."""
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    root = home / "AppData" / "Local" / "ms-playwright"
    if not root.is_dir():
        return None, "no Playwright browser directory on this host"
    builds = sorted(
        item.name.split("-", 1)[1]
        for item in root.iterdir()
        if item.is_dir() and item.name.startswith("chromium-")
    )
    if not builds:
        return None, "the browser directory holds no chromium build"
    return builds[-1], f"builds present: {', '.join(builds)}"


def candidate_version(tool_id: str) -> tuple[str | None, str]:
    """What the registry offers, read and nothing more.

    Chromium has no registry of its own; Playwright decides which build it
    wants, so a chromium candidate is only ever discovered through Playwright.
    """
    package = _REGISTRY.get(tool_id)
    if package is None:
        return None, f"{tool_id} publishes no version of its own"
    npm = shutil.which("npm")
    if npm is None:
        return None, "npm is not on the path, so no candidate can be discovered"
    code, text = _run([npm, "view", package, "version"])
    if code != 0:
        return None, f"exit {code}: {text[:160]}"
    return _first_version(text), f"{package}: {text[:80]}"


def discover(tool_id: str) -> Observation:
    """One tool, observed rather than assumed."""
    present, present_detail = installed_version(tool_id)
    offered, offered_detail = candidate_version(tool_id)
    return Observation(
        tool_id=tool_id,
        installed_version=present,
        candidate_version=offered,
        source=_REGISTRY.get(tool_id, "playwright-managed"),
        detail=f"installed: {present_detail}; candidate: {offered_detail}",
    )


def certify(tool_id: str, worktree: Path) -> dict[str, GateState]:
    """Drive the tool and report each contract check as a gate state.

    A check that could not be run is UNKNOWN rather than PASS, because the
    governor treats anything it cannot read as a reason to hold.
    """
    states = {name: GateState.UNKNOWN for name in CONTRACT_SMOKE_CHECKS}
    present, _ = installed_version(tool_id)
    states["version"] = GateState.PASS if present else GateState.FAIL
    if present is None:
        return states

    if tool_id in {"playwright", "chromium"}:
        return _certify_browser(states, worktree)
    return _certify_worker(states, tool_id, worktree)


def _certify_worker(
    states: dict[str, GateState], tool_id: str, worktree: Path
) -> dict[str, GateState]:
    from .worker_certification import certify_worker

    outcome = certify_worker(tool_id)
    # certify_worker reports auth as a named state rather than a flag, so the
    # gate follows what it actually says instead of a boolean that is not there.
    authorised = str(getattr(outcome, "auth", "")).casefold()
    states["auth"] = {
        "ready": GateState.PASS,
        "authenticated": GateState.PASS,
        "required": GateState.FAIL,
        "auth_required": GateState.FAIL,
    }.get(authorised, GateState.UNKNOWN)

    # The check that a version probe cannot make: can this worker actually
    # start and finish a trivial piece of real work in a real directory?
    from .worker_discovery import probe_worker
    from .worker_execution import WORKER_COMMANDS, build_argv

    probe = probe_worker(tool_id)
    executable = getattr(probe, "executable", None)
    command = WORKER_COMMANDS.get(tool_id)
    if executable and command:
        code, text = _run(
            [*build_argv(str(executable), command)][:-1] + ["--help"], cwd=worktree
        )
        started = code == 0 and "sandbox" not in text.casefold().split("error")[-1][:400]
        states["cwd"] = GateState.PASS if code == 0 else GateState.FAIL
        states["git-worktree"] = GateState.PASS if started else GateState.FAIL
    return states


def _certify_browser(
    states: dict[str, GateState], worktree: Path
) -> dict[str, GateState]:
    from .browser_capability import browser_capability

    report = browser_capability()
    ready = report.state.value.casefold() == "certified"
    for name in ("auth", "headless", "cwd", "git-worktree"):
        states[name] = GateState.PASS if ready else GateState.FAIL
    return states


def observations_payload(tool_ids: Sequence[str], worktree: Path) -> str:
    """A record of what was seen, for the evidence ledger."""
    return json.dumps(
        [
            {
                **discover(tool_id).to_dict(),
                "certification": {
                    name: state.value for name, state in certify(tool_id, worktree).items()
                },
            }
            for tool_id in tool_ids
        ],
        ensure_ascii=False,
        indent=2,
    )
