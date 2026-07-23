from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY = ROOT / "plugins" / "sadrazam" / "company"
if str(COMPANY) not in sys.path:
    sys.path.insert(0, str(COMPANY))

import goals  # noqa: E402
import project_os  # noqa: E402
import receipts  # noqa: E402

_SUITE_STATE_DIRECTORY = tempfile.TemporaryDirectory(
    prefix="divan-suite-state-",
    dir=os.environ.get("LOCALAPPDATA") if os.name == "nt" else None,
)
_SUITE_STATE_PATH = pathlib.Path(_SUITE_STATE_DIRECTORY.name)
if os.name == "nt":
    _SUITE_STATE_PATH.rmdir()
os.environ["DIVAN_STATE_HOME"] = str(_SUITE_STATE_PATH)


def add_receipt_artifact(
    project: pathlib.Path,
    receipt_path: pathlib.Path,
    name: str,
    content: bytes = b"verified evidence\n",
) -> str:
    artifact = receipt_path.parent / name
    artifact.write_bytes(content)
    relative = artifact.relative_to(project).as_posix()
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["artifacts"][relative] = hashlib.sha256(content).hexdigest()
    receipt_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return relative


def advance_receipt(
    receipt_path: pathlib.Path,
    destination: str,
    *,
    evidence: list[str] | None = None,
    results: dict[str, dict[str, object]] | None = None,
) -> None:
    phases = [
        "DISCOVERED",
        "SPECIFIED",
        "PLANNED",
        "IMPLEMENTING",
        "VERIFIED",
        "PREVIEWED",
    ]
    current = receipts.verify_receipt(receipt_path)["state"]
    for phase in phases[phases.index(current) + 1 : phases.index(destination) + 1]:
        final = phase == destination
        receipts.append_transition(
            receipt_path,
            phase,
            evidence=evidence if final else None,
            results=results if final else None,
        )


def initialize_library_project(project: pathlib.Path) -> None:
    (project / "pyproject.toml").write_text(
        "[project]\nname='sample'\nversion='1.0.0'\n",
        encoding="utf-8",
    )
    (project / "sample").mkdir()
    (project / "sample" / "__init__.py").write_text("", encoding="utf-8")
    project_os.apply_init_plan(
        project_os.build_init_plan(
            project, "standard", "en", ("agents",), False
        )
    )


def two_goal_receipts(
    project: pathlib.Path, label: str
) -> list[pathlib.Path]:
    receipts_by_id = []
    for suffix in ("alpha", "omega"):
        goal = goals.start_goal(
            project, f"{label} {suffix}", "verified", execute=True
        )
        receipts_by_id.append((goal["goal_id"], project / goal["receipt"]))
    return [path for _, path in sorted(receipts_by_id)]


def append_dps_005_claim(
    receipt_path: pathlib.Path, status: str, phase: str
) -> None:
    artifacts = list(
        json.loads(receipt_path.read_text(encoding="utf-8"))["artifacts"]
    )
    advance_receipt(
        receipt_path,
        phase,
        evidence=artifacts,
        results={
            "DPS-005": {
                "status": status,
                "evidence": artifacts,
            }
        },
    )


