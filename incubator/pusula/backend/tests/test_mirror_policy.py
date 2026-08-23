from __future__ import annotations

from unittest import TestCase

from pusula.integrations.mirror_policy import MirrorPolicyViolation, build_github_downstream_mirror


class MirrorPolicyTests(TestCase):
    def test_builds_explicit_forgejo_to_github_plan(self) -> None:
        plan = build_github_downstream_mirror(
            remote_url="https://github.com/acme/demo.git",
            branch_filters=("main", "release/*"),
        )

        self.assertEqual(plan.source_provider, "forgejo")
        self.assertEqual(plan.target_provider, "github")
        self.assertEqual(plan.branch_filters, ("main", "release/*"))
        self.assertEqual(plan.branch_filter, "main, release/*")
        self.assertTrue(plan.sync_on_commit)

    def test_rejects_empty_branch_filters(self) -> None:
        with self.assertRaisesRegex(MirrorPolicyViolation, "allowlist"):
            build_github_downstream_mirror(
                remote_url="https://github.com/acme/demo.git",
                branch_filters=(),
            )

    def test_rejects_global_wildcard(self) -> None:
        with self.assertRaisesRegex(MirrorPolicyViolation, "wildcard"):
            build_github_downstream_mirror(
                remote_url="https://github.com/acme/demo.git",
                branch_filters=("*",),
            )

    def test_rejects_credentials_embedded_in_url(self) -> None:
        with self.assertRaisesRegex(MirrorPolicyViolation, "credentials"):
            build_github_downstream_mirror(
                remote_url="https://user:token@github.com/acme/demo.git",
                branch_filters=("main",),
            )

    def test_rejects_non_github_target(self) -> None:
        with self.assertRaisesRegex(MirrorPolicyViolation, "GitHub"):
            build_github_downstream_mirror(
                remote_url="https://gitlab.com/acme/demo.git",
                branch_filters=("main",),
            )

    def test_rejects_target_without_dot_git_suffix(self) -> None:
        with self.assertRaisesRegex(MirrorPolicyViolation, "end with .git"):
            build_github_downstream_mirror(
                remote_url="https://github.com/acme/demo",
                branch_filters=("main",),
            )

    def test_rejects_duplicate_filters(self) -> None:
        with self.assertRaisesRegex(MirrorPolicyViolation, "duplicate"):
            build_github_downstream_mirror(
                remote_url="https://github.com/acme/demo.git",
                branch_filters=("main", "main"),
            )

    def test_rejects_ref_style_filter(self) -> None:
        with self.assertRaisesRegex(MirrorPolicyViolation, "branch names"):
            build_github_downstream_mirror(
                remote_url="https://github.com/acme/demo.git",
                branch_filters=("refs/heads/main",),
            )
