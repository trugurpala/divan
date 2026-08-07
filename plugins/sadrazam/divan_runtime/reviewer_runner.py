from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .executable_locator import locate_executable
from .review_gate import CheckResult

Runner = Callable[[Sequence[str], Path, float, str], tuple[int, str, str]]


class ReviewerUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class AutomatedReview:
    reviewer: str
    verdict: str
    summary: str
    findings: tuple[str, ...]

    def check(self) -> CheckResult:
        return CheckResult(
            name=f"independent-review:{self.reviewer}",
            passed=self.verdict == "PASS",
            required=True,
            summary=self.summary,
        )


class AutomatedReviewer:
    """Run an installed coding agent as a read-only independent reviewer."""

    def __init__(
        self,
        *,
        binaries: Mapping[str, str] | None = None,
        which: Callable[[str], str | None] = shutil.which,
        runner: Runner | None = None,
    ) -> None:
        self.binaries = dict(binaries or _discover(which))
        self.runner = runner or _run

    def review(
        self,
        *,
        task_title: str,
        diff: str,
        worker_agent: str | None = None,
    ) -> AutomatedReview:
        if not diff.strip():
            return AutomatedReview(
                "builtin",
                "RETRY",
                "No code diff to review.",
                ("empty diff",),
            )
        reviewer = self._select(worker_agent)
        argv = _reviewer_argv(reviewer, self.binaries[reviewer])
        prompt = _review_prompt(task_title, diff)
        code, stdout, stderr = self.runner(argv, Path.cwd(), 600.0, prompt)
        if code != 0:
            detail = (stderr or stdout).strip()[:500]
            raise ReviewerUnavailable(f"{reviewer} reviewer failed: {detail or code}")
        return _parse_review(reviewer, stdout)

    def _select(self, worker_agent: str | None) -> str:
        for candidate in ("claude", "codex"):
            if candidate in self.binaries and candidate != worker_agent:
                return candidate
        for candidate in ("claude", "codex"):
            if candidate in self.binaries:
                return candidate
        raise ReviewerUnavailable("no supported independent reviewer is installed")


def _discover(which: Callable[[str], str | None]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in ("claude", "codex"):
        path = locate_executable((name,), which=which)
        if path:
            result[name] = path
    return result


def _reviewer_argv(reviewer: str, binary: str) -> tuple[str, ...]:
    if reviewer == "claude":
        return (
            binary,
            "-p",
            "--output-format",
            "json",
            "--permission-mode",
            "plan",
            "--max-turns",
            "6",
        )
    if reviewer == "codex":
        return (
            binary,
            "exec",
            "--json",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "-",
        )
    raise ReviewerUnavailable(f"unsupported reviewer: {reviewer}")


def _review_prompt(task_title: str, diff: str) -> str:
    return (
        "You are Divan's independent code reviewer. Do not edit files or run mutating "
        "commands. Review only the supplied patch for correctness, regressions, security, "
        "tests, and whether it satisfies the task. Return exactly one JSON object with "
        'keys: {"verdict":"PASS|RETRY","summary":"short text","findings":["..."]}. '
        f"\n\nTASK:\n{task_title}\n\nPATCH:\n{diff}"
    )


def _parse_review(reviewer: str, stdout: str) -> AutomatedReview:
    payload = _extract_payload(reviewer, stdout)
    verdict = str(payload.get("verdict", "")).upper()
    if verdict not in {"PASS", "RETRY"}:
        raise ReviewerUnavailable("reviewer returned an invalid verdict")
    summary = str(payload.get("summary", "")).strip()[:1000]
    raw_findings = payload.get("findings", [])
    findings = (
        tuple(str(item).strip()[:500] for item in raw_findings if str(item).strip())
        if isinstance(raw_findings, list)
        else ()
    )
    return AutomatedReview(
        reviewer=reviewer,
        verdict=verdict,
        summary=summary
        or ("Review passed." if verdict == "PASS" else "Review needs changes."),
        findings=findings[:20],
    )


def _extract_payload(reviewer: str, stdout: str) -> Mapping[str, object]:
    text = stdout.strip()
    if reviewer == "claude":
        outer = json.loads(text)
        result = outer.get("result") if isinstance(outer, Mapping) else None
        if not isinstance(result, str):
            raise ReviewerUnavailable("Claude reviewer returned no result")
        value = json.loads(_json_object_text(result))
    else:
        value = _last_codex_message(text)
    if not isinstance(value, Mapping):
        raise ReviewerUnavailable("reviewer response is not a JSON object")
    return value


def _last_codex_message(text: str) -> Mapping[str, object]:
    for line in reversed(text.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping):
            continue
        message = _codex_message_text(event)
        if message:
            value = json.loads(_json_object_text(message))
            if isinstance(value, Mapping):
                return value
    raise ReviewerUnavailable("Codex reviewer returned no final message")


def _codex_message_text(event: Mapping[str, object]) -> str | None:
    item = event.get("item")
    if isinstance(item, Mapping):
        text = item.get("text")
        if isinstance(text, str):
            return text
    message = event.get("message")
    return message if isinstance(message, str) else None


def _json_object_text(value: str) -> str:
    start = value.find("{")
    end = value.rfind("}")
    if start < 0 or end <= start:
        raise ReviewerUnavailable("reviewer did not return JSON")
    return value[start : end + 1]


def _run(
    argv: Sequence[str],
    cwd: Path,
    timeout: float,
    stdin_text: str,
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
    except subprocess.TimeoutExpired:
        return 124, "", "reviewer timed out"
    except OSError as error:
        return 127, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr
