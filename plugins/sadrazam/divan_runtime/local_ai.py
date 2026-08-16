"""Bounded local Ollama adapter for Ottoman's offline workbench."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:8b"
MAX_PROMPT_CHARS = 12_000


@dataclass(frozen=True)
class LocalAiStatus:
    available: bool
    endpoint: str
    default_model: str
    models: tuple[dict[str, str], ...]
    message: str | None = None


def status() -> dict[str, Any]:
    """Return a redacted local-only model inventory without starting a model."""
    try:
        payload = _request("/api/tags", method="GET", timeout=3.0)
    except (OSError, URLError, ValueError) as error:
        return asdict(
            LocalAiStatus(
                available=False,
                endpoint=OLLAMA_URL,
                default_model=DEFAULT_MODEL,
                models=(),
                message=str(error)[:180],
            )
        )
    raw_models = payload.get("models") if isinstance(payload, dict) else None
    models: list[dict[str, str]] = []
    if isinstance(raw_models, list):
        for item in raw_models[:100]:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            models.append(
                {
                    "name": item["name"],
                    "size": str(item.get("size", "")),
                    "modified_at": str(item.get("modified_at", "")),
                }
            )
    return asdict(
        LocalAiStatus(
            available=True,
            endpoint=OLLAMA_URL,
            default_model=DEFAULT_MODEL,
            models=tuple(models),
        )
    )


def draft(prompt: str, *, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Ask the locally running model for a non-executing Ottoman work draft."""
    text = prompt.strip()
    if not text:
        raise ValueError("local AI prompt is required")
    if len(text) > MAX_PROMPT_CHARS:
        raise ValueError(f"local AI prompt exceeds {MAX_PROMPT_CHARS} characters")
    selected_model = model.strip() or DEFAULT_MODEL
    if len(selected_model) > 160:
        raise ValueError("local AI model name is too long")
    payload = _request(
        "/api/chat",
        method="POST",
        timeout=120.0,
        body={
            "model": selected_model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Ottoman's local planning assistant. Produce a concise "
                        "implementation draft only. Do not claim code was run, do not issue "
                        "shell commands, and do not request secrets."
                    ),
                },
                {"role": "user", "content": text},
            ],
        },
    )
    message = payload.get("message") if isinstance(payload, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("local AI returned no draft")
    return {"model": selected_model, "draft": content.strip(), "executed": False}


def _request(
    path: str,
    *,
    method: str,
    timeout: float,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        f"{OLLAMA_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed loopback URL
        decoded = json.loads(response.read().decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("local AI response must be an object")
    return decoded
