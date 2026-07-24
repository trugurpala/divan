from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY = ROOT / "plugins" / "sadrazam" / "company"
if str(COMPANY) not in sys.path:
    sys.path.insert(0, str(COMPANY))

import goals  # noqa: E402
import project_os  # noqa: E402
import providers  # noqa: E402
import receipts  # noqa: E402

SOURCE_COMMIT = "a" * 40
PROJECT_IDENTITY = "github.com/example/project"
VERCEL_PROJECT_ID = "prj_project_42"
VERCEL_ACCOUNT_ID = "team_example_42"


def runtime_proof(provider: str, operation: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "provider": provider,
        "operation": operation,
        "available": True,
        "evidence": f"trusted-adapter:{provider}:{operation}",
    }


def runtime_for(provider: str, operations: tuple[str, ...]) -> dict[str, object]:
    return {
        provider: {
            operation: runtime_proof(provider, operation)
            for operation in operations
        }
    }


class ProviderCapabilityTests(unittest.TestCase):
    def test_arbitrary_runtime_mapping_cannot_authorize_operations(self) -> None:
        with self.assertRaises(TypeError):
            providers.discover_capabilities(  # type: ignore[call-arg]
                runtime=runtime_for(
                    "github", providers.RELEASE_OPERATIONS["github"]
                )
            )

    def test_discovery_returns_exact_schema_for_every_builtin(self) -> None:
        discovered = providers.discover_capabilities(environ={}, which=lambda _: None)

        self.assertEqual(
            [item["id"] for item in discovered],
            ["local", "github", "context7", "vercel"],
        )
        self.assertEqual(
            set(providers.ProviderCapabilityV1.__annotations__),
            {"id", "available", "operations", "missing", "evidence"},
        )
        for item in discovered:
            self.assertIsInstance(item, providers.ProviderCapabilityV1)
            self.assertEqual(
                set(item),
                {"id", "available", "operations", "missing", "evidence"},
            )
        self.assertTrue(discovered[0]["available"])
        self.assertEqual(
            discovered[1]["missing"],
            [f"github.{item}" for item in providers.PROVIDER_OPERATIONS["github"]],
        )

    def test_ambient_signals_are_diagnostic_only(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"GITHUB_ACTIONS": "true", "DIVAN_VERCEL_AVAILABLE": "1"},
            clear=True,
        ):
            discovered = providers.discover_capabilities(
                which=lambda name: f"/bin/{name}"
            )

        for provider in ("github", "context7", "vercel"):
            item = next(row for row in discovered if row["id"] == provider)
            self.assertFalse(item["available"])
            self.assertEqual(item["operations"], [])
            self.assertEqual(
                item["missing"],
                [
                    f"{provider}.{operation}"
                    for operation in providers.PROVIDER_OPERATIONS[provider]
                ],
            )
        serialized = json.dumps(discovered)
        self.assertIn("environment:GITHUB_ACTIONS", serialized)
        self.assertIn("executable:gh", serialized)

    def test_discovery_never_exposes_secret_values(self) -> None:
        secret = "github_pat_this-value-must-never-appear"
        with mock.patch.dict(
            os.environ,
            {"GH_TOKEN": secret, "GITHUB_ACTIONS": "true", "PATH": ""},
            clear=True,
        ):
            result = providers.discover_capabilities()

        serialized = json.dumps(result)
        self.assertNotIn(secret, serialized)
        self.assertNotIn("GH_TOKEN", serialized)


class RecordingRunner:
    def __init__(self, responses: list[str], returncode: int = 0) -> None:
        self.responses = list(responses)
        self.returncode = returncode
        self.calls: list[list[str]] = []

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(command)
        stdout = self.responses.pop(0) if self.responses else ""
        return subprocess.CompletedProcess(command, self.returncode, stdout, "denied")


class RecordingHTTPSVerifier:
    def __init__(self, observation: object) -> None:
        self.observation = observation
        self.calls: list[str] = []

    def __call__(self, url: str) -> object:
        self.calls.append(url)
        return self.observation


class CommandRunner:
    def __init__(
        self,
        responses: dict[tuple[str, ...], list[tuple[int, str]]],
    ) -> None:
        self.responses = {
            command: list(values) for command, values in responses.items()
        }
        self.calls: list[list[str]] = []

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(command)
        values = self.responses.get(tuple(command), [])
        if not values:
            return subprocess.CompletedProcess(command, 1, "", "denied")
        returncode, stdout = values.pop(0)
        return subprocess.CompletedProcess(command, returncode, stdout, "")


