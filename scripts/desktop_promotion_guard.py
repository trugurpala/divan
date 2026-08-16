#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

from desktop_update_feed import TARGET, UpdateFeedError, validate_feed

_GIT_ID_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PromotionError(ValueError):
    pass


def _git_identity(value: str, name: str) -> str:
    clean = value.strip().lower()
    if not _GIT_ID_RE.fullmatch(clean):
        raise PromotionError(f"{name} must be a 40-character lowercase Git object id")
    return clean


def _https_url(value: str, name: str) -> str:
    clean = value.strip()
    parsed = urlsplit(clean)
    if parsed.scheme != "https" or not parsed.netloc:
        raise PromotionError(f"{name} must be an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise PromotionError(f"{name} must not contain credentials")
    if parsed.fragment:
        raise PromotionError(f"{name} must not contain a fragment")
    return clean


def _load_json(path: pathlib.Path, name: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PromotionError(f"could not read {name}: {error}") from error
    if not isinstance(payload, Mapping):
        raise PromotionError(f"{name} must contain a JSON object")
    return payload


def _sha256(path: pathlib.Path) -> str:
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise PromotionError(f"could not hash {path.name}: {error}") from error
    if not _SHA256_RE.fullmatch(digest):
        raise PromotionError(f"invalid SHA-256 for {path.name}")
    return digest


def _single(root: pathlib.Path, pattern: str, name: str) -> pathlib.Path:
    matches = sorted(path for path in root.rglob(pattern) if path.is_file())
    if len(matches) != 1:
        raise PromotionError(f"candidate must contain exactly one {name}; found {len(matches)}")
    return matches[0]


def _record(payload: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = payload.get(name)
    if not isinstance(value, Mapping):
        raise PromotionError(f"promotion manifest {name} record is missing or invalid")
    return value


def _expect_digest(record: Mapping[str, Any], path: pathlib.Path, label: str) -> None:
    if record.get("sha256") != _sha256(path):
        raise PromotionError(f"{label} SHA-256 does not match promotion manifest")
    try:
        size = path.stat().st_size
    except OSError as error:
        raise PromotionError(f"could not stat {label}: {error}") from error
    if record.get("bytes") != size:
        raise PromotionError(f"{label} byte length does not match promotion manifest")


def _candidate_files(
    root: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path, pathlib.Path]:
    installer = _single(root, "*-setup.exe", "NSIS installer")
    signature = pathlib.Path(f"{installer}.sig")
    if not signature.is_file():
        raise PromotionError("candidate updater signature paired with the NSIS installer is missing")
    feed = _single(root, "latest.json", "latest.json updater feed")
    manifest = _single(root, "ottoman-update-manifest.json", "promotion manifest")
    return installer, signature, feed, manifest


def _signature_text(path: pathlib.Path) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise PromotionError(f"could not read updater signature: {error}") from error
    if not value:
        raise PromotionError("updater signature must not be empty")
    return value


def _validate_feed_contract(
    feed: Mapping[str, Any],
    *,
    version: str,
    installer: pathlib.Path,
    artifact_base_url: str,
    signature: str,
) -> None:
    try:
        validate_feed(
            feed,
            version=version,
            installer_name=installer.name,
            artifact_base_url=artifact_base_url,
            signature=signature,
        )
    except UpdateFeedError as error:
        raise PromotionError(str(error)) from error


def _validate_manifest_identity(
    manifest: Mapping[str, Any],
    feed: Mapping[str, Any],
    *,
    version: str,
    source_commit: str,
    source_tree: str,
) -> None:
    if manifest.get("schema_version") != 1 or manifest.get("product") != "Ottoman":
        raise PromotionError("promotion manifest schema/product is invalid")
    if manifest.get("version") != version or manifest.get("target") != TARGET:
        raise PromotionError("promotion manifest version/target does not match the candidate")
    if manifest.get("source_commit") != source_commit or manifest.get("source_tree") != source_tree:
        raise PromotionError("promotion manifest is not bound to the exact release source")
    if manifest.get("pub_date") != feed.get("pub_date"):
        raise PromotionError("promotion manifest pub_date does not match updater feed")


def _validate_manifest_files(
    manifest: Mapping[str, Any],
    *,
    installer: pathlib.Path,
    signature: pathlib.Path,
    feed: pathlib.Path,
) -> Mapping[str, Any]:
    installer_record = _record(manifest, "installer")
    signature_record = _record(manifest, "updater_signature")
    feed_record = _record(manifest, "feed")
    expected_names = (
        (installer_record, installer.name, "installer"),
        (signature_record, signature.name, "signature"),
        (feed_record, feed.name, "feed"),
    )
    for record, expected, label in expected_names:
        if record.get("name") != expected:
            raise PromotionError(f"promotion manifest {label} name does not match the candidate")
    _expect_digest(installer_record, installer, "installer")
    _expect_digest(signature_record, signature, "updater signature")
    if feed_record.get("sha256") != _sha256(feed):
        raise PromotionError("updater feed SHA-256 does not match promotion manifest")
    return installer_record


def _validate_manifest_url(
    installer_record: Mapping[str, Any], feed: Mapping[str, Any]
) -> None:
    platforms = feed.get("platforms")
    windows = platforms.get(TARGET) if isinstance(platforms, Mapping) else None
    if not isinstance(windows, Mapping) or installer_record.get("url") != windows.get("url"):
        raise PromotionError("promotion manifest installer URL does not match updater feed")


def _report(
    *,
    version: str,
    source_commit: str,
    source_tree: str,
    updater_endpoint: str,
    installer: pathlib.Path,
    signature: pathlib.Path,
    feed: pathlib.Path,
    manifest: pathlib.Path,
) -> dict[str, Any]:
    return {
        "status": "pass",
        "product": "Ottoman",
        "version": version,
        "target": TARGET,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "updater_endpoint": updater_endpoint,
        "installer": {"name": installer.name, "sha256": _sha256(installer)},
        "updater_signature": {"name": signature.name, "sha256": _sha256(signature)},
        "feed": {"name": feed.name, "sha256": _sha256(feed)},
        "manifest": {"name": manifest.name, "sha256": _sha256(manifest)},
    }


def validate_candidate(
    *,
    candidate_dir: pathlib.Path,
    source_commit: str,
    source_tree: str,
    version: str,
    artifact_base_url: str,
    updater_endpoint: str,
) -> dict[str, Any]:
    root = candidate_dir.resolve()
    if not root.is_dir():
        raise PromotionError("candidate directory does not exist")
    commit = _git_identity(source_commit, "source_commit")
    tree = _git_identity(source_tree, "source_tree")
    artifact_base = _https_url(artifact_base_url, "artifact base URL")
    endpoint = _https_url(updater_endpoint, "updater endpoint")
    installer, signature, feed_path, manifest_path = _candidate_files(root)
    feed = _load_json(feed_path, "updater feed")
    manifest = _load_json(manifest_path, "promotion manifest")
    signature_text = _signature_text(signature)
    _validate_feed_contract(
        feed,
        version=version,
        installer=installer,
        artifact_base_url=artifact_base,
        signature=signature_text,
    )
    _validate_manifest_identity(
        manifest, feed, version=version, source_commit=commit, source_tree=tree
    )
    installer_record = _validate_manifest_files(
        manifest, installer=installer, signature=signature, feed=feed_path
    )
    _validate_manifest_url(installer_record, feed)
    return _report(
        version=version,
        source_commit=commit,
        source_tree=tree,
        updater_endpoint=endpoint,
        installer=installer,
        signature=signature,
        feed=feed_path,
        manifest=manifest_path,
    )


def write_checksums(report: Mapping[str, Any], output: pathlib.Path) -> None:
    lines: list[str] = []
    for key in ("installer", "updater_signature", "feed", "manifest"):
        record = report.get(key)
        if not isinstance(record, Mapping):
            raise PromotionError(f"promotion report {key} record is invalid")
        name = record.get("name")
        digest = record.get("sha256")
        valid_name = isinstance(name, str) and bool(name)
        valid_digest = isinstance(digest, str) and bool(_SHA256_RE.fullmatch(digest))
        if not valid_name or not valid_digest:
            raise PromotionError(f"promotion report {key} identity is invalid")
        lines.append(f"{digest}  {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail closed before promoting a signed Ottoman Desktop candidate."
    )
    parser.add_argument("--candidate-dir", type=pathlib.Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--artifact-base-url", required=True)
    parser.add_argument("--updater-endpoint", required=True)
    parser.add_argument("--checksums", type=pathlib.Path)
    args = parser.parse_args()
    try:
        report = validate_candidate(
            candidate_dir=args.candidate_dir,
            source_commit=args.source_commit,
            source_tree=args.source_tree,
            version=args.version,
            artifact_base_url=args.artifact_base_url,
            updater_endpoint=args.updater_endpoint,
        )
        if args.checksums is not None:
            write_checksums(report, args.checksums.resolve())
    except PromotionError as error:
        parser.error(str(error))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
