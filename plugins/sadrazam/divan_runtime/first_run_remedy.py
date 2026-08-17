"""What can be done about a capability that is not ready, and by whom.

The first-run wizard already promised that Divan would try to prepare a missing
dependency itself. Nothing kept that promise: the renderer looked for a hint the
Core never sent, so every degraded step fell back to the same sentence.

The line this module draws is the important part. A missing tool is Divan's job:
it is fetched from the vendor's own official channel, by name, with the command
written down so the owner can read it afterwards. A missing credential is the
owner's job and only the owner's. Divan does not type a password, does not carry
a token, does not read a browser's stored session, and does not look for a
credential anywhere on the machine. It says which application to sign in to and
stops there.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Capabilities Divan may prepare on its own, and the official command for each.
#: A command appears here only if it comes from the vendor's own distribution
#: channel; nothing is fetched from a mirror, an archive or a URL.
PREPARATION_COMMANDS: dict[str, tuple[str, ...]] = {
    "git": ("winget", "install", "--exact", "--id", "Git.Git"),
    "codex": ("npm", "install", "--global", "@openai/codex"),
    "claude": ("npm", "install", "--global", "@anthropic-ai/claude-code"),
    "browser-qa": ("npx", "playwright", "install", "chromium"),
}

#: Reason codes that mean a person has to sign in. No command can close these,
#: and offering one would be an invitation to bypass the provider's own flow.
OWNER_ONLY_CODES: frozenset[str] = frozenset(
    {
        "AUTH_REQUIRED",
        "AUTH_NOT_VERIFIED",
        "LOGIN_REQUIRED",
        "CREDENTIAL_REQUIRED",
        "SESSION_EXPIRED",
    }
)

#: What the owner is asked to do, per capability, when a credential is missing.
OWNER_ACTIONS: dict[str, str] = {
    "codex": "Codex uygulamasında oturum açın.",
    "claude": "Claude Code uygulamasında oturum açın.",
}


class RemedyKind(StrEnum):
    DIVAN_PREPARES = "divan-prepares"
    OWNER_ACTION = "owner-action"
    NOTHING_TO_DO = "nothing-to-do"
    OUT_OF_REACH = "out-of-reach"


@dataclass(frozen=True)
class Remedy:
    """One sentence for the owner, and the command behind it if there is one."""

    kind: RemedyKind
    sentence: str
    command: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind is RemedyKind.OWNER_ACTION and self.command:
            raise ValueError("an owner action must not carry a command to run for them")
        if self.kind is RemedyKind.DIVAN_PREPARES and not self.command:
            raise ValueError("Divan cannot prepare something without a command")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": self.kind.value,
            "sentence": self.sentence,
            "command": list(self.command),
        }


def remedy_for(
    capability_id: str, state: str, code: str | None, version: str | None = None
) -> Remedy:
    """Decide who closes this, reading what the Core actually reported.

    A capability that reports a version is installed, so it never gets an
    install command however its reason code reads. Reinstalling something that
    is already there is not a remedy, and offering it would send the owner to
    do work that cannot help.
    """
    if state.casefold() == "certified":
        return Remedy(RemedyKind.NOTHING_TO_DO, "Hazır.")

    installed = bool(version and version.strip())
    if code and code.upper() in OWNER_ONLY_CODES:
        if capability_id in OWNER_ACTIONS:
            return Remedy(RemedyKind.OWNER_ACTION, OWNER_ACTIONS[capability_id])
        if installed:
            # Installed, and signing in is not a thing this capability does.
            return Remedy(
                RemedyKind.OUT_OF_REACH,
                "Kurulu görünüyor; Divan bunun ötesini kendisi doğrulayamıyor.",
            )

    command = PREPARATION_COMMANDS.get(capability_id)
    if command and not installed:
        return Remedy(
            RemedyKind.DIVAN_PREPARES,
            "Divan bunu kendisi hazırlayacak.",
            command,
        )
    if command and installed:
        return Remedy(
            RemedyKind.OUT_OF_REACH,
            "Kurulu; eksik olan kurulum değil, ayrıntı teknik görünümde.",
        )

    if state.casefold() == "blocked":
        return Remedy(
            RemedyKind.OUT_OF_REACH,
            "Bu, Windows politikası nedeniyle engelli; Divan bunu kendisi açamaz.",
        )
    return Remedy(
        RemedyKind.OUT_OF_REACH,
        "Bunu Divan kendisi hazırlayamaz; ayrıntıyı teknik görünümde bulabilirsiniz.",
    )


def annotate(payload: dict[str, object]) -> dict[str, object]:
    """Add the remedy to one capability payload, leaving everything else alone."""
    def text(key: str) -> str | None:
        value = payload.get(key)
        return value if isinstance(value, str) else None

    remedy = remedy_for(
        str(payload.get("capability_id", "")),
        str(payload.get("state", "")),
        text("code"),
        text("version"),
    )
    annotated = dict(payload)
    annotated["remedy"] = remedy.to_dict()
    # The wizard reads action_hint for the sentence it shows; keep it filled so
    # the renderer needs no knowledge of how the sentence was chosen.
    annotated["action_hint"] = remedy.sentence
    return annotated


def annotate_report(payload: dict[str, object]) -> dict[str, object]:
    """Add a remedy to every capability in a doctor payload."""
    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, list):
        return payload
    annotated = dict(payload)
    annotated["capabilities"] = [
        annotate(item) if isinstance(item, dict) else item for item in capabilities
    ]
    return annotated
