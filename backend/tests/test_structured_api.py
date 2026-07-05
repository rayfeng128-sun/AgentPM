from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def write_plan(project_dir: Path, title: str, user_story: str) -> None:
    (project_dir / "agentpm.yaml").write_text(
        f"""
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: task-1
        title: {title}
        status: doing
        user_story: {user_story}
""",
        encoding="utf-8",
    )


def test_structured_state_refresh_and_task_plan_use_persisted_snapshot(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    write_plan(project_dir, "Original task", "As a user, I want the original snapshot.")

    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.codex_db_path = tmp_path / "missing-codex.sqlite"
    client = TestClient(app)

    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})
    project_id = created.json()["id"]

    initial_state = client.get(f"/api/projects/{project_id}/structured-state")
    assert initial_state.status_code == 200
    assert initial_state.json()["milestones"][0]["tasks"][0]["title"] == "Original task"
    assert initial_state.json()["milestones"][0]["tasks"][0]["user_story"]["state"] == "explicit"

    write_plan(project_dir, "Updated task", "As a user, I want the updated plan.")

    persisted_tasks = client.get(f"/api/projects/{project_id}/tasks")
    assert persisted_tasks.status_code == 200
    assert persisted_tasks.json()["milestones"][0]["tasks"][0]["title"] == "Original task"

    refreshed = client.post(f"/api/projects/{project_id}/structured-refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["milestones"][0]["tasks"][0]["title"] == "Updated task"

    latest_tasks = client.get(f"/api/projects/{project_id}/tasks")
    assert latest_tasks.status_code == 200
    assert latest_tasks.json()["milestones"][0]["tasks"][0]["title"] == "Updated task"
