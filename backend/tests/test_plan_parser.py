from pathlib import Path

from app.plan_parser import calculate_progress, load_plan


def test_missing_plan_returns_unavailable_progress(tmp_path: Path) -> None:
    plan = load_plan(str(tmp_path))
    progress = calculate_progress(plan)

    assert plan.missing is True
    assert progress.model_dump() == {"done": None, "total": None, "blocked": None, "percent": None}


def test_valid_plan_calculates_progress_and_blocked(tmp_path: Path) -> None:
    (tmp_path / "agentpm.yaml").write_text(
        """
milestones:
  - id: mvp
    title: MVP
    tasks:
      - id: one
        title: One
        status: done
      - id: two
        title: Two
        status: blocked
      - id: three
        title: Three
        status: todo
""",
        encoding="utf-8",
    )

    plan = load_plan(str(tmp_path))
    progress = calculate_progress(plan)

    assert plan.missing is False
    assert progress.done == 1
    assert progress.total == 3
    assert progress.blocked == 1
    assert progress.percent == 33


def test_invalid_status_falls_back_to_todo_with_warning(tmp_path: Path) -> None:
    (tmp_path / "agentpm.yaml").write_text(
        """
milestones:
  - id: mvp
    title: MVP
    tasks:
      - id: odd
        title: Odd
        status: strange
""",
        encoding="utf-8",
    )

    plan = load_plan(str(tmp_path))
    progress = calculate_progress(plan)

    assert plan.milestones[0].tasks[0].status == "todo"
    assert plan.warnings == ["Unknown task status for odd: strange"]
    assert progress.percent == 0


def test_invalid_yaml_returns_invalid_plan(tmp_path: Path) -> None:
    (tmp_path / "agentpm.yaml").write_text("milestones: [", encoding="utf-8")

    plan = load_plan(str(tmp_path))
    progress = calculate_progress(plan)

    assert plan.invalid is True
    assert progress.total is None


def test_v02_task_metadata_and_milestone_progress(tmp_path: Path) -> None:
    (tmp_path / "agentpm.yaml").write_text(
        """
milestones:
  - id: analytics
    title: Task Analytics
    tasks:
      - id: task-token-chart
        title: Build task token chart
        status: doing
        assignee: Alex Chen
        created_at: 2026-06-27
        updated_at: 2026-06-30
        session_note: Type mismatch in user model validation.
        prd_refs:
          - docs/product/02-task-progress-token-analytics-prd.md#story-2-inspect-task-token-consumption
        codex_sessions:
          - session-a
        token_budget: 300000
      - id: prd-coverage
        title: Build PRD coverage view
        status: done
        prd_refs:
          - PRD-02-STORY-5
        codex_sessions:
          - session-b
""",
        encoding="utf-8",
    )

    plan = load_plan(str(tmp_path))
    progress = calculate_progress(plan)
    milestone = plan.milestones[0]
    task = milestone.tasks[0]

    assert progress.done == 1
    assert progress.total == 2
    assert progress.percent == 50
    assert milestone.progress.done == 1
    assert milestone.progress.total == 2
    assert milestone.progress.percent == 50
    assert task.assignee == "Alex Chen"
    assert task.created_at == "2026-06-27"
    assert task.updated_at == "2026-06-30"
    assert task.session_note == "Type mismatch in user model validation."
    assert task.prd_refs == ["docs/product/02-task-progress-token-analytics-prd.md#story-2-inspect-task-token-consumption"]
    assert task.codex_sessions == ["session-a"]
    assert task.token_budget == 300000


def test_task_delivery_metadata_is_optional_and_preserved(tmp_path: Path) -> None:
    (tmp_path / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: rich-task
        title: Rich task
        status: doing
        user_story: As a PM, I want richer task rows.
        scope: Show traceability fields directly on the board.
        acceptance_criteria: Rows expose story, scope, acceptance, and verification.
        verification_method: Backend parser test and frontend build.
      - id: sparse-task
        title: Sparse task
        status: todo
""",
        encoding="utf-8",
    )

    plan = load_plan(str(tmp_path))
    rich_task = plan.milestones[0].tasks[0]
    sparse_task = plan.milestones[0].tasks[1]

    assert rich_task.user_story == "As a PM, I want richer task rows."
    assert rich_task.scope == "Show traceability fields directly on the board."
    assert rich_task.acceptance_criteria == "Rows expose story, scope, acceptance, and verification."
    assert rich_task.verification_method == "Backend parser test and frontend build."
    assert sparse_task.user_story is None
    assert sparse_task.scope is None
    assert sparse_task.acceptance_criteria is None
    assert sparse_task.verification_method is None


def test_duplicate_task_ids_mark_plan_invalid(tmp_path: Path) -> None:
    (tmp_path / "agentpm.yaml").write_text(
        """
milestones:
  - id: one
    title: One
    tasks:
      - id: duplicate
        title: First
        status: done
  - id: two
    title: Two
    tasks:
      - id: duplicate
        title: Second
        status: todo
""",
        encoding="utf-8",
    )

    plan = load_plan(str(tmp_path))
    progress = calculate_progress(plan)

    assert plan.invalid is True
    assert "Duplicate task id: duplicate" in plan.warnings
    assert progress.total is None
