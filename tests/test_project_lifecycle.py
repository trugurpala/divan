from __future__ import annotations

import importlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY = ROOT / "plugins" / "sadrazam" / "company"
if str(COMPANY) not in sys.path:
    sys.path.insert(0, str(COMPANY))

try:
    project_state = importlib.import_module("project_state")
except ModuleNotFoundError:
    project_state = None
try:
    project_lifecycle = importlib.import_module("project_lifecycle")
except ModuleNotFoundError:
    project_lifecycle = None

import project_os  # noqa: E402


def valid_state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "product": "divan-project-os",
        "contract_schema": 2,
        "installed": {
            "version": "0.16.0",
            "source_repository": "https://github.com/trugurpala/divan",
            "source_ref": "v0.16.0",
            "source_commit": "a" * 40,
        },
        "project_identity": "sha256:" + "b" * 64,
        "managed_files": [
            {
                "path": ".divan/PROJECT_RULES.md",
                "mode": "whole-file",
                "payload_sha256": "sha256:" + "c" * 64,
            },
            {
                "path": "AGENTS.md",
                "mode": "marked-block",
                "payload_sha256": "sha256:" + "d" * 64,
            },
        ],
    }


class ProjectStateSchemaTests(unittest.TestCase):
    def require_module(self):
        if project_state is None:
            self.fail("project_state module is not implemented")
        return project_state

    def test_valid_state_has_stable_utf8_serialization(self) -> None:
        module = self.require_module()

        self.assertEqual(module.validate_install_state(valid_state()), [])
        encoded = module.serialize_install_state(valid_state())

        self.assertTrue(encoded.endswith(b"\n"))
        self.assertEqual(json.loads(encoded), valid_state())
        self.assertEqual(encoded, module.serialize_install_state(valid_state()))

    def test_schema_rejects_unknown_keys_future_schema_and_noncanonical_source(self) -> None:
        module = self.require_module()
        cases = []
        extra = valid_state()
        extra["extra"] = True
        cases.append(extra)
        future = valid_state()
        future["schema_version"] = 2
        cases.append(future)
        mutable_ref = valid_state()
        mutable_ref["installed"]["source_ref"] = "main"  # type: ignore[index]
        cases.append(mutable_ref)
        uppercase_commit = valid_state()
        uppercase_commit["installed"]["source_commit"] = "A" * 40  # type: ignore[index]
        cases.append(uppercase_commit)

        for value in cases:
            with self.subTest(value=value):
                self.assertTrue(module.validate_install_state(value))

    def test_managed_paths_are_unique_sorted_relative_and_mode_locked(self) -> None:
        module = self.require_module()
        cases = []
        duplicate = valid_state()
        duplicate["managed_files"] = [
            duplicate["managed_files"][0],  # type: ignore[index]
            duplicate["managed_files"][0],  # type: ignore[index]
        ]
        cases.append(duplicate)
        traversal = valid_state()
        traversal["managed_files"][0]["path"] = "../AGENTS.md"  # type: ignore[index]
        cases.append(traversal)
        absolute = valid_state()
        absolute["managed_files"][0]["path"] = "C:/Users/Pala/AGENTS.md"  # type: ignore[index]
        cases.append(absolute)
        unknown_mode = valid_state()
        unknown_mode["managed_files"][0]["mode"] = "directory"  # type: ignore[index]
        cases.append(unknown_mode)
        unsorted = valid_state()
        unsorted["managed_files"] = list(  # type: ignore[arg-type]
            reversed(unsorted["managed_files"])  # type: ignore[arg-type]
        )
        cases.append(unsorted)

        for value in cases:
            with self.subTest(value=value):
                self.assertTrue(module.validate_install_state(value))


