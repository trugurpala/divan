from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .git_provider import PullRequestRef, RepositoryRef


class ForgejoApiError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True, slots=True)
class ForgejoConfig:
    base_url: str
    token: str = field(repr=False)
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        base_url = self.base_url.rstrip("/")
        if not base_url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
            raise ValueError("Forgejo base_url must use HTTPS except for localhost development")
        if not self.token:
            raise ValueError("Forgejo token is required")
        if self.timeout_seconds <= 0:
            raise ValueError("Forgejo timeout must be positive")
        object.__setattr__(self, "base_url", base_url)


OpenUrl = Callable[..., Any]


class ForgejoClient:
    """Minimal Forgejo adapter for Pusula's provider-neutral Git boundary."""

    def __init__(self, config: ForgejoConfig, *, opener: OpenUrl = urlopen) -> None:
        self._config = config
        self._opener = opener

    def version(self) -> str:
        payload = self._request("GET", "/version")
        version = payload.get("version") if isinstance(payload, dict) else None
        if not isinstance(version, str) or not version:
            raise ForgejoApiError("Forgejo version response is malformed")
        return version

    def list_repositories(self) -> tuple[RepositoryRef, ...]:
        payload = self._request("GET", "/user/repos?limit=50")
        if not isinstance(payload, list):
            raise ForgejoApiError("Forgejo repository list response is malformed")
        return tuple(self._repository(item) for item in payload)

    def get_repository(self, owner: str, name: str) -> RepositoryRef:
        payload = self._request("GET", f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}")
        return self._repository(payload)

    def create_branch(self, owner: str, name: str, *, branch: str, from_branch: str) -> None:
        self._request(
            "POST",
            f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}/branches",
            {"new_branch_name": branch, "old_branch_name": from_branch},
        )

    def create_pull_request(
        self,
        owner: str,
        name: str,
        *,
        title: str,
        head_branch: str,
        base_branch: str,
        body: str,
    ) -> PullRequestRef:
        payload = self._request(
            "POST",
            f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}/pulls",
            {"title": title, "head": head_branch, "base": base_branch, "body": body},
        )
        if not isinstance(payload, dict):
            raise ForgejoApiError("Forgejo pull request response is malformed")
        try:
            return PullRequestRef(
                number=int(payload["number"]),
                title=str(payload["title"]),
                state=str(payload["state"]),
                head_branch=str(payload["head"]["ref"]),
                base_branch=str(payload["base"]["ref"]),
                web_url=str(payload["html_url"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ForgejoApiError("Forgejo pull request response is malformed") from exc

    def _request(self, method: str, path: str, payload: dict[str, object] | None = None) -> Any:
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Authorization": f"token {self._config.token}",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self._config.base_url}/api/v1{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            response = self._opener(request, timeout=self._config.timeout_seconds)
            raw = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise ForgejoApiError(f"Forgejo API returned HTTP {exc.code}: {detail}", status=exc.code) from exc
        except URLError as exc:
            raise ForgejoApiError(f"Forgejo API is unreachable: {exc.reason}") from exc
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ForgejoApiError("Forgejo API returned invalid JSON") from exc

    @staticmethod
    def _repository(payload: object) -> RepositoryRef:
        if not isinstance(payload, dict):
            raise ForgejoApiError("Forgejo repository response is malformed")
        try:
            owner = payload["owner"]
            if not isinstance(owner, dict):
                raise TypeError("owner is not an object")
            return RepositoryRef(
                owner=str(owner["login"]),
                name=str(payload["name"]),
                default_branch=str(payload["default_branch"]),
                clone_url=str(payload["clone_url"]),
                private=bool(payload["private"]),
            )
        except (KeyError, TypeError) as exc:
            raise ForgejoApiError("Forgejo repository response is malformed") from exc
