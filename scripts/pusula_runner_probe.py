from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "incubator" / "pusula" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pusula.integrations.runner.host_probe import probe_microvm_host  # noqa: E402


def main() -> int:
    facts = probe_microvm_host()
    payload = {
        "schema": "pusula.runner-host-facts.v1",
        "eligible_for_untrusted": facts.ready_for_untrusted,
        "blocking_reasons": list(facts.blocking_reasons()),
        "facts": asdict(facts),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
