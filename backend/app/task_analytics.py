from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .codex_reader import codex_state_available, read_sessions_by_ids, read_sessions_for_path
from .models import (
    Alert,
    CodexSession,
    DailyTokenModelSegment,
    DailyTokenProjectDay,
    DailyTokenTaskDay,
    DailyTokenTaskSeries,
    DailyTokenUsageResponse,
    PlanLoadResult,
    TaskPlanResponse,
    TaskTokenSession,
    TaskTokenUsageItem,
    TaskTokenUsageResponse,
)
from .plan_parser import build_plan_alerts, calculate_progress
from .prd_reader import enrich_plan_with_prd_details
from .structured_models import StructuredProjectSnapshot
from .structured_service import snapshot_to_plan


def build_task_plan(
    project_id: str,
    plan: PlanLoadResult | None,
    project_path: str,
    snapshot: StructuredProjectSnapshot | None = None,
) -> TaskPlanResponse:
    if snapshot is not None:
        plan = snapshot_to_plan(snapshot)
    elif plan is None:
        plan = PlanLoadResult(milestones=[], missing=True)
    else:
        enrich_plan_with_prd_details(project_path, plan)
    return TaskPlanResponse(
        project_id=project_id,
        progress=calculate_progress(plan),
        milestones=plan.milestones,
        alerts=build_plan_alerts(plan),
    )


