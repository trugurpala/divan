#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

try:
    from divan_desktop_build_info import SOURCE_COMMIT, SOURCE_TREE
except ImportError:
    SOURCE_COMMIT = "development"
    SOURCE_TREE = "development"

from divan_runtime.desktop_protocol import handle_request
from divan_runtime.runtime_composition import build_execution_router


def _attach_build_provenance(payload: MappingLike, response: dict[str, Any]) -> None:
    if payload.get("command") != "capabilities" or response.get("ok") is not True:
        return
    result = response.get("result")
    if not isinstance(result, dict):
        return
    result["build_provenance"] = {
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
    }


MappingLike = dict[str, Any]


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
