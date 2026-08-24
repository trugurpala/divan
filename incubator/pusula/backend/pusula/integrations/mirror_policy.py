from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


class MirrorPolicyViolation(ValueError):
    """Raised when a mirror request could violate Pusula's authority boundary."""


@dataclass(frozen=True, slots=True)
class MirrorPlan:
    source_provider: str
    target_provider: str
    remote_url: str
    branch_filters: tuple[str, ...]
    sync_on_commit: bool

    @property
    def branch_filter(self) -> str:
        return ", ".join(self.branch_filters)


def build_github_downstream_mirror(
    *,
    remote_url: str,
    branch_filters: tuple[str, ...],
    sync_on_commit: bool = True,
) -> MirrorPlan:
    """Build the only V1 mirror direction: Forgejo -> GitHub.

    The explicit branch allowlist is mandatory because Forgejo uses
    ``git push --mirror`` when the filter is empty, which can force-update the
    downstream repository. GitHub is therefore a disposable downstream mirror,
    never a source of canonical Pusula state.
    """

    normalized_url = remote_url.strip()
    if not normalized_url:
        raise MirrorPolicyViolation("mirror remote URL is required")

    parsed = urlsplit(normalized_url)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise MirrorPolicyViolation("V1 mirror target must be an HTTPS GitHub repository")
    if parsed.username is not None or parsed.password is not None:
        raise MirrorPolicyViolation("credentials must not be embedded in the mirror URL")
    if parsed.query or parsed.fragment:
        raise MirrorPolicyViolation("mirror URL must not contain query parameters or fragments")
    if not parsed.path.endswith(".git"):
        raise MirrorPolicyViolation("mirror URL must end with .git")

    cleaned = tuple(item.strip() for item in branch_filters if item.strip())
    if not cleaned:
        raise MirrorPolicyViolation("an explicit branch allowlist is required")
    if len(set(cleaned)) != len(cleaned):
        raise MirrorPolicyViolation("duplicate branch filters are not allowed")
    if any(item == "*" for item in cleaned):
        raise MirrorPolicyViolation("a global wildcard mirror is not allowed")
    if any(item.startswith("refs/") or item.startswith("-") for item in cleaned):
        raise MirrorPolicyViolation("branch filters must be branch names or positive globs")
    if any(".." in item or " " in item for item in cleaned):
        raise MirrorPolicyViolation("branch filters contain an invalid branch pattern")

    return MirrorPlan(
        source_provider="forgejo",
        target_provider="github",
        remote_url=normalized_url,
        branch_filters=cleaned,
        sync_on_commit=sync_on_commit,
    )
