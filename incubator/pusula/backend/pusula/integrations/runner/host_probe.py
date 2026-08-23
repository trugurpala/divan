from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class MicrovmHostFacts:
    kvm_available: bool
    firecracker_path: str | None
    firecracker_sha256: str | None
    jailer_path: str | None
    jailer_sha256: str | None
    cgroup_v2: bool
    network_namespace_tool: bool
    dedicated_worker: bool
    control_plane: bool

    @property
    def ready_for_untrusted(self) -> bool:
        return all(
            (
                self.kvm_available,
                self.firecracker_path,
                self.firecracker_sha256,
                self.jailer_path,
                self.jailer_sha256,
                self.cgroup_v2,
                self.network_namespace_tool,
                self.dedicated_worker,
                not self.control_plane,
            )
        )

    def blocking_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.kvm_available:
            reasons.append("kvm_unavailable")
        if not self.firecracker_path or not self.firecracker_sha256:
            reasons.append("firecracker_unverified")
        if not self.jailer_path or not self.jailer_sha256:
            reasons.append("jailer_unverified")
        if not self.cgroup_v2:
            reasons.append("cgroup_v2_unavailable")
        if not self.network_namespace_tool:
            reasons.append("network_namespace_unavailable")
        if not self.dedicated_worker:
            reasons.append("not_dedicated_worker")
        if self.control_plane:
            reasons.append("control_plane_host_forbidden")
        return tuple(reasons)


def _sha256_file(path: str | None) -> str | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.is_file():
        return None
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_microvm_host(
    *,
    environ: Mapping[str, str] | None = None,
    kvm_path: str = "/dev/kvm",
    cgroup_controllers_path: str = "/sys/fs/cgroup/cgroup.controllers",
) -> MicrovmHostFacts:
    env = dict(os.environ if environ is None else environ)
    firecracker = shutil.which("firecracker")
    jailer = shutil.which("jailer")
    dedicated_worker = env.get("PUSULA_RUNNER_ROLE", "").strip().lower() == "isolated-worker"
    control_plane = env.get("PUSULA_CONTROL_PLANE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    return MicrovmHostFacts(
        kvm_available=Path(kvm_path).exists() and os.access(kvm_path, os.R_OK | os.W_OK),
        firecracker_path=firecracker,
        firecracker_sha256=_sha256_file(firecracker),
        jailer_path=jailer,
        jailer_sha256=_sha256_file(jailer),
        cgroup_v2=Path(cgroup_controllers_path).is_file(),
        network_namespace_tool=shutil.which("ip") is not None,
        dedicated_worker=dedicated_worker,
        control_plane=control_plane,
    )
