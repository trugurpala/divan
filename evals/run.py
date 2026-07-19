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
import pathlib
import random
import shlex
import subprocess
import sys
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "evals" / "results" / "latest.json"
MAX_ADAPTER_OUTPUT = 2_000_000
PROVENANCE_REQUIRED_FIELDS = (
    "agent",
    "agent_version",
    "judge",
    "judge_version",
    "source_commit",
    "environment",
)


class EvalError(RuntimeError):
    """Kullanıcıya gösterilebilir eval sözleşmesi veya koşu hatası."""


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
        if "sk-" in value.lower():
            raise EvalError(f"{path}: provenance gizli anahtar benzeri değer içeremez: {field}")
        provenance[field] = value.strip()
    if "notes" in data:
        notes = data["notes"]
        if not isinstance(notes, str) or not notes.strip():
            raise EvalError(f"{path}: provenance alanı eksik veya geçersiz: notes")
        if "sk-" in notes.lower():
            raise EvalError(f"{path}: provenance gizli anahtar benzeri değer içeremez: notes")
        provenance["notes"] = notes.strip()
    return provenance


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
    if not args:
        raise EvalError("adaptör komutu boş")
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise EvalError(f"adaptör çalışmadı: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip()[-1000:] or "stderr boş"
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
    return {"output": output, "events": events, "changed_files": changed_files}


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
    return {"winner": winner, "reasons": reasons, "expectation_scores": scores}


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
        candidates = {
            label: _public_candidate(outputs[condition]) for label, condition in mapping.items()
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
                **judgement,
                "winner_condition": winner_condition,
            }
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
        "cases": key_cases,
    }
    return result, key


def write_results(output: pathlib.Path, result: dict[str, Any], key: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    key_path = output.with_name(output.stem + ".key" + output.suffix)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Divan skill-vs-baseline eval koşucusu")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Sözleşmeleri doğrula, model çalıştırma")
    mode.add_argument("--run", action="store_true", help="Baseline ve skill koşularını çalıştır")
    parser.add_argument("--skill", action="append", default=[], help="Yalnız seçilen skill; tekrarlanabilir")
    parser.add_argument("--adapter", help="JSON stdin/stdout ajan adaptörü komutu")
    parser.add_argument("--judge", help="JSON stdin/stdout kör hakem adaptörü komutu")
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
            raise EvalError("--run için --adapter zorunlu")
        provenance = _read_provenance(args.provenance) if args.provenance else None
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