def build_task_token_usage(
    project_id: str,
    plan: PlanLoadResult | None,
    project_path: str,
    codex_db_path: Path,
    snapshot: StructuredProjectSnapshot | None = None,
) -> TaskTokenUsageResponse:
    if snapshot is not None:
        plan = snapshot_to_plan(snapshot)
    if plan is None:
        plan = PlanLoadResult(milestones=[], missing=True)
    alerts = build_plan_alerts(plan)
    tasks = [task for milestone in plan.milestones for task in milestone.tasks]
    if plan.missing or plan.invalid:
        return TaskTokenUsageResponse(project_id=project_id, tasks=[], alerts=alerts)

    session_ids_by_task = {task.id: set(task.codex_sessions) for task in tasks}
    task_count_by_session: dict[str, int] = {}
    for session_ids in session_ids_by_task.values():
        for session_id in session_ids:
            task_count_by_session[session_id] = task_count_by_session.get(session_id, 0) + 1

    unavailable = not codex_state_available(codex_db_path)
    project_sessions = read_sessions_for_path(project_path, db_path=codex_db_path) if not unavailable else []
    linked_session_ids = sorted(
        {
            session_id
            for task in tasks
            for session_id in task.codex_sessions
            if session_id
        }
    )
    session_by_id = {session.id: session for session in read_sessions_by_ids(linked_session_ids, db_path=codex_db_path)}

    response_tasks: list[TaskTokenUsageItem] = []
    token_totals: list[int] = []
    for task in tasks:
        item_alerts: list[Alert] = []
        missing_sessions: list[str] = []
        linked_sessions: list[TaskTokenSession] = []
        total_tokens = 0
        models: set[str] = set()
        model_providers: set[str] = set()
        input_tokens = 0
        cached_input_tokens = 0
        output_tokens = 0
        reasoning_output_tokens = 0
        has_breakdown = False
        any_shared = False

        if unavailable and task.codex_sessions:
            item = TaskTokenUsageItem(
                task_id=task.id,
                task_title=task.title,
                status=task.status,
                prd_refs=task.prd_refs,
                codex_sessions=task.codex_sessions,
                total_tokens=None,
                model_label="Token data unavailable",
                token_budget=task.token_budget,
                attribution="unavailable",
                sessions=[],
                missing_sessions=[],
                alerts=[],
            )
            response_tasks.append(item)
            continue

        for session_id in task.codex_sessions:
            session = session_by_id.get(session_id)
            if session is None:
                missing_sessions.append(session_id)
                linked_sessions.append(TaskTokenSession(id=session_id, source="codex_state_db", missing=True))
                continue
            shared = task_count_by_session.get(session_id, 0) > 1
            any_shared = any_shared or shared
            total_tokens += session.tokens_used
            if session.model:
                models.add(session.model)
            if session.model_provider:
                model_providers.add(session.model_provider)
            if session.input_tokens is not None:
                input_tokens += session.input_tokens
                has_breakdown = True
            if session.cached_input_tokens is not None:
                cached_input_tokens += session.cached_input_tokens
            if session.output_tokens is not None:
                output_tokens += session.output_tokens
            if session.reasoning_output_tokens is not None:
                reasoning_output_tokens += session.reasoning_output_tokens
            linked_sessions.append(
                TaskTokenSession(
                    id=session.id,
                    title=session.title,
                    model=session.model,
                    model_provider=session.model_provider,
                    updated_at_ms=session.updated_at_ms,
                    tokens=session.tokens_used,
                    input_tokens=session.input_tokens,
                    cached_input_tokens=session.cached_input_tokens,
                    output_tokens=session.output_tokens,
                    reasoning_output_tokens=session.reasoning_output_tokens,
                    token_snapshots=session.token_snapshots,
                    timezone=session.timezone,
                    source="codex_state_db",
                )
            )

        if missing_sessions:
            for session_id in missing_sessions:
                item_alerts.append(Alert(level="warning", message=f"Missing linked session {session_id} for task {task.id}."))

        if not task.codex_sessions:
            attribution = "none"
            item_total_tokens: int | None = 0
        elif any_shared:
            attribution = "shared"
            item_total_tokens = total_tokens
        else:
            attribution = "direct"
            item_total_tokens = total_tokens

        if item_total_tokens is not None:
            token_totals.append(item_total_tokens)

        ordered_models = sorted(models)
        ordered_providers = sorted(model_providers)
        if attribution == "none":
            model_label = "No model"
        elif len(ordered_models) == 0:
            if ordered_providers:
                provider_label = format_provider_label(ordered_providers[0]) if len(ordered_providers) == 1 else "Multiple providers"
                model_label = f"{provider_label} model"
            elif attribution == "unavailable":
                model_label = "Token data unavailable"
            else:
                model_label = "Unknown model"
        elif len(ordered_models) == 1:
            model_label = ordered_models[0]
        else:
            model_label = "Multiple models"

        if task.token_budget is not None and item_total_tokens is not None and item_total_tokens > task.token_budget:
            item_alerts.append(Alert(level="warning", message=f"Task {task.id} exceeded its token budget."))
            if item_total_tokens > task.token_budget * 2:
                item_alerts.append(Alert(level="error", message=f"Task {task.id} heavily exceeded its token budget."))

        response_tasks.append(
            TaskTokenUsageItem(
                task_id=task.id,
                task_title=task.title,
                status=task.status,
                prd_refs=task.prd_refs,
                codex_sessions=task.codex_sessions,
                total_tokens=item_total_tokens,
                model_label=model_label,
                models=ordered_models,
                model_providers=ordered_providers,
                input_tokens=input_tokens if has_breakdown else None,
                cached_input_tokens=cached_input_tokens if has_breakdown else None,
                output_tokens=output_tokens if has_breakdown else None,
                reasoning_output_tokens=reasoning_output_tokens if has_breakdown else None,
                token_budget=task.token_budget,
                attribution=attribution,
                sessions=linked_sessions,
                missing_sessions=missing_sessions,
                alerts=item_alerts,
            )
        )

    if unavailable:
        alerts.append(Alert(level="warning", message="Token data unavailable: Codex local state could not be read."))

    if any(task.attribution == "shared" for task in response_tasks):
        alerts.append(Alert(level="info", message="Some tasks use shared attribution because one Codex session is linked to multiple tasks."))

    if token_totals:
        threshold_index = max(0, int(len(sorted(token_totals)) * 0.8) - 1)
        high_token_threshold = sorted(token_totals)[threshold_index]
    else:
        high_token_threshold = None

    for task in response_tasks:
        for alert in task.alerts:
            alerts.append(alert)
        if task.missing_sessions:
            continue
        if high_token_threshold is not None and task.total_tokens is not None:
            if task.total_tokens >= high_token_threshold and task.status != "done":
                alerts.append(Alert(level="warning", message=f"Task {task.task_id} is a high-token incomplete task."))
                if not task.prd_refs:
                    alerts.append(
                        Alert(level="warning", message=f"Task {task.task_id} is high-token, incomplete, and missing a PRD association.")
                    )

    return TaskTokenUsageResponse(
        project_id=project_id,
        tasks=response_tasks,
        alerts=dedupe_alerts(alerts),
        daily_token_usage=build_daily_token_usage(response_tasks, project_sessions=project_sessions),
    )


