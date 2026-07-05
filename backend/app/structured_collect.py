from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .plan_parser import load_plan
from .prd_reader import derive_task_details, split_prd_ref
from .structured_models import (
    FieldState,
    SourceRef,
    StructuredFieldValue,
    StructuredMilestone,
    StructuredProjectSnapshot,
    StructuredTask,
)


def collect_project_snapshot(project_path: Path, project_id: str) -> StructuredProjectSnapshot:
    plan = load_plan(str(project_path))
    collected_at = datetime.now(timezone.utc).isoformat()
    warnings = list(plan.warnings)

    if plan.missing:
        warnings.append("agentpm.yaml is missing; structured snapshot contains no task rows.")
        return StructuredProjectSnapshot(project_id=project_id, collected_at=collected_at, status="missing_plan", warnings=warnings)
    if plan.invalid:
        warnings.append("agentpm.yaml has invalid task data; structured snapshot may be incomplete.")

    plans_ref = project_path / "PLANS.md"
    plan_refs = ["PLANS.md"] if plans_ref.exists() else []
    cache: dict[str, tuple[str, list[str]]] = {}

    milestones: list[StructuredMilestone] = []
    for milestone in plan.milestones:
        structured_tasks: list[StructuredTask] = []
        for task in milestone.tasks:
            collection_refs = [*task.prd_refs, *plan_refs]
            structured_tasks.append(
                StructuredTask(
                    task_key=task.id,
                    title=task.title,
                    status=task.status,
                    milestone_id=milestone.id,
                    milestone_title=milestone.title,
                    user_story=build_field_value(
                        project_path=project_path,
                        task_key=task.id,
                        field_name="user_story",
                        explicit_value=task.user_story,
                        refs=collection_refs,
                        cache=cache,
                    ),
                    scope=build_field_value(
                        project_path=project_path,
                        task_key=task.id,
                        field_name="scope",
                        explicit_value=task.scope,
                        refs=collection_refs,
                        cache=cache,
                    ),
                    acceptance_criteria=build_field_value(
                        project_path=project_path,
                        task_key=task.id,
                        field_name="acceptance_criteria",
                        explicit_value=task.acceptance_criteria,
                        refs=collection_refs,
                        cache=cache,
                    ),
                    verification_method=build_field_value(
                        project_path=project_path,
                        task_key=task.id,
                        field_name="verification_method",
                        explicit_value=task.verification_method,
                        refs=collection_refs,
                        cache=cache,
                    ),
                    prd_refs=task.prd_refs,
                    codex_sessions=task.codex_sessions,
                    token_budget=task.token_budget,
                )
            )
        milestones.append(StructuredMilestone(milestone_id=milestone.id, title=milestone.title, tasks=structured_tasks))

    return StructuredProjectSnapshot(project_id=project_id, collected_at=collected_at, status="complete", warnings=warnings, milestones=milestones)


def build_field_value(
    *,
    project_path: Path,
    task_key: str,
    field_name: str,
    explicit_value: str | None,
    refs: list[str],
    cache: dict[str, tuple[str, list[str]]],
) -> StructuredFieldValue:
    if explicit_value:
        return StructuredFieldValue(
            value=explicit_value,
            state=FieldState.explicit,
            source=SourceRef(source_type="agentpm.yaml", path_or_id="agentpm.yaml", locator=f"tasks.{task_key}.{field_name}"),
            confidence=1.0,
        )

    for ref in refs:
        derived = derive_task_details(str(project_path), [ref], cache=cache)
        value = derived.get(field_name)
        if not value:
            continue
        ref_path, anchor = split_prd_ref(ref)
        source_type = "plans.md" if ref_path.upper() == "PLANS.MD" else "prd"
        state = FieldState.needs_review if source_type == "plans.md" else FieldState.inferred
        confidence = 0.6 if source_type == "plans.md" else 0.8
        locator = anchor or field_name
        return StructuredFieldValue(
            value=value,
            state=state,
            source=SourceRef(source_type=source_type, path_or_id=ref_path, locator=locator),
            confidence=confidence,
        )

    return StructuredFieldValue(
        value=None,
        state=FieldState.missing,
        source=None,
        confidence=None,
    )
