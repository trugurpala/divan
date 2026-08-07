#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.parse import quote, urlsplit, urlunsplit

TARGET = "windows-x86_64"
_VERSION_RE = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
_GIT_ID_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class UpdateFeedError(ValueError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _version(value: str) -> str:
    clean = value.strip()
    if not _VERSION_RE.fullmatch(clean):
        raise UpdateFeedError("version must be a SemVer-compatible value")
    return clean


def _git_identity(value: str, name: str) -> str:
    clean = value.strip().lower()
    if not _GIT_ID_RE.fullmatch(clean):
        raise UpdateFeedError(f"{name} must be a 40-character lowercase Git object id")
    return clean


def _https_base_url(value: str) -> str:
    clean = value.strip()
    parsed = urlsplit(clean)
    if parsed.scheme != "https" or not parsed.netloc:
        raise UpdateFeedError("artifact base URL must be an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise UpdateFeedError("artifact base URL must not contain credentials")
    if parsed.query or parsed.fragment:
        raise UpdateFeedError("artifact base URL must not contain a query or fragment")
    return clean


def _artifact_url(base_url: str, installer_name: str) -> str:
    parsed = urlsplit(_https_base_url(base_url))
    base_path = parsed.path.rstrip("/")
    path = f"{base_path}/{quote(installer_name)}" if base_path else f"/{quote(installer_name)}"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _pub_date(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    clean = value.strip()
    if not clean:
        raise UpdateFeedError("pub_date must not be empty")
    try:
        parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError as error:
        raise UpdateFeedError("pub_date must be ISO-8601") from error
    if parsed.tzinfo is None:
        raise UpdateFeedError("pub_date must include a timezone")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _signature(path: pathlib.Path) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise UpdateFeedError(f"could not read updater signature: {error}") from error
    if not value:
        raise UpdateFeedError("updater signature file must not be empty")
    return value


def build_feed(
    *,
    version: str,
    installer_name: str,
    artifact_base_url: str,
    signature: str,
    pub_date: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    clean_signature = signature.strip()
    if not clean_signature:
        raise UpdateFeedError("updater signature must not be empty")
    return {
        "version": _version(version),
        "notes": notes.strip(),
        "pub_date": _pub_date(pub_date),
        "platforms": {
            TARGET: {
                "signature": clean_signature,
                "url": _artifact_url(artifact_base_url, installer_name),
            }
        },
    }


def validate_feed(
    payload: Mapping[str, Any],
    *,
    version: str,
    installer_name: str,
    artifact_base_url: str,
    signature: str,
) -> None:
    if payload.get("version") != _version(version):
        raise UpdateFeedError("feed version does not match the candidate version")
    platforms = payload.get("platforms")
    if not isinstance(platforms, Mapping) or set(platforms) != {TARGET}:
        raise UpdateFeedError("feed must contain exactly the windows-x86_64 platform")
    windows = platforms.get(TARGET)
    if not isinstance(windows, Mapping):
        raise UpdateFeedError("windows-x86_64 updater entry is invalid")
    expected_url = _artifact_url(artifact_base_url, installer_name)
    if windows.get("url") != expected_url:
        raise UpdateFeedError("feed URL does not match the signed installer artifact")
    if windows.get("signature") != signature.strip():
        raise UpdateFeedError("feed signature does not match the exact .sig contents")
    pub_date = payload.get("pub_date")
    if not isinstance(pub_date, str):
        raise UpdateFeedError("feed pub_date is required")
    _pub_date(pub_date)


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def generate(
    *,
    installer: pathlib.Path,
    signature_path: pathlib.Path,
    version: str,
    artifact_base_url: str,
    source_commit: str,
    source_tree: str,
    output: pathlib.Path,
    manifest: pathlib.Path,
    pub_date: str | None = None,
    notes: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        installer_bytes = installer.read_bytes()
        signature_bytes = signature_path.read_bytes()
    except OSError as error:
        raise UpdateFeedError(f"could not read signed updater artifact: {error}") from error
    if not installer_bytes:
        raise UpdateFeedError("installer must not be empty")
    signature = _signature(signature_path)
    clean_version = _version(version)
    clean_commit = _git_identity(source_commit, "source_commit")
    clean_tree = _git_identity(source_tree, "source_tree")
    feed = build_feed(
        version=clean_version,
        installer_name=installer.name,
        artifact_base_url=artifact_base_url,
        signature=signature,
        pub_date=pub_date,
        notes=notes,
    )
    validate_feed(
        feed,
        version=clean_version,
        installer_name=installer.name,
        artifact_base_url=artifact_base_url,
        signature=signature,
    )
    feed_bytes = _json_bytes(feed)
    artifact_url = feed["platforms"][TARGET]["url"]
    evidence = {
        "schema_version": 1,
        "product": "Divan",
        "version": clean_version,
        "target": TARGET,
        "source_commit": clean_commit,
        "source_tree": clean_tree,
        "installer": {
            "name": installer.name,
            "bytes": len(installer_bytes),
            "sha256": _sha256_bytes(installer_bytes),
            "url": artifact_url,
        },
        "updater_signature": {
            "name": signature_path.name,
            "bytes": len(signature_bytes),
            "sha256": _sha256_bytes(signature_bytes),
        },
        "feed": {
            "name": output.name,
            "sha256": _sha256_bytes(feed_bytes),
        },
        "pub_date": feed["pub_date"],
    }
    for digest in (
        evidence["installer"]["sha256"],
        evidence["updater_signature"]["sha256"],
        evidence["feed"]["sha256"],
    ):
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise UpdateFeedError("generated release digest is invalid")

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(feed_bytes)
    manifest.write_bytes(_json_bytes(evidence))
    return feed, evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate and validate Divan's source-bound Tauri Windows updater feed."
    )
    parser.add_argument("--installer", type=pathlib.Path, required=True)
    parser.add_argument("--signature", type=pathlib.Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--artifact-base-url", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    parser.add_argument("--pub-date")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    try:
        _, evidence = generate(
            installer=args.installer.resolve(),
            signature_path=args.signature.resolve(),
            version=args.version,
            artifact_base_url=args.artifact_base_url,
            source_commit=args.source_commit,
            source_tree=args.source_tree,
            output=args.output.resolve(),
            manifest=args.manifest.resolve(),
            pub_date=args.pub_date,
            notes=args.notes,
        )
    except UpdateFeedError as error:
        parser.error(str(error))
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
