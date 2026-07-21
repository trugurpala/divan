"""Shared execution boundary for native host transactions."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

import host_journal

Operation = Callable[..., dict[str, Any]]


def serialized(
    normalize: Callable[[str], str], error_type: type[RuntimeError]
) -> Callable[[Operation], Operation]:
    def decorate(operation: Operation) -> Operation:
        @wraps(operation)
        def wrapped(options: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
            if not options.execute:
                return operation(options, *args, **kwargs)
            try:
                with host_journal.UpgradeLock(options.state_dir):
                    host_journal.assert_no_active(options.state_dir, normalize)
                    return operation(options, *args, **kwargs)
            except host_journal.JournalError as exc:
                raise error_type(str(exc)) from exc

        return wrapped

    return decorate
