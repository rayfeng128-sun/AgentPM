from app.models import CodexSession, GitState, PlanLoadResult, ProgressSummary, TestState, TokenSummary
from app.status_rules import build_alerts, calculate_status, token_spike_alert


def progress(blocked: int = 0) -> ProgressSummary:
    return ProgressSummary(done=0, total=1, blocked=blocked, percent=0)


def git(dirty_files: int = 0, latest_commit: str | None = None) -> GitState:
    return GitState(is_repo=True, branch="main", dirty_files=dirty_files, latest_commit=latest_commit)


def test_status_priority_matches_prd() -> None:
    plan = PlanLoadResult(milestones=[], missing=True)
    failing_test = TestState(status="failing", confidence="low")

    assert calculate_status(plan, progress(blocked=1), [], git(dirty_files=1), failing_test) == "missing_plan"
    assert calculate_status(PlanLoadResult(milestones=[]), progress(blocked=1), [], git(), failing_test) == "blocked"
    assert calculate_status(PlanLoadResult(milestones=[]), progress(), [], git(), failing_test) == "tests_failing"
    assert calculate_status(PlanLoadResult(milestones=[]), progress(), [], git(dirty_files=1), TestState()) == "active"
    assert calculate_status(PlanLoadResult(milestones=[]), progress(), [], git(latest_commit="abc"), TestState()) == "idle"
    assert calculate_status(PlanLoadResult(milestones=[]), progress(), [], git(), TestState()) == "unknown"


def test_token_spike_alert_uses_previous_five_session_average() -> None:
    sessions = [
        CodexSession(id="new", title="new", cwd="/p", tokens_used=101),
        *[CodexSession(id=str(i), title=str(i), cwd="/p", tokens_used=50) for i in range(5)],
    ]

    alert = token_spike_alert(sessions)

    assert alert is not None
    assert alert.level == "info"


def test_build_alerts_covers_missing_local_signals() -> None:
    alerts = build_alerts(
        plan=PlanLoadResult(milestones=[], missing=True, warnings=["Unknown task status for odd: strange"]),
        progress=ProgressSummary(done=None, total=None, blocked=None, percent=None),
        sessions=[],
        tokens=TokenSummary(total=None, recent_session=None, unavailable=True),
        git=GitState(is_repo=False, branch=None, dirty_files=0, latest_commit=None),
        test=TestState(status="unknown", confidence="low"),
    )

    messages = [alert.message for alert in alerts]
    assert "Project path has no readable agentpm.yaml." in messages
    assert "Unknown task status for odd: strange" in messages
    assert "Test state is unknown." in messages
    assert "Local Codex state is unavailable." in messages
    assert "Git state is unavailable for this project path." in messages


def test_build_alerts_reports_long_idle_project() -> None:
    alerts = build_alerts(
        plan=PlanLoadResult(milestones=[]),
        progress=ProgressSummary(done=0, total=1, blocked=0, percent=0),
        sessions=[CodexSession(id="old", title="Old work", cwd="/p", tokens_used=10, updated_at_ms=0)],
        tokens=TokenSummary(total=10, recent_session=10),
        git=GitState(is_repo=True, branch="main", dirty_files=0, latest_commit="abc123"),
        test=TestState(status="passing", confidence="low"),
    )

    assert any(alert.level == "info" and "No Codex session update in 7 days." == alert.message for alert in alerts)
