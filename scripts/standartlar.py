"""Divan Community Standards registry controller."""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import sys
from datetime import date
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED_IDS = tuple(f"DCS-{number:03d}" for number in range(1, 11))
REQUIRED_STANDARD_FIELDS = (
    "id",
    "title_tr",
    "title_en",
    "level",
    "purpose",
    "checks",
    "evidence",
    "exception_policy",
)
REQUIRED_EXCEPTION_FIELDS = (
    "standard_id",
    "target",
    "reason",
    "owner",
    "created_on",
    "expires_on",
    "evidence",
)


def load_contract(root: pathlib.Path) -> dict[str, Any]:
    """Load the canonical community standards contract from *root*."""
    path = root / "registry" / "community-standards.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("community-standards.json root must be an object")
    return value


def _load_exceptions(root: pathlib.Path) -> Any:
    path = root / "registry" / "standard-exceptions.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _repository_path_exists(root: pathlib.Path, value: str) -> bool:
    return value.startswith(("https://", "http://")) or (root / value).exists()


def _check_script_path(root: pathlib.Path, command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return "komut alintisi gecersiz"
    if not parts:
        return "komut bos"
    for part in parts[1:]:
        if part.endswith(".py") and not (root / part).is_file():
            return f"bulunamadi: {part}"
    return None


def _validate_standards(root: pathlib.Path, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != 1:
        errors.append("community-standards.json.schema_version 1 olmali")
    standards = contract.get("standards")
    if not isinstance(standards, list):
        return [*errors, "community-standards.json.standards dizi olmali"]

    seen_ids: set[str] = set()
    for index, row in enumerate(standards, 1):
        label = f"standards[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} nesne olmali")
            continue
        standard_id = row.get("id")
        if not isinstance(standard_id, str) or not standard_id:
            errors.append(f"{label}.id dolu metin olmali")
            continue
        if standard_id in seen_ids:
            errors.append(f"{standard_id} tekrarli")
        seen_ids.add(standard_id)
        for field in REQUIRED_STANDARD_FIELDS:
            if field not in row:
                errors.append(f"{standard_id}.{field} zorunlu")
        for field in ("title_tr", "title_en", "purpose", "exception_policy"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{standard_id}.{field} dolu metin olmali")
        if row.get("level") != "required":
            errors.append(f"{standard_id}.level required olmali")
        for field in ("checks", "evidence"):
            if not _nonempty_strings(row.get(field)):
                errors.append(f"{standard_id}.{field} en az bir dolu metin icermeli")
                continue
            for value in row[field]:
                if field == "checks":
                    issue = _check_script_path(root, value)
                    if issue:
                        errors.append(f"{standard_id}.checks {issue}: {value}")
                elif not _repository_path_exists(root, value):
                    errors.append(f"{standard_id}.evidence bulunamadi: {value}")

    for standard_id in REQUIRED_IDS:
        if standard_id not in seen_ids:
            errors.append(f"{standard_id} eksik")
    for standard_id in sorted(seen_ids - set(REQUIRED_IDS)):
        errors.append(f"beklenmeyen standart kimligi: {standard_id}")
    if len(standards) != len(REQUIRED_IDS):
        errors.append(f"standards tam {len(REQUIRED_IDS)} kayit icermeli")
    return errors


def _parse_date(value: Any, label: str, errors: list[str]) -> date | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label} YYYY-AA-GG tarihi olmali")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} YYYY-AA-GG tarihi olmali")
        return None