class ProjectBootstrapTests(unittest.TestCase):
    def test_shallow_runtime_path_does_not_index_a_missing_parent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-shallow-runtime-") as temporary:
            project = pathlib.Path(temporary)
            (project / "index.html").write_text(
                "<!doctype html><html><head></head><body></body></html>",
                encoding="utf-8",
            )
            with mock.patch.object(project_os, "__file__", "/project_os.py"):
                with self.assertRaisesRegex(
                    ValueError, "bundled SEO policy is unavailable"
                ):
                    project_os._seo_contract(project, "standard")

    def setUp(self) -> None:
        self._state_directory = tempfile.TemporaryDirectory(
            prefix="divan-state-",
            dir=os.environ.get("LOCALAPPDATA") if os.name == "nt" else None,
        )
        self._previous_state_home = os.environ.get("DIVAN_STATE_HOME")
        os.environ["DIVAN_STATE_HOME"] = self._state_directory.name
        if os.name == "nt":
            pathlib.Path(self._state_directory.name).rmdir()

    def tearDown(self) -> None:
        if self._previous_state_home is None:
            os.environ.pop("DIVAN_STATE_HOME", None)
        else:
            os.environ["DIVAN_STATE_HOME"] = self._previous_state_home
        self._state_directory.cleanup()

    def _write_legacy_init_journal(
        self,
        project: pathlib.Path,
        *,
        existed: bool,
        backup: bytes | None,
    ) -> None:
        staging = project / project_os.INIT_STAGING
        staging.mkdir()
        backup_name = "0000.bin" if backup is not None else None
        if backup is not None:
            (staging / backup_name).write_bytes(backup)
        journal = {
            "schema_version": 1,
            "entries": [
                {
                    "path": "AGENTS.md",
                    "existed": existed,
                    "backup": backup_name,
                    "original_sha256": (
                        hashlib.sha256(backup).hexdigest()
                        if backup is not None
                        else None
                    ),
                }
            ],
            "created_dirs": [],
        }
        (project / project_os.INIT_JOURNAL).write_text(
            json.dumps(journal), encoding="utf-8"
        )

    def _prepare_valid_interrupted_init(
        self, project: pathlib.Path
    ) -> tuple[dict[str, object], pathlib.Path, pathlib.Path]:
        plan = project_os.build_init_plan(
            project, "standard", "en", ("agents",), False
        )
        prepared = project_os._prepare_init_plan(plan, project)
        changed = [
            item for item in prepared if item["desired"] != item["original"]
        ]
        journal_path, _journal, _authority, transaction, _marker = (
            project_os._start_init_transaction(
                project, changed, project_os._init_plan_digest(plan)
            )
        )
        return plan, journal_path, transaction

    def test_forged_init_journal_cannot_delete_user_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("owner content\n", encoding="utf-8")
            self._write_legacy_init_journal(
                project, existed=False, backup=None
            )
            with self.assertRaisesRegex(ValueError, "journal|transaction"):
                project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents",), False
                    )
                )
            self.assertEqual(agents.read_text(encoding="utf-8"), "owner content\n")

    def test_forged_init_journal_cannot_overwrite_user_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("owner content\n", encoding="utf-8")
            self._write_legacy_init_journal(
                project, existed=True, backup=b"attacker bytes\n"
            )
            with self.assertRaisesRegex(ValueError, "journal|transaction"):
                project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents",), False
                    )
                )
            self.assertEqual(agents.read_text(encoding="utf-8"), "owner content\n")

    def test_recomputed_repo_authority_cannot_forge_trusted_recovery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("owner content\n", encoding="utf-8")
            plan = project_os.build_init_plan(
                project, "standard", "en", ("agents",), False
            )
            prepared = project_os._prepare_init_plan(plan, project)
            changed = [
                item for item in prepared
                if item["desired"] != item["original"]
            ]
            (
                journal_path,
                journal,
                authority,
                transaction,
                _trusted_marker,
            ) = project_os._start_init_transaction(
                project, changed, project_os._init_plan_digest(plan)
            )
            attacker = b"attacker bytes\n"
            (transaction / "0000.bin").write_bytes(attacker)
            authority["entries"][0].update(
                {
                    "backup": "0000.bin",
                    "existed": True,
                    "preimage_sha256": (
                        f"sha256:{hashlib.sha256(attacker).hexdigest()}"
                    ),
                    "postimage_sha256": (
                        f"sha256:{hashlib.sha256(agents.read_bytes()).hexdigest()}"
                    ),
                    "backup_sha256": (
                        f"sha256:{hashlib.sha256(attacker).hexdigest()}"
                    ),
                }
            )
            authority_bytes = project_os._json_bytes(authority)
            (transaction / "authority.json").write_bytes(authority_bytes)
            journal["authority_sha256"] = (
                f"sha256:{hashlib.sha256(authority_bytes).hexdigest()}"
            )
            journal_path.write_bytes(project_os._json_bytes(journal))

            with self.assertRaisesRegex(ValueError, "trusted|binding"):
                project_os.apply_init_plan(plan)

            self.assertEqual(agents.read_text(encoding="utf-8"), "owner content\n")

    def test_stale_init_preimage_fails_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("stale owner edit\n", encoding="utf-8")
            self._write_legacy_init_journal(
                project, existed=True, backup=b"older owner content\n"
            )
            with self.assertRaisesRegex(ValueError, "journal|transaction|state"):
                project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents",), False
                    )
                )
            self.assertEqual(
                agents.read_text(encoding="utf-8"), "stale owner edit\n"
            )

    def test_valid_but_stale_init_transaction_preserves_new_owner_edit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("original owner content\n", encoding="utf-8")
            plan, _journal, _transaction = (
                self._prepare_valid_interrupted_init(project)
            )
            agents.write_text("new owner edit\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "stale|state"):
                project_os.apply_init_plan(plan)

            self.assertEqual(agents.read_text(encoding="utf-8"), "new owner edit\n")

    def test_ambiguous_staging_is_rejected_without_cleanup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            plan, _journal, transaction = self._prepare_valid_interrupted_init(
                project
            )
            evidence = transaction / "unowned.bin"
            evidence.write_bytes(b"do not delete")

            with self.assertRaisesRegex(ValueError, "ambiguous|staging"):
                project_os.apply_init_plan(plan)

            self.assertEqual(evidence.read_bytes(), b"do not delete")

    def test_second_process_cannot_enter_live_project_initialization(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary) / "project"
            project.mkdir()
            ready = pathlib.Path(temporary) / "ready"
            script = (
                "import pathlib,sys,time\n"
                f"sys.path.insert(0,{str(COMPANY)!r})\n"
                "import project_os\n"
                f"root=pathlib.Path({str(project)!r})\n"
                f"ready=pathlib.Path({str(ready)!r})\n"
                "plan=project_os.build_init_plan("
                "root,'standard','en',('agents',),False)\n"
                "original=project_os._atomic_replace\n"
                "def pause(path, content):\n"
                "    if path == root / 'AGENTS.md':\n"
                "        ready.write_text('locked',encoding='utf-8')\n"
                "        time.sleep(3)\n"
                "    original(path, content)\n"
                "project_os._atomic_replace=pause\n"
                "project_os.apply_init_plan(plan)\n"
            )
            first = subprocess.Popen(
                [sys.executable, "-c", script],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            deadline = time.monotonic() + 10
            while not ready.is_file() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(ready.is_file(), "first initializer did not acquire lock")
            started = time.monotonic()
            with self.assertRaisesRegex(ValueError, "live|lock|initialization"):
                project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents",), False
                    )
                )
            self.assertLess(time.monotonic() - started, 1.0)
            self.assertIsNone(first.poll())
            stdout, stderr = first.communicate(timeout=10)
            self.assertEqual(first.returncode, 0, stdout + stderr)
            repeated = project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            self.assertEqual(repeated["status"], "unchanged")

    def test_dead_process_lock_is_reclaimed_before_crash_recovery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary) / "project"
            project.mkdir()
            script = (
                "import os,pathlib,sys\n"
                f"sys.path.insert(0,{str(COMPANY)!r})\n"
                "import project_os\n"
                f"root=pathlib.Path({str(project)!r})\n"
                "project_os._acquire_init_lock(root)\n"
                "os._exit(71)\n"
            )
            crashed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(crashed.returncode, 71)
            with self.assertRaisesRegex(ValueError, "too new|retry|lock"):
                project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents",), False
                    )
                )
            with mock.patch.object(
                project_os, "INIT_LOCK_STALE_SECONDS", 0
            ):
                result = project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents",), False
                    )
                )
            self.assertEqual(result["status"], "applied")

    def test_lock_release_never_deletes_a_replacement_owner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            lock_path, owner = project_os._acquire_init_lock(project)
            replacement = json.loads(owner)
            replacement["nonce"] = "f" * 32
            replacement_bytes = project_os._json_bytes(replacement)
            lock_path.write_bytes(replacement_bytes)

            project_os._release_init_lock(lock_path, owner)

            self.assertEqual(lock_path.read_bytes(), replacement_bytes)

    @unittest.skipIf(os.name == "nt", "POSIX mode contract")
    def test_insecure_state_override_is_rejected_without_chmod(self) -> None:
        state = pathlib.Path(self._state_directory.name)
        state.chmod(0o777)
        project = state.parent / f"{state.name}-project"
        project.mkdir()
        try:
            with self.assertRaisesRegex(
                ValueError, "private|permission|state directory"
            ):
                project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents",), False
                    )
                )
            self.assertEqual(state.stat().st_mode & 0o777, 0o777)
            self.assertEqual(list(project.iterdir()), [])
        finally:
            shutil.rmtree(project)

    @unittest.skipIf(os.name == "nt", "POSIX mode contract")
    def test_private_posix_state_override_is_accepted(self) -> None:
        state = pathlib.Path(self._state_directory.name)
        state.chmod(0o700)
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            result = project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            self.assertEqual(result["status"], "applied")
            self.assertEqual(state.stat().st_mode & 0o777, 0o700)
            self.assertEqual(
                (state / "project-init").stat().st_mode & 0o777, 0o700
            )

    @unittest.skipUnless(os.name == "nt", "Windows DACL contract")
    def test_private_windows_state_override_is_accepted(self) -> None:
        state = pathlib.Path(self._state_directory.name)
        project_os._ensure_trusted_init_root()
        project_os._verify_private_state_directory(state)
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            result = project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            self.assertEqual(result["status"], "applied")
            project_os._verify_private_state_directory(state / "project-init")

    @unittest.skipUnless(os.name == "nt", "Windows DACL contract")
    def test_windows_foreign_read_is_safe_but_mutation_rights_are_not(self) -> None:
        self.assertFalse(
            project_os._windows_ace_grants_mutation(0x80000000 | 0x20000000, 0)
        )
        for mask in (
            0x00000002,
            0x00000004,
            0x00000010,
            0x00000040,
            0x00000100,
            0x00010000,
            0x00040000,
            0x00080000,
            0x10000000,
            0x40000000,
        ):
            self.assertTrue(project_os._windows_ace_grants_mutation(mask, 0))
        self.assertFalse(
            project_os._windows_ace_grants_mutation(0x10000000, 0x08)
        )

    @unittest.skipUnless(os.name == "nt", "Windows DACL contract")
    def test_actual_default_local_appdata_divan_acl_is_read_only_verified(self) -> None:
        default_state = (
            pathlib.Path(os.environ["LOCALAPPDATA"]) / "Divan"
        )
        if not default_state.is_dir():
            self.skipTest("default LocalAppData Divan state is absent")
        before = default_state.stat()
        project_os._verify_private_state_directory(default_state)
        after = default_state.stat()
        self.assertEqual(
            (before.st_dev, before.st_ino, before.st_mtime_ns),
            (after.st_dev, after.st_ino, after.st_mtime_ns),
        )

    @unittest.skipUnless(os.name == "nt", "Windows ancestor contract")
    def test_windows_mutable_temp_ancestor_is_rejected_before_creation(self) -> None:
        state = pathlib.Path(os.environ["TEMP"]) / (
            f"divan-unsafe-{os.getpid()}-{time.time_ns()}"
        )
        previous = os.environ["DIVAN_STATE_HOME"]
        os.environ["DIVAN_STATE_HOME"] = str(state)
        try:
            with self.assertRaisesRegex(
                ValueError, "ancestor|mutation|trusted"
            ):
                project_os._ensure_trusted_init_root()
        finally:
            os.environ["DIVAN_STATE_HOME"] = previous
        self.assertFalse(state.exists())

    @unittest.skipUnless(os.name == "nt", "Windows DACL contract")
    def test_inherited_shared_windows_override_is_rejected_untouched(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-shared-state-") as shared:
            state = pathlib.Path(shared)
            sentinel = state / "owner.txt"
            sentinel.write_text("keep\n", encoding="utf-8")
            previous = os.environ["DIVAN_STATE_HOME"]
            os.environ["DIVAN_STATE_HOME"] = str(state)
            try:
                with self.assertRaisesRegex(
                    ValueError, "DACL|private|principal|privacy"
                ):
                    project_os._ensure_trusted_init_root()
            finally:
                os.environ["DIVAN_STATE_HOME"] = previous
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse((state / "project-init").exists())

    def test_state_override_symlink_or_reparse_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-state-target-") as temporary:
            target = pathlib.Path(temporary)
            link = target.parent / f"{target.name}-link"
            try:
                os.symlink(target, link, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")
            previous = os.environ["DIVAN_STATE_HOME"]
            os.environ["DIVAN_STATE_HOME"] = str(link)
            try:
                with self.assertRaisesRegex(
                    ValueError, "symlink|reparse|state directory"
                ):
                    project_os._ensure_trusted_init_root()
            finally:
                os.environ["DIVAN_STATE_HOME"] = previous
                link.unlink()

    @unittest.skipIf(os.name == "nt", "POSIX ancestor contract")
    def test_nonsticky_shared_state_ancestor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-ancestor-") as temporary:
            shared = pathlib.Path(temporary) / "shared"
            shared.mkdir(mode=0o777)
            shared.chmod(0o777)
            state = shared / "private"
            previous = os.environ["DIVAN_STATE_HOME"]
            os.environ["DIVAN_STATE_HOME"] = str(state)
            try:
                with self.assertRaisesRegex(
                    ValueError, "ancestor|writable|private"
                ):
                    project_os._ensure_trusted_init_root()
            finally:
                os.environ["DIVAN_STATE_HOME"] = previous
            self.assertFalse(state.exists())

    @unittest.skipIf(os.name == "nt", "POSIX ancestor contract")
    def test_sticky_shared_ancestor_with_private_child_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-ancestor-") as temporary:
            shared = pathlib.Path(temporary) / "sticky"
            shared.mkdir()
            shared.chmod(0o1777)
            state = shared / "private"
            previous = os.environ["DIVAN_STATE_HOME"]
            os.environ["DIVAN_STATE_HOME"] = str(state)
            try:
                root = project_os._ensure_trusted_init_root()
            finally:
                os.environ["DIVAN_STATE_HOME"] = previous
            self.assertEqual(state.stat().st_mode & 0o777, 0o700)
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)

    def test_recovery_transaction_id_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("owner content\n", encoding="utf-8")
            plan, journal_path, _transaction = (
                self._prepare_valid_interrupted_init(project)
            )
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
            journal["transaction_id"] = "../outside"
            journal_path.write_bytes(project_os._json_bytes(journal))

            with self.assertRaisesRegex(ValueError, "transaction id|binding"):
                project_os.apply_init_plan(plan)

            self.assertEqual(agents.read_text(encoding="utf-8"), "owner content\n")

    def test_symlinked_recovery_authority_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary) / "project"
            project.mkdir()
            agents = project / "AGENTS.md"
            agents.write_text("owner content\n", encoding="utf-8")
            plan, _journal, transaction = self._prepare_valid_interrupted_init(
                project
            )
            authority = transaction / "authority.json"
            outside = pathlib.Path(temporary) / "outside.json"
            outside.write_bytes(authority.read_bytes())
            authority.unlink()
            try:
                os.symlink(outside, authority)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")

            with self.assertRaisesRegex(ValueError, "marker|authority|symlink"):
                project_os.apply_init_plan(plan)

            self.assertEqual(agents.read_text(encoding="utf-8"), "owner content\n")

    def test_orphan_init_staging_is_never_silently_deleted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            staging = project / project_os.INIT_STAGING
            staging.mkdir()
            evidence = staging / "owner.bin"
            evidence.write_bytes(b"owner")
            with self.assertRaisesRegex(ValueError, "orphan|staging|transaction"):
                project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents",), False
                    )
                )
            self.assertEqual(evidence.read_bytes(), b"owner")

    def test_runtime_public_web_requires_managed_expected_url(self) -> None:
        project = ROOT / "tests" / "fixtures" / "projects" / "nextjs"
        blocked = project_os.build_init_plan(
            project, "standard", "en", ("agents",), False
        )
        blocked_paths = {item["path"] for item in blocked["writes"]}
        self.assertNotIn(".github/workflows/divan-seo.yml", blocked_paths)
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("--expected-url", blocked["continuation_command"])
        ready = project_os.build_init_plan(
            project,
            "standard",
            "en",
            ("agents",),
            False,
            expected_url="https://app.example.test/",
        )
        ready_paths = {item["path"] for item in ready["writes"]}
        self.assertIn(".github/workflows/divan-seo.yml", ready_paths)
        tools = json.loads(
            next(
                item["content"]
                for item in ready["writes"]
                if item["path"] == ".divan/seo-tools.json"
            )
        )
        self.assertEqual(tools["expected_url"], "https://app.example.test/")

    def test_public_web_init_writes_bounded_seo_tool_contracts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            shutil.copytree(
                ROOT / "tests" / "fixtures" / "projects" / "static-site",
                project,
                dirs_exist_ok=True,
            )
            plan = project_os.build_init_plan(
                project, "standard", "en", ("agents",), False
            )
            writes = {item["path"]: item for item in plan["writes"]}
            self.assertIn(".divan/lighthouse.json", writes)
            self.assertIn(".divan/seo-tools.json", writes)
            self.assertIn(".github/workflows/divan-seo.yml", writes)
            tools = json.loads(writes[".divan/seo-tools.json"]["content"])
            self.assertEqual(tools["schema_version"], 1)
            self.assertEqual(tools["network_during_audit"], False)
            self.assertRegex(tools["command_plan_digest"], r"^sha256:[0-9a-f]{64}$")
            lighthouse = json.loads(writes[".divan/lighthouse.json"]["content"])
            self.assertEqual(lighthouse["ci"]["collect"]["numberOfRuns"], 1)
            self.assertEqual(lighthouse["ci"]["upload"]["target"], "filesystem")
            workflow = writes[".github/workflows/divan-seo.yml"]["content"]
            self.assertIn(
                "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
                workflow,
            )
            self.assertNotIn("actions/setup-node@", workflow)
            self.assertIn(
                "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
                workflow,
            )
            self.assertIn(
                "patrickhulce/lhci-client@sha256:"
                "558210c5e422a7babaaa09c285b7469da3f00fac1a9880c37883c65d666a7fc9",
                workflow,
            )
            self.assertNotIn("npm install", workflow)
            self.assertNotIn("npm ci", workflow)
            self.assertIn(
                "/tmp/divan-lychee/lychee-x86_64-unknown-linux-gnu/lychee",
                workflow,
            )
            self.assertNotIn("cargo install", workflow)
            self.assertIn("divan-seo-evidence", workflow)

    def test_init_is_dry_run_first_and_has_locked_schema(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            (project / "README.md").write_text("# Hello\n", encoding="utf-8")
            plan = project_os.build_init_plan(
                project, "standard", "auto", ("agents", "claude"), False
            )

            self.assertFalse((project / ".divan").exists())
            self.assertEqual(plan["schema_version"], 1)
            config = json.loads(
                next(
                    item["content"]
                    for item in plan["writes"]
                    if item["path"] == ".divan/config.json"
                )
            )
            self.assertEqual(
                list(config),
                [
                    "schema_version",
                    "profile",
                    "locale",
                    "autonomy",
                    "project_types",
                    "workspaces",
                    "providers",
                    "capabilities",
                    "commands",
                    "standards",
                    "managed_files",
                ],
            )
            self.assertEqual(config["autonomy"], "supervised")
            self.assertEqual(config["locale"], "en")
            self.assertEqual(config["managed_files"], ["AGENTS.md", "CLAUDE.md"])

    def test_apply_is_idempotent_and_preserves_external_host_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_text("# Owner rules\n\nKeep this.\n", encoding="utf-8")
            plan = project_os.build_init_plan(
                project, "standard", "en", ("agents",), False
            )
            first = project_os.apply_init_plan(plan)
            first_bytes = agents.read_bytes()
            second = project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )

            text = agents.read_text(encoding="utf-8")
            self.assertEqual(first["status"], "applied")
            self.assertEqual(second["status"], "unchanged")
            self.assertEqual(first_bytes, agents.read_bytes())
            self.assertTrue(text.startswith("# Owner rules\n\nKeep this.\n"))
            self.assertEqual(text.count(project_os.BEGIN_MARKER), 1)
            self.assertEqual(text.count(project_os.END_MARKER), 1)
            self.assertEqual(
                json.loads((project / ".divan" / "waivers.json").read_text()),
                {"schema_version": 1, "waivers": []},
            )

    def test_reinitializing_does_not_erase_existing_waivers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            waiver_path = project / ".divan" / "waivers.json"
            waiver = {
                "schema_version": 1,
                "waivers": [{"standard_id": "DPS-001", "reason": "owned"}],
            }
            waiver_path.write_text(json.dumps(waiver), encoding="utf-8")
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            self.assertEqual(json.loads(waiver_path.read_text()), waiver)

    def test_unmatched_or_duplicate_markers_fail_without_partial_writes(self) -> None:
        bad_values = (
            f"before\n{project_os.BEGIN_MARKER}\n",
            (
                f"{project_os.BEGIN_MARKER}\none\n{project_os.END_MARKER}\n"
                f"{project_os.BEGIN_MARKER}\ntwo\n{project_os.END_MARKER}\n"
            ),
        )
        for bad in bad_values:
            with self.subTest(bad=bad), tempfile.TemporaryDirectory(
                prefix="divan-project-"
            ) as temporary:
                project = pathlib.Path(temporary)
                (project / "AGENTS.md").write_text(bad, encoding="utf-8")
                plan = project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
                with self.assertRaisesRegex(ValueError, "managed markers"):
                    project_os.apply_init_plan(plan)
                self.assertFalse((project / ".divan").exists())
                self.assertEqual((project / "AGENTS.md").read_text(), bad)

    def test_plan_paths_cannot_escape_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            plan = project_os.build_init_plan(
                project, "standard", "en", ("agents",), False
            )
            plan["writes"][0]["path"] = "../escaped.json"
            with self.assertRaisesRegex(ValueError, "project"):
                project_os.apply_init_plan(plan)
            self.assertFalse(project.parent.joinpath("escaped.json").exists())

    def test_modified_plan_content_is_rejected_before_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            plan = project_os.build_init_plan(
                project, "standard", "en", ("agents",), False
            )
            plan["writes"][0]["content"] = '{"tampered":true}\n'
            with self.assertRaisesRegex(ValueError, "hash"):
                project_os.apply_init_plan(plan)
            self.assertFalse((project / ".divan").exists())

    def test_plan_path_and_kind_are_bound_and_destinations_are_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            readme = project / "README.md"
            readme.write_text("owner content\n", encoding="utf-8")
            plan = project_os.build_init_plan(
                project, "standard", "en", ("agents",), False
            )
            plan["writes"][0]["path"] = "README.md"
            with self.assertRaisesRegex(ValueError, "digest|destination|allow"):
                project_os.apply_init_plan(plan)
            self.assertEqual(readme.read_text(), "owner content\n")

            plan = project_os.build_init_plan(
                project, "standard", "en", ("agents",), False
            )
            waiver = next(
                item
                for item in plan["writes"]
                if item["path"] == ".divan/waivers.json"
            )
            waiver["kind"] = "replace"
            with self.assertRaisesRegex(ValueError, "digest|kind|policy"):
                project_os.apply_init_plan(plan)
            self.assertFalse((project / ".divan").exists())

    def test_ci_is_opt_in_and_uses_an_immutable_action_pin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            without_ci = project_os.build_init_plan(
                project, "standard", "en", ("agents",), False
            )
            with mock.patch.object(
                project_os,
                "_trusted_action_commit",
                return_value="b" * 40,
                create=True,
            ):
                with_ci = project_os.build_init_plan(
                    project, "standard", "en", ("agents",), True
                )
            self.assertNotIn(
                project_os.CI_PATH,
                [item["path"] for item in without_ci["writes"]],
            )
            workflow = next(
                item["content"]
                for item in with_ci["writes"]
                if item["path"] == project_os.CI_PATH
            )
            self.assertRegex(
                workflow,
                r"trugurpala/divan/\.github/actions/divan-project@b{40}",
            )
            self.assertIn("permissions:\n  contents: read", workflow)
            self.assertNotIn("secrets.", workflow)
            self.assertNotIn("deploy", workflow.casefold())

    def test_ci_init_fails_without_a_proven_immutable_action_commit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            with mock.patch.object(
                project_os,
                "_trusted_action_commit",
                side_effect=ValueError("immutable action commit unavailable"),
                create=True,
            ), self.assertRaisesRegex(ValueError, "immutable action commit"):
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), True
                )

    def test_crlf_host_file_stays_crlf_around_managed_block(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            agents = project / "AGENTS.md"
            agents.write_bytes(b"# Owner\r\n\r\nKeep this.\r\n")
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            content = agents.read_bytes()
            self.assertEqual(content.replace(b"\r\n", b"").count(b"\n"), 0)
            self.assertTrue(content.startswith(b"# Owner\r\n\r\nKeep this.\r\n"))

    def test_interruption_rolls_back_files_and_created_directories(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            with mock.patch.object(
                project_os, "_trusted_action_commit", return_value="b" * 40
            ):
                plan = project_os.build_init_plan(
                    project, "standard", "en", ("agents", "claude"), True
                )
            original = project_os._atomic_replace

            def interrupts(path: pathlib.Path, content: bytes) -> None:
                if path.name == "CLAUDE.md":
                    raise KeyboardInterrupt()
                original(path, content)

            with mock.patch.object(project_os, "_atomic_replace", interrupts):
                with self.assertRaises(KeyboardInterrupt):
                    project_os.apply_init_plan(plan)
            self.assertEqual(list(project.iterdir()), [])

    def test_next_apply_recovers_a_process_interrupted_transaction(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-project-") as temporary:
            project = pathlib.Path(temporary)
            script = (
                "import os,pathlib,sys\n"
                f"sys.path.insert(0,{str(COMPANY)!r})\n"
                "import project_os\n"
                f"root=pathlib.Path({str(project)!r})\n"
                "plan=project_os.build_init_plan(root,'standard','en',"
                "('agents','claude'),False)\n"
                "original=project_os._atomic_replace\n"
                "def crash(path, content):\n"
                "    if path.name == 'CLAUDE.md': os._exit(73)\n"
                "    original(path, content)\n"
                "project_os._atomic_replace=crash\n"
                "project_os.apply_init_plan(plan)\n"
            )
            crashed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(crashed.returncode, 73)
            journal_path = project / project_os.INIT_JOURNAL
            self.assertTrue(journal_path.is_file())
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
            self.assertEqual(journal["schema_version"], 2)
            self.assertRegex(journal["transaction_id"], r"^[0-9a-f]{32}$")
            self.assertRegex(journal["project_identity"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(journal["plan_digest"], r"^sha256:[0-9a-f]{64}$")
            transaction = (
                project
                / project_os.INIT_STAGING
                / journal["transaction_id"]
            )
            self.assertTrue((transaction / "authority.json").is_file())
            with mock.patch.object(
                project_os, "INIT_LOCK_STALE_SECONDS", 0
            ):
                result = project_os.apply_init_plan(
                    project_os.build_init_plan(
                        project, "standard", "en", ("agents", "claude"), False
                    )
                )
            self.assertEqual(result["status"], "applied")
            self.assertFalse((project / project_os.INIT_JOURNAL).exists())
            self.assertFalse((project / project_os.INIT_STAGING).exists())
            repeated = project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents", "claude"), False
                )
            )
            self.assertEqual(repeated["status"], "unchanged")


class GoalAndReceiptTests(unittest.TestCase):
    def test_goal_rejects_symlink_escape_before_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-goal-") as temporary:
            base = pathlib.Path(temporary)
            project = base / "project"
            outside = base / "outside"
            project.mkdir()
            outside.mkdir()
            try:
                os.symlink(outside, project / ".divan", target_is_directory=True)
            except OSError:
                original = pathlib.Path.is_symlink

                def reports_escape(path: pathlib.Path) -> bool:
                    return path == project / ".divan" or original(path)

                with mock.patch.object(
                    pathlib.Path, "is_symlink", reports_escape
                ), self.assertRaisesRegex(ValueError, "symlink"):
                    goals.start_goal(
                        project, "Ship the API", "verified", execute=True
                    )
            else:
                with self.assertRaisesRegex(ValueError, "symlink"):
                    goals.start_goal(
                        project, "Ship the API", "verified", execute=True
                    )
            self.assertEqual(list(outside.iterdir()), [])

    def test_goal_id_is_stable_and_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-goal-") as temporary:
            project = pathlib.Path(temporary)
            (project / "README.md").write_text("# Example\n", encoding="utf-8")
            first = goals.start_goal(
                project, "  Ship   the API  ", "verified", execute=False
            )
            second = goals.start_goal(
                project, "ship the api", "VERIFIED", execute=False
            )
            self.assertEqual(first["goal_id"], second["goal_id"])
            self.assertRegex(first["goal_id"], r"^goal-[0-9a-f]{12}$")
            self.assertFalse((project / ".divan").exists())

    def test_goal_status_and_resume_reject_external_identifiers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-goal-") as temporary:
            project = pathlib.Path(temporary)
            outside = pathlib.Path(temporary).parent / "outside-receipt.json"
            outside.write_text("{}\n", encoding="utf-8")
            for action in (
                lambda: goals.goal_status(project, "../../../outside"),
                lambda: goals.resume_goal(
                    project, "../../../outside", execute=True
                ),
                lambda: goals.goal_status(project, "goal-ABCDEF123456"),
            ):
                with self.assertRaisesRegex(ValueError, "goal"):
                    action()
            self.assertEqual(outside.read_text(), "{}\n")
            outside.unlink()

    def test_goal_execute_writes_exact_artifacts_and_valid_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-goal-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship the API", "verified", execute=True
            )
            goal_id = result["goal_id"]
            spec_dir = project / ".divan" / "specs" / goal_id
            receipt_path = (
                project / ".divan" / "evidence" / goal_id / "receipt.json"
            )
            self.assertEqual(
                sorted(item.name for item in spec_dir.iterdir()),
                ["plan.md", "spec.md", "tasks.md"],
            )
            self.assertTrue(receipt_path.is_file())
            verification = receipts.verify_receipt(receipt_path)
            self.assertEqual(verification["errors"], [])
            self.assertEqual(verification["state"], "DISCOVERED")
            self.assertEqual(
                result["receipt"],
                f".divan/evidence/{goal_id}/receipt.json",
            )

    def test_receipt_enforces_transitions_terminal_states_and_resume_from(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship the API", "observed", execute=True
            )
            receipt_path = project / result["receipt"]
            receipts.append_transition(receipt_path, "SPECIFIED")
            with self.assertRaisesRegex(ValueError, "transition"):
                receipts.append_transition(receipt_path, "RELEASED")
            receipts.append_transition(
                receipt_path,
                "BLOCKED",
                reason="github provider unavailable",
            )
            blocked = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(blocked["events"][-1]["resume_from"], "SPECIFIED")
            receipts.resume_receipt(receipt_path)
            receipts.append_transition(receipt_path, "FAILED", reason="build failed")
            with self.assertRaisesRegex(ValueError, "terminal"):
                receipts.append_transition(receipt_path, "BLOCKED")

    def test_receipt_rejects_secret_absolute_path_and_changed_hash(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship the API", "verified", execute=True
            )
            receipt_path = project / result["receipt"]
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            payload["events"][0]["reason"] = (
                f"token=secret-value at {pathlib.Path.home() / 'private'}"
            )
            receipt_path.write_text(json.dumps(payload), encoding="utf-8")
            errors = receipts.verify_receipt(receipt_path)["errors"]
            self.assertTrue(any("secret" in error for error in errors))
            self.assertTrue(any("absolute" in error or "home" in error for error in errors))

            payload["events"][0]["reason"] = ""
            artifact = next(iter(payload["artifacts"]))
            payload["artifacts"][artifact] = hashlib.sha256(b"wrong").hexdigest()
            receipt_path.write_text(json.dumps(payload), encoding="utf-8")
            errors = receipts.verify_receipt(receipt_path)["errors"]
            self.assertTrue(any("hash" in error for error in errors))

    def test_receipt_event_hash_chain_detects_nonsecret_tampering(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship the API", "verified", execute=True
            )
            receipt_path = project / result["receipt"]
            receipts.append_transition(receipt_path, "SPECIFIED", reason="approved")
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            payload["events"][0]["reason"] = "changed later"
            receipt_path.write_text(json.dumps(payload), encoding="utf-8")
            errors = receipts.verify_receipt(receipt_path)["errors"]
            self.assertTrue(any("event hash" in error for error in errors))

    def test_receipt_rejects_symlinked_artifact_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship the API", "verified", execute=True
            )
            receipt_path = project / result["receipt"]
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            relative = next(iter(payload["artifacts"]))
            artifact = project.joinpath(*pathlib.PurePosixPath(relative).parts)
            original = pathlib.Path.is_symlink

            def reports_escape(path: pathlib.Path) -> bool:
                return path == artifact or original(path)

            with mock.patch.object(pathlib.Path, "is_symlink", reports_escape):
                errors = receipts.verify_receipt(receipt_path)["errors"]
            self.assertTrue(any("symlink" in error for error in errors))

    def test_receipt_path_must_be_real_nonsymlink_and_canonical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship the API", "verified", execute=True
            )
            receipt_path = project / result["receipt"]
            copy = project / "copied-receipt.json"
            copy.write_bytes(receipt_path.read_bytes())
            self.assertFalse(receipts.verify_receipt(copy)["ok"])

            original = pathlib.Path.is_symlink

            def reports_receipt_link(path: pathlib.Path) -> bool:
                return path == receipt_path or original(path)

            with mock.patch.object(
                pathlib.Path, "is_symlink", reports_receipt_link
            ):
                verification = receipts.verify_receipt(receipt_path)
            self.assertFalse(verification["ok"])
            self.assertTrue(
                any("symlink" in error for error in verification["errors"])
            )

    def test_receipt_schema_target_artifacts_and_events_are_exact(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = "goal-0123456789ab"
            path = (
                project
                / ".divan"
                / "evidence"
                / goal_id
                / "receipt.json"
            )
            path.parent.mkdir(parents=True)
            payload = {
                "schema_version": 1,
                "goal_id": goal_id,
                "intent": 7,
                "target": "BANANA",
                "state": "DISCOVERED",
                "artifacts": {},
                "events": [
                    {
                        "sequence": 1,
                        "from_state": None,
                        "to_state": "DISCOVERED",
                        "reason": "",
                        "evidence": [],
                        "resume_from": "DISCOVERED",
                        "previous_hash": None,
                        "hash": "0" * 64,
                    }
                ],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            verification = receipts.verify_receipt(path)
            self.assertFalse(verification["ok"])
            joined = "\n".join(verification["errors"])
            self.assertIn("intent", joined)
            self.assertIn("target", joined)
            self.assertIn("artifacts", joined)
            self.assertIn("resume_from", joined)

    def test_transition_redacts_arbitrary_posix_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship API", "verified", execute=True
            )
            receipt_path = project / result["receipt"]
            receipts.append_transition(
                receipt_path,
                "SPECIFIED",
                reason="Inspect /etc/shadow and https://example.com/a/b",
            )
            persisted = receipt_path.read_text(encoding="utf-8")
            self.assertNotIn("/etc/shadow", persisted)
            self.assertIn("[REDACTED_PATH]", persisted)
            self.assertIn("https://example.com/a/b", persisted)

    def test_transition_redacts_tilde_home_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship API", "verified", execute=True
            )
            receipt_path = project / result["receipt"]
            receipts.append_transition(
                receipt_path, "SPECIFIED", reason="Read ~/private/key"
            )
            persisted = receipt_path.read_text(encoding="utf-8")
            self.assertNotIn("~/private/key", persisted)
            self.assertIn("[REDACTED_HOME]", persisted)

    def test_goal_redacts_secret_and_home_path_before_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            intent = f"Use token=private-value from {pathlib.Path.home() / 'keys'}"
            result = goals.start_goal(
                project, intent, "verified", execute=True
            )
            receipt_path = project / result["receipt"]
            persisted = receipt_path.read_text(encoding="utf-8")
            self.assertNotIn("private-value", persisted)
            self.assertNotIn(str(pathlib.Path.home()), persisted)
            self.assertIn("[REDACTED_SECRET]", persisted)
            self.assertEqual(receipts.verify_receipt(receipt_path)["errors"], [])

    def test_transition_redacts_secret_before_appending(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-receipt-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project, "Ship API", "verified", execute=True
            )
            receipt_path = project / result["receipt"]
            receipts.append_transition(
                receipt_path, "SPECIFIED", reason="token=private-value approved"
            )
            persisted = receipt_path.read_text(encoding="utf-8")
            self.assertNotIn("private-value", persisted)
            self.assertIn("[REDACTED_SECRET]", persisted)


