#!/usr/bin/env python3
"""Divan davranış eval koşucusu.

Eval vakalarını skill klasörlerinden keşfeder, aynı promptu baseline ve skill
koşullarında harici bir ajan adaptörüne gönderir, çıktıları A/B olarak
körleştirir ve isteğe bağlı bir hakem adaptörüyle ölçer. Yalnız stdlib kullanır.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import secrets
import shlex
import subprocess
import sys
from typing import Any

try:
    from evals import provenance as _provenance
    from evals import result_contracts as _contracts
except ModuleNotFoundError:  # Direct ``python evals/run.py`` execution.
    import provenance as _provenance  # type: ignore[no-redef]
    import result_contracts as _contracts  # type: ignore[no-redef]

PUBLIC_PATTERNS = _contracts.PUBLIC_PATTERNS
PROVENANCE_REQUIRED_FIELDS = _provenance.PROVENANCE_REQUIRED_FIELDS
EvalError = _contracts.EvalError
_bind_provenance_core = _provenance._bind_provenance
_public_candidate = _contracts._public_candidate
_read_json = _provenance._read_json
_read_provenance = _provenance._read_provenance
_redact_public_text = _contracts._redact_public_text
_repository_identity = _provenance._repository_identity
_run_evaluations_core = _contracts.run_evaluations
_sanitize_public = _contracts._sanitize_public
_validate_agent_result = _contracts._validate_agent_result
_validate_judgement = _contracts._validate_judgement
_version_for_command = _provenance._version_for_command
write_results = _contracts.write_results

# Compatibility re-exports for code that imported stdlib modules through this runner.
hashlib = _provenance.hashlib
platform = _provenance.platform
random = _contracts.random
re = _contracts.re
shutil = _provenance.shutil
time = _contracts.time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "evals" / "results" / "latest.json"
MAX_ADAPTER_OUTPUT = 2_000_000
FIRST_PARTY_NON_TOOL_SKILLS = {"baglam-muhafizi"}


def _validate_provider_skill_scope(skills: set[str]) -> None:
    unsupported = sorted(skills - FIRST_PARTY_NON_TOOL_SKILLS)
    if unsupported:
        raise EvalError(
            "first-party preset only supports audited non-tool eval skills; rejected: "
            + ", ".join(unsupported)
        )


def _select_blind_seed(
    provider_preset: str | None, declared_seed: int | None
) -> int | bytes:
    if provider_preset == "claude-codex":
        if declared_seed is not None:
            raise EvalError("publishable provider runs generate blinding internally; omit --seed")
        return secrets.token_bytes(32)
    return 0 if declared_seed is None else declared_seed


def _bind_provenance(
    provenance: dict[str, str],
    *,
    provider_preset: str | None,
    seed: int | bytes = 0,
    selected_skills: list[str] | None = None,
    timeout: float = 120.0,
    min_skill_win_rate: float | None = None,
    root: pathlib.Path = ROOT,
) -> dict[str, str]:
    return _bind_provenance_core(
        provenance,
        provider_preset=provider_preset,
        seed=seed,
        selected_skills=selected_skills,
        timeout=timeout,
        min_skill_win_rate=min_skill_win_rate,
        root=root,
        repository_identity=_repository_identity,
        version_for_command=_version_for_command,
    )


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


def run_evaluations(
    cases: list[dict[str, Any]],
    adapter: str,
    judge: str | None = None,
    *,
    timeout: float = 120.0,
    seed: int | bytes = 0,
    min_skill_win_rate: float | None = None,
    provenance: dict[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Gerçek adaptör koşularını yap; kamu sonucu ve gizli A/B anahtarını döndür."""
    return _run_evaluations_core(
        cases,
        adapter,
        judge,
        timeout=timeout,
        seed=seed,
        min_skill_win_rate=min_skill_win_rate,
        provenance=provenance,
        run_adapter=_run_adapter,
    )


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
    parser.add_argument("--seed", type=int, help="Özel adaptör koşuları için A/B tohumu")
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
        run_seed = _select_blind_seed(args.provider_preset, args.seed)
        provenance = _read_provenance(args.provenance) if args.provenance else None
        if args.provider_preset and provenance is None:
            raise EvalError("--provider-preset requires --provenance")
        if provenance is not None:
            provenance = _bind_provenance(
                provenance,
                provider_preset=args.provider_preset,
                seed=run_seed,
                selected_skills=skills,
                timeout=args.timeout,
                min_skill_win_rate=args.min_skill_win_rate,
            )
        result, key = run_evaluations(
            cases,
            args.adapter,
            args.judge,
            timeout=args.timeout,
            seed=run_seed,
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