def _validate_exceptions(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    try:
        exceptions = _load_exceptions(root)
    except (OSError, json.JSONDecodeError) as error:
        return [f"standard-exceptions.json okunamadi: {error}"]
    if not isinstance(exceptions, list):
        return ["standard-exceptions.json dizi olmali"]

    seen: set[tuple[str, str]] = set()
    for index, exception in enumerate(exceptions, 1):
        label = f"exceptions[{index}]"
        if not isinstance(exception, dict):
            errors.append(f"{label} nesne olmali")
            continue
        for field in REQUIRED_EXCEPTION_FIELDS:
            if not isinstance(exception.get(field), str) or not exception[field].strip():
                errors.append(f"{label}.{field} dolu metin olmali")
        standard_id = exception.get("standard_id")
        target = exception.get("target")
        if isinstance(standard_id, str) and standard_id not in REQUIRED_IDS:
            errors.append(f"{label}.standard_id bilinmiyor: {standard_id}")
        if isinstance(target, str):
            if any(marker in target for marker in "*?[]"):
                errors.append(f"{label}.target joker hedef olamaz: {target}")
            if isinstance(standard_id, str):
                key = (standard_id, target)
                if key in seen:
                    errors.append(f"{label}: tekrarli istisna: {standard_id} {target}")
                seen.add(key)
        created = _parse_date(exception.get("created_on"), f"{label}.created_on", errors)
        expires = _parse_date(exception.get("expires_on"), f"{label}.expires_on", errors)
        if created and expires:
            if expires < created:
                errors.append(f"{label}.expires_on created_on tarihinden once olamaz")
            if (expires - created).days > 180:
                errors.append(f"{label}.expires_on 180 gunden uzun olamaz")
            if expires < date.today():
                errors.append(f"{label}.expires_on suresi dolmus")
        evidence = exception.get("evidence")
        if isinstance(evidence, str) and evidence and not _repository_path_exists(root, evidence):
            errors.append(f"{label}.evidence bulunamadi: {evidence}")
    return errors


def render_markdown(contract: dict[str, Any]) -> str:
    """Render the canonical standards page in a stable order."""
    standards = contract.get("standards", [])
    rows = [row for row in standards if isinstance(row, dict)]
    by_id = {str(row.get("id", "")): row for row in rows}
    lines = [
        "# Divan Topluluk Standartlari",
        "",
        "> Bu dosya `registry/community-standards.json` kaynagindan uretilir. Elle degistirmeyin.",
        "",
        "Dogrulama: `python scripts/standartlar.py --check`",
        "",
    ]
    for standard_id in REQUIRED_IDS:
        row = by_id.get(standard_id)
        if not row:
            continue
        lines.extend(
            [
                f"## {standard_id} - {row.get('title_tr', '')}",
                "",
                f"**English:** {row.get('title_en', '')}",
                "",
                f"**Duzey:** {row.get('level', '')}",
                "",
                str(row.get("purpose", "")),
                "",
                "**Kontroller:**",
            ]
        )
        lines.extend(f"- `{check}`" for check in row.get("checks", []) if isinstance(check, str))
        lines.extend(["", "**Kanıt:**"])
        lines.extend(f"- `{evidence}`" for evidence in row.get("evidence", []) if isinstance(evidence, str))
        lines.extend(["", f"**Istisna politikasi:** {row.get('exception_policy', '')}", ""])
    return "\n".join(lines)


def validate_contract(root: pathlib.Path) -> list[str]:
    """Return all registry, exception, evidence, and generated-page errors."""
    try:
        contract = load_contract(root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"community-standards.json okunamadi: {error}"]
    errors = _validate_standards(root, contract)
    errors.extend(_validate_exceptions(root))
    document = root / "docs" / "Topluluk-Standartlari.md"
    expected = render_markdown(contract)
    if not document.is_file():
        errors.append("docs/Topluluk-Standartlari.md eksik")
    elif document.read_text(encoding="utf-8") != expected:
        errors.append("docs/Topluluk-Standartlari.md uretilmis belge eski")
    return errors


def _validate_for_render(root: pathlib.Path) -> list[str]:
    try:
        contract = load_contract(root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"community-standards.json okunamadi: {error}"]
    return [*_validate_standards(root, contract), *_validate_exceptions(root)]


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Divan topluluk standartlarini denetler.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Salt okunur denetim yapar.")
    modes.add_argument("--render", action="store_true", help="Uretilmis belgeyi yazar.")
    modes.add_argument("--json", action="store_true", help="Yalniz JSON durum nesnesi yazar.")
    options = parser.parse_args(arguments)

    if options.render:
        errors = _validate_for_render(ROOT)
        if not errors:
            destination = ROOT / "docs" / "Topluluk-Standartlari.md"
            destination.write_text(render_markdown(load_contract(ROOT)), encoding="utf-8", newline="\n")
    else:
        errors = validate_contract(ROOT)
    status = {"errors": errors, "ok": not errors}
    if options.json:
        print(json.dumps(status, ensure_ascii=False, sort_keys=True))
    elif errors:
        print("TOPLULUK STANDARTLARI BASARISIZ:")
        for error in errors:
            print(f"  X {error}")
    elif options.render:
        print("TOPLULUK STANDARTLARI URETILDI")
    else:
        print("TOPLULUK STANDARTLARI TEMIZ")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
