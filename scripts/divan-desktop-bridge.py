#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_protocol import handle_request
from divan_runtime.runtime_composition import build_execution_router


def _build_provenance() -> dict[str, str]:
    try:
        module = importlib.import_module("divan_desktop_build_info")
    except ModuleNotFoundError:
        return {"source_commit": "development", "source_tree": "development"}
    return {
        "source_commit": str(getattr(module, "SOURCE_COMMIT", "development")),
        "source_tree": str(getattr(module, "SOURCE_TREE", "development")),
    }


def _attach_build_provenance(payload: dict[str, Any], response: dict[str, Any]) -> None:
    if payload.get("command") != "capabilities" or response.get("ok") is not True:
        return
    result = response.get("result")
    if isinstance(result, dict):
        result["build_provenance"] = _build_provenance()


def main() -> int:
    raw = sys.stdin.readline()
    if not raw:
        print(
            json.dumps(
                {
                    "api_version": 1,
                    "ok": False,
                    "error": {
                        "code": "DESKTOP_REQUEST_REQUIRED",
                        "message": "one JSON request line is required",
                    },
                },
                sort_keys=True,
            )
        )
        return 2
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError:
        print(
            json.dumps(
                {
                    "api_version": 1,
                    "ok": False,
                    "error": {
                        "code": "DESKTOP_REQUEST_INVALID_JSON",
                        "message": "request must be valid JSON",
                    },
                },
                sort_keys=True,
            )
        )
        return 2
    if not isinstance(payload, dict):
        print(
            json.dumps(
                {
                    "api_version": 1,
                    "ok": False,
                    "error": {
                        "code": "DESKTOP_REQUEST_INVALID",
                        "message": "request root must be an object",
                    },
                },
                sort_keys=True,
            )
        )
        return 2

    router = build_execution_router()
    response = handle_request(payload, router=router)
    _attach_build_provenance(payload, response)
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
