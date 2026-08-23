from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class RepositoryRef:
    owner: str
    name: str
    default_branch: str
    clone_url: str
    private: bool

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True, slots=True)
class PullRequestRef:
    number: int
    title: str
    state: str
    head_branch: str
    base_branch: str
    web_url: str


@runtime_checkable
class GitProvider(Protocol):
    """Replaceable Git collaboration surface.

    Provider results are evidence inputs. They never mutate Mizan's canonical
    state directly.
    """

    def version(self) -> str: ...

    def list_repositories(self) -> tuple[RepositoryRef, ...]: ...

    def get_repository(self, owner: str, name: str) -> RepositoryRef: ...

    def create_branch(self, owner: str, name: str, *, branch: str, from_branch: str) -> None: ...

    def create_pull_request(
        self,
        owner: str,
        name: str,
        *,
        title: str,
        head_branch: str,
        base_branch: str,
        body: str,
    ) -> PullRequestRef: ...
