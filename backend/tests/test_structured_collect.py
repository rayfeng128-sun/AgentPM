from pathlib import Path

from app.structured_collect import collect_project_snapshot
from app.structured_models import FieldState


def write_agentpm(project_dir: Path) -> None:
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: explicit
        title: Explicit task
        status: doing
        user_story: As a PM, I want explicit values.
        scope: Explicit scope
        acceptance_criteria: Explicit acceptance
        verification_method: Explicit verification
        prd_refs:
          - docs/product/feature-prd.md
      - id: prd-fallback
        title: PRD fallback
        status: todo
        prd_refs:
          - docs/product/feature-prd.md
      - id: plans-fallback
        title: Plans fallback
        status: blocked
""",
        encoding="utf-8",
    )


def write_prd(project_dir: Path) -> None:
    (project_dir / "docs").mkdir()
    (project_dir / "docs" / "product").mkdir()
    (project_dir / "docs" / "product" / "feature-prd.md").write_text(
        """
# Demo PRD

As a user, I want the dashboard to preserve field provenance.

Scope:
- This should cover the PRD fallback task.

Acceptance Criteria
- The fallback task shows a derived story.
- The fallback task shows acceptance text.

Verification Plan
- Run backend tests.
""",
        encoding="utf-8",
    )


def write_plans(project_dir: Path) -> None:
    (project_dir / "PLANS.md").write_text(
        """
## plans-fallback

As a planner, I want structured plans to remain stable.

Scope:
- This should be read from PLANS.md.

Acceptance Criteria
- The fallback task uses PLANS.md when agentpm.yaml is incomplete.

Verification Plan
- Run the structured collector tests.
""",
        encoding="utf-8",
    )


def test_collect_snapshot_prefers_explicit_yaml_values(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    write_agentpm(project_dir)
    write_prd(project_dir)
    write_plans(project_dir)

    snapshot = collect_project_snapshot(project_dir, "demo")
    tasks = {task.task_key: task for task in snapshot.as_task_rows()}

    assert tasks["explicit"].user_story.value == "As a PM, I want explicit values."
    assert tasks["explicit"].user_story.state == FieldState.explicit
    assert tasks["explicit"].scope.state == FieldState.explicit
    assert tasks["explicit"].acceptance_criteria.state == FieldState.explicit
    assert tasks["explicit"].verification_method.state == FieldState.explicit
    assert tasks["explicit"].prd_refs == ["docs/product/feature-prd.md"]


def test_collect_snapshot_uses_prd_and_plans_fallbacks(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    write_agentpm(project_dir)
    write_prd(project_dir)
    write_plans(project_dir)

    snapshot = collect_project_snapshot(project_dir, "demo")
    tasks = {task.task_key: task for task in snapshot.as_task_rows()}

    assert tasks["prd-fallback"].user_story.state == FieldState.inferred
    assert tasks["prd-fallback"].scope.value == "This should cover the PRD fallback task."
    assert tasks["prd-fallback"].acceptance_criteria.value == "The fallback task shows a derived story.\nThe fallback task shows acceptance text."
    assert tasks["prd-fallback"].verification_method.value == "Run backend tests."
    assert tasks["plans-fallback"].user_story.state == FieldState.needs_review
    assert tasks["plans-fallback"].scope.value == "This should be read from PLANS.md."
    assert snapshot.status == "complete"
