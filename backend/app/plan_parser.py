from pathlib import Path
from typing import Any

import yaml

from .models import Alert, Milestone, PlanLoadResult, ProgressSummary, TaskItem

VALID_STATUSES = {"todo", "doing", "done", "blocked"}


def load_plan(project_path: str) -> PlanLoadResult:
    plan_path = Path(project_path) / "agentpm.yaml"
    if not plan_path.exists():
        return PlanLoadResult(milestones=[], missing=True)
    try:
        data = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return PlanLoadResult(milestones=[], invalid=True, warnings=["agentpm.yaml could not be parsed"])
    if not isinstance(data, dict):
        return PlanLoadResult(milestones=[], invalid=True, warnings=["agentpm.yaml must contain a mapping"])
    return parse_plan_data(data)


def parse_plan_data(data: dict[str, Any]) -> PlanLoadResult:
    milestones: list[Milestone] = []
    warnings: list[str] = []
    seen_task_ids: set[str] = set()
    duplicate_task_ids: set[str] = set()
    raw_milestones = data.get("milestones", [])
    if not isinstance(raw_milestones, list):
        return PlanLoadResult(milestones=[], invalid=True, warnings=["milestones must be a list"])

    for milestone_index, milestone in enumerate(raw_milestones):
        if not isinstance(milestone, dict):
            warnings.append(f"Skipped invalid milestone at index {milestone_index}")
            continue
        tasks: list[TaskItem] = []
        raw_tasks = milestone.get("tasks", [])
        if not isinstance(raw_tasks, list):
            warnings.append(f"Milestone {milestone.get('id', milestone_index)} tasks must be a list")
            raw_tasks = []
        for task_index, task in enumerate(raw_tasks):
            if not isinstance(task, dict):
                warnings.append(f"Skipped invalid task at index {task_index}")
                continue
            task_id = str(task.get("id", f"task-{task_index}"))
            if task_id in seen_task_ids:
                duplicate_task_ids.add(task_id)
                warnings.append(f"Duplicate task id: {task_id}")
            seen_task_ids.add(task_id)
            status = str(task.get("status", "todo"))
            if status not in VALID_STATUSES:
                warnings.append(f"Unknown task status for {task_id}: {status}")
                status = "todo"
            tasks.append(
                TaskItem(
                    id=task_id,
                    title=str(task.get("title", task_id)),
                    status=status,
                    assignee=optional_str(task.get("assignee")),
                    created_at=optional_str(task.get("created_at")),
                    updated_at=optional_str(task.get("updated_at")),
                    session_note=optional_str(task.get("session_note")),
                    user_story=optional_str(task.get("user_story")),
                    scope=optional_str(task.get("scope")),
                    acceptance_criteria=optional_str(task.get("acceptance_criteria")),
                    verification_method=optional_str(task.get("verification_method")),
                    prd_refs=string_list(task.get("prd_refs", [])),
                    codex_sessions=string_list(task.get("codex_sessions", [])),
                    token_budget=optional_int(task.get("token_budget")),
                )
            )
        milestone_id = str(milestone.get("id", f"milestone-{milestone_index}"))
        milestone_result = Milestone(id=milestone_id, title=str(milestone.get("title", milestone_id)), tasks=tasks)
        milestone_result.progress = calculate_milestone_progress(milestone_result)
        milestones.append(milestone_result)
    return PlanLoadResult(milestones=milestones, invalid=bool(duplicate_task_ids), warnings=warnings)


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    parsed = str(value).strip()
    return parsed or None


def calculate_progress(plan: PlanLoadResult) -> ProgressSummary:
    if plan.missing or plan.invalid:
        return ProgressSummary(done=None, total=None, blocked=None, percent=None)
    tasks = [task for milestone in plan.milestones for task in milestone.tasks]
    total = len(tasks)
    done = len([task for task in tasks if task.status == "done"])
    blocked = len([task for task in tasks if task.status == "blocked"])
    percent = 0 if total == 0 else round(done / total * 100)
    return ProgressSummary(done=done, total=total, blocked=blocked, percent=percent)


def calculate_milestone_progress(milestone: Milestone) -> ProgressSummary:
    total = len(milestone.tasks)
    done = len([task for task in milestone.tasks if task.status == "done"])
    blocked = len([task for task in milestone.tasks if task.status == "blocked"])
    percent = 0 if total == 0 else round(done / total * 100)
    return ProgressSummary(done=done, total=total, blocked=blocked, percent=percent)


def build_plan_alerts(plan: PlanLoadResult) -> list[Alert]:
    alerts: list[Alert] = []
    if plan.missing:
        return [Alert(level="warning", message="Plan unavailable: agentpm.yaml is missing.")]
    if plan.invalid:
        alerts.append(Alert(level="warning", message="Plan unavailable: agentpm.yaml has invalid task data."))
    for warning in plan.warnings:
        alerts.append(Alert(level="warning", message=warning))
    for milestone in plan.milestones:
        for task in milestone.tasks:
            if not task.prd_refs:
                alerts.append(Alert(level="info", message=f"Task {task.id} has no PRD association."))
    linked_sessions = [
        session_id
        for milestone in plan.milestones
        for task in milestone.tasks
        for session_id in task.codex_sessions
    ]
    task_count = sum(len(milestone.tasks) for milestone in plan.milestones)
    if task_count and not linked_sessions:
        alerts.append(Alert(level="info", message="No task session links found in agentpm.yaml."))
    return alerts