class ProjectStateInitializationTests(unittest.TestCase):
    SOURCE = {
        "version": "0.16.0",
        "source_repository": "https://github.com/trugurpala/divan",
        "source_ref": "v0.16.0",
        "source_commit": "a" * 40,
    }

    def test_init_plan_writes_schema_2_config_and_ownership_state_last(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-state-init-") as temporary:
            project = pathlib.Path(temporary)
            with mock.patch.object(
                project_os,
                "_runtime_source_identity",
                return_value=self.SOURCE,
                create=True,
            ):
                plan = project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )

        paths = [row["path"] for row in plan["writes"]]
        self.assertIn(".divan/install-state.json", paths)
        config = json.loads(
            next(row["content"] for row in plan["writes"] if row["path"] == ".divan/config.json")
        )
        state = json.loads(
            next(
                row["content"]
                for row in plan["writes"]
                if row["path"] == ".divan/install-state.json"
            )
        )
        self.assertEqual(config["schema_version"], 2)
        self.assertEqual(paths[-1], ".divan/install-state.json")
        self.assertEqual(state["installed"], self.SOURCE)
        self.assertEqual(
            [row["path"] for row in state["managed_files"]],
            [".divan/PROJECT_RULES.md", ".divan/config.json", "AGENTS.md"],
        )
        self.assertEqual(project_state.validate_install_state(state), [])

    def test_init_execution_is_idempotent_with_ownership_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-state-init-") as temporary:
            project = pathlib.Path(temporary)
            with mock.patch.object(
                project_os,
                "_runtime_source_identity",
                return_value=self.SOURCE,
                create=True,
            ):
                first = project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "tr", ("agents",), False
                    )
                )
                snapshot = {
                    path.relative_to(project).as_posix(): path.read_bytes()
                    for path in project.rglob("*")
                    if path.is_file()
                }
                second = project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "tr", ("agents",), False
                    )
                )
                after_snapshot = {
                    path.relative_to(project).as_posix(): path.read_bytes()
                    for path in project.rglob("*")
                    if path.is_file()
                }

        self.assertEqual(first["status"], "applied")
        self.assertEqual(second["changed"], [])
        self.assertEqual(snapshot, after_snapshot)


class ProjectLifecycleStatusTests(unittest.TestCase):
    SOURCE = ProjectStateInitializationTests.SOURCE

    def require_module(self):
        if project_lifecycle is None:
            self.fail("project_lifecycle module is not implemented")
        return project_lifecycle

    def initialize(self, project: pathlib.Path) -> None:
        with mock.patch.object(
            project_os, "_runtime_source_identity", return_value=self.SOURCE
        ):
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )

    @staticmethod
    def snapshot(project: pathlib.Path) -> dict[str, bytes]:
        return {
            path.relative_to(project).as_posix(): path.read_bytes()
            for path in project.rglob("*")
            if path.is_file()
        }

    def test_status_is_read_only_and_ignores_text_outside_managed_block(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-status-") as temporary:
            project = pathlib.Path(temporary)
            (project / "AGENTS.md").write_text(
                "# User rules\n\nKeep this text.\n", encoding="utf-8"
            )
            self.initialize(project)
            before = self.snapshot(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=self.SOURCE
            ):
                result = module.project_status(project)
            after = self.snapshot(project)

        self.assertEqual(result["status"], "CURRENT")
        self.assertEqual(
            {row["path"]: row["classification"] for row in result["surfaces"]},
            {
                ".divan/PROJECT_RULES.md": "current",
                ".divan/config.json": "current",
                "AGENTS.md": "current",
            },
        )
        self.assertEqual(before, after)

    def test_user_modified_whole_file_is_drifted_without_mutation(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-status-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            rules = project / ".divan" / "PROJECT_RULES.md"
            rules.write_text("# User replacement\n", encoding="utf-8")
            before = self.snapshot(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=self.SOURCE
            ):
                result = module.project_status(project)
            after = self.snapshot(project)

        self.assertEqual(result["status"], "DRIFTED")
        row = next(
            item
            for item in result["surfaces"]
            if item["path"] == ".divan/PROJECT_RULES.md"
        )
        self.assertEqual(row["classification"], "user-modified")
        self.assertEqual(before, after)

    def test_damaged_markers_are_blocked_with_safe_continuation(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-status-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            agents = project / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8").replace(
                    "<!-- divan:end v1 -->", "<!-- broken -->"
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=self.SOURCE
            ):
                result = module.project_status(project)

        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("continuation_command", result)
        self.assertTrue(result["errors"])

    def test_new_runtime_source_reports_update_available(self) -> None:
        module = self.require_module()
        newer = {**self.SOURCE, "version": "0.16.1", "source_ref": "v0.16.1"}
        with tempfile.TemporaryDirectory(prefix="divan-status-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=newer
            ):
                result = module.project_status(project)

        self.assertEqual(result["status"], "UPDATE_AVAILABLE")
        self.assertEqual(result["desired"]["version"], "0.16.1")