def build_daily_token_usage(
    tasks: list[TaskTokenUsageItem],
    project_sessions: list[CodexSession] | None = None,
) -> DailyTokenUsageResponse:
    project_totals: dict[str, int] = {}
    project_model_totals: dict[str, dict[str, int]] = {}
    project_model_labels: dict[str, str] = {}
    task_series: list[DailyTokenTaskSeries] = []
    notes: list[str] = []
    has_partial_data = False
    has_task_links = any(task.codex_sessions for task in tasks)
    project_sessions_by_id: dict[str, TaskTokenSession] = {}

    for task in tasks:
        day_totals, task_partial = build_task_daily_series(task)
        has_partial_data = has_partial_data or task_partial
        task_series.append(build_daily_task_series(task, day_totals))

    if project_sessions is not None:
        for session in project_sessions:
            if not session.token_snapshots:
                continue
            project_sessions_by_id[session.id] = TaskTokenSession(
                id=session.id,
                title=session.title,
                model=session.model,
                model_provider=session.model_provider,
                updated_at_ms=session.updated_at_ms,
                tokens=session.tokens_used,
                input_tokens=session.input_tokens,
                cached_input_tokens=session.cached_input_tokens,
                output_tokens=session.output_tokens,
                reasoning_output_tokens=session.reasoning_output_tokens,
                token_snapshots=session.token_snapshots,
                timezone=session.timezone,
                source="codex_state_db",
            )
    if not project_sessions_by_id:
        for task in tasks:
            for session in task.sessions:
                if not session.missing and session.id not in project_sessions_by_id:
                    project_sessions_by_id[session.id] = session

    for session in project_sessions_by_id.values():
        daily_deltas = reconstruct_session_daily_tokens(session)
        if daily_deltas is None:
            has_partial_data = True
            continue
        model_key, model_label = model_identity(session)
        project_model_labels[model_key] = model_label
        for date, tokens in daily_deltas.items():
            project_totals[date] = project_totals.get(date, 0) + tokens
            day_models = project_model_totals.setdefault(date, {})
            day_models[model_key] = day_models.get(model_key, 0) + tokens

    if has_partial_data:
        notes.append("Some project session totals could not be reconstructed from cumulative snapshots into daily history.")
    if not has_task_links:
        notes.append("Task-based daily views require linked Codex sessions.")

    return DailyTokenUsageResponse(
        default_mode="project_total",
        project_days=[
            DailyTokenProjectDay(
                date=date,
                tokens=tokens,
                models=[
                    DailyTokenModelSegment(model_key=model_key, model_label=project_model_labels[model_key], tokens=model_tokens)
                    for model_key, model_tokens in sorted(
                        project_model_totals.get(date, {}).items(),
                        key=lambda item: (-item[1], project_model_labels[item[0]].lower(), item[0]),
                    )
                ],
            )
            for date, tokens in sorted(project_totals.items())
        ],
        tasks=task_series,
        notes=notes,
        has_partial_data=has_partial_data,
        has_task_links=has_task_links,
    )


def day_key(updated_at_ms: int | None, timezone: str | None = None) -> str | None:
    if updated_at_ms is None:
        return None
    timestamp = datetime.fromtimestamp(updated_at_ms / 1000, tz=UTC)
    if timezone:
        try:
            timestamp = timestamp.astimezone(ZoneInfo(timezone))
        except ZoneInfoNotFoundError:
            pass
    return timestamp.date().isoformat()


def reconstruct_session_daily_tokens(session: TaskTokenSession) -> dict[str, int] | None:
    if not session.token_snapshots:
        return None

    ordered_snapshots = sorted(session.token_snapshots, key=lambda snapshot: snapshot.timestamp_ms)
    previous_total = 0
    day_totals: dict[str, int] = {}
    for snapshot in ordered_snapshots:
        date = day_key(snapshot.timestamp_ms, session.timezone)
        if date is None:
            return None
        delta = snapshot.total_tokens - previous_total
        if delta < 0:
            return None
        if delta:
            day_totals[date] = day_totals.get(date, 0) + delta
        previous_total = snapshot.total_tokens

    if session.tokens is not None and previous_total != session.tokens:
        return None
    return day_totals


def build_task_daily_series(task: TaskTokenUsageItem) -> tuple[dict[str, int], bool]:
    day_totals: dict[str, int] = {}
    has_partial_data = False
    for session in task.sessions:
        if session.missing:
            continue
        daily_deltas = reconstruct_session_daily_tokens(session)
        if daily_deltas is None:
            has_partial_data = True
            continue
        for date, tokens in daily_deltas.items():
            day_totals[date] = day_totals.get(date, 0) + tokens
    return day_totals, has_partial_data


def build_daily_task_series(task: TaskTokenUsageItem, day_totals: dict[str, int]) -> DailyTokenTaskSeries:
    return DailyTokenTaskSeries(
        task_id=task.task_id,
        task_title=task.task_title,
        status=task.status,
        attribution=task.attribution,
        days=[
            DailyTokenTaskDay(date=date, tokens=tokens, attribution=task.attribution)
            for date, tokens in sorted(day_totals.items())
        ],
    )


def model_identity(session: TaskTokenSession) -> tuple[str, str]:
    if session.model:
        return session.model.lower(), session.model
    if session.model_provider:
        label = f"{format_provider_label(session.model_provider)} model"
        return session.model_provider.lower(), label
    return "unknown-model", "Unknown model"


def dedupe_alerts(alerts: list[Alert]) -> list[Alert]:
    seen: set[tuple[str, str]] = set()
    deduped: list[Alert] = []
    for alert in alerts:
        key = (alert.level, alert.message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(alert)
    return deduped


def format_provider_label(provider: str) -> str:
    aliases = {
        "openai": "OpenAI",
    }
    return aliases.get(provider.lower(), provider.title())
