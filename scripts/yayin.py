#!/usr/bin/env python3
"""Divan yayın kontrol düzlemi: hazırla, sapmayı denetle, release notu üret."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import stat
import sys
import tempfile
import zlib

KOK = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = pathlib.Path("release-manifest.json")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunks(payload: bytes) -> list[tuple[bytes, bytes]]:
    chunks: list[tuple[bytes, bytes]] = []
    offset = len(PNG_SIGNATURE)
    while offset < len(payload):
        if len(payload) - offset < 12:
            raise ValueError("PNG chunk is truncated")
        length = int.from_bytes(payload[offset : offset + 4], "big")
        chunk_end = offset + 12 + length
        if chunk_end > len(payload):
            raise ValueError("PNG chunk payload is truncated")
        kind = payload[offset + 4 : offset + 8]
        data = payload[offset + 8 : offset + 8 + length]
        expected_crc = int.from_bytes(payload[offset + 8 + length : chunk_end], "big")
        actual_crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"PNG {kind!r} CRC is invalid")
        chunks.append((kind, data))
        offset = chunk_end
        if kind == b"IEND":
            if offset != len(payload):
                raise ValueError("PNG has data after IEND")
            break
    return chunks


def _png_dimensions(payload: bytes) -> tuple[int, int]:
    if len(payload) < 8 or payload[:8] != PNG_SIGNATURE:
        raise ValueError("valid PNG signature is missing")
    chunks = _png_chunks(payload)
    if not chunks or chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13:
        raise ValueError("PNG must begin with one 13-byte IHDR chunk")
    kinds = [kind for kind, _data in chunks]
    if kinds.count(b"IHDR") != 1:
        raise ValueError("PNG must contain exactly one IHDR chunk")
    if b"IDAT" not in kinds:
        raise ValueError("PNG IDAT chunk is missing")
    if not kinds or kinds[-1] != b"IEND" or chunks[-1][1]:
        raise ValueError("PNG must end with an empty IEND chunk")
    ihdr = chunks[0][1]
    return int.from_bytes(ihdr[:4], "big"), int.from_bytes(ihdr[4:8], "big")


def _validate_binary_surface(path: pathlib.Path, contract: object) -> None:
    if not isinstance(contract, dict) or contract.get("format") != "png":
        raise ValueError(f"{path}: only a png binary contract is supported")
    width = contract.get("width")
    height = contract.get("height")
    max_bytes = contract.get("max_bytes")
    values = (width, height, max_bytes)
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and value > 0
        for value in values
    ):
        raise ValueError(f"{path}: width, height and max_bytes must be positive integers")
    assert isinstance(width, int) and isinstance(height, int) and isinstance(max_bytes, int)
    payload = path.read_bytes()
    if len(payload) > max_bytes:
        raise ValueError(f"{path}: dosya boyutu {len(payload)} bayt; limit {max_bytes}")
    actual = _png_dimensions(payload)
    if actual != (width, height):
        raise ValueError(f"{path}: png boyutlar {actual[0]}x{actual[1]}; expected {width}x{height}")


def manifesti_oku(kok: pathlib.Path = KOK) -> dict:
    veri = json.loads((kok / MANIFEST).read_text(encoding="utf-8"))
    if veri.get("schema_version") != 1 or veri.get("version_source") != "VERSION":
        raise ValueError("release-manifest.json şeması geçersiz")
    yuzeyler = veri.get("public_surfaces")
    if not isinstance(yuzeyler, list) or not yuzeyler:
        raise ValueError("release manifesti public_surfaces içermeli")
    return veri


def surum(kok: pathlib.Path = KOK) -> str:
    deger = (kok / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(deger):
        raise ValueError(f"VERSION SemVer değil: {deger!r}")
    return deger


def changelog_bolumu(kok: pathlib.Path = KOK, version: str | None = None) -> str:
    version = version or surum(kok)
    metin = (kok / "CHANGELOG.md").read_text(encoding="utf-8")
    eslesme = re.search(
        rf"^## \[{re.escape(version)}\](?:\s+-\s+[^\n]+)?\n(?P<body>.*?)(?=^## \[|\Z)",
        metin,
        re.MULTILINE | re.DOTALL,
    )
    if not eslesme:
        raise ValueError(f"CHANGELOG.md içinde [{version}] bölümü yok")
    govde = eslesme.group("body").strip()
    if not govde:
        raise ValueError(f"CHANGELOG [{version}] bölümü boş")
    return govde


def release_notu(kok: pathlib.Path = KOK) -> str:
    version = surum(kok)
    govde = changelog_bolumu(kok, version)
    return (
        f"# Divan v{version}\n\n{govde}\n\n"
        "## Sabitlenmiş kurulum\n\n"
        f"- Claude Code/Desktop Code + Codex: `python scripts/kur-hostlar.py --host both --ref v{version} --execute`.\n"
        f"- Önce dry-run için aynı komutu `--execute` olmadan çalıştırın.\n"
        f"- Eski-host fallback varlıkları: `divan-v{version}.zip` ve `divan-v{version}.sha256`.\n\n"
        "Yükseltmeden önce [kurulum](https://github.com/trugurpala/divan/wiki/Kurulum) ve "
        "[kaldırma/geri alma](https://github.com/trugurpala/divan/wiki/Kaldirma) rehberlerini okuyun.\n"
    )


def _surface_identity(surface: object, identities: set[str]) -> tuple[str, str]:
    if not isinstance(surface, dict):
        raise ValueError("public surface must be an object")
    identity = surface.get("id")
    relative = surface.get("path")
    if not all(isinstance(value, str) and value for value in (identity, relative)):
        raise ValueError(f"public surface is missing id/path: {surface}")
    assert isinstance(identity, str) and isinstance(relative, str)
    if identity in identities:
        raise ValueError(f"duplicate public surface id: {identity}")
    identities.add(identity)
    return identity, relative


def _validate_surface_content(
    root: pathlib.Path, surface: dict, identity: str, relative: str, version: str
) -> None:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"{identity}: file is missing: {relative}")
    marker = surface.get("marker")
    binary = surface.get("binary")
    if binary is not None:
        if marker is not None or surface.get("replace_version"):
            raise ValueError(f"{identity}: binary surface cannot use marker/replace_version")
        _validate_binary_surface(path, binary)
        return
    if not isinstance(marker, str) or not marker:
        raise ValueError(f"{identity}: marker is missing")
    expected = marker.format(version=version)
    if expected not in path.read_text(encoding="utf-8"):
        raise ValueError(f"{identity}: expected marker is missing: {expected}")


def denetle(kok: pathlib.Path = KOK) -> dict:
    veri = manifesti_oku(kok)
    version = surum(kok)
    hatalar: list[str] = []
    kimlikler: set[str] = set()
    for yuzey in veri["public_surfaces"]:
        try:
            kimlik, yol_metni = _surface_identity(yuzey, kimlikler)
            assert isinstance(yuzey, dict)
            _validate_surface_content(kok, yuzey, kimlik, yol_metni, version)
        except ValueError as hata:
            hatalar.append(str(hata))

    try:
        changelog_bolumu(kok, version)
    except ValueError as hata:
        hatalar.append(str(hata))

    pazar = json.loads((kok / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    if pazar.get("version") != version or (pazar.get("metadata") or {}).get("version") != version:
        hatalar.append("marketplace version/metadata VERSION ile eşleşmiyor")
    codex_pazar_yolu = kok / ".agents/plugins/marketplace.json"
    if codex_pazar_yolu.is_file():
        codex_pazar = json.loads(codex_pazar_yolu.read_text(encoding="utf-8"))
        if codex_pazar.get("version") != version:
            hatalar.append("Codex marketplace version VERSION ile eşleşmiyor")

    if hatalar:
        raise ValueError("Yayın yüzeyleri farklı:\n- " + "\n- ".join(hatalar))
    return {"status": "valid", "version": version, "surface_count": len(kimlikler)}


def _staged_file(path: pathlib.Path, payload: bytes) -> pathlib.Path:
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    staged = pathlib.Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(staged, stat.S_IMODE(path.stat().st_mode))
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
    return staged


def _write_transaction(updates: list[tuple[pathlib.Path, str]]) -> None:
    """Stage every release surface and restore replaced files on any failure."""
    if len({path for path, _content in updates}) != len(updates):
        raise ValueError("yayın işleminde yinelenen hedef yolu")
    staged: list[tuple[pathlib.Path, pathlib.Path, pathlib.Path]] = []
    replaced: list[tuple[pathlib.Path, pathlib.Path]] = []
    retained_backups: set[pathlib.Path] = set()
    try:
        for path, content in updates:
            staged.append(
                (
                    path,
                    _staged_file(path, content.encode("utf-8")),
                    _staged_file(path, path.read_bytes()),
                )
            )
        for path, new_file, backup_file in staged:
            os.replace(new_file, path)
            replaced.append((path, backup_file))
    except BaseException as error:
        rollback_errors: list[str] = []
        for path, backup_file in reversed(replaced):
            try:
                os.replace(backup_file, path)
            except OSError as rollback_error:
                retained_backups.add(backup_file)
                rollback_errors.append(
                    f"{path}: {rollback_error}; kurtarma yedeği: {backup_file}"
                )
        if rollback_errors:
            raise RuntimeError(
                "yayın hazırlığı ve geri alma tamamlanamadı: " + "; ".join(rollback_errors)
            ) from error
        raise
    finally:
        for _path, new_file, backup_file in staged:
            new_file.unlink(missing_ok=True)
            if backup_file not in retained_backups:
                backup_file.unlink(missing_ok=True)


def hazirla(yeni: str, kok: pathlib.Path = KOK) -> None:
    if not SEMVER.fullmatch(yeni):
        raise ValueError(f"Yeni sürüm SemVer değil: {yeni!r}")
    eski = surum(kok)
    if yeni == eski:
        raise ValueError(f"VERSION zaten {yeni}")
    veri = manifesti_oku(kok)
    pazar_yolu = kok / ".claude-plugin/marketplace.json"
    pazar = json.loads(pazar_yolu.read_text(encoding="utf-8"))
    pazar["version"] = yeni
    pazar.setdefault("metadata", {})["version"] = yeni
    codex_pazar_yolu = kok / ".agents/plugins/marketplace.json"
    codex_pazar = None
    if codex_pazar_yolu.is_file():
        codex_pazar = json.loads(codex_pazar_yolu.read_text(encoding="utf-8"))
        codex_pazar["version"] = yeni
    guncellemeler: list[tuple[pathlib.Path, str]] = []
    for yuzey in veri["public_surfaces"]:
        if not yuzey.get("replace_version"):
            continue
        yol = (kok / yuzey["path"]).resolve()
        if not yol.is_relative_to(kok.resolve()) or not yol.is_file():
            raise ValueError(f"Hazırlanacak yüzey bulunamadı: {yuzey['path']}")
        metin = yol.read_text(encoding="utf-8")
        desenler = yuzey.get("version_patterns")
        if not isinstance(desenler, list) or not desenler or not all(
            isinstance(desen, str) and "{version}" in desen for desen in desenler
        ):
            raise ValueError(
                f"{yuzey['path']}: replace_version yüzeyi version_patterns ister"
            )
        for desen in desenler:
            eski_metin = desen.format(version=eski)
            if eski_metin not in metin:
                raise ValueError(
                    f"{yuzey['path']}: {eski_metin} bulunamadı; sessiz geçilmedi"
                )
            metin = metin.replace(eski_metin, desen.format(version=yeni))
        guncellemeler.append((yol, metin))

    # Bütün yüzeyler önce okunup doğrulanır ve aynı işlem için temp dosyalara
    # yazılır. Bir replace hatası önceki dosyaları snapshot'lardan geri alır.
    updates = [
        (kok / "VERSION", yeni + "\n"),
        (pazar_yolu, json.dumps(pazar, ensure_ascii=False, indent=2) + "\n"),
    ]
    if codex_pazar is not None:
        updates.append(
            (
                codex_pazar_yolu,
                json.dumps(codex_pazar, ensure_ascii=False, indent=2) + "\n",
            )
        )
    updates.extend(guncellemeler)
    _write_transaction(updates)
    print(
        f"v{eski} -> v{yeni}: deterministik yüzeyler hazırlandı. "
        "Şimdi CHANGELOG ve BLUEPRINT anlatısını yaz; sonra --check çalıştır."
    )


def main() -> int:
    ayrac = argparse.ArgumentParser()
    kip = ayrac.add_mutually_exclusive_group(required=True)
    kip.add_argument("--check", action="store_true")
    kip.add_argument("--prepare", metavar="SEMVER")
    kip.add_argument("--notes", type=pathlib.Path, metavar="DOSYA")
    kip.add_argument("--status", action="store_true")
    secim = ayrac.parse_args()
    try:
        if secim.prepare:
            hazirla(secim.prepare)
        elif secim.notes:
            secim.notes.write_text(release_notu(), encoding="utf-8")
            print(secim.notes)
        else:
            print(json.dumps(denetle(), ensure_ascii=False))
    except (OSError, ValueError, json.JSONDecodeError) as hata:
        print(f"HATA: {hata}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
