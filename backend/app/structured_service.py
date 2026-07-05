from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Milestone, PlanLoadResult, Project, TaskItem
from .plan_parser import calculate_milestone_progress
from .structured_collect import collect_project_snapshot
from .structured_models import StructuredProjectSnapshot
from .structured_store import load_latest_snapshot, save_snapshot


def refresh_project_snapshot(conn: sqlite3.Connection, project: Project) -> StructuredProjectSnapshot:
    snapshot = collect_project_snapshot(Path(project.path), project.id)
    save_snapshot(conn, snapshot)
    return snapshot


def load_project_snapshot(conn: sqlite3.Connection, project_id: str) -> StructuredProjectSnapshot | None:
    return load_latest_snapshot(conn, project_id)


def snapshot_to_plan(snapshot: StructuredProjectSnapshot) -> PlanLoadResult:
    milestones: list[Milestone] = []
    for milestone in snapshot.milestones:
        tasks: list[TaskItem] = []
        for task in milestone.tasks:
            tasks.append(
                TaskItem(
                    id=task.task_key,
                    title=task.title,
                    status=task.status,
                    user_story=task.user_story.value,
                    scope=task.scope.value,
                    acceptance_criteria=task.acceptance_criteria.value,
                    verification_method=task.verification_method.value,
                    prd_refs=task.prd_refs,
                    codex_sessions=task.codex_sessions,
                    token_budget=task.token_budget,
                )
            )
        milestone_plan = Milestone(id=milestone.milestone_id, title=milestone.title, tasks=tasks)
        milestone_plan.progress = calculate_milestone_progress(milestone_plan)
        milestones.append(milestone_plan)

    return PlanLoadResult(milestones=milestones, warnings=snapshot.warnings)
