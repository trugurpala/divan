#!/usr/bin/env python3
"""Divan davranış eval koşucusu.

Eval vakalarını skill klasörlerinden keşfeder, aynı promptu baseline ve skill
koşullarında harici bir ajan adaptörüne gönderir, çıktıları A/B olarak
körleştirir ve isteğe bağlı bir hakem adaptörüyle ölçer. Yalnız stdlib kullanır.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import random
import re
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "evals" / "results" / "latest.json"
MAX_ADAPTER_OUTPUT = 2_000_000
PUBLIC_PATTERNS = (
    re.compile(
        r"(?i)(?:sk-[a-z0-9_-]{8,}|github_pat_[a-z0-9_]{8,}|gh[opusr]_[a-z0-9]{8,}|"
        r"(?:api[_-]?key|access[_-]?token|token|secret|password|passwd)\s*[=:]\s*[^\s,;]+)"
    ),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\/\s]+"),
    re.compile(r"/(?:home|Users)/[^/\s]+"),
)
PROVENANCE_REQUIRED_FIELDS = (
    "agent",
    "agent_version",
    "judge",
    "judge_version",
    "source_commit",
    "environment",
)
FIRST_PARTY_NON_TOOL_SKILLS = {"baglam-muhafizi"}


class EvalError(RuntimeError):
    """Kullanıcıya gösterilebilir eval sözleşmesi veya koşu hatası."""


def _redact_public_text(value: str) -> str:
    redacted = value
    for pattern in PUBLIC_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _sanitize_public(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_public_text(value)
    if isinstance(value, list):
        return [_sanitize_public(item) for item in value]
    if isinstance(value, dict):
        return {
            _redact_public_text(str(key)): _sanitize_public(item)
            for key, item in value.items()
        }
    return value


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvalError(f"{path}: JSON okunamadı: {error}") from error
    if not isinstance(value, dict):
        raise EvalError(f"{path}: kök JSON nesne olmalı")
    return value


def _read_provenance(path: pathlib.Path) -> dict[str, str]:
    """Read redacted runner provenance without accepting secret-like values."""
    data = _read_json(path)
    allowed = set(PROVENANCE_REQUIRED_FIELDS) | {"notes"}
    unexpected = sorted(set(data) - allowed)
    if unexpected:
        raise EvalError(f"{path}: bilinmeyen provenance alanı: {', '.join(unexpected)}")
    provenance: dict[str, str] = {}
    for field in PROVENANCE_REQUIRED_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EvalError(f"{path}: provenance alanı eksik veya geçersiz: {field}")
        if _redact_public_text(value) != value:
            raise EvalError(f"{path}: provenance gizli/kişisel değer içeremez: {field}")
        provenance[field] = value.strip()
    if "notes" in data:
        notes = data["notes"]
        if not isinstance(notes, str) or not notes.strip():
            raise EvalError(f"{path}: provenance alanı eksik veya geçersiz: notes")
        if _redact_public_text(notes) != notes:
            raise EvalError(f"{path}: provenance gizli/kişisel değer içeremez: notes")
        provenance["notes"] = notes.strip()
    return provenance


def _repository_identity(root: pathlib.Path = ROOT) -> dict[str, str]:
    def git(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode:
            detail = _redact_public_text(completed.stderr.strip()) or "git failed"
            raise EvalError(f"repository identity cannot be derived: {detail}")
        return completed.stdout.strip()

    source_commit = git("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise EvalError("repository HEAD is not a full Git commit")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise EvalError("real eval requires a clean repository worktree")
    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise EvalError("repository VERSION cannot be read") from exc
    if not version:
        raise EvalError("repository VERSION is empty")
    return {"source_commit": source_commit, "divan_version": version}


def _validate_provider_skill_scope(skills: set[str]) -> None:
    unsupported = sorted(skills - FIRST_PARTY_NON_TOOL_SKILLS)
    if unsupported:
        raise EvalError(
            "first-party preset only supports audited non-tool eval skills; rejected: "
            + ", ".join(unsupported)
        )


def _version_for_command(variable: str, default: str) -> str:
    command_text = os.environ.get(variable, default)
    args = shlex.split(command_text, posix=sys.platform != "win32")
    if sys.platform == "win32":
        args = [
            item[1:-1]
            if len(item) >= 2 and item[0] == item[-1] and item[0] in {'"', "'"}
            else item
            for item in args
        ]
    resolved = shutil.which(args[0]) if args else None
    if resolved is None:
        raise EvalError(f"provider version executable cannot be found: {variable}")
    invocation = [resolved, *args[1:], "--version"]
    if os.name == "nt" and pathlib.Path(resolved).suffix.lower() in {".cmd", ".bat"}:
        invocation = ["cmd.exe", "/d", "/s", "/c", resolved, *args[1:], "--version"]
    try:
        completed = subprocess.run(
            invocation,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EvalError(f"provider version cannot be derived: {variable}") from exc
    version = (completed.stdout or completed.stderr).strip().splitlines()
    if completed.returncode or not version:
        raise EvalError(f"provider version cannot be derived: {variable}")
    value = _redact_public_text(version[0])
    if value != version[0]:
        raise EvalError(f"provider version contains private data: {variable}")
    return value


def _bind_provenance(
    provenance: dict[str, str],
    *,
    provider_preset: str | None,
    seed: int = 0,
    selected_skills: list[str] | None = None,
    timeout: float = 120.0,
    min_skill_win_rate: float | None = None,
    root: pathlib.Path = ROOT,
) -> dict[str, str]:
    identity = _repository_identity(root)
    if provenance["source_commit"] != identity["source_commit"]:
        raise EvalError("provenance source_commit does not match clean repository HEAD")
    bound = dict(provenance)
    bound.update(identity)
    bound["environment"] = "; ".join(
        filter(None, (platform.system(), platform.release(), platform.machine()))
    )
    if provider_preset == "claude-codex":
        models: dict[str, str] = {}
        for variable, field in (
            ("DIVAN_CLAUDE_MODEL", "agent_model"),
            ("DIVAN_CODEX_MODEL", "judge_model"),
        ):
            value = os.environ.get(variable, "").strip()
            if not value:
                raise EvalError(f"{variable} must pin the provider model for publishable runs")
            if _redact_public_text(value) != value:
                raise EvalError(f"{variable} contains private data")
            models[field] = value
        if seed < 0 or seed.bit_length() < 128:
            raise EvalError(
                "publishable provider runs require a private seed with at least 128-bit entropy"
            )
        skills = sorted(selected_skills or [])
        command = [
            "python",
            "evals/run.py",
            "--run",
            "--provider-preset",
            "claude-codex",
        ]
        for skill in skills:
            command.extend(["--skill", skill])
        command.extend(["--seed", "[PRIVATE]", "--timeout", f"{timeout:g}"])
        if min_skill_win_rate is not None:
            command.extend(["--min-skill-win-rate", f"{min_skill_win_rate:g}"])
        bound.update(
            {
                "agent": "Claude Code",
                "agent_version": _version_for_command("DIVAN_CLAUDE_BIN", "claude"),
                "judge": "Codex CLI",
                "judge_version": _version_for_command("DIVAN_CODEX_BIN", "codex"),
                **models,
                "blind_seed_sha256": hashlib.sha256(str(seed).encode("ascii")).hexdigest(),
                "blind_seed_entropy_bits": str(seed.bit_length()),
                "selected_skills": ",".join(skills),
                "timeout_seconds": f"{timeout:g}",
                "minimum_skill_win_rate": (
                    "none" if min_skill_win_rate is None else f"{min_skill_win_rate:g}"
                ),
                "run_command": subprocess.list2cmdline(command),
            }
        )
    return bound


def discover_cases(
    root: pathlib.Path = ROOT, selected_skills: set[str] | None = None
) -> list[dict[str, Any]]:
    """Bütün eval sözleşmelerini doğrula ve düz vaka listesine çevir."""
    cases: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    paths = sorted(root.glob("plugins/*/skills/*/evals/evals.json"))
    for path in paths:
        data = _read_json(path)
        skill_name = data.get("skill_name")
        skill_dir = path.parents[1]
        if not isinstance(skill_name, str) or not skill_name.strip():
            raise EvalError(f"{path}: skill_name dolu metin olmalı")
        if skill_name != skill_dir.name:
            raise EvalError(
                f"{path}: skill_name '{skill_name}' klasör adı '{skill_dir.name}' ile eşleşmiyor"
            )
        if selected_skills and skill_name not in selected_skills:
            continue
        raw_cases = data.get("evals")
        if not isinstance(raw_cases, list) or not raw_cases:
            raise EvalError(f"{path}: en az bir eval vakası gerekli")

        for raw in raw_cases:
            if not isinstance(raw, dict):
                raise EvalError(f"{path}: her eval nesne olmalı")
            case_id = raw.get("id")
            prompt = raw.get("prompt")
            expected = raw.get("expected_output")
            expectations = raw.get("expectations")
            files = raw.get("files", [])
            if not isinstance(case_id, int) or isinstance(case_id, bool):
                raise EvalError(f"{path}: eval id benzersiz tamsayı olmalı: {case_id!r}")
            key = (skill_name, case_id)
            if key in seen:
                raise EvalError(f"{path}: eval id benzersiz tamsayı olmalı: {case_id!r}")
            if not isinstance(prompt, str) or not prompt.strip():
                raise EvalError(f"{path}: eval {case_id} prompt eksik")
            if not isinstance(expected, str) or not expected.strip():
                raise EvalError(f"{path}: eval {case_id} expected_output eksik")
            if not isinstance(expectations, list) or not expectations or not all(
                isinstance(item, str) and item.strip() for item in expectations
            ):
                raise EvalError(f"{path}: eval {case_id} expectations eksik")
            if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
                raise EvalError(f"{path}: eval {case_id} files metin dizisi olmalı")

            seen.add(key)
            cases.append(
                {
                    "skill_name": skill_name,
                    "skill_path": str(skill_dir.relative_to(root)),
                    "case_id": case_id,
                    "prompt": prompt,
                    "expected_output": expected,
                    "expectations": expectations,
                    "files": files,
                }
            )

    if selected_skills:
        found = {case["skill_name"] for case in cases}
        missing = sorted(selected_skills - found)
        if missing:
            raise EvalError("eval sözleşmesi bulunamayan skill: " + ", ".join(missing))
    if not cases:
        raise EvalError("sıfır eval vakası başarı sayılamaz")
    return cases


def _run_adapter(command: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    # Windows paths commonly contain backslashes (for example, the temporary
    # adapters created by the test suite). POSIX parsing treats those as escape
    # characters and turns a valid executable path into a non-existent one.
    args = shlex.split(command, posix=sys.platform != "win32")
    if sys.platform == "win32":
        args = [
            arg[1:-1] if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in {'"', "'"} else arg
            for arg in args
        ]
    if not args:
        raise EvalError("adaptör komutu boş")
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise EvalError(f"adaptör çalışmadı: {_redact_public_text(str(error))}") from error
    if completed.returncode != 0:
        detail = _redact_public_text(completed.stderr.strip()[-1000:]) or "stderr boş"
        raise EvalError(f"adaptör exit={completed.returncode}: {detail}")
    if len(completed.stdout.encode("utf-8")) > MAX_ADAPTER_OUTPUT:
        raise EvalError("adaptör çıktısı 2 MB sınırını aştı")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise EvalError(f"adaptör geçerli tek JSON nesnesi döndürmedi: {error}") from error
    if not isinstance(result, dict):
        raise EvalError("adaptör çıktısı JSON nesnesi olmalı")
    return result


def _validate_agent_result(result: dict[str, Any]) -> dict[str, Any]:
    output = result.get("output")
    events = result.get("events", [])
    changed_files = result.get("changed_files", [])
    if not isinstance(output, str) or not output.strip():
        raise EvalError("ajan adaptörü dolu output döndürmeli")
    if not isinstance(events, list) or not all(isinstance(item, str) for item in events):
        raise EvalError("ajan adaptörü events için metin dizisi döndürmeli")
    if not isinstance(changed_files, list) or not all(
        isinstance(item, str) for item in changed_files
    ):
        raise EvalError("ajan adaptörü changed_files için metin dizisi döndürmeli")
    return _sanitize_public(
        {"output": output, "events": events, "changed_files": changed_files}
    )


def _validate_judgement(result: dict[str, Any]) -> dict[str, Any]:
    winner = result.get("winner")
    reasons = result.get("reasons")
    if winner not in {"A", "B", "tie"}:
        raise EvalError("hakem adaptörü winner için A, B veya tie döndürmeli")
    if not isinstance(reasons, list) or not reasons or not all(
        isinstance(item, str) and item.strip() for item in reasons
    ):
        raise EvalError("hakem adaptörü en az bir gerekçe döndürmeli")
    scores = result.get("expectation_scores", {})
    if not isinstance(scores, dict):
        raise EvalError("hakem expectation_scores nesne olmalı")
    return _sanitize_public(
        {"winner": winner, "reasons": reasons, "expectation_scores": scores}
    )


def _public_candidate(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "output": result["output"],
        "events": result["events"],
        "changed_files": result["changed_files"],
    }


def run_evaluations(
    cases: list[dict[str, Any]],
    adapter: str,
    judge: str | None = None,
    *,
    timeout: float = 120.0,
    seed: int = 0,
    min_skill_win_rate: float | None = None,
    provenance: dict[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Gerçek adaptör koşularını yap; kamu sonucu ve gizli A/B anahtarını döndür."""
    if not cases:
        raise EvalError("sıfır eval vakası başarı sayılamaz")
    if min_skill_win_rate is not None and judge is None:
        raise EvalError("min-skill-win-rate için --judge zorunlu")
    if min_skill_win_rate is not None and not 0 <= min_skill_win_rate <= 1:
        raise EvalError("min-skill-win-rate 0 ile 1 arasında olmalı")

    rng = random.Random(seed)
    public_cases: list[dict[str, Any]] = []
    key_cases: list[dict[str, Any]] = []
    totals = {"skill": 0, "baseline": 0, "tie": 0}

    for case in cases:
        outputs: dict[str, dict[str, Any]] = {}
        for condition in ("baseline", "skill"):
            request = {
                "protocol_version": 1,
                "condition": condition,
                "skill_name": case["skill_name"],
                "case_id": case["case_id"],
                "prompt": case["prompt"],
                "files": case["files"],
                "skill_path": case["skill_path"] if condition == "skill" else None,
            }
            outputs[condition] = _validate_agent_result(
                _run_adapter(adapter, request, timeout)
            )

        labels = ["A", "B"]
        rng.shuffle(labels)
        mapping = {labels[0]: "baseline", labels[1]: "skill"}
        # Public and judge-visible candidate order must be stable and independent
        # from the randomized baseline/skill mapping. Otherwise dict insertion
        # order itself reconstructs the supposedly private mapping.
        candidates = {
            label: _public_candidate(outputs[mapping[label]]) for label in ("A", "B")
        }
        public_case: dict[str, Any] = {
            "skill_name": case["skill_name"],
            "case_id": case["case_id"],
            "prompt": case["prompt"],
            "expected_output": case["expected_output"],
            "expectations": case["expectations"],
            "candidates": candidates,
        }
        key_case: dict[str, Any] = {
            "skill_name": case["skill_name"],
            "case_id": case["case_id"],
            "mapping": mapping,
        }

        if judge:
            judgement = _validate_judgement(
                _run_adapter(
                    judge,
                    {
                        "protocol_version": 1,
                        "skill_name": case["skill_name"],
                        "case_id": case["case_id"],
                        "prompt": case["prompt"],
                        "expected_output": case["expected_output"],
                        "expectations": case["expectations"],
                        "candidates": candidates,
                    },
                    timeout,
                )
            )
            winner_label = judgement["winner"]
            winner_condition = "tie" if winner_label == "tie" else mapping[winner_label]
            totals[winner_condition] += 1
            public_case["judgement"] = {
                "expectation_scores": judgement["expectation_scores"],
            }
            key_case["reasons"] = judgement["reasons"]
            key_case["winner_label"] = winner_label
            key_case["winner_condition"] = winner_condition

        public_cases.append(public_case)
        key_cases.append(key_case)

    judged_count = sum(totals.values())
    decisive = totals["skill"] + totals["baseline"]
    skill_win_rate = totals["skill"] / decisive if decisive else None
    status = "completed" if judge else "review_required"
    gate_passed: bool | None = None
    if min_skill_win_rate is not None:
        gate_passed = skill_win_rate is not None and skill_win_rate >= min_skill_win_rate

    result = {
        "schema_version": 1,
        "status": status,
        "generated_at": int(time.time()),
        "case_count": len(public_cases),
        "judged_count": judged_count,
        "summary": {
            "skill_wins": totals["skill"],
            "baseline_wins": totals["baseline"],
            "ties": totals["tie"],
            "skill_win_rate": skill_win_rate,
            "minimum_skill_win_rate": min_skill_win_rate,
            "gate_passed": gate_passed,
        },
        "cases": public_cases,
    }
    if provenance is not None:
        result["provenance"] = provenance
    key = {
        "schema_version": 1,
        "notice": "Kör inceleme tamamlanmadan bu dosyayı açmayın.",
        "blind_seed": seed,
        "cases": key_cases,
    }
    return result, key


