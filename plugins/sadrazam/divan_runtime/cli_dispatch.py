"""Focused command dispatch helpers for the portable Divan CLI."""
from __future__ import annotations

import argparse
import hashlib
import pathlib
from typing import Any, Callable

from . import (
    adoption,
    adoption_proof,
    engine,
    engine_registry,
    goal_archive,
    goal_execution,
    goals,
    governance,
    kernel,
    orca_coordinator,
    project_lifecycle,
    seyir_state,
)

DIRECTORY = pathlib.Path(__file__).resolve().parent


def read_only_result(options: argparse.Namespace) -> dict[str, Any] | None:
    if options.command == "inspect":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.inspect_project(options.project, contracts)
    if options.command == "plan":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.plan_intent(
            options.intent,
            options.project,
            contracts,
            options.target,
            host_profile=options.host_profile,
            context_window=options.context_window,
        )
    if options.command == "impact":
        contracts = engine.load_contracts(DIRECTORY)
        return engine.calculate_impact(options.paths, contracts)
    if options.command == "architecture":
        return kernel.load_architecture(DIRECTORY)
    if options.command == "engines":
        if options.engines_command == "validate":
            result, exit_code = engine_registry.validate_registry_path(
                options.registry
            )
            return {**result, "_exit_code": exit_code}
        if options.engines_command == "status":
            return orca_coordinator.status()
    return None


def mutation_authority(options: argparse.Namespace) -> dict[str, Any] | None:
    if not getattr(options, "execute", False):
        return None
    excluded = {"actor", "execute", "json", "lang", "prompt"}
    scope = {
        key: str(value) if isinstance(value, pathlib.Path) else value
        for key, value in vars(options).items()
        if key not in excluded and value is not None
    }
    prompt = getattr(options, "prompt", None)
    if prompt is not None:
        scope["prompt_sha256"] = hashlib.sha256(
            str(prompt).encode("utf-8")
        ).hexdigest()
    operation = ".".join(
        str(value)
        for value in (
            options.command,
            getattr(options, "project_command", None),
            getattr(options, "goal_command", None),
            getattr(options, "engines_command", None),
        )
        if value is not None
    )
    return governance.authorize_mutation(
        options.actor,
        operation,
        scope,
        explicit_authority=True,
        directory=DIRECTORY,
    )


def execute_project(options: argparse.Namespace) -> dict[str, Any]:
    if options.project_command == "status":
        return project_lifecycle.project_status(options.project)
    if options.project_command == "update":
        plan = project_lifecycle.build_update_plan(options.project)
        return (
            project_lifecycle.apply_update_plan(plan)
            if options.execute and plan.get("status") == "PLANNED"
            else plan
        )
    plan = project_lifecycle.build_repair_plan(options.project)
    return (
        project_lifecycle.apply_repair_plan(plan)
        if options.execute and plan.get("status") == "PLANNED"
        else plan
    )


def execute_goal(options: argparse.Namespace) -> dict[str, Any]:
    if options.goal_command == "start":
        return goals.start_goal(
            options.project,
            options.intent,
            options.target,
            options.execute,
            host_profile=options.host_profile,
            context_window=options.context_window,
        )
    if options.goal_command == "status":
        return goals.goal_status(options.project, options.goal)
    if options.goal_command == "prepare":
        return goal_execution.prepare_goal(
            options.project,
            options.goal,
            execute=options.execute,
        )
    if options.goal_command == "progress":
        return seyir_state.update(
            options.project,
            options.goal,
            completed_task_ids=options.completed,
            current_task_id=options.current,
            next_task_id=options.next_task,
            execute=options.execute,
        )
    if options.goal_command == "advance":
        return seyir_state.advance_goal(
            options.project,
            options.goal,
            options.to,
            options.execute,
            reason=options.reason,
            evidence=options.evidence,
        )
    if options.goal_command == "archive":
        plan = goal_archive.build_archive_plan(
            options.project, options.goal, options.recorded_on
        )
        return (
            goal_archive.apply_archive_plan(plan)
            if options.execute and plan.get("status") == "PLANNED"
            else plan
        )
    return goals.resume_goal(options.project, options.goal, options.execute)


def execute_engines(
    options: argparse.Namespace,
    authority: dict[str, Any] | None,
) -> dict[str, Any]:
    if options.engines_command != "worktree-create":
        raise ValueError(f"unsupported engine command: {options.engines_command}")
    return orca_coordinator.create_worktree(
        options.project,
        options.goal,
        name=options.name,
        actor_id=options.actor,
        execute=options.execute,
        repo_selector=options.repo_selector,
        agent=options.agent,
        prompt=options.prompt,
        setup=options.setup,
        mandate=authority,
    )


def execute_adoption(
    options: argparse.Namespace,
    preview_renderer: Callable[[dict[str, Any], str, str], dict[str, Any]],
) -> dict[str, Any]:
    if options.adoption_command == "verify":
        return adoption.verify_adoption(options.path)
    if options.adoption_command == "prove":
        plan = adoption_proof.build_proof_plan(
            options.project, options.goal, options.host, options.operator_role
        )
        if options.execute:
            return {
                "kind": "adoption-proof-result",
                **adoption_proof.execute_proof(plan),
            }
        return preview_renderer(plan, options.host, options.operator_role)
    return adoption.export_adoption(
        options.project,
        options.goal,
        options.host,
        options.host_version,
        options.submitter,
    )
