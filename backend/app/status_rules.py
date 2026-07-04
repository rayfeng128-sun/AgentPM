from datetime import datetime, timezone

from .models import Alert, CodexSession, GitState, PlanLoadResult, ProgressSummary, TestState, TokenSummary

RECENT_ACTIVITY_HOURS = 48
IDLE_THRESHOLD_DAYS = 7


def is_recent_session(sessions: list[CodexSession], now_ms: int | None = None) -> bool:
    updated_values = [session.updated_at_ms for session in sessions if session.updated_at_ms is not None]
    if not updated_values:
        return False
    latest = max(updated_values)
    now = now_ms or int(datetime.now(timezone.utc).timestamp() * 1000)
    return now - latest <= RECENT_ACTIVITY_HOURS * 60 * 60 * 1000


def token_spike_alert(sessions: list[CodexSession]) -> Alert | None:
    if len(sessions) < 6:
        return None
    recent = sessions[0].tokens_used
    previous = [session.tokens_used for session in sessions[1:6]]
    average = sum(previous) / len(previous)
    if average > 0 and recent > average * 2:
        return Alert(level="info", message="Recent session token usage is more than 2x the previous five-session average.")
    return None


def long_idle_alert(sessions: list[CodexSession], git: GitState, now_ms: int | None = None) -> Alert | None:
    if git.dirty_files > 0:
        return None
    updated_values = [session.updated_at_ms for session in sessions if session.updated_at_ms is not None]
    if not updated_values:
        return None
    latest = max(updated_values)
    now = now_ms or int(datetime.now(timezone.utc).timestamp() * 1000)
    idle_ms = IDLE_THRESHOLD_DAYS * 24 * 60 * 60 * 1000
    if now - latest > idle_ms:
        return Alert(level="info", message="No Codex session update in 7 days.")
    return None


def calculate_status(
    plan: PlanLoadResult,
    progress: ProgressSummary,
    sessions: list[CodexSession],
    git: GitState,
    test: TestState,
) -> str:
    if plan.missing or plan.invalid:
        return "missing_plan"
    if progress.blocked and progress.blocked > 0:
        return "blocked"
    if test.status == "failing":
        return "tests_failing"
    if is_recent_session(sessions) or git.dirty_files > 0:
        return "active"
    if sessions or git.latest_commit:
        return "idle"
    return "unknown"


def build_alerts(
    plan: PlanLoadResult,
    progress: ProgressSummary,
    sessions: list[CodexSession],
    tokens: TokenSummary,
    git: GitState,
    test: TestState,
) -> list[Alert]:
    alerts: list[Alert] = []
    if plan.missing:
        alerts.append(Alert(level="warning", message="Project path has no readable agentpm.yaml."))
    if plan.invalid:
        alerts.append(Alert(level="warning", message="agentpm.yaml exists but cannot be parsed."))
    for warning in plan.warnings:
        alerts.append(Alert(level="warning", message=warning))
    if progress.blocked and progress.blocked > 0:
        alerts.append(Alert(level="warning", message=f"{progress.blocked} task is blocked."))
    if test.status == "unknown":
        alerts.append(Alert(level="warning", message="Test state is unknown."))
    if test.status == "failing":
        alerts.append(Alert(level="error", message="Tests are failing."))
    spike = token_spike_alert(sessions)
    if spike:
        alerts.append(spike)
    idle = long_idle_alert(sessions, git)
    if idle:
        alerts.append(idle)
    if tokens.unavailable:
        alerts.append(Alert(level="warning", message="Local Codex state is unavailable."))
    if not git.is_repo or git.unavailable:
        alerts.append(Alert(level="info", message="Git state is unavailable for this project path."))
    return alerts
