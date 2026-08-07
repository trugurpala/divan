from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from .executable_locator import locate_executable


@dataclass(frozen=True)
class InstalledApp:
    name: str
    version: str | None = None
    install_location: str | None = None


@dataclass(frozen=True)
class ToolSpec:
    id: str
    display_name: str
    aliases: tuple[str, ...]
    required: bool = False
    version_args: tuple[str, ...] = ("--version",)
    auth_args: tuple[str, ...] | None = None
    subscription_supported: bool = False
    api_env: tuple[str, ...] = ()
    windows_app_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolStatus:
    id: str
    available: bool
    path: str | None
    required: bool
    display_name: str = ""
    version: str | None = None
    auth: str = "unknown"
    auth_detail: str | None = None
    subscription_supported: bool = False
    api_key_configured: bool = False
    app_installed: bool = False
    app_version: str | None = None


@dataclass(frozen=True)
class ProjectReadiness:
    ready: bool
    tools: tuple[ToolStatus, ...]


TOOL_SPECS = (
    ToolSpec("git", "Git", ("git",), required=True),
    ToolSpec(
        "gh",
        "GitHub CLI",
        ("gh",),
        auth_args=("auth", "status"),
        windows_app_names=("GitHub CLI",),
    ),
    ToolSpec("orca", "Orca", ("orca",), windows_app_names=("Orca",)),
    ToolSpec(
        "codex",
        "Codex",
        ("codex",),
        auth_args=("login", "status"),
        subscription_supported=True,
        api_env=("OPENAI_API_KEY",),
        windows_app_names=("Codex", "OpenAI Codex"),
    ),
    ToolSpec(
        "claude",
        "Claude Code",
        ("claude",),
        subscription_supported=True,
        api_env=("ANTHROPIC_API_KEY",),
        windows_app_names=("Claude", "Claude Code"),
    ),
    ToolSpec(
        "opencode",
        "OpenCode",
        ("opencode",),
        auth_args=("auth", "list"),
        subscription_supported=False,
        windows_app_names=("OpenCode",),
    ),
    ToolSpec(
        "cursor-agent",
        "Cursor Agent",
        ("cursor-agent",),
        auth_args=("status",),
        subscription_supported=True,
        api_env=("CURSOR_API_KEY",),
        windows_app_names=("Cursor",),
    ),
)


ProbeRunner = Callable[[Sequence[str], float], tuple[int, str, str]]
Which = Callable[[str], str | None]
AuthResult = tuple[str, str | None]


def discover_tools(
    which: Which = shutil.which,
    *,
    runner: ProbeRunner | None = None,
    env: Mapping[str, str] | None = None,
    installed_apps: Sequence[InstalledApp] | None = None,
) -> ProjectReadiness:
    runner = runner or _probe
    environment = env or os.environ
    apps = tuple(installed_apps) if installed_apps is not None else discover_installed_apps()
    tools = tuple(
        _discover_one(spec, which=which, runner=runner, env=environment, apps=apps)
        for spec in TOOL_SPECS
    )
    return ProjectReadiness(
        ready=all(tool.available for tool in tools if tool.required),
        tools=tools,
    )


def discover_installed_apps() -> tuple[InstalledApp, ...]:
    if sys.platform != "win32":
        return ()
    try:
        import winreg
    except ImportError:
        return ()

    roots = (
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
    )
    result: dict[str, InstalledApp] = {}
    for hive, key_path in roots:
        try:
            with winreg.OpenKey(hive, key_path) as root:
                count = winreg.QueryInfoKey(root)[0]
                for index in range(count):
                    try:
                        child_name = winreg.EnumKey(root, index)
                        with winreg.OpenKey(root, child_name) as child:
                            name = _registry_string(winreg, child, "DisplayName")
                            if not name:
                                continue
                            version = _registry_string(winreg, child, "DisplayVersion")
                            location = _registry_string(winreg, child, "InstallLocation")
                            result.setdefault(name.casefold(), InstalledApp(name, version, location))
                    except OSError:
                        continue
        except OSError:
            continue
    return tuple(sorted(result.values(), key=lambda item: item.name.casefold()))


def _discover_one(
    spec: ToolSpec,
    *,
    which: Which,
    runner: ProbeRunner,
    env: Mapping[str, str],
    apps: Sequence[InstalledApp],
) -> ToolStatus:
    path = locate_executable(spec.aliases, which=which, env=env)
    app = _matching_app(spec, apps)
    version = _version(path, spec.version_args, runner) if path else None
    auth, auth_detail = _auth(spec, path, runner, env)
    return ToolStatus(
        id=spec.id,
        available=path is not None,
        path=path,
        required=spec.required,
        display_name=spec.display_name,
        version=version or (app.version if app else None),
        auth=auth,
        auth_detail=auth_detail,
        subscription_supported=spec.subscription_supported,
        api_key_configured=any(bool(env.get(name)) for name in spec.api_env),
        app_installed=app is not None,
        app_version=app.version if app else None,
    )


def _matching_app(spec: ToolSpec, apps: Sequence[InstalledApp]) -> InstalledApp | None:
    candidates = tuple(name.casefold() for name in spec.windows_app_names)
    if not candidates:
        return None
    for app in apps:
        name = app.name.casefold()
        if any(candidate in name for candidate in candidates):
            return app
    return None


def _version(path: str, args: Sequence[str], runner: ProbeRunner) -> str | None:
    code, stdout, stderr = runner((path, *args), 5.0)
    if code != 0:
        return None
    text = (stdout or stderr).strip().splitlines()
    return text[0][:160] if text else None


def _auth(
    spec: ToolSpec,
    path: str | None,
    runner: ProbeRunner,
    env: Mapping[str, str],
) -> AuthResult:
    if any(bool(env.get(name)) for name in spec.api_env):
        return "connected", "api-key-env"
    if not path:
        return "unavailable", None
    if spec.auth_args is None:
        return "unknown", "installed"
    code, stdout, stderr = runner((path, *spec.auth_args), 8.0)
    text = f"{stdout}\n{stderr}".strip()
    specialized = _specialized_auth(spec.id, code, text)
    if specialized is not None:
        return specialized
    return ("connected", "authenticated") if code == 0 else ("unknown", "probe-failed")


def _specialized_auth(tool_id: str, code: int, text: str) -> AuthResult | None:
    if tool_id == "codex":
        return _codex_auth(text)
    if tool_id == "opencode":
        return ("connected", "provider-auth") if code == 0 and text else (
            "not-connected",
            "login-required",
        )
    if tool_id == "cursor-agent":
        return _status_auth(code, "cursor-account")
    if tool_id == "gh":
        return _status_auth(code, "github-account")
    return None


def _codex_auth(text: str) -> AuthResult | None:
    normalized = text.casefold()
    states = (
        ("not logged in", ("not-connected", "login-required")),
        ("logged in using chatgpt", ("connected", "chatgpt")),
        ("logged in using an api key", ("connected", "api-key")),
        ("logged in using agent identity", ("connected", "agent-identity")),
    )
    for marker, result in states:
        if marker in normalized:
            return result
    return None


def _status_auth(code: int, detail: str) -> AuthResult:
    if code == 0:
        return "connected", detail
    return "not-connected", "login-required"


def _probe(argv: Sequence[str], timeout: float) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, "", ""
    return completed.returncode, completed.stdout, completed.stderr


def _registry_string(winreg: object, key: object, name: str) -> str | None:
    try:
        value, _ = winreg.QueryValueEx(key, name)  # type: ignore[attr-defined]
    except OSError:
        return None
    return str(value).strip() or None
