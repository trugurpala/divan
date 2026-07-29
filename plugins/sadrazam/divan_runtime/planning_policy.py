"""Explainable risk, model-class, and workstream policy for Nizam-i Sefer."""

from __future__ import annotations

from typing import Any

TARGET_WEIGHTS = {"verified": 0, "previewed": 1, "released": 2, "observed": 3}
MODEL_POLICY = {
    "low": ("economy", "low", "gpt-5.6-luna"),
    "moderate": ("balanced", "medium", "gpt-5.6-terra"),
    "high": ("frontier", "high", "gpt-5.6-sol"),
    "critical": ("frontier", "max", "gpt-5.6-sol"),
}
HIGH_RISK_WORKFLOWS = {
    "deployment-delivery",
    "release-delivery",
    "security-delivery",
}
MODERATE_RISK_WORKFLOWS = {"integration-delivery"}
HIGH_RISK_TERMS = {
    "credential",
    "financial",
    "payment",
    "production",
    "secret",
}
CRITICAL_RISK_TERMS = {
    "delete production",
    "destructive",
    "production data",
    "rotate leaked",
}
LEVEL_ORDER = {"low": 0, "moderate": 1, "high": 2, "critical": 3}


def _floor(level: str, minimum: str) -> str:
    return minimum if LEVEL_ORDER[level] < LEVEL_ORDER[minimum] else level


def complexity(route: dict[str, Any], target: str) -> dict[str, Any]:
    """Classify structural risk and apply fail-safe production/security floors."""
    workflows = route["workflows"]
    roles = route["roles"]
    workspaces = route["workspaces"]
    providers = route["providers"]
    high_workflows = sorted(set(workflows) & HIGH_RISK_WORKFLOWS)
    moderate_workflows = sorted(set(workflows) & MODERATE_RISK_WORKFLOWS)
    intent = route["intent"].casefold()
    high_terms = sorted(term for term in HIGH_RISK_TERMS if term in intent)
    critical_terms = sorted(term for term in CRITICAL_RISK_TERMS if term in intent)
    conflicts = len(route["package_manager_conflicts"])
    score = (
        1
        + max(0, len(workflows) - 1) * 2
        + min(3, len(roles) // 3)
        + min(3, max(0, len(workspaces) - 1))
        + len(providers)
        + len(high_workflows) * 2
        + len(moderate_workflows)
        + conflicts * 2
        + TARGET_WEIGHTS[target]
    )
    level = "low" if score <= 5 else "moderate" if score <= 9 else "high"
    if score > 14:
        level = "critical"
    if moderate_workflows:
        level = _floor(level, "moderate")
    if high_workflows or high_terms or conflicts or target in {"released", "observed"}:
        level = _floor(level, "high")
    if critical_terms:
        level = "critical"
    working_set = (
        3_000
        + sum(len(row["stages"]) for row in route["workflow_contracts"]) * 800
        + len(roles) * 500
        + len(workflows) * 700
        + len(route["required_evidence"]) * 350
        + len(route["commands"]) * 250
        + len(workspaces) * 500
    )
    return {
        "level": level,
        "score": score,
        "estimated_working_set_tokens": working_set,
        "signals": {
            "workflow_count": len(workflows),
            "role_count": len(roles),
            "workspace_count": len(workspaces),
            "provider_count": len(providers),
            "high_risk_workflows": high_workflows,
            "moderate_risk_workflows": moderate_workflows,
            "high_risk_terms": high_terms,
            "critical_risk_terms": critical_terms,
            "package_manager_conflicts": conflicts,
            "target": target,
        },
    }


def model_policy(level: str, host_id: str) -> dict[str, Any]:
    """Recommend a portable capability class; exact Codex model stays a candidate."""
    capability, effort, codex_candidate = MODEL_POLICY[level]
    candidate = None
    if host_id == "codex":
        candidate = {
            "model": codex_candidate,
            "status": "candidate",
            "availability": "host-confirmation-required",
            "evidence_source": "official-openai-model-guide-2026-07-29",
        }
    return {
        "capability_class": capability,
        "reasoning_effort": effort,
        "selection": "risk-based",
        "host_candidate": candidate,
        "fallback": "host-selects-an-available-equivalent",
    }


def workstreams(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose dependency-ready workflow lanes that join at integrated verification."""
    workflows = list(
        dict.fromkeys(
            task["workflow"]
            for task in tasks
            if task["workflow"] != "integrated-delivery"
        )
    )
    return [
        {
            "id": f"workstream-{index + 1:03d}",
            "workflow": workflow,
            "task_ids": [
                task["id"] for task in tasks if task["workflow"] == workflow
            ],
            "parallel_ready": True,
        }
        for index, workflow in enumerate(workflows)
    ]
