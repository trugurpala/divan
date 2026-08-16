from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class EvidenceRecord:
    task_id: str
    kind: str
    status: str
    summary: str
    at: str
    data: Mapping[str, Any]
    sha256: str


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def build_evidence(
    task_id: str,
    kind: str,
    status: str,
    summary: str,
    data: Mapping[str, Any],
) -> EvidenceRecord:
    at = datetime.now(timezone.utc).isoformat()
    evidence_data = dict(data)
    body: dict[str, Any] = {
        "task_id": task_id,
        "kind": kind,
        "status": status,
        "summary": summary,
        "at": at,
        "data": evidence_data,
    }
    digest = hashlib.sha256(_canonical(body)).hexdigest()
    return EvidenceRecord(
        task_id=task_id,
        kind=kind,
        status=status,
        summary=summary,
        at=at,
        data=evidence_data,
        sha256=digest,
    )


class EvidenceStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def append(self, record: EvidenceRecord) -> Path:
        folder = self.root / record.task_id
        stem = f"{record.at.replace(':', '-')}-{record.kind}"
        path = folder / f"{stem}.json"
        suffix = 1
        while path.exists():
            path = folder / f"{stem}-{suffix}.json"
            suffix += 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(record), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def list(self, task_id: str) -> Sequence[dict[str, Any]]:
        folder = self.root / task_id
        if not folder.exists():
            return ()
        result: list[dict[str, Any]] = []
        for path in sorted(folder.glob("*.json")):
            result.append(json.loads(path.read_text(encoding="utf-8")))
        return tuple(result)

    @staticmethod
    def verify(payload: Mapping[str, Any]) -> bool:
        expected = payload.get("sha256")
        if not isinstance(expected, str):
            return False
        body = {key: value for key, value in payload.items() if key != "sha256"}
        return hashlib.sha256(_canonical(body)).hexdigest() == expected