class ProjectReleaseTests(unittest.TestCase):
    def test_repository_identity_is_canonical_across_git_remote_forms(self) -> None:
        expected = "github.com/example/project"
        for remote in (
            "https://GitHub.com/Example/Project.git",
            "git@github.com:Example/Project.git",
            "ssh://git@github.com/Example/Project.git",
        ):
            with self.subTest(remote=remote):
                self.assertEqual(
                    providers._canonical_remote(remote),
                    expected,
                )

    def test_default_https_verifier_records_transport_metadata_only(self) -> None:
        url = "https://preview-42.vercel.app"

        class Response:
            status = 204
            headers = {"x-vercel-id": "sfo1::native-check-42"}

            def __init__(self) -> None:
                self.reads: list[int] = []

            def __enter__(self) -> Response:
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def geturl(self) -> str:
                return url

            def read(self, amount: int) -> bytes:
                self.reads.append(amount)
                return b"{"

        class Opener:
            def __init__(self, response: Response) -> None:
                self.response = response
                self.calls: list[tuple[providers.Request, int]] = []

            def open(
                self, request: providers.Request, timeout: int
            ) -> Response:
                self.calls.append((request, timeout))
                return self.response

        response = Response()
        opener = Opener(response)
        with mock.patch.object(
            providers, "build_opener", return_value=opener
        ), mock.patch.object(
            providers.ssl,
            "create_default_context",
            return_value=mock.sentinel.tls_context,
        ):
            observed = providers._default_https_verifier(url)

        self.assertEqual(
            observed,
            providers.HTTPSObservation(
                status=204,
                final_url=url,
                request_id="sfo1::native-check-42",
                tls_verified=True,
            ),
        )
        self.assertEqual(response.reads, [1])
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(opener.calls[0][0].full_url, url)
        self.assertEqual(opener.calls[0][1], 15)

    def test_generic_internal_live_shape_cannot_establish_authority(self) -> None:
        live = {
            "source_commit": SOURCE_COMMIT,
            "resource_id": "42",
            "resource_url": "https://github.com/example/project/pull/42",
            "status": "MERGED",
            "readback": "MERGED",
        }
        raw = json.dumps(live, separators=(",", ":"), sort_keys=True)
        proof = {
            **live,
            "observed_status": live["status"],
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
        }
        runner = RecordingRunner([raw])

        self.assertFalse(
            providers._live_matches("github", "pr", proof, runner)
        )

    def test_native_github_ruleset_and_tag_responses_are_verified(self) -> None:
        fixtures = (
            (
                "ruleset",
                {
                    "id": 314,
                    "name": "main protection",
                    "target": "branch",
                    "enforcement": "active",
                    "_links": {
                        "html": {
                            "href": (
                                "https://github.com/example/project/rules/314"
                            )
                        }
                    },
                },
                {
                    "resource_id": "314",
                    "resource_url": (
                        "https://github.com/example/project/rules/314"
                    ),
                    "observed_status": "ACTIVE",
                    "readback": "branch:main protection",
                },
            ),
            (
                "tag",
                {
                    "ref": "refs/tags/v1.2.3",
                    "url": (
                        "https://api.github.com/repos/example/project/"
                        "git/refs/tags/v1.2.3"
                    ),
                    "object": {
                        "sha": SOURCE_COMMIT,
                        "type": "commit",
                    },
                },
                {
                    "resource_id": "refs/tags/v1.2.3",
                    "resource_url": (
                        "https://api.github.com/repos/example/project/"
                        "git/refs/tags/v1.2.3"
                    ),
                    "observed_status": "VERIFIED",
                    "readback": "commit",
                },
            ),
        )
        for operation, live, expected in fixtures:
            with self.subTest(operation=operation):
                raw = json.dumps(live, separators=(",", ":"), sort_keys=True)
                proof = {
                    "source_commit": SOURCE_COMMIT,
                    "sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    **expected,
                }
                self.assertTrue(
                    providers._live_matches(
                        "github", operation, proof, RecordingRunner([raw])
                    )
                )

    def test_vercel_operations_require_distinct_native_observations(self) -> None:
        fixtures = {
            "preview": (
                {
                    "uid": "dpl_preview_42",
                    "projectId": VERCEL_PROJECT_ID,
                    "ownerId": VERCEL_ACCOUNT_ID,
                    "gitSource": {
                        "type": "github",
                        "repoId": 991_337,
                        "sha": SOURCE_COMMIT,
                        "ref": "main",
                    },
                    "url": "preview-42.vercel.app",
                    "readyState": "READY",
                    "target": "preview",
                    "meta": {
                        "githubCommitOrg": "example",
                        "githubCommitRepo": "project",
                        "githubCommitSha": SOURCE_COMMIT,
                    },
                },
                {
                    "resource_id": "dpl_preview_42",
                    "resource_url": "https://preview-42.vercel.app",
                    "observed_status": "READY",
                    "readback": "target=preview",
                },
            ),
            "browser-verify": (
                providers.HTTPSObservation(
                    status=200,
                    final_url="https://preview-42.vercel.app",
                    request_id="sfo1::browser-check-42",
                    tls_verified=True,
                ),
                {
                    "resource_id": "sfo1::browser-check-42",
                    "resource_url": "https://preview-42.vercel.app",
                    "observed_status": "PASS",
                    "readback": (
                        "tls=verified;http=200;"
                        "final=https://preview-42.vercel.app"
                    ),
                },
            ),
            "staged-production": (
                {
                    "uid": "dpl_staged_42",
                    "projectId": VERCEL_PROJECT_ID,
                    "ownerId": VERCEL_ACCOUNT_ID,
                    "gitSource": {
                        "type": "github",
                        "repoId": 991_337,
                        "commitSha": SOURCE_COMMIT,
                        "ref": "main",
                    },
                    "url": "staged-42.vercel.app",
                    "readyState": "READY",
                    "target": "production",
                    "aliases": [],
                    "meta": {
                        "githubCommitOrg": "example",
                        "githubCommitRepo": "project",
                        "githubCommitSha": SOURCE_COMMIT,
                    },
                },
                {
                    "resource_id": "dpl_staged_42",
                    "resource_url": "https://staged-42.vercel.app",
                    "observed_status": "READY",
                    "readback": "target=production;aliases=0",
                },
            ),
            "promote": (
                {
                    "aliases": [
                        {
                            "alias": "project.vercel.app",
                        }
                    ]
                },
                {
                    "resource_id": "dpl_staged_42",
                    "resource_url": "https://project.vercel.app",
                    "observed_status": "VERIFIED",
                    "readback": "alias=project.vercel.app",
                },
            ),
            "live-readback": (
                {
                    "uid": "dpl_staged_42",
                    "projectId": VERCEL_PROJECT_ID,
                    "ownerId": VERCEL_ACCOUNT_ID,
                    "gitSource": {
                        "type": "github",
                        "repoId": 991_337,
                        "sha": SOURCE_COMMIT,
                        "commitSha": SOURCE_COMMIT,
                        "ref": "main",
                    },
                    "url": "staged-42.vercel.app",
                    "readyState": "READY",
                    "target": "production",
                    "aliases": ["project.vercel.app"],
                    "meta": {
                        "githubCommitOrg": "example",
                        "githubCommitRepo": "project",
                        "githubCommitSha": SOURCE_COMMIT,
                    },
                },
                {
                    "resource_id": "dpl_staged_42",
                    "resource_url": "https://project.vercel.app",
                    "observed_status": "READY",
                    "readback": "production-alias=project.vercel.app",
                },
            ),
        }
        for operation, (live, expected) in fixtures.items():
            with self.subTest(operation=operation):
                raw = (
                    providers._https_observation_json(live)
                    if isinstance(live, providers.HTTPSObservation)
                    else json.dumps(live, separators=(",", ":"), sort_keys=True)
                )
                proof = {
                    "project_identity": PROJECT_IDENTITY,
                    "source_commit": SOURCE_COMMIT,
                    "sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    **expected,
                }
                self.assertTrue(
                    providers._live_matches(
                        "vercel",
                        operation,
                        proof,
                        RecordingRunner([raw]),
                        RecordingHTTPSVerifier(live),
                    )
                )

        preview_live, preview_expected = fixtures["preview"]
        raw = json.dumps(preview_live, separators=(",", ":"), sort_keys=True)
        for operation in (
            "browser-verify",
            "staged-production",
            "promote",
            "live-readback",
        ):
            with self.subTest(replay_as=operation):
                proof = {
                    "project_identity": PROJECT_IDENTITY,
                    "source_commit": SOURCE_COMMIT,
                    "sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    **preview_expected,
                }
                self.assertFalse(
                    providers._live_matches(
                        "vercel", operation, proof, RecordingRunner([raw])
                    )
                )

    def test_vercel_operation_proofs_must_form_one_deployment_chain(self) -> None:
        scenarios = {
            "browser-verify": (
                None,
                "readback",
                (
                    "tls=verified;http=200;"
                    "final=https://other-preview.vercel.app"
                ),
                None,
                None,
            ),
            "promote": (3, "resource_id", "dpl_other", None, None),
            "live-readback": (
                4,
                "resource_id",
                "dpl_other",
                "uid",
                "dpl_other",
            ),
        }
        for operation, (
            response_index,
            proof_key,
            proof_value,
            live_key,
            live_value,
        ) in scenarios.items():
            with self.subTest(operation=operation):
                with tempfile.TemporaryDirectory(
                    prefix="divan-vercel-chain-"
                ) as temporary:
                    project = pathlib.Path(temporary)
                    goal_id, receipt_path = self._verified_goal(project)
                    responses = self._proofs(
                        project, goal_id, receipt_path, "vercel"
                    )
                    proof_path = (
                        project
                        / ".divan"
                        / "evidence"
                        / goal_id
                        / f"{operation}-vercel.json"
                    )
                    proof = json.loads(
                        proof_path.read_text(encoding="utf-8")
                    )
                    proof[proof_key] = proof_value
                    if response_index is not None and live_key is not None:
                        live = json.loads(responses[response_index])
                        live[live_key] = live_value
                        responses[response_index] = json.dumps(
                            live, separators=(",", ":"), sort_keys=True
                        )
                    if response_index is not None:
                        proof["sha256"] = hashlib.sha256(
                            responses[response_index].encode()
                        ).hexdigest()
                    proof_path.write_text(
                        json.dumps(proof, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    receipt = json.loads(
                        receipt_path.read_text(encoding="utf-8")
                    )
                    relative = proof_path.relative_to(project).as_posix()
                    receipt["artifacts"][relative] = hashlib.sha256(
                        proof_path.read_bytes()
                    ).hexdigest()
                    receipt_path.write_text(
                        json.dumps(receipt, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    runner = RecordingRunner(responses)

                    result = providers.release_project(
                        project,
                        goal_id,
                        "vercel",
                        execute=False,
                        runner=runner,
                    )

                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(
                        result["missing"], ["vercel.evidence.chain"]
                    )
                    self.assertEqual(runner.calls, [])

    def test_proof_context_rejects_cross_goal_project_and_commit_replay(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-proof-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = "goal-123456789abc"
            relative = f".divan/evidence/{goal_id}/pr-github.json"
            path = project.joinpath(*pathlib.PurePosixPath(relative).parts)
            path.parent.mkdir(parents=True)
            base = {
                "schema_version": 1,
                "goal_id": goal_id,
                "project_identity": PROJECT_IDENTITY,
                "provider": "github",
                "operation": "pr",
                "source_commit": SOURCE_COMMIT,
                "resource_id": "42",
                "resource_url": "https://github.com/example/project/pull/42",
                "sha256": "b" * 64,
                "observed_status": "MERGED",
                "readback": "MERGED",
            }
            for key, replay in (
                ("goal_id", "goal-fedcba987654"),
                ("project_identity", "github.com/attacker/replay"),
                ("source_commit", "c" * 40),
            ):
                with self.subTest(key=key):
                    proof = {**base, key: replay}
                    path.write_text(json.dumps(proof), encoding="utf-8")
                    loaded = providers._load_proof(
                        project,
                        goal_id,
                        PROJECT_IDENTITY,
                        SOURCE_COMMIT,
                        "github",
                        "pr",
                        {relative: hashlib.sha256(path.read_bytes()).hexdigest()},
                    )
                    self.assertIsNone(loaded)

    def test_github_proof_url_must_belong_to_canonical_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-proof-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = "goal-123456789abc"
            relative = f".divan/evidence/{goal_id}/pr-github.json"
            path = project.joinpath(*pathlib.PurePosixPath(relative).parts)
            path.parent.mkdir(parents=True)
            proof = {
                "schema_version": 1,
                "goal_id": goal_id,
                "project_identity": PROJECT_IDENTITY,
                "provider": "github",
                "operation": "pr",
                "source_commit": SOURCE_COMMIT,
                "resource_id": "42",
                "resource_url": "https://github.com/attacker/replay/pull/42",
                "sha256": "b" * 64,
                "observed_status": "MERGED",
                "readback": "MERGED",
            }
            path.write_text(json.dumps(proof), encoding="utf-8")

            loaded = providers._load_proof(
                project,
                goal_id,
                PROJECT_IDENTITY,
                SOURCE_COMMIT,
                "github",
                "pr",
                {relative: hashlib.sha256(path.read_bytes()).hexdigest()},
            )

            self.assertIsNone(loaded)

    def test_tag_proof_rejects_mutable_branch_reference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-proof-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = "goal-123456789abc"
            relative = f".divan/evidence/{goal_id}/tag-github.json"
            path = project.joinpath(*pathlib.PurePosixPath(relative).parts)
            path.parent.mkdir(parents=True)
            proof = {
                "schema_version": 1,
                "goal_id": goal_id,
                "project_identity": PROJECT_IDENTITY,
                "provider": "github",
                "operation": "tag",
                "source_commit": SOURCE_COMMIT,
                "resource_id": "refs/heads/main",
                "resource_url": (
                    "https://api.github.com/repos/example/project/"
                    "git/refs/heads/main"
                ),
                "sha256": "b" * 64,
                "observed_status": "VERIFIED",
                "readback": "commit",
            }
            path.write_text(json.dumps(proof), encoding="utf-8")

            loaded = providers._load_proof(
                project,
                goal_id,
                PROJECT_IDENTITY,
                SOURCE_COMMIT,
                "github",
                "tag",
                {relative: hashlib.sha256(path.read_bytes()).hexdigest()},
            )

            self.assertIsNone(loaded)

    def test_ruleset_command_derives_fixed_api_route_from_native_url(self) -> None:
        proof = {
            "resource_id": "314",
            "resource_url": "https://github.com/example/project/rules/314",
        }

        self.assertEqual(
            providers._github_command("ruleset", proof),
            ["gh", "api", "repos/example/project/rulesets/314"],
        )

    def test_malformed_ruleset_route_fails_closed(self) -> None:
        raw = "{}"
        proof = {
            "source_commit": SOURCE_COMMIT,
            "resource_id": "314",
            "resource_url": "https://github.com/example/project/issues/314",
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "observed_status": "ACTIVE",
            "readback": "branch:main protection",
        }

        self.assertFalse(
            providers._live_matches(
                "github", "ruleset", proof, RecordingRunner([raw])
            )
        )

    def test_completed_ci_without_success_conclusion_fails_closed(self) -> None:
        live = {
            "databaseId": 4242,
            "url": "https://github.com/example/project/actions/runs/4242",
            "headSha": SOURCE_COMMIT,
            "status": "COMPLETED",
            "conclusion": None,
        }
        raw = json.dumps(live, separators=(",", ":"), sort_keys=True)
        proof = {
            "source_commit": SOURCE_COMMIT,
            "resource_id": "4242",
            "resource_url": live["url"],
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "observed_status": "COMPLETED",
            "readback": "COMPLETED",
        }

        self.assertFalse(
            providers._live_matches(
                "github", "ci", proof, RecordingRunner([raw])
            )
        )

    def test_non_git_project_blocks_release_before_live_commands(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            started = goals.start_goal(
                project, "Release project", "released", execute=True
            )
            goal_id = started["goal_id"]
            receipt_path = project / started["receipt"]
            for state in ("SPECIFIED", "PLANNED", "IMPLEMENTING", "VERIFIED"):
                receipts.append_transition(receipt_path, state)
            runner = RecordingRunner([])

            result = providers.release_project(
                project,
                goal_id,
                "github",
                execute=False,
                runner=runner,
            )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["missing"], ["source.identity"])
            self.assertEqual(runner.calls, [])

    def test_short_numeric_github_resource_id_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-proof-") as temporary:
            project = pathlib.Path(temporary)
            goal_id = "goal-123456789abc"
            relative = f".divan/evidence/{goal_id}/pr-github.json"
            path = project.joinpath(*pathlib.PurePosixPath(relative).parts)
            path.parent.mkdir(parents=True)
            proof = {
                "schema_version": 1,
                "goal_id": goal_id,
                "project_identity": PROJECT_IDENTITY,
                "provider": "github",
                "operation": "pr",
                "source_commit": SOURCE_COMMIT,
                "resource_id": "42",
                "resource_url": "https://github.com/example/project/pull/42",
                "sha256": "b" * 64,
                "observed_status": "MERGED",
                "readback": "MERGED",
            }
            path.write_text(json.dumps(proof), encoding="utf-8")

            loaded = providers._load_proof(
                project,
                goal_id,
                PROJECT_IDENTITY,
                SOURCE_COMMIT,
                "github",
                "pr",
                {relative: hashlib.sha256(path.read_bytes()).hexdigest()},
            )

            self.assertIsNotNone(loaded)

    def test_live_match_normalizes_native_github_cli_response(self) -> None:
        raw = json.dumps(
            {
                "number": 42,
                "url": "https://github.com/trugurpala/divan/pull/42",
                "headRefOid": SOURCE_COMMIT,
                "state": "MERGED",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        proof = {
            "source_commit": SOURCE_COMMIT,
            "resource_id": "42",
            "resource_url": "https://github.com/trugurpala/divan/pull/42",
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "observed_status": "MERGED",
            "readback": "MERGED",
        }
        runner = RecordingRunner([raw])

        self.assertTrue(
            providers._live_matches("github", "pr", proof, runner)
        )

    def test_live_match_normalizes_native_vercel_preview_response(self) -> None:
        raw = json.dumps(
            {
                "uid": "dpl_immutable_42",
                "projectId": VERCEL_PROJECT_ID,
                "ownerId": VERCEL_ACCOUNT_ID,
                "gitSource": {
                    "type": "github",
                    "repoId": 991_337,
                    "sha": SOURCE_COMMIT,
                    "ref": "main",
                },
                "url": "divan-42.vercel.app",
                "readyState": "READY",
                "target": "preview",
                "meta": {
                    "githubCommitOrg": "example",
                    "githubCommitRepo": "project",
                    "githubCommitSha": SOURCE_COMMIT,
                },
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        proof = {
            "project_identity": PROJECT_IDENTITY,
            "source_commit": SOURCE_COMMIT,
            "resource_id": "dpl_immutable_42",
            "resource_url": "https://divan-42.vercel.app",
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "observed_status": "READY",
            "readback": "target=preview",
        }
        runner = RecordingRunner([raw])

        self.assertTrue(
            providers._live_matches("vercel", "preview", proof, runner)
        )

    def test_browser_verification_uses_native_https_observation_not_app_body(
        self,
    ) -> None:
        url = "https://preview-42.vercel.app"
        observation = providers.HTTPSObservation(
            status=200,
            final_url=url,
            request_id="sfo1::browser-check-42",
            tls_verified=True,
        )
        raw = providers._https_observation_json(observation)
        proof = {
            "source_commit": SOURCE_COMMIT,
            "resource_id": observation.request_id,
            "resource_url": url,
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "observed_status": "PASS",
            "readback": f"tls=verified;http=200;final={url}",
        }
        runner = RecordingRunner(
            [
                json.dumps(
                    {
                        "status": 200,
                        "url": url,
                        "requestId": observation.request_id,
                        "deploymentId": "dpl_preview_42",
                    }
                )
            ]
        )
        verifier = RecordingHTTPSVerifier(observation)

        self.assertTrue(
            providers._live_matches(
                "vercel",
                "browser-verify",
                proof,
                runner,
                verifier,
            )
        )
        self.assertEqual(runner.calls, [])
        self.assertEqual(verifier.calls, [url])

    def test_app_body_cannot_authorize_failed_native_https_observation(
        self,
    ) -> None:
        url = "https://preview-42.vercel.app"
        recorded = providers.HTTPSObservation(
            status=503,
            final_url=url,
            request_id="sfo1::failed-check-42",
            tls_verified=True,
        )
        claimed = {
            "status": 200,
            "url": url,
            "requestId": "sfo1::browser-check-42",
            "deploymentId": "dpl_preview_42",
        }
        raw = json.dumps(claimed, separators=(",", ":"), sort_keys=True)
        proof = {
            "source_commit": SOURCE_COMMIT,
            "resource_id": claimed["requestId"],
            "resource_url": url,
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "observed_status": "PASS",
            "readback": "http=200;deployment=dpl_preview_42",
        }
        runner = RecordingRunner([raw])
        verifier = RecordingHTTPSVerifier(recorded)

        self.assertFalse(
            providers._live_matches(
                "vercel",
                "browser-verify",
                proof,
                runner,
                verifier,
            )
        )
        self.assertEqual(runner.calls, [])
        self.assertEqual(verifier.calls, [url])

    def test_vercel_preview_metadata_cannot_establish_repository_identity(
        self,
    ) -> None:
        live = {
            "uid": "dpl_immutable_42",
            "projectId": VERCEL_PROJECT_ID,
            "ownerId": VERCEL_ACCOUNT_ID,
            "gitSource": {
                "type": "github",
                "repoId": 991_337,
                "sha": SOURCE_COMMIT,
                "ref": "main",
            },
            "url": "divan-42.vercel.app",
            "readyState": "READY",
            "target": "preview",
            "meta": {
                "githubCommitOrg": "attacker",
                "githubCommitRepo": "replayed-project",
                "githubCommitSha": SOURCE_COMMIT,
            },
        }
        raw = json.dumps(live, separators=(",", ":"), sort_keys=True)
        proof = {
            "project_identity": PROJECT_IDENTITY,
            "source_commit": SOURCE_COMMIT,
            "resource_id": "dpl_immutable_42",
            "resource_url": "https://divan-42.vercel.app",
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "observed_status": "READY",
            "readback": "target=preview",
        }

        self.assertTrue(
            providers._live_matches(
                "vercel", "preview", proof, RecordingRunner([raw])
            )
        )

    def test_project_os_goal_state_is_allowed_without_gitignore_but_product_is_not(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-source-") as temporary:
            project = pathlib.Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            subprocess.run(
                ["git", "config", "user.email", "divan@example.invalid"],
                cwd=project,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Divan Test"],
                cwd=project,
                check=True,
            )
            (project / "README.md").write_text("fixture\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=project, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "fixture"],
                cwd=project,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "remote",
                    "add",
                    "origin",
                    "https://github.com/example/project.git",
                ],
                cwd=project,
                check=True,
            )
            init_plan = project_os.build_init_plan(
                project, "standard", "en", "agents", False
            )
            project_os.apply_init_plan(init_plan)
            subprocess.run(
                ["git", "add", "AGENTS.md", ".divan"],
                cwd=project,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", "initialize project os"],
                cwd=project,
                check=True,
            )
            started = goals.start_goal(
                project, "Release project", "released", execute=True
            )
            goal_id = started["goal_id"]
            receipt_path = project / started["receipt"]
            for state in ("SPECIFIED", "PLANNED", "IMPLEMENTING", "VERIFIED"):
                receipts.append_transition(receipt_path, state)
            responses = self._proofs(
                project, goal_id, receipt_path, "github"
            )

            context = providers._source_context(project)
            release = providers.release_project(
                project,
                goal_id,
                "github",
                execute=True,
                runner=RecordingRunner(responses),
            )

            self.assertIsNotNone(context)
            self.assertFalse((project / ".gitignore").exists())
            self.assertEqual(release["status"], "RELEASED")

            product = project / "src" / "product.py"
            product.parent.mkdir()
            product.write_text("unsafe = True\n", encoding="utf-8")

            self.assertIsNone(providers._source_context(project))

    def test_vercel_release_rejects_same_commit_from_another_repository(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(
                project, goal_id, receipt_path, "vercel"
            )
            self._scope_vercel_deployments(
                project, goal_id, receipt_path, responses
            )
            runner = self._vercel_command_runner(
                responses,
                self._vercel_project_response(
                    owner="attacker",
                    repository="replayed-project",
                ),
            )

            result = providers.release_project(
                project,
                goal_id,
                "vercel",
                execute=True,
                runner=runner,
                https_verifier=self._vercel_https_verifier(),
            )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(
                result["missing"],
                ["vercel.project.identity"],
            )
            self.assertNotEqual(
                receipts.verify_receipt(receipt_path)["state"],
                "RELEASED",
            )

    def test_managed_source_paths_reject_traversal_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-source-") as temporary:
            project = pathlib.Path(temporary)
            self.assertFalse(
                providers._managed_project_os_path(project, "../outside.json")
            )
            managed = (
                project
                / ".divan"
                / "specs"
                / "goal-123456789abc"
                / "spec.md"
            )
            managed.parent.mkdir(parents=True)
            managed.write_text("managed\n", encoding="utf-8")
            original_is_symlink = pathlib.Path.is_symlink

            def reports_managed_symlink(path: pathlib.Path) -> bool:
                return path == managed or original_is_symlink(path)

            with mock.patch.object(
                pathlib.Path,
                "is_symlink",
                autospec=True,
                side_effect=reports_managed_symlink,
            ):
                self.assertFalse(
                    providers._managed_project_os_path(
                        project,
                        ".divan/specs/goal-123456789abc/spec.md",
                    )
                )

    def test_only_schema_valid_project_os_config_state_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-source-") as temporary:
            project = pathlib.Path(temporary)
            plan = project_os.build_init_plan(
                project, "standard", "en", "agents", False
            )
            project_os.apply_init_plan(plan)
            relative = ".divan/config.json"

            self.assertTrue(
                providers._managed_project_os_path(project, relative)
            )

            path = project / ".divan" / "config.json"
            config = json.loads(path.read_text(encoding="utf-8"))
            config["providers"] = []
            path.write_text(json.dumps(config), encoding="utf-8")

            self.assertFalse(
                providers._managed_project_os_path(project, relative)
            )

    def _verified_goal(self, project: pathlib.Path) -> tuple[str, pathlib.Path]:
        subprocess.run(
            ["git", "init", "-q"],
            cwd=project,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "divan@example.invalid"],
            cwd=project,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Divan Test"],
            cwd=project,
            check=True,
            capture_output=True,
        )
        (project / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=project,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "fixture"],
            cwd=project,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                "https://github.com/example/project.git",
            ],
            cwd=project,
            check=True,
            capture_output=True,
        )
        result = goals.start_goal(project, "Release project", "released", execute=True)
        receipt_path = project / result["receipt"]
        for state in ("SPECIFIED", "PLANNED", "IMPLEMENTING", "VERIFIED"):
            receipts.append_transition(receipt_path, state)
        return result["goal_id"], receipt_path

    def _github_observation(
        self,
        operation: str,
        source_commit: str,
        *,
        mismatch: bool,
    ) -> tuple[str, str, str, str, dict[str, object]]:
        live_commit = "b" * 40 if mismatch else source_commit
        if operation == "pr":
            return (
                "42",
                "https://github.com/example/project/pull/42",
                "MERGED",
                "MERGED",
                {
                    "number": 42,
                    "url": "https://github.com/example/project/pull/42",
                    "headRefOid": live_commit,
                    "state": "MERGED",
                },
            )
        if operation == "ci":
            return (
                "4242",
                "https://github.com/example/project/actions/runs/4242",
                "SUCCESS",
                "SUCCESS",
                {
                    "databaseId": 4242,
                    "url": "https://github.com/example/project/actions/runs/4242",
                    "headSha": live_commit,
                    "status": "completed",
                    "conclusion": "success",
                },
            )
        if operation == "ruleset":
            return (
                "314",
                "https://github.com/example/project/rules/314",
                "ACTIVE",
                "branch:main protection",
                {
                    "id": 314,
                    "name": "main protection",
                    "target": "branch",
                    "enforcement": "active",
                    "_links": {
                        "html": {
                            "href": "https://github.com/example/project/rules/314"
                        }
                    },
                },
            )
        if operation == "tag":
            tag_url = (
                "https://api.github.com/repos/example/project/"
                "git/refs/tags/v1.2.3"
            )
            return (
                "refs/tags/v1.2.3",
                tag_url,
                "VERIFIED",
                "commit",
                {
                    "ref": "refs/tags/v1.2.3",
                    "url": tag_url,
                    "object": {"sha": live_commit, "type": "commit"},
                },
            )
        return (
            "v1.2.3",
            "https://github.com/example/project/releases/tag/v1.2.3",
            "PUBLISHED",
            "PUBLISHED",
            {
                "tagName": "v1.2.3",
                "url": "https://github.com/example/project/releases/tag/v1.2.3",
                "targetCommitish": live_commit,
                "isDraft": False,
            },
        )

    def _vercel_observation(
        self, operation: str, source_commit: str
    ) -> tuple[str, str, str, str, dict[str, object]]:
        if operation == "preview":
            return (
                "dpl_preview_42",
                "https://preview-42.vercel.app",
                "READY",
                "target=preview",
                {
                    "uid": "dpl_preview_42",
                    "projectId": VERCEL_PROJECT_ID,
                    "ownerId": VERCEL_ACCOUNT_ID,
                    "gitSource": {
                        "type": "github",
                        "repoId": 991_337,
                        "sha": source_commit,
                        "ref": "main",
                    },
                    "url": "preview-42.vercel.app",
                    "readyState": "READY",
                    "target": "preview",
                    "meta": {
                        "githubCommitOrg": "example",
                        "githubCommitRepo": "project",
                        "githubCommitSha": source_commit,
                    },
                },
            )
        if operation == "browser-verify":
            return (
                "sfo1::browser-check-42",
                "https://preview-42.vercel.app",
                "PASS",
                (
                    "tls=verified;http=200;"
                    "final=https://preview-42.vercel.app"
                ),
                providers.HTTPSObservation(
                    status=200,
                    final_url="https://preview-42.vercel.app",
                    request_id="sfo1::browser-check-42",
                    tls_verified=True,
                ),
            )
        if operation == "staged-production":
            return (
                "dpl_staged_42",
                "https://staged-42.vercel.app",
                "READY",
                "target=production;aliases=0",
                {
                    "uid": "dpl_staged_42",
                    "projectId": VERCEL_PROJECT_ID,
                    "ownerId": VERCEL_ACCOUNT_ID,
                    "gitSource": {
                        "type": "github",
                        "repoId": 991_337,
                        "commitSha": source_commit,
                        "ref": "main",
                    },
                    "url": "staged-42.vercel.app",
                    "readyState": "READY",
                    "target": "production",
                    "aliases": [],
                    "meta": {
                        "githubCommitOrg": "example",
                        "githubCommitRepo": "project",
                        "githubCommitSha": source_commit,
                    },
                },
            )
        if operation == "promote":
            return (
                "dpl_staged_42",
                "https://project.vercel.app",
                "VERIFIED",
                "alias=project.vercel.app",
                {
                    "aliases": [
                        {
                            "alias": "project.vercel.app",
                        }
                    ]
                },
            )
        return (
            "dpl_staged_42",
            "https://project.vercel.app",
            "READY",
            "production-alias=project.vercel.app",
            {
                "uid": "dpl_staged_42",
                "projectId": VERCEL_PROJECT_ID,
                "ownerId": VERCEL_ACCOUNT_ID,
                "gitSource": {
                    "type": "github",
                    "repoId": 991_337,
                    "sha": source_commit,
                    "commitSha": source_commit,
                    "ref": "main",
                },
                "url": "staged-42.vercel.app",
                "readyState": "READY",
                "target": "production",
                "aliases": ["project.vercel.app"],
                "meta": {
                    "githubCommitOrg": "example",
                    "githubCommitRepo": "project",
                    "githubCommitSha": source_commit,
                },
            },
        )

    def _proofs(
        self,
        project: pathlib.Path,
        goal_id: str,
        receipt_path: pathlib.Path,
        provider: str,
        *,
        mismatch_operation: str | None = None,
        observed_status: str = "SUCCESS",
    ) -> list[str]:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        responses: list[str] = ["authenticated"]
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=project,
            text=True,
            encoding="utf-8",
        ).strip()
        for operation in providers.RELEASE_OPERATIONS[provider]:
            if provider == "github":
                resource_id, resource_url, status, readback, live = (
                    self._github_observation(
                        operation,
                        source_commit,
                        mismatch=operation == mismatch_operation,
                    )
                )
            else:
                resource_id, resource_url, status, readback, live = (
                    self._vercel_observation(operation, source_commit)
                )
            if observed_status != "SUCCESS":
                status = observed_status
            response = (
                providers._https_observation_json(live)
                if isinstance(live, providers.HTTPSObservation)
                else json.dumps(live, separators=(",", ":"), sort_keys=True)
            )
            if operation != "browser-verify":
                responses.append(response)
            proof = {
                "schema_version": 1,
                "goal_id": goal_id,
                "project_identity": PROJECT_IDENTITY,
                "provider": provider,
                "operation": operation,
                "source_commit": source_commit,
                "resource_id": resource_id,
                "resource_url": resource_url,
                "sha256": hashlib.sha256(response.encode()).hexdigest(),
                "observed_status": status,
                "readback": readback,
            }
            relative = f".divan/evidence/{goal_id}/{operation}-{provider}.json"
            path = project.joinpath(*pathlib.PurePosixPath(relative).parts)
            path.write_text(json.dumps(proof, sort_keys=True) + "\n", encoding="utf-8")
            payload["artifacts"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        receipt_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return responses

    def _scope_vercel_deployments(
        self,
        project: pathlib.Path,
        goal_id: str,
        receipt_path: pathlib.Path,
        responses: list[str],
        *,
        scopes: dict[str, tuple[object, object]] | None = None,
        meta_repository: tuple[str, str] | None = None,
    ) -> None:
        selected = scopes or {}
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for operation, response_index in (
            ("preview", 1),
            ("staged-production", 2),
            ("live-readback", 4),
        ):
            live = json.loads(responses[response_index])
            project_id, account_id = selected.get(
                operation,
                (VERCEL_PROJECT_ID, VERCEL_ACCOUNT_ID),
            )
            live.pop("projectId", None)
            live.pop("ownerId", None)
            if project_id is not None:
                live["projectId"] = project_id
            if account_id is not None:
                live["ownerId"] = account_id
            if meta_repository is not None:
                live["meta"]["githubCommitOrg"] = meta_repository[0]
                live["meta"]["githubCommitRepo"] = meta_repository[1]
            response = json.dumps(
                live, separators=(",", ":"), sort_keys=True
            )
            responses[response_index] = response
            proof_path = (
                project
                / ".divan"
                / "evidence"
                / goal_id
                / f"{operation}-vercel.json"
            )
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            proof["sha256"] = hashlib.sha256(response.encode()).hexdigest()
            proof_path.write_text(
                json.dumps(proof, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            relative = proof_path.relative_to(project).as_posix()
            receipt["artifacts"][relative] = hashlib.sha256(
                proof_path.read_bytes()
            ).hexdigest()
        receipt_path.write_text(
            json.dumps(receipt, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _vercel_command_runner(
        self,
        responses: list[str],
        project_response: dict[str, object],
        *,
        project_returncode: int = 0,
    ) -> CommandRunner:
        project_raw = json.dumps(
            project_response, separators=(",", ":"), sort_keys=True
        )
        return CommandRunner(
            {
                ("vercel", "whoami"): [(0, responses[0])],
                (
                    "vercel",
                    "api",
                    "/v13/deployments/dpl_preview_42",
                ): [(0, responses[1])],
                (
                    "vercel",
                    "api",
                    (
                        f"/v9/projects/{VERCEL_PROJECT_ID}"
                        f"?teamId={VERCEL_ACCOUNT_ID}"
                    ),
                ): [(project_returncode, project_raw)],
                (
                    "vercel",
                    "api",
                    "/v13/deployments/dpl_staged_42",
                ): [(0, responses[2]), (0, responses[4])],
                (
                    "vercel",
                    "api",
                    "/v2/deployments/dpl_staged_42/aliases",
                ): [(0, responses[3])],
            }
        )

    def _set_vercel_git_sources(
        self,
        project: pathlib.Path,
        goal_id: str,
        receipt_path: pathlib.Path,
        responses: list[str],
        *,
        git_sources: dict[str, dict[str, object] | None] | None = None,
        meta_commit: str | None = None,
        deployment_source: str | None = None,
    ) -> None:
        selected = git_sources or {}
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        preview_proof = json.loads(
            (
                project
                / ".divan"
                / "evidence"
                / goal_id
                / "preview-vercel.json"
            ).read_text(encoding="utf-8")
        )
        source_commit = preview_proof["source_commit"]
        defaults: dict[str, dict[str, object]] = {
            "preview": {
                "type": "github",
                "repoId": 991_337,
                "sha": source_commit,
                "ref": "main",
            },
            "staged-production": {
                "type": "github",
                "repoId": 991_337,
                "commitSha": source_commit,
                "ref": "main",
            },
            "live-readback": {
                "type": "github",
                "repoId": 991_337,
                "sha": source_commit,
                "commitSha": source_commit,
                "ref": "main",
            },
        }
        for operation, response_index in (
            ("preview", 1),
            ("staged-production", 2),
            ("live-readback", 4),
        ):
            live = json.loads(responses[response_index])
            git_source = (
                selected[operation]
                if operation in selected
                else defaults[operation]
            )
            if git_source is None:
                live.pop("gitSource", None)
            else:
                live["gitSource"] = git_source
            if meta_commit is not None:
                live["meta"]["githubCommitSha"] = meta_commit
            if deployment_source is not None:
                live["source"] = deployment_source
            response = json.dumps(
                live, separators=(",", ":"), sort_keys=True
            )
            responses[response_index] = response
            proof_path = (
                project
                / ".divan"
                / "evidence"
                / goal_id
                / f"{operation}-vercel.json"
            )
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            proof["sha256"] = hashlib.sha256(response.encode()).hexdigest()
            proof_path.write_text(
                json.dumps(proof, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            relative = proof_path.relative_to(project).as_posix()
            receipt["artifacts"][relative] = hashlib.sha256(
                proof_path.read_bytes()
            ).hexdigest()
        receipt_path.write_text(
            json.dumps(receipt, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _vercel_project_response(
        self,
        *,
        owner: str = "example",
        repository: str = "project",
    ) -> dict[str, object]:
        return {
            "id": VERCEL_PROJECT_ID,
            "accountId": VERCEL_ACCOUNT_ID,
            "link": {
                "type": "github",
                "org": owner,
                "repo": repository,
                "repoId": 991_337,
                "repoOwnerId": 771_224,
            },
        }

    def _vercel_https_verifier(self) -> RecordingHTTPSVerifier:
        return RecordingHTTPSVerifier(
            providers.HTTPSObservation(
                status=200,
                final_url="https://preview-42.vercel.app",
                request_id="sfo1::browser-check-42",
                tls_verified=True,
            )
        )

    def test_matching_failed_status_is_not_release_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(
                project,
                goal_id,
                receipt_path,
                "github",
                observed_status="FAILED",
            )
            runner = RecordingRunner(responses)

            result = providers.release_project(
                project,
                goal_id,
                "github",
                execute=True,
                runner=runner,
            )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["missing"], ["github.evidence.pr"])

    def test_release_requires_pr_proof(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            self._proofs(project, goal_id, receipt_path, "github")
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            relative = f".divan/evidence/{goal_id}/pr-github.json"
            del payload["artifacts"][relative]
            receipt_path.write_text(
                json.dumps(payload, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            before = receipt_path.read_bytes()

            result = providers.release_project(
                project,
                goal_id,
                "github",
                execute=False,
            )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["missing"], ["github.evidence.pr"])
            self.assertEqual(receipt_path.read_bytes(), before)

    def test_execute_blocks_when_cli_or_auth_readback_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(project, goal_id, receipt_path, "github")
            runner = RecordingRunner(responses, returncode=1)

            result = providers.release_project(
                project,
                goal_id,
                "github",
                execute=True,
                runner=runner,
            )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["missing"], ["github.authority"])
            self.assertEqual(receipts.verify_receipt(receipt_path)["state"], "BLOCKED")

    def test_live_response_identity_mismatch_never_releases(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(
                project,
                goal_id,
                receipt_path,
                "github",
                mismatch_operation="ci",
            )
            runner = RecordingRunner(responses)

            result = providers.release_project(
                project,
                goal_id,
                "github",
                execute=True,
                runner=runner,
            )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["missing"], ["github.verification.ci"])
            self.assertNotEqual(receipts.verify_receipt(receipt_path)["state"], "RELEASED")

    def test_malformed_proof_is_rejected_before_runner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(project, goal_id, receipt_path, "github")
            proof_path = (
                project
                / ".divan"
                / "evidence"
                / goal_id
                / "pr-github.json"
            )
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            proof["resource_url"] = "http://github.com/unsafe"
            proof_path.write_text(json.dumps(proof), encoding="utf-8")
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            relative = proof_path.relative_to(project).as_posix()
            payload["artifacts"][relative] = hashlib.sha256(proof_path.read_bytes()).hexdigest()
            receipt_path.write_text(json.dumps(payload), encoding="utf-8")
            runner = RecordingRunner(responses)

            result = providers.release_project(
                project,
                goal_id,
                "github",
                execute=False,
                runner=runner,
            )

            self.assertEqual(result["missing"], ["github.evidence.pr"])
            self.assertEqual(runner.calls, [])

    def test_verified_operations_use_fixed_shell_free_commands_and_dps_result(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(project, goal_id, receipt_path, "github")
            runner = RecordingRunner(responses)

            result = providers.release_project(
                project,
                goal_id,
                "github",
                execute=True,
                runner=runner,
            )

            self.assertEqual(result["status"], "RELEASED")
            self.assertEqual(len(runner.calls), 7)
            self.assertTrue(all(call[0] == "gh" for call in runner.calls))
            self.assertEqual(
                runner.calls[0],
                ["gh", "auth", "status", "--active"],
            )
            self.assertEqual(runner.calls[1][:3], ["gh", "pr", "view"])
            self.assertEqual(runner.calls[2][:3], ["gh", "run", "view"])
            self.assertNotIn("shell=True", json.dumps(runner.calls))
            verified = receipts.verify_receipt(receipt_path)
            self.assertEqual(verified["state"], "RELEASED")
            self.assertEqual(verified["results"]["DPS-007"]["status"], "PASS")
            self.assertEqual(
                len(verified["results"]["DPS-007"]["evidence"]),
                len(providers.RELEASE_OPERATIONS["github"]),
            )

    def test_vercel_uses_authenticated_project_link_not_forged_deployment_meta(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(
                project, goal_id, receipt_path, "vercel"
            )
            self._scope_vercel_deployments(
                project,
                goal_id,
                receipt_path,
                responses,
                meta_repository=("attacker", "forged-repository"),
            )
            runner = self._vercel_command_runner(
                responses,
                self._vercel_project_response(),
            )

            result = providers.release_project(
                project,
                goal_id,
                "vercel",
                execute=False,
                runner=runner,
                https_verifier=RecordingHTTPSVerifier(
                    providers.HTTPSObservation(
                        status=200,
                        final_url="https://preview-42.vercel.app",
                        request_id="sfo1::browser-check-42",
                        tls_verified=True,
                    )
                ),
            )

            self.assertEqual(result["status"], "planned")
            self.assertIn(
                [
                    "vercel",
                    "api",
                    (
                        f"/v9/projects/{VERCEL_PROJECT_ID}"
                        f"?teamId={VERCEL_ACCOUNT_ID}"
                    ),
                ],
                runner.calls,
            )

    def test_vercel_rejects_provider_project_link_from_another_repository(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(
                project, goal_id, receipt_path, "vercel"
            )
            self._scope_vercel_deployments(
                project, goal_id, receipt_path, responses
            )
            runner = self._vercel_command_runner(
                responses,
                self._vercel_project_response(
                    owner="attacker",
                    repository="replayed-project",
                ),
            )

            result = providers.release_project(
                project,
                goal_id,
                "vercel",
                execute=True,
                runner=runner,
                https_verifier=self._vercel_https_verifier(),
            )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(
                result["missing"],
                ["vercel.project.identity"],
            )
            self.assertNotEqual(
                receipts.verify_receipt(receipt_path)["state"],
                "RELEASED",
            )

    def test_vercel_project_lookup_rejects_inaccessible_or_ambiguous_links(
        self,
    ) -> None:
        invalid_projects: dict[str, tuple[dict[str, object], int]] = {
            "inaccessible": (self._vercel_project_response(), 1),
            "missing-link": (
                {
                    "id": VERCEL_PROJECT_ID,
                    "accountId": VERCEL_ACCOUNT_ID,
                },
                0,
            ),
            "project-mismatch": (
                {
                    **self._vercel_project_response(),
                    "id": "prj_other_42",
                },
                0,
            ),
            "account-mismatch": (
                {
                    **self._vercel_project_response(),
                    "accountId": "team_other_42",
                },
                0,
            ),
            "mutable-repository-name": (
                {
                    **self._vercel_project_response(),
                    "link": {
                        "type": "github",
                        "org": "example",
                        "repo": "example/project",
                        "repoId": 991_337,
                        "repoOwnerId": 771_224,
                    },
                },
                0,
            ),
            "missing-immutable-id": (
                {
                    **self._vercel_project_response(),
                    "link": {
                        "type": "github",
                        "org": "example",
                        "repo": "project",
                    },
                },
                0,
            ),
            "ambiguous-provider-fields": (
                {
                    **self._vercel_project_response(),
                    "link": {
                        "type": "github",
                        "org": "example",
                        "repo": "project",
                        "repoId": 991_337,
                        "repoOwnerId": 771_224,
                        "owner": "other-workspace",
                        "slug": "other-repository",
                    },
                },
                0,
            ),
        }
        for scenario, (project_response, returncode) in invalid_projects.items():
            with self.subTest(scenario=scenario):
                with tempfile.TemporaryDirectory(
                    prefix="divan-release-"
                ) as temporary:
                    project = pathlib.Path(temporary)
                    goal_id, receipt_path = self._verified_goal(project)
                    responses = self._proofs(
                        project, goal_id, receipt_path, "vercel"
                    )
                    self._scope_vercel_deployments(
                        project, goal_id, receipt_path, responses
                    )
                    runner = self._vercel_command_runner(
                        responses,
                        project_response,
                        project_returncode=returncode,
                    )

                    result = providers.release_project(
                        project,
                        goal_id,
                        "vercel",
                        execute=False,
                        runner=runner,
                        https_verifier=self._vercel_https_verifier(),
                    )

                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(
                        result["missing"],
                        ["vercel.project.identity"],
                    )

    def test_vercel_deployments_must_share_project_and_account_scope(
        self,
    ) -> None:
        scenarios: dict[str, dict[str, tuple[object, object]]] = {
            "preview-missing-project": {
                "preview": (None, VERCEL_ACCOUNT_ID),
            },
            "staged-other-project": {
                "staged-production": (
                    "prj_other_42",
                    VERCEL_ACCOUNT_ID,
                ),
            },
            "live-other-account": {
                "live-readback": (
                    VERCEL_PROJECT_ID,
                    "team_other_42",
                ),
            },
        }
        expected_operations = {
            "preview-missing-project": "preview",
            "staged-other-project": "staged-production",
            "live-other-account": "live-readback",
        }
        for scenario, scopes in scenarios.items():
            with self.subTest(scenario=scenario):
                with tempfile.TemporaryDirectory(
                    prefix="divan-release-"
                ) as temporary:
                    project = pathlib.Path(temporary)
                    goal_id, receipt_path = self._verified_goal(project)
                    responses = self._proofs(
                        project, goal_id, receipt_path, "vercel"
                    )
                    self._scope_vercel_deployments(
                        project,
                        goal_id,
                        receipt_path,
                        responses,
                        scopes=scopes,
                    )
                    runner = self._vercel_command_runner(
                        responses,
                        self._vercel_project_response(),
                    )

                    result = providers.release_project(
                        project,
                        goal_id,
                        "vercel",
                        execute=False,
                        runner=runner,
                        https_verifier=self._vercel_https_verifier(),
                    )

                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(
                        result["missing"],
                        [
                            "vercel.verification."
                            + expected_operations[scenario]
                        ],
                    )

    def test_vercel_uses_native_git_source_not_forged_commit_metadata(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(
                project, goal_id, receipt_path, "vercel"
            )
            self._scope_vercel_deployments(
                project, goal_id, receipt_path, responses
            )
            self._set_vercel_git_sources(
                project,
                goal_id,
                receipt_path,
                responses,
                meta_commit="b" * 40,
            )
            runner = self._vercel_command_runner(
                responses,
                self._vercel_project_response(),
            )

            result = providers.release_project(
                project,
                goal_id,
                "vercel",
                execute=False,
                runner=runner,
                https_verifier=self._vercel_https_verifier(),
            )

            self.assertEqual(result["status"], "planned")

    def test_vercel_rejects_meta_only_cli_and_local_upload_deployments(
        self,
    ) -> None:
        for deployment_source in ("cli", "api"):
            with self.subTest(deployment_source=deployment_source):
                with tempfile.TemporaryDirectory(
                    prefix="divan-release-"
                ) as temporary:
                    project = pathlib.Path(temporary)
                    goal_id, receipt_path = self._verified_goal(project)
                    responses = self._proofs(
                        project, goal_id, receipt_path, "vercel"
                    )
                    self._scope_vercel_deployments(
                        project, goal_id, receipt_path, responses
                    )
                    self._set_vercel_git_sources(
                        project,
                        goal_id,
                        receipt_path,
                        responses,
                        git_sources={
                            "preview": None,
                            "staged-production": None,
                            "live-readback": None,
                        },
                        deployment_source=deployment_source,
                    )
                    runner = self._vercel_command_runner(
                        responses,
                        self._vercel_project_response(),
                    )

                    result = providers.release_project(
                        project,
                        goal_id,
                        "vercel",
                        execute=False,
                        runner=runner,
                        https_verifier=self._vercel_https_verifier(),
                    )

                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(
                        result["missing"],
                        ["vercel.verification.preview"],
                    )

    def test_vercel_native_git_source_binds_project_repo_and_clean_head(
        self,
    ) -> None:
        scenarios: dict[str, tuple[dict[str, object], str]] = {
            "repository-mismatch": (
                {
                    "type": "github",
                    "repoId": 771_224,
                    "sha": None,
                    "ref": "main",
                },
                "vercel.project.identity",
            ),
            "commit-mismatch": (
                {
                    "type": "github",
                    "repoId": 991_337,
                    "sha": "c" * 40,
                    "ref": "main",
                },
                "vercel.verification.preview",
            ),
            "ambiguous-commit-fields": (
                {
                    "type": "github",
                    "repoId": 991_337,
                    "sha": "c" * 40,
                    "commitSha": "d" * 40,
                    "ref": "main",
                },
                "vercel.verification.preview",
            ),
        }
        for scenario, (git_source, missing) in scenarios.items():
            with self.subTest(scenario=scenario):
                with tempfile.TemporaryDirectory(
                    prefix="divan-release-"
                ) as temporary:
                    project = pathlib.Path(temporary)
                    goal_id, receipt_path = self._verified_goal(project)
                    responses = self._proofs(
                        project, goal_id, receipt_path, "vercel"
                    )
                    self._scope_vercel_deployments(
                        project, goal_id, receipt_path, responses
                    )
                    preview_proof = json.loads(
                        (
                            project
                            / ".divan"
                            / "evidence"
                            / goal_id
                            / "preview-vercel.json"
                        ).read_text(encoding="utf-8")
                    )
                    if git_source["sha"] is None:
                        git_source["sha"] = preview_proof["source_commit"]
                    self._set_vercel_git_sources(
                        project,
                        goal_id,
                        receipt_path,
                        responses,
                        git_sources={"preview": git_source},
                    )
                    runner = self._vercel_command_runner(
                        responses,
                        self._vercel_project_response(),
                    )

                    result = providers.release_project(
                        project,
                        goal_id,
                        "vercel",
                        execute=False,
                        runner=runner,
                        https_verifier=self._vercel_https_verifier(),
                    )

                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(result["missing"], [missing])

    def test_vercel_deployment_chain_requires_consistent_native_git_source(
        self,
    ) -> None:
        scenarios = {
            "staged-commit-mismatch": (
                "staged-production",
                {
                    "type": "github",
                    "repoId": 991_337,
                    "sha": "c" * 40,
                    "ref": "main",
                },
            ),
            "live-repository-mismatch": (
                "live-readback",
                {
                    "type": "github",
                    "repoId": 771_224,
                    "sha": "a" * 40,
                    "ref": "main",
                },
            ),
        }
        for scenario, (operation, git_source) in scenarios.items():
            with self.subTest(scenario=scenario):
                with tempfile.TemporaryDirectory(
                    prefix="divan-release-"
                ) as temporary:
                    project = pathlib.Path(temporary)
                    goal_id, receipt_path = self._verified_goal(project)
                    responses = self._proofs(
                        project, goal_id, receipt_path, "vercel"
                    )
                    self._scope_vercel_deployments(
                        project, goal_id, receipt_path, responses
                    )
                    if operation == "live-readback":
                        preview_proof = json.loads(
                            (
                                project
                                / ".divan"
                                / "evidence"
                                / goal_id
                                / "preview-vercel.json"
                            ).read_text(encoding="utf-8")
                        )
                        git_source["sha"] = preview_proof["source_commit"]
                    self._set_vercel_git_sources(
                        project,
                        goal_id,
                        receipt_path,
                        responses,
                        git_sources={operation: git_source},
                    )
                    runner = self._vercel_command_runner(
                        responses,
                        self._vercel_project_response(),
                    )

                    result = providers.release_project(
                        project,
                        goal_id,
                        "vercel",
                        execute=False,
                        runner=runner,
                        https_verifier=self._vercel_https_verifier(),
                    )

                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(
                        result["missing"],
                        [f"vercel.verification.{operation}"],
                    )

    def test_vercel_uses_documented_fixed_read_only_commands(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-") as temporary:
            project = pathlib.Path(temporary)
            goal_id, receipt_path = self._verified_goal(project)
            responses = self._proofs(project, goal_id, receipt_path, "vercel")
            self._scope_vercel_deployments(
                project, goal_id, receipt_path, responses
            )
            runner = self._vercel_command_runner(
                responses,
                self._vercel_project_response(),
            )

            result = providers.release_project(
                project,
                goal_id,
                "vercel",
                execute=False,
                runner=runner,
                https_verifier=RecordingHTTPSVerifier(
                    providers.HTTPSObservation(
                        status=200,
                        final_url="https://preview-42.vercel.app",
                        request_id="sfo1::browser-check-42",
                        tls_verified=True,
                    )
                ),
            )

            self.assertEqual(result["status"], "planned")
            self.assertEqual(len(runner.calls), 6)
            self.assertTrue(all(call[0] == "vercel" for call in runner.calls))
            self.assertEqual(runner.calls[0], ["vercel", "whoami"])
            self.assertEqual(
                runner.calls[1:],
                [
                    ["vercel", "api", "/v13/deployments/dpl_preview_42"],
                    [
                        "vercel",
                        "api",
                        (
                            f"/v9/projects/{VERCEL_PROJECT_ID}"
                            f"?teamId={VERCEL_ACCOUNT_ID}"
                        ),
                    ],
                    ["vercel", "api", "/v13/deployments/dpl_staged_42"],
                    [
                        "vercel",
                        "api",
                        "/v2/deployments/dpl_staged_42/aliases",
                    ],
                    ["vercel", "api", "/v13/deployments/dpl_staged_42"],
                ],
            )


if __name__ == "__main__":
    unittest.main()
