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

    def test_development_source_identity_requires_a_clean_checkout(self) -> None:
        with mock.patch.object(
            project_os.subprocess,
            "check_output",
            side_effect=[" M plugins/sadrazam/company/project_os.py\n"],
        ), self.assertRaisesRegex(ValueError, "clean checkout"):
            project_os._runtime_source_identity()

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

    def test_existing_unowned_desired_target_blocks_before_mutation(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-status-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            state_path = project / ".divan" / "install-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["managed_files"] = [
                row
                for row in state["managed_files"]
                if row["path"] != ".divan/PROJECT_RULES.md"
            ]
            state_path.write_bytes(project_state.serialize_install_state(state))
            before = self.snapshot(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=self.SOURCE
            ):
                result = module.project_status(project)
                update = module.build_update_plan(project)
            after = self.snapshot(project)

        row = next(
            item
            for item in result["surfaces"]
            if item["path"] == ".divan/PROJECT_RULES.md"
        )
        self.assertEqual(row["classification"], "unmanaged")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(update["status"], "BLOCKED")
        self.assertEqual(before, after)


class ProjectLifecycleMutationTests(ProjectLifecycleStatusTests):
    def test_update_is_dry_run_then_applies_new_immutable_source(self) -> None:
        module = self.require_module()
        newer = {
            **self.SOURCE,
            "version": "0.16.1",
            "source_ref": "v0.16.1",
            "source_commit": "e" * 40,
        }
        with tempfile.TemporaryDirectory(prefix="divan-update-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            before = self.snapshot(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=newer
            ):
                plan = module.build_update_plan(project)
                after_plan = self.snapshot(project)
                result = module.apply_update_plan(plan)
            state = json.loads(
                (project / ".divan" / "install-state.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(plan["status"], "PLANNED")
        self.assertEqual(before, after_plan)
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(state["installed"], newer)

    def test_update_blocks_user_modified_file_without_writing(self) -> None:
        module = self.require_module()
        newer = {
            **self.SOURCE,
            "version": "0.16.1",
            "source_ref": "v0.16.1",
        }
        with tempfile.TemporaryDirectory(prefix="divan-update-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            rules = project / ".divan" / "PROJECT_RULES.md"
            rules.write_text("# Owner text\n", encoding="utf-8")
            before = self.snapshot(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=newer
            ):
                plan = module.build_update_plan(project)
            after = self.snapshot(project)

        self.assertEqual(plan["status"], "BLOCKED")
        self.assertEqual(before, after)
        self.assertIn(".divan/PROJECT_RULES.md", json.dumps(plan))

    def test_update_rejects_stale_preimage_before_mutation(self) -> None:
        module = self.require_module()
        newer = {
            **self.SOURCE,
            "version": "0.16.1",
            "source_ref": "v0.16.1",
        }
        with tempfile.TemporaryDirectory(prefix="divan-update-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=newer
            ):
                plan = module.build_update_plan(project)
                rules = project / ".divan" / "PROJECT_RULES.md"
                rules.write_text("# Changed after plan\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "changed"):
                    module.apply_update_plan(plan)
            self.assertEqual(
                rules.read_text(encoding="utf-8"), "# Changed after plan\n"
            )

    def test_schema_1_project_migrates_only_from_reproducible_state(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-migrate-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            (project / ".divan" / "install-state.json").unlink()
            config_path = project / ".divan" / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["schema_version"] = 1
            config_path.write_bytes(
                (
                    json.dumps(
                        config, ensure_ascii=False, indent=2, sort_keys=False
                    )
                    + "\n"
                ).encode("utf-8")
            )
            before = self.snapshot(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=self.SOURCE
            ):
                plan = module.build_update_plan(project)
                after_plan = self.snapshot(project)
                result = module.apply_update_plan(plan)
            migrated = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(plan["migration"], "config-schema-1-to-2")
        self.assertEqual(before, after_plan)
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(migrated["schema_version"], 2)

    def test_schema_1_migration_matrix_preserves_unicode_and_crlf_host_text(
        self,
    ) -> None:
        module = self.require_module()
        fixtures = {
            "library": {
                "pyproject.toml": (
                    "[project]\nname='kitaplik'\n"
                    "[build-system]\nrequires=['setuptools']\n"
                )
            },
            "public-web": {
                "index.html": "<!doctype html><title>Divan sample</title>\n"
            },
            "monorepo": {
                "package.json": '{"private":true,"workspaces":["apps/*"]}\n',
                "apps/web/package.json": '{"name":"web","version":"1.0.0"}\n',
            },
        }
        for name, files in fixtures.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix=f"divan-migrate-{name}-"
            ) as temporary:
                project = pathlib.Path(temporary)
                for relative, content in files.items():
                    path = project / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")
                (project / "AGENTS.md").write_text(
                    "# Kullanıcı kuralları\r\n\r\nİçeriği koru.\r\n",
                    encoding="utf-8",
                    newline="",
                )
                with mock.patch.object(
                    project_os,
                    "_runtime_source_identity",
                    return_value=self.SOURCE,
                ):
                    init = project_os.build_init_plan(
                        project,
                        "standard",
                        "tr",
                        ("agents",),
                        False,
                        expected_url=(
                            "https://example.com/"
                            if name == "public-web"
                            else None
                        ),
                    )
                    project_os.apply_init_plan(init)
                state_path = project / ".divan" / "install-state.json"
                state_path.unlink()
                config_path = project / ".divan" / "config.json"
                config = json.loads(config_path.read_text(encoding="utf-8"))
                config["schema_version"] = 1
                config_path.write_bytes(project_os._json_bytes(config))
                before_host = (project / "AGENTS.md").read_bytes()
                with mock.patch.object(
                    project_os,
                    "_runtime_source_identity",
                    return_value=self.SOURCE,
                ):
                    plan = module.build_update_plan(project)
                    result = module.apply_update_plan(plan)

                self.assertEqual(plan["migration"], "config-schema-1-to-2")
                self.assertEqual(result["status"], "APPLIED")
                self.assertEqual(
                    (project / "AGENTS.md").read_bytes(), before_host
                )
                self.assertEqual(
                    json.loads(config_path.read_text(encoding="utf-8"))[
                        "schema_version"
                    ],
                    2,
                )

    def test_repair_restores_only_missing_owned_whole_file(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(prefix="divan-repair-") as temporary:
            project = pathlib.Path(temporary)
            self.initialize(project)
            rules = project / ".divan" / "PROJECT_RULES.md"
            expected = rules.read_bytes()
            rules.unlink()
            before = self.snapshot(project)
            with mock.patch.object(
                project_os, "_runtime_source_identity", return_value=self.SOURCE
            ):
                plan = module.build_repair_plan(project)
                after_plan = self.snapshot(project)
                result = module.apply_repair_plan(plan)
                repaired = rules.read_bytes()

        self.assertEqual(plan["status"], "PLANNED")
        self.assertEqual(before, after_plan)
        self.assertEqual(result["status"], "REPAIRED")
        self.assertEqual(repaired, expected)
