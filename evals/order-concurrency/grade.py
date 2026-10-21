"""Check same-process order submission behavior in an isolated temp directory.

Only run this against candidate code you trust: importing orders.py executes it.
"""

import builtins
import importlib.util
import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from os import PathLike
from pathlib import Path
from threading import Barrier, BrokenBarrierError
from unittest.mock import patch


def load_candidate(folder: Path):
    source = folder / "orders.py"
    if not source.is_file():
        raise FileNotFoundError(source)
    spec = importlib.util.spec_from_file_location("candidate_orders", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exercise(module, requests):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "orders.json"
        path.write_text("[]", encoding="utf-8")
        barrier = Barrier(2)
        original_path_open = Path.open
        original_builtin_open = builtins.open

        class SynchronizedReader:
            def __init__(self, handle):
                self.handle = handle
                self.waited = False

            def read(self, *args, **kwargs):
                content = self.handle.read(*args, **kwargs)
                if not self.waited:
                    self.waited = True
                    try:
                        barrier.wait(timeout=0.25)
                    except BrokenBarrierError:
                        # A correct lock prevents the second read until the
                        # first caller has written and released the lock.
                        pass
                return content

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.handle, name)

        def reader_for(file, handle, mode):
            if isinstance(file, (str, PathLike)) and Path(file) == path and "r" in mode:
                return SynchronizedReader(handle)
            return handle

        def path_open(file, *args, **kwargs):
            mode = kwargs.get("mode", args[0] if args else "r")
            return reader_for(file, original_path_open(file, *args, **kwargs), mode)

        def builtin_open(file, *args, **kwargs):
            mode = kwargs.get("mode", args[0] if args else "r")
            return reader_for(file, original_builtin_open(file, *args, **kwargs), mode)

        def submit(request):
            try:
                return ("ok", module.submit_order(path, *request))
            except Exception as error:
                return ("error", type(error).__name__)

        with patch.object(Path, "open", path_open), patch.object(builtins, "open", builtin_open):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(submit, request) for request in requests]
                outcomes = [future.result(timeout=5) for future in futures]
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            stored = None
        return outcomes, stored


def evaluate(folder: Path):
    module = load_candidate(folder)
    distinct, distinct_stored = exercise(
        module, [("a", "tea", 1), ("b", "coffee", 2)]
    )
    distinct_ok = (
        all(outcome[0] == "ok" for outcome in distinct)
        and isinstance(distinct_stored, list)
        and sorted(distinct_stored, key=lambda order: order["request_id"])
        == [
            {"request_id": "a", "product": "tea", "quantity": 1},
            {"request_id": "b", "product": "coffee", "quantity": 2},
        ]
        and sorted(
            (outcome[1] for outcome in distinct),
            key=lambda order: order["request_id"],
        ) == sorted(distinct_stored, key=lambda order: order["request_id"])
    )

    conflict, conflict_stored = exercise(
        module, [("same", "tea", 1), ("same", "coffee", 2)]
    )
    successes = [outcome[1] for outcome in conflict if outcome[0] == "ok"]
    conflict_ok = (
        len(successes) == 1
        and sorted(outcome[1] for outcome in conflict if outcome[0] == "error") == ["ValueError"]
        and isinstance(conflict_stored, list)
        and conflict_stored == successes
    )
    return {"distinct_requests": distinct_ok, "conflicting_request": conflict_ok}


def main(folder: Path):
    checks = evaluate(folder)
    print(json.dumps(checks, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
