from pathlib import Path

from .codex_reader import DEFAULT_CODEX_STATE_DB, codex_state_available, read_sessions_by_ids, read_sessions_for_path, summarize_tokens
from .database import APP_DB, connect, init_db
from .git_reader import read_git_state
from .models import BriefingResponse, BriefingText, Project, TestState, TokenSummary
from .plan_parser import calculate_progress, load_plan
from .status_rules import build_alerts, calculate_status
from .task_analytics import build_task_plan, build_task_token_usage
from .structured_service import load_project_snapshot, snapshot_to_plan


def build_briefing(
    project: Project,
    codex_db_path: Path = DEFAULT_CODEX_STATE_DB,
    app_db_path: Path = APP_DB,
) -> BriefingResponse:
    structured_snapshot = None
    with connect(app_db_path) as conn:
        init_db(conn)
        structured_snapshot = load_project_snapshot(conn, project.id)
    plan = snapshot_to_plan(structured_snapshot) if structured_snapshot is not None else load_plan(project.path)
    progress = calculate_progress(plan)
    sessions = read_sessions_for_path(project.path, db_path=codex_db_path)
    tokens = token_summary_for_project(project, codex_db_path=codex_db_path, plan=plan, sessions=sessions)
    git = read_git_state(project.path)
    test = TestState(status="unknown", confidence="low")
    status = calculate_status(plan=plan, progress=progress, sessions=sessions, git=git, test=test)
    alerts = build_alerts(plan=plan, progress=progress, sessions=sessions, tokens=tokens, git=git, test=test)
    task_plan = build_task_plan(project.id, plan, project.path, snapshot=structured_snapshot)
    task_token_usage = build_task_token_usage(project.id, plan, project.path, codex_db_path, snapshot=structured_snapshot)
    alerts.extend(task_plan.alerts)
    alerts.extend(task_token_usage.alerts)

    if progress.total is None:
        summary = f"{project.name} has no usable plan data yet."
    else:
        summary = f"{project.name} is {progress.percent}% complete with {progress.done}/{progress.total} tasks done."

    next_action_by_status = {
        "missing_plan": "Create or fix agentpm.yaml with milestones and tasks.",
        "blocked": "Resolve the blocked task before starting new work.",
        "tests_failing": "Run or inspect the relevant test suite before continuing feature work.",
        "active": "Review the current dirty files or latest Codex session and continue the active task.",
        "idle": "Review the plan and choose the next todo task.",
        "unknown": "Check local Codex, Git, and plan availability.",
    }

    return BriefingResponse(
        project=project,
        progress=progress,
        briefing=BriefingText(status=status, summary=summary, next_action=next_action_by_status[status]),
        tokens=tokens,
        git=git,
        test=test,
        sessions=sessions,
        alerts=alerts,
        task_plan=task_plan,
        task_token_usage=task_token_usage,
        daily_token_usage=task_token_usage.daily_token_usage,
    )


def token_summary_for_project(
    project: Project,
    codex_db_path: Path = DEFAULT_CODEX_STATE_DB,
    plan=None,
    sessions=None,
) -> TokenSummary:
    project_sessions = sessions if sessions is not None else read_sessions_for_path(project.path, db_path=codex_db_path)
    if project_sessions:
        return summarize_tokens(project_sessions, unavailable=not codex_state_available(codex_db_path))
    if plan is None:
        plan = load_plan(project.path)
    linked_ids = [
        session_id
        for milestone in plan.milestones
        for task in milestone.tasks
        for session_id in task.codex_sessions
    ]
    if linked_ids:
        linked_sessions = read_sessions_by_ids(linked_ids, db_path=codex_db_path)
        if linked_sessions:
            return summarize_tokens(linked_sessions, unavailable=False)
    return summarize_tokens(project_sessions, unavailable=not codex_state_available(codex_db_path))
