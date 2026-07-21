"""Strict, reusable state evidence for transactional Divan host changes."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from collections.abc import Callable
from typing import Any

import host_adapters

PACKAGES = ("sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack")
HOSTS = {"claude", "codex"}
Run = Callable[[list[str]], str]
Normalize = Callable[[str], str]


class StateError(RuntimeError):
    """Raised when live host state cannot be proven exactly."""


def _catalog(root: pathlib.Path) -> tuple[dict[str, str], str]:
    path = root / ".agents" / "plugins" / "marketplace.json"
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise StateError(f"cannot prove marketplace version contract: {path}") from exc
    versions = {
        row["name"]: row["version"]
        for row in value.get("plugins", [])
        if isinstance(row, dict)
        and isinstance(row.get("name"), str)
        and isinstance(row.get("version"), str)
    }
    if set(versions) != set(PACKAGES):
        raise StateError("marketplace contract does not define the expected five packages")
    return versions, hashlib.sha256(raw).hexdigest()


def _git_evidence(root: pathlib.Path, ref: str, run: Run) -> tuple[str, str]:
    dirty = run(["git", "-C", str(root), "status", "--porcelain"]).strip()
    if dirty:
        raise StateError(f"dirty checkout cannot be used transactionally: {root}")
    commit = run(["git", "-C", str(root), "rev-parse", "HEAD"]).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise StateError(f"checkout commit cannot be proven: {root}")
    actual = commit
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        actual = run(["git", "-C", str(root), "describe", "--tags", "--exact-match"]).strip()
    if actual != ref:
        raise StateError(f"checkout ref cannot be proven: {root}")
    return commit, actual


def checkout_evidence(
    root: pathlib.Path, source: str, ref: str, run: Run, normalize: Normalize
) -> dict[str, Any]:
    resolved = root.expanduser().resolve()
    local = pathlib.Path(source).expanduser()
    commit, actual_ref = _git_evidence(resolved, ref, run)
    if local.exists():
        proven_source = str(local.resolve())
        if resolved != local.resolve():
            raise StateError("local marketplace root does not match the requested source")
    else:
        proven_source = run(
            ["git", "-C", str(resolved), "remote", "get-url", "origin"]
        ).strip()
        if normalize(proven_source) != normalize(source):
            raise StateError("marketplace source does not match requested repository")
    contract, digest = _catalog(resolved)
    return {
        "source": proven_source,
        "ref": actual_ref,
        "root": str(resolved),
        "commit": commit,
        "catalog_digest": digest,
        "contract": contract,
    }


def marketplace_evidence(
    host: str,
    row: dict[str, Any],
    source: str,
    ref: str,
    run: Run,
    normalize: Normalize,
) -> dict[str, Any]:
    root = host_adapters.marketplace_root(host, row)
    if root is None:
        raise StateError(f"{host}: divan marketplace root is missing")
    reported = host_adapters.marketplace_ref(row)
    if reported is not None and reported != ref:
        raise StateError(f"{host}: marketplace ref cannot be proven")
    return checkout_evidence(pathlib.Path(root), source, ref, run, normalize)


def plugin_fingerprint(
    host: str, selector: str, row: dict[str, Any], root: pathlib.Path
) -> dict[str, Any]:
    install_path = host_adapters.plugin_install_path(host, row)
    expected_path = (root / "plugins" / selector.removesuffix("@divan")).resolve()
    if install_path is None or pathlib.Path(install_path).resolve() != expected_path:
        raise StateError(f"{host}: {selector} install path is outside its marketplace root")
    if row.get("enabled") is not True or not host_adapters.plugin_provenance_valid(host, row):
        raise StateError(f"{host}: {selector} native provenance cannot be proven")
    version = row.get("version")
    if not isinstance(version, str) or not version:
        raise StateError(f"{host}: {selector} version cannot be proven")
    return {
        "host": host,
        "id": selector,
        "version": version,
        "marketplace_root": str(root.resolve()),
        "install_path": str(expected_path),
        "native_provenance": True,
    }


def validate_plugins(
    host: str,
    root: pathlib.Path,
    contract: dict[str, str],
    rows: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    expected = {f"{package}@divan" for package in PACKAGES}
    owned = {selector: row for selector, row in rows.items() if selector.endswith("@divan")}
    if set(owned) != expected:
        raise StateError(f"{host}: installed Divan package set does not match contract")
    for selector, row in owned.items():
        fingerprint = plugin_fingerprint(host, selector, row, root)
        package = selector.removesuffix("@divan")
        if fingerprint["version"] != contract[package]:
            raise StateError(f"{host}: {selector} version does not match contract")
    return owned


def capture_host(
    host: str,
    source: str,
    ref: str,
    marketplace_rows: dict[str, dict[str, Any]],
    plugin_rows: dict[str, dict[str, Any]],
    run: Run,
    normalize: Normalize,
) -> dict[str, Any]:
    marketplace = marketplace_rows.get("divan")
    if marketplace is None:
        raise StateError(f"{host}: divan marketplace is missing")
    evidence = marketplace_evidence(host, marketplace, source, ref, run, normalize)
    plugins = validate_plugins(
        host, pathlib.Path(evidence["root"]), evidence["contract"], plugin_rows
    )
    return {**evidence, "marketplace": marketplace, "plugins": plugins}


def marketplace_fingerprint(host: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "host": host,
        **{
            key: evidence[key]
            for key in ("source", "ref", "root", "commit", "catalog_digest")
        },
    }


def plugin_fingerprints(host: str, snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    root = pathlib.Path(snapshot["root"])
    return {
        selector: plugin_fingerprint(host, selector, row, root)
        for selector, row in snapshot["plugins"].items()
    }


def snapshot_key(host: str, snapshot: dict[str, Any], normalize: Normalize) -> dict[str, Any]:
    return {
        "source": normalize(snapshot["source"]),
        **{
            key: snapshot[key]
            for key in ("ref", "root", "commit", "catalog_digest", "contract")
        },
        "plugins": plugin_fingerprints(host, snapshot),
    }


def target_matches(snapshot: dict[str, Any], target: dict[str, Any], normalize: Normalize) -> bool:
    return bool(
        normalize(snapshot["source"]) == normalize(target["source"])
        and snapshot["ref"] == target["ref"]
        and snapshot["commit"] == target["commit"]
        and snapshot["catalog_digest"] == target["catalog_digest"]
        and snapshot["contract"] == target["versions"]
    )


def assert_same_ref_reproducible(
    snapshot: dict[str, Any], target: dict[str, Any], normalize: Normalize
) -> None:
    same_identity = normalize(snapshot["source"]) == normalize(target["source"]) and snapshot[
        "ref"
    ] == target["ref"]
    if same_identity and not target_matches(snapshot, target, normalize):
        raise StateError("same source/ref has a different contract, commit, or catalog digest; not reproducible")