def write_results(output: pathlib.Path, result: dict[str, Any], key: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    key_path = output.with_name(output.stem + ".key" + output.suffix)
    public_result = _sanitize_public(result)
    output.write_text(
        json.dumps(public_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Divan skill-vs-baseline eval koşucusu")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Sözleşmeleri doğrula, model çalıştırma")
    mode.add_argument("--run", action="store_true", help="Baseline ve skill koşularını çalıştır")
    parser.add_argument("--skill", action="append", default=[], help="Yalnız seçilen skill; tekrarlanabilir")
    parser.add_argument("--adapter", help="JSON stdin/stdout ajan adaptörü komutu")
    parser.add_argument("--judge", help="JSON stdin/stdout kör hakem adaptörü komutu")
    parser.add_argument(
        "--provider-preset",
        choices=("claude-codex",),
        help="Birinci taraf gerçek ajan/hakem adaptörlerini seç",
    )
    parser.add_argument("--timeout", type=float, default=120.0, help="Her adaptör çağrısı için saniye")
    parser.add_argument("--seed", type=int, default=0, help="A/B körleme tohumu")
    parser.add_argument("--min-skill-win-rate", type=float, help="0..1 yayın kapısı; hakem gerekir")
    parser.add_argument("--provenance", type=pathlib.Path, help="Gerçek koşu için redakte edilmiş provenance JSON'u")
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        selected = set(args.skill) or None
        cases = discover_cases(ROOT, selected)
        skills = sorted({case["skill_name"] for case in cases})
        if args.check:
            if args.provenance:
                raise EvalError("--provenance yalnız --run ile kullanılabilir")
            print(
                json.dumps(
                    {"status": "valid", "skill_count": len(skills), "case_count": len(cases)},
                    ensure_ascii=False,
                )
            )
            return 0
        if not args.adapter:
            if args.provider_preset == "claude-codex":
                _validate_provider_skill_scope(set(skills))
                args.adapter = subprocess.list2cmdline(
                    [sys.executable, str(ROOT / "evals" / "adapters" / "claude_agent.py")]
                )
                args.judge = subprocess.list2cmdline(
                    [sys.executable, str(ROOT / "evals" / "adapters" / "codex_judge.py")]
                )
            else:
                raise EvalError("--run için --adapter veya --provider-preset zorunlu")
        elif args.provider_preset:
            raise EvalError("--provider-preset ile --adapter/--judge birlikte kullanılamaz")
        provenance = _read_provenance(args.provenance) if args.provenance else None
        if args.provider_preset and provenance is None:
            raise EvalError("--provider-preset requires --provenance")
        if provenance is not None:
            provenance = _bind_provenance(
                provenance,
                provider_preset=args.provider_preset,
                seed=args.seed,
                selected_skills=skills,
                timeout=args.timeout,
                min_skill_win_rate=args.min_skill_win_rate,
            )
        result, key = run_evaluations(
            cases,
            args.adapter,
            args.judge,
            timeout=args.timeout,
            seed=args.seed,
            min_skill_win_rate=args.min_skill_win_rate,
            provenance=provenance,
        )
        write_results(args.output, result, key)
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "case_count": result["case_count"],
                    "output": str(args.output),
                    "summary": result["summary"],
                },
                ensure_ascii=False,
            )
        )
        if result["summary"]["gate_passed"] is False:
            return 2
        return 0
    except EvalError as error:
        print(f"EVAL HATASI: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
