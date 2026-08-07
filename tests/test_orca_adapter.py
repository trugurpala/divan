from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.execution_contract import ExecutionAction, ExecutionRequest
from divan_runtime.orca_adapter import OrcaExecutionAdapter
from divan_runtime.orca_engine import OrcaResult


class FakeOrca:
    def __init__(self) -> None:
        self.calls = []

    def status(self):
        self.calls.append(("status",))
        return OrcaResult(
            action="status",
            argv=("orca", "status", "--json"),
            mutating=False,
            mandate_id=None,
            exit_code=0,
            payload={"ready": True},
            stdout="",
            stderr="",
        )

    def worktree_create(self, **kwargs):
        self.calls.append(("worktree_create", kwargs))
        return OrcaResult(
            action="worktree.create",
            argv=("orca", "worktree", "create"),
            mutating=True,
            mandate_id=kwargs["authority"].mandate_id,
            exit_code=0,
            payload={"created": True},
            stdout="",
            stderr="",
        )


class OrcaExecutionAdapterTests(unittest.TestCase):
    def test_status_maps_to_generic_receipt(self):
        fake = FakeOrca()
        adapter = OrcaExecutionAdapter(fake)
        receipt = adapter.execute(ExecutionRequest(ExecutionAction.STATUS, project_root="C:/repo"))
        self.assertEqual(receipt.engine, "orca")
        self.assertTrue(receipt.ok)
        self.assertEqual(fake.calls[0], ("status",))

    def test_worktree_create_forwards_mandate(self):
        fake = FakeOrca()
        adapter = OrcaExecutionAdapter(fake)
        receipt = adapter.execute(ExecutionRequest(
            ExecutionAction.WORKTREE_CREATE,
            project_root="C:/repo",
            mandate_id="m-1",
            args={"name": "fix-login", "agent": "codex"},
        ))
        self.assertEqual(receipt.mandate_id, "m-1")
        call = fake.calls[0][1]
        self.assertEqual(call["name"], "fix-login")
        self.assertTrue(call["authority"].execute)


if __name__ == "__main__":
    unittest.main()