class ProjectAuditTests(unittest.TestCase):
    def test_dps_fail_dominates_pass_in_both_goal_orders(self) -> None:
        for pass_index in (0, 1):
            with self.subTest(pass_index=pass_index):
                with tempfile.TemporaryDirectory(
                    prefix="divan-audit-"
                ) as temporary:
                    project = pathlib.Path(temporary)
                    initialize_library_project(project)
                    receipt_paths = two_goal_receipts(
                        project, f"pass-fail-{pass_index}"
                    )
                    append_dps_005_claim(
                        receipt_paths[pass_index], "PASS", "PLANNED"
                    )
                    append_dps_005_claim(
                        receipt_paths[1 - pass_index], "FAIL", "PLANNED"
                    )

                    result = project_os.verify_project(project)
                    dps_005 = next(
                        row for row in result["standards"] if row["id"] == "DPS-005"
                    )

                    self.assertEqual(dps_005["status"], "FAIL")

    def test_invalid_pass_dominates_valid_pass_in_both_goal_orders(self) -> None:
        for valid_index in (0, 1):
            with self.subTest(valid_index=valid_index):
                with tempfile.TemporaryDirectory(
                    prefix="divan-audit-"
                ) as temporary:
                    project = pathlib.Path(temporary)
                    initialize_library_project(project)
                    receipt_paths = two_goal_receipts(
                        project, f"valid-invalid-{valid_index}"
                    )
                    append_dps_005_claim(
                        receipt_paths[valid_index], "PASS", "PLANNED"
                    )
                    append_dps_005_claim(
                        receipt_paths[1 - valid_index], "PASS", "SPECIFIED"
                    )

                    result = project_os.verify_project(project)
                    dps_005 = next(
                        row for row in result["standards"] if row["id"] == "DPS-005"
                    )

                    self.assertEqual(dps_005["status"], "FAIL")

    def test_all_blocked_claims_remain_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            initialize_library_project(project)
            for receipt_path in two_goal_receipts(project, "blocked"):
                append_dps_005_claim(receipt_path, "BLOCKED", "PLANNED")

            result = project_os.verify_project(project)
            dps_005 = next(
                row for row in result["standards"] if row["id"] == "DPS-005"
            )

            self.assertEqual(dps_005["status"], "BLOCKED")

    def test_pass_only_claims_pass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            initialize_library_project(project)
            for receipt_path in two_goal_receipts(project, "pass"):
                append_dps_005_claim(receipt_path, "PASS", "PLANNED")

            result = project_os.verify_project(project)
            dps_005 = next(
                row for row in result["standards"] if row["id"] == "DPS-005"
            )

            self.assertEqual(dps_005["status"], "PASS")

    def test_config_classification_drift_is_a_fail_closed_error(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\nname='sample'\nversion='1.0.0'\n",
                encoding="utf-8",
            )
            (project / "sample").mkdir()
            (project / "sample" / "__init__.py").write_text("", encoding="utf-8")
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            config_path = project / ".divan" / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["project_types"] = []
            config["workspaces"] = []
            config["commands"] = []
            config["standards"] = []
            config_path.write_text(json.dumps(config), encoding="utf-8")

            result = project_os.verify_project(project)

            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("inspection drift" in error for error in result["errors"]))

    def test_initialized_contract_has_direct_evidence_without_receipt_claims(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\nname='sample'\nversion='1.0.0'\n",
                encoding="utf-8",
            )
            (project / "sample").mkdir()
            (project / "sample" / "__init__.py").write_text("", encoding="utf-8")
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )

            result = project_os.verify_project(project)
            by_id = {row["id"]: row["status"] for row in result["standards"]}

            self.assertEqual(result["status"], "BLOCKED")
            for standard_id in ("DPS-001", "DPS-002", "DPS-003", "DPS-004", "DPS-009"):
                self.assertEqual(by_id[standard_id], "PASS")
            for standard_id in ("DPS-005", "DPS-006", "DPS-007", "DPS-008"):
                self.assertEqual(by_id[standard_id], "BLOCKED")

    def test_event_evidence_must_be_an_existing_hashed_receipt_artifact(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            goal = goals.start_goal(
                project, "Ship API", "verified", execute=True
            )
            receipt_path = project / goal["receipt"]

            with self.assertRaisesRegex(ValueError, "evidence"):
                receipts.append_transition(
                    receipt_path,
                    "SPECIFIED",
                    evidence=[".divan/evidence/missing.txt"],
                )

    def test_receipt_results_must_stay_inside_their_registry_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            goal = goals.start_goal(
                project, "Ship API", "previewed", execute=True
            )
            receipt_path = project / goal["receipt"]
            spec = next(
                item
                for item in json.loads(
                    receipt_path.read_text(encoding="utf-8")
                )["artifacts"]
                if item.endswith("/spec.md")
            )

            with self.assertRaisesRegex(ValueError, "registry boundary"):
                receipts.append_transition(
                    receipt_path,
                    "SPECIFIED",
                    results={
                        "DPS-007": {
                            "status": "PASS",
                            "evidence": [spec],
                        }
                    },
                )

    def test_blocked_uses_resume_phase_and_failed_never_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\nname='sample'\nversion='1.0.0'\n",
                encoding="utf-8",
            )
            (project / "sample").mkdir()
            (project / "sample" / "__init__.py").write_text("", encoding="utf-8")
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            goal = goals.start_goal(
                project, "Ship API", "verified", execute=True
            )
            receipt_path = project / goal["receipt"]
            artifacts = list(
                json.loads(receipt_path.read_text(encoding="utf-8"))["artifacts"]
            )
            advance_receipt(
                receipt_path,
                "PLANNED",
                evidence=artifacts,
                results={
                    "DPS-005": {
                        "status": "PASS",
                        "evidence": artifacts,
                    }
                },
            )
            receipts.append_transition(receipt_path, "BLOCKED")

            blocked = project_os.verify_project(project)
            blocked_dps = {row["id"]: row["status"] for row in blocked["standards"]}
            self.assertEqual(blocked_dps["DPS-005"], "PASS")

            receipts.resume_receipt(receipt_path)
            receipts.append_transition(receipt_path, "IMPLEMENTING")
            receipts.append_transition(receipt_path, "FAILED")
            failed = project_os.verify_project(project)
            failed_dps = {row["id"]: row["status"] for row in failed["standards"]}
            self.assertNotEqual(failed_dps["DPS-005"], "PASS")

    def test_later_phase_cannot_launder_an_early_pass_claim(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\nname='sample'\nversion='1.0.0'\n",
                encoding="utf-8",
            )
            (project / "sample").mkdir()
            (project / "sample" / "__init__.py").write_text("", encoding="utf-8")
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            goal = goals.start_goal(
                project, "Ship API", "verified", execute=True
            )
            receipt_path = project / goal["receipt"]
            verification = add_receipt_artifact(
                project, receipt_path, "verification.txt"
            )
            receipts.append_transition(
                receipt_path,
                "SPECIFIED",
                evidence=[verification],
                results={
                    "DPS-006": {
                        "status": "PASS",
                        "evidence": [verification],
                    }
                },
            )
            advance_receipt(receipt_path, "VERIFIED")

            result = project_os.verify_project(project)
            by_id = {row["id"]: row["status"] for row in result["standards"]}

            self.assertNotEqual(by_id["DPS-006"], "PASS")

    def test_public_web_receipt_can_pass_only_with_phase_bound_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            (project / "README.md").write_text("# Sample\n", encoding="utf-8")
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {"build": "next build"},
                        "dependencies": {"next": "15.0.0", "react": "19.0.0"},
                    }
                ),
                encoding="utf-8",
            )
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            goal = goals.start_goal(
                project, "Preview public site", "previewed", execute=True
            )
            receipt_path = project / goal["receipt"]
            spec_artifacts = [
                item
                for item in json.loads(
                    receipt_path.read_text(encoding="utf-8")
                )["artifacts"]
                if "/specs/" in item
            ]
            verification = add_receipt_artifact(
                project, receipt_path, "verification.txt"
            )
            provider = add_receipt_artifact(
                project, receipt_path, "provider.json"
            )
            redaction = add_receipt_artifact(
                project, receipt_path, "redaction.txt"
            )
            seo = add_receipt_artifact(project, receipt_path, "seo.json")
            accessibility = add_receipt_artifact(
                project, receipt_path, "accessibility.json"
            )
            preview = add_receipt_artifact(
                project, receipt_path, "preview.png", b"\x89PNG evidence"
            )
            results = {
                "DPS-005": {"status": "PASS", "evidence": spec_artifacts},
                "DPS-006": {"status": "PASS", "evidence": [verification]},
                "DPS-007": {"status": "PASS", "evidence": [provider]},
                "DPS-008": {"status": "PASS", "evidence": [redaction]},
                "DPS-011": {
                    "status": "PASS",
                    "evidence": [seo, accessibility, preview],
                },
            }
            event_evidence = [
                *spec_artifacts,
                verification,
                provider,
                redaction,
                seo,
                accessibility,
                preview,
            ]
            advance_receipt(
                receipt_path,
                "PREVIEWED",
                evidence=event_evidence,
                results=results,
            )

            result = project_os.verify_project(project)
            by_id = {row["id"]: row["status"] for row in result["standards"]}

            self.assertEqual(result["status"], "PASS")
            for standard_id in ("DPS-005", "DPS-006", "DPS-007", "DPS-008", "DPS-011"):
                self.assertEqual(by_id[standard_id], "PASS")

    def test_inapplicable_claim_cannot_make_unclassified_project_pass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            goal = goals.start_goal(
                project, "Preview evidence", "previewed", execute=True
            )
            receipt_path = project / goal["receipt"]
            seo = add_receipt_artifact(project, receipt_path, "seo.json")
            accessibility = add_receipt_artifact(
                project, receipt_path, "accessibility.json"
            )
            preview = add_receipt_artifact(
                project, receipt_path, "preview.png", b"\x89PNG evidence"
            )
            advance_receipt(
                receipt_path,
                "PREVIEWED",
                evidence=[seo, accessibility, preview],
                results={
                    "DPS-011": {
                        "status": "PASS",
                        "evidence": [seo, accessibility, preview],
                    }
                },
            )

            result = project_os.verify_project(project)
            by_id = {row["id"]: row["status"] for row in result["standards"]}

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(by_id["DPS-011"], "NOT_APPLICABLE")

    def test_receipt_verification_rejects_secret_bearing_artifact_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            goal = goals.start_goal(
                project, "Ship API", "verified", execute=True
            )
            receipt_path = project / goal["receipt"]
            add_receipt_artifact(
                project,
                receipt_path,
                "verification.txt",
                b"sk-proj-abcdefghijklmnopqrstuvwxyz012345\n",
            )

            result = receipts.verify_receipt(receipt_path)

            self.assertFalse(result["ok"])
            self.assertTrue(any("standalone secret" in error for error in result["errors"]))

    def test_standalone_credentials_are_redacted_from_goal_and_receipt_text(self) -> None:
        tokens = (
            "sk-proj-abcdefghijklmnopqrstuvwxyz012345",
            "ghp_abcdefghijklmnopqrstuvwxyz0123456789",
            "github_pat_abcdefghijklmnopqrstuvwxyz012345",
            "xox" + "b-123456789012-123456789012-abcdefghijklmnopqrstuvwx",
            "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.signaturevalue",
        )
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            goal = goals.start_goal(
                project, "Use " + " ".join(tokens), "verified", execute=True
            )
            receipt_path = project / goal["receipt"]
            receipts.append_transition(
                receipt_path, "SPECIFIED", reason="Observed " + " ".join(tokens)
            )
            persisted = "\n".join(
                path.read_text(encoding="utf-8")
                for path in [
                    *(project / ".divan" / "specs" / goal["goal_id"]).glob("*.md"),
                    receipt_path,
                ]
            )
            for token in tokens:
                self.assertNotIn(token, persisted)
            self.assertIn("[REDACTED_SECRET]", persisted)

    def test_partial_target_waiver_never_waives_the_whole_standard(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\nname='sample'\nversion='1.0.0'\n",
                encoding="utf-8",
            )
            (project / "sample").mkdir()
            (project / "sample" / "__init__.py").write_text("", encoding="utf-8")
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            (project / ".divan" / "PROJECT_RULES.md").unlink()
            (project / "waiver-proof.md").write_text("approved\n", encoding="utf-8")
            (project / ".divan" / "waivers.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "waivers": [
                            {
                                "standard_id": "DPS-001",
                                "target": ".divan/config.json",
                                "reason": "temporary migration",
                                "owner": "maintainer",
                                "created_on": "2026-07-23",
                                "expires_on": "2026-08-23",
                                "evidence": "waiver-proof.md",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = project_os.verify_project(project)
            dps_001 = next(row for row in result["standards"] if row["id"] == "DPS-001")

            self.assertEqual(dps_001["status"], "FAIL")
            self.assertEqual(dps_001["waived_targets"], [".divan/config.json"])
            self.assertTrue(
                all(
                    row["status"] in {"PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE"}
                    for row in result["standards"]
                )
            )

    def test_verified_receipt_without_results_cannot_make_project_pass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            goals.start_goal(project, "Document intent", "verified", execute=True)

            result = project_os.verify_project(project)

            self.assertEqual(result["status"], "BLOCKED")

    def test_verify_requires_rules_and_canonical_receipt_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\nname='sample'\nversion='1.0.0'\n",
                encoding="utf-8",
            )
            (project / "sample").mkdir()
            (project / "sample" / "__init__.py").write_text("", encoding="utf-8")
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            without_goal = project_os.verify_project(project)
            applicable = {
                item["id"]: item["status"]
                for item in without_goal["standards"]
                if item["status"] != "NOT_APPLICABLE"
            }
            self.assertNotEqual(without_goal["status"], "PASS")
            for standard_id in ("DPS-001", "DPS-002", "DPS-003", "DPS-004", "DPS-009"):
                self.assertEqual(applicable[standard_id], "PASS")
            for standard_id in ("DPS-005", "DPS-006", "DPS-007", "DPS-008"):
                self.assertEqual(applicable[standard_id], "BLOCKED")

            goal = goals.start_goal(
                project, "Ship API", "verified", execute=True
            )
            receipt_path = project / goal["receipt"]
            artifacts = json.loads(
                receipt_path.read_text(encoding="utf-8")
            )["artifacts"]
            receipts.append_transition(
                receipt_path,
                "SPECIFIED",
                results={
                    "DPS-005": {
                        "status": "PASS",
                        "evidence": list(artifacts),
                    }
                },
            )
            with_goal = project_os.verify_project(project)
            by_id = {item["id"]: item["status"] for item in with_goal["standards"]}
            self.assertNotEqual(by_id["DPS-005"], "PASS")
            self.assertNotEqual(by_id["DPS-006"], "PASS")

            advance_receipt(
                receipt_path,
                "PLANNED",
                evidence=list(artifacts),
                results={
                    "DPS-005": {
                        "status": "PASS",
                        "evidence": list(artifacts),
                    }
                },
            )
            planned = project_os.verify_project(project)
            by_id = {item["id"]: item["status"] for item in planned["standards"]}
            self.assertEqual(by_id["DPS-005"], "PASS")

            (project / ".divan" / "PROJECT_RULES.md").unlink()
            missing_rules = project_os.verify_project(project)
            self.assertEqual(missing_rules["status"], "FAIL")
            self.assertTrue(
                any("PROJECT_RULES" in error for error in missing_rules["errors"])
            )

    def test_missing_provider_is_blocked_and_audit_verify_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            config_path = project / ".divan" / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["providers"] = ["github"]
            config_path.write_text(json.dumps(config), encoding="utf-8")
            before = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            audit = project_os.audit_project(project)
            verification = project_os.verify_project(project)
            after = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            self.assertEqual(audit["status"], "BLOCKED")
            self.assertEqual(verification["status"], "BLOCKED")
            self.assertIn("github", verification["missing_providers"])
            self.assertEqual(before, after)

    def test_malformed_provider_values_fail_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            config_path = project / ".divan" / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["providers"] = [1, "github", "github", "Türkçe"]
            config_path.write_text(json.dumps(config), encoding="utf-8")
            audit = project_os.audit_project(project)
            verify = project_os.verify_project(project)
            self.assertEqual(audit["status"], "FAIL")
            self.assertEqual(verify["status"], "FAIL")
            self.assertTrue(any("providers" in error for error in audit["errors"]))

    def test_invalid_waiver_fields_fail_verification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            waiver_path = project / ".divan" / "waivers.json"
            waiver_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "waivers": [
                            {
                                "standard_id": "DPS-001",
                                "target": "README.md",
                                "created_on": "2026-07-01",
                                "expires_on": "2026-08-01",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = project_os.verify_project(project)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("reason" in error for error in result["errors"]))

    def test_waiver_requires_real_project_relative_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-audit-") as temporary:
            project = pathlib.Path(temporary)
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    project, "standard", "en", ("agents",), False
                )
            )
            waiver_path = project / ".divan" / "waivers.json"
            waiver_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "waivers": [
                            {
                                "standard_id": "DPS-001",
                                "target": ".divan/config.json",
                                "reason": "migration",
                                "owner": "maintainer",
                                "created_on": "2026-07-01",
                                "expires_on": "2026-08-01",
                                "evidence": "missing-proof.md",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = project_os.verify_project(project)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("missing-proof" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
