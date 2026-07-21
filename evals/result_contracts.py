"""Public eval result validation, redaction, and persistence contracts."""

from __future__ import annotations

import json
import pathlib
import random
import re
import time
from collections.abc import Callable
from typing import Any

PUBLIC_PATTERNS = (
    re.compile(
        r"(?i)(?:sk-[a-z0-9_-]{8,}|github_pat_[a-z0-9_]{8,}|gh[opusr]_[a-z0-9]{8,}|"
        r"(?:api[_-]?key|access[_-]?token|token|secret|password|passwd)\s*[=:]\s*[^\s,;]+)"
    ),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\/\s]+"),
    re.compile(r"/(?:home|Users)/[^/\s]+"),
)


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


AdapterRunner = Callable[[str, dict[str, Any], float], dict[str, Any]]


def run_evaluations(
    cases: list[dict[str, Any]],
    adapter: str,
    judge: str | None = None,
    *,
    timeout: float = 120.0,
    seed: int | bytes = 0,
    min_skill_win_rate: float | None = None,
    provenance: dict[str, str] | None = None,
    run_adapter: AdapterRunner,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run adapter pairs and return the public result and private blind key."""
    _validate_run(cases, judge, min_skill_win_rate)
    rng = random.Random(seed)
    public_cases: list[dict[str, Any]] = []
    key_cases: list[dict[str, Any]] = []
    totals = {"skill": 0, "baseline": 0, "tie": 0}
    for case in cases:
        public_case, key_case, winner = _evaluate_case(
            case, adapter, judge, timeout, rng, run_adapter
        )
        if winner is not None:
            totals[winner] += 1
        public_cases.append(public_case)
        key_cases.append(key_case)
    result = _public_result(public_cases, totals, judge, min_skill_win_rate)
    if provenance is not None:
        result["provenance"] = provenance
    key = {
        "schema_version": 1,
        "notice": "Kör inceleme tamamlanmadan bu dosyayı açmayın.",
        "blind_seed": seed.hex() if isinstance(seed, bytes) else seed,
        "cases": key_cases,
    }
    return result, key


def _validate_run(
    cases: list[dict[str, Any]], judge: str | None, min_skill_win_rate: float | None
) -> None:
    if not cases:
        raise EvalError("sıfır eval vakası başarı sayılamaz")
    if min_skill_win_rate is not None and judge is None:
        raise EvalError("min-skill-win-rate için --judge zorunlu")
    if min_skill_win_rate is not None and not 0 <= min_skill_win_rate <= 1:
        raise EvalError("min-skill-win-rate 0 ile 1 arasında olmalı")


def _evaluate_case(
    case: dict[str, Any],
    adapter: str,
    judge: str | None,
    timeout: float,
    rng: random.Random,
    run_adapter: AdapterRunner,
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    outputs = {
        condition: _validate_agent_result(
            run_adapter(adapter, _agent_request(case, condition), timeout)
        )
        for condition in ("baseline", "skill")
    }
    labels = ["A", "B"]
    rng.shuffle(labels)
    mapping = {labels[0]: "baseline", labels[1]: "skill"}
    candidates = {
        label: _public_candidate(outputs[mapping[label]]) for label in ("A", "B")
    }
    public_case = _case_contract(case, candidates)
    key_case: dict[str, Any] = {
        "skill_name": case["skill_name"],
        "case_id": case["case_id"],
        "mapping": mapping,
    }
    if not judge:
        return public_case, key_case, None
    judgement = _validate_judgement(
        run_adapter(judge, _judge_request(case, candidates), timeout)
    )
    winner_label = judgement["winner"]
    winner = "tie" if winner_label == "tie" else mapping[winner_label]
    public_case["judgement"] = {"expectation_scores": judgement["expectation_scores"]}
    key_case.update(
        {
            "reasons": judgement["reasons"],
            "winner_label": winner_label,
            "winner_condition": winner,
        }
    )
    return public_case, key_case, winner


def _agent_request(case: dict[str, Any], condition: str) -> dict[str, Any]:
    return {
        "protocol_version": 1,
        "condition": condition,
        "skill_name": case["skill_name"],
        "case_id": case["case_id"],
        "prompt": case["prompt"],
        "files": case["files"],
        "skill_path": case["skill_path"] if condition == "skill" else None,
    }


def _judge_request(
    case: dict[str, Any], candidates: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    return {
        "protocol_version": 1,
        "skill_name": case["skill_name"],
        "case_id": case["case_id"],
        "prompt": case["prompt"],
        "expected_output": case["expected_output"],
        "expectations": case["expectations"],
        "candidates": candidates,
    }


def _case_contract(
    case: dict[str, Any], candidates: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    return {
        "skill_name": case["skill_name"],
        "case_id": case["case_id"],
        "prompt": case["prompt"],
        "expected_output": case["expected_output"],
        "expectations": case["expectations"],
        "candidates": candidates,
    }


def _public_result(
    cases: list[dict[str, Any]],
    totals: dict[str, int],
    judge: str | None,
    min_skill_win_rate: float | None,
) -> dict[str, Any]:
    judged_count = sum(totals.values())
    decisive = totals["skill"] + totals["baseline"]
    skill_win_rate = totals["skill"] / decisive if decisive else None
    gate_passed: bool | None = None
    if min_skill_win_rate is not None:
        gate_passed = skill_win_rate is not None and skill_win_rate >= min_skill_win_rate
    return {
        "schema_version": 1,
        "status": "completed" if judge else "review_required",
        "generated_at": int(time.time()),
        "case_count": len(cases),
        "judged_count": judged_count,
        "summary": {
            "skill_wins": totals["skill"],
            "baseline_wins": totals["baseline"],
            "ties": totals["tie"],
            "skill_win_rate": skill_win_rate,
            "minimum_skill_win_rate": min_skill_win_rate,
            "gate_passed": gate_passed,
        },
        "cases": cases,
    }


def write_results(output: pathlib.Path, result: dict[str, Any], key: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    key_path = output.with_name(output.stem + ".key" + output.suffix)
    public_result = _sanitize_public(result)
    output.write_text(
        json.dumps(public_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
