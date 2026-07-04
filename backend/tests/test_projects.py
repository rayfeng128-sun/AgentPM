from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def client_with_db(tmp_path: Path) -> TestClient:
    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.browse_roots = [tmp_path]
    return TestClient(app)


def test_create_and_list_project_with_plan(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text("milestones: []\n", encoding="utf-8")
    client = client_with_db(tmp_path)

    response = client.post("/api/projects", json={"name": "Demo Project", "path": str(project_dir)})
    listed = client.get("/api/projects")

    assert response.status_code == 200
    assert response.json()["id"] == "demo-project"
    assert response.json()["has_plan"] is True
    assert response.json()["is_git_repo"] is False
    assert listed.status_code == 200
    assert [project["id"] for project in listed.json()] == ["demo-project"]


def test_rejects_empty_and_missing_paths(tmp_path: Path) -> None:
    client = client_with_db(tmp_path)

    empty_name = client.post("/api/projects", json={"name": " ", "path": str(tmp_path)})
    missing_path = client.post("/api/projects", json={"name": "Missing", "path": str(tmp_path / "nope")})

    assert empty_name.status_code == 422
    assert missing_path.status_code == 422


def test_duplicate_path_updates_existing_project(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    client = client_with_db(tmp_path)

    first = client.post("/api/projects", json={"name": "First Name", "path": str(project_dir)})
    second = client.post("/api/projects", json={"name": "Second Name", "path": str(project_dir)})
    listed = client.get("/api/projects")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == "second-name"
    assert len(listed.json()) == 1
    assert listed.json()[0]["name"] == "Second Name"


def test_delete_project_removes_it_from_registry(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    client = client_with_db(tmp_path)

    created = client.post("/api/projects", json={"name": "Disposable", "path": str(project_dir)})
    project_id = created.json()["id"]

    deleted = client.delete(f"/api/projects/{project_id}")
    listed = client.get("/api/projects")

    assert deleted.status_code == 204
    assert listed.status_code == 200
    assert listed.json() == []


def test_browse_directories_lists_roots_and_children(tmp_path: Path) -> None:
    alpha = tmp_path / "Alpha"
    beta = tmp_path / "Beta"
    nested = alpha / "Nested"
    alpha.mkdir()
    beta.mkdir()
    nested.mkdir()
    client = client_with_db(tmp_path)

    roots = client.get("/api/directories")
    child = client.get("/api/directories", params={"path": str(alpha)})

    assert roots.status_code == 200
    assert roots.json()["roots"][0]["path"] == str(tmp_path)
    assert {item["name"] for item in roots.json()["directories"]} == {"Alpha", "Beta"}
    assert child.status_code == 200
    assert child.json()["current_path"] == str(alpha)
    assert child.json()["parent_path"] == str(tmp_path)
    assert child.json()["directories"] == [{"name": "Nested", "path": str(nested)}]


def test_browse_directories_rejects_paths_outside_allowed_roots(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path.parent
    client = client_with_db(tmp_path)

    response = client.get("/api/directories", params={"path": str(outside)})

    assert response.status_code == 403


def test_read_project_prd_returns_markdown_content_and_anchor(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    prd_dir = project_dir / "docs" / "product"
    prd_dir.mkdir(parents=True)
    (project_dir / "agentpm.yaml").write_text("milestones: []\n", encoding="utf-8")
    (prd_dir / "01-demo-prd.md").write_text(
        "# Demo PRD\n\n## Story 1\n\nAcceptance content.\n",
        encoding="utf-8",
    )
    client = client_with_db(tmp_path)
    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})

    response = client.get(
        f"/api/projects/{created.json()['id']}/prd",
        params={"ref": "docs/product/01-demo-prd.md#story-1"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ref": "docs/product/01-demo-prd.md#story-1",
        "path": "docs/product/01-demo-prd.md",
        "anchor": "story-1",
        "title": "Demo PRD",
        "content": "# Demo PRD\n\n## Story 1\n\nAcceptance content.\n",
        "unavailable": False,
    }


def test_read_project_prd_marks_missing_or_non_markdown_refs_unavailable(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text("milestones: []\n", encoding="utf-8")
    client = client_with_db(tmp_path)
    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})
    project_id = created.json()["id"]

    missing = client.get(f"/api/projects/{project_id}/prd", params={"ref": "docs/product/missing.md"})
    requirement_id = client.get(f"/api/projects/{project_id}/prd", params={"ref": "PRD-02-STORY-5"})

    assert missing.status_code == 200
    assert missing.json()["unavailable"] is True
    assert missing.json()["content"] == ""
    assert requirement_id.status_code == 200
    assert requirement_id.json()["unavailable"] is True
    assert requirement_id.json()["path"] == "PRD-02-STORY-5"


def test_read_project_prd_rejects_path_traversal(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text("milestones: []\n", encoding="utf-8")
    client = client_with_db(tmp_path)
    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})

    response = client.get(f"/api/projects/{created.json()['id']}/prd", params={"ref": "../secret.md"})

    assert response.status_code == 403


def test_tasks_endpoint_derives_task_details_from_prd_refs(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    prd_dir = project_dir / "docs" / "product"
    prd_dir.mkdir(parents=True)
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: analytics
    title: Analytics
    tasks:
      - id: traceability
        title: Traceability task
        status: doing
        prd_refs:
          - docs/product/02-demo-prd.md#story-5-trace-tasks-back-to-prds
""",
        encoding="utf-8",
    )
    (prd_dir / "02-demo-prd.md").write_text(
        """
# Demo PRD

## 3. User Stories

### Story 5: Trace Tasks Back to PRDs

As a project manager reviewing delivery scope,
in the context of multiple PRDs and implementation tasks,
I want each task to show which PRD requirement it supports,
so that I can verify coverage, identify unplanned work, and discuss scope changes with the team.

Acceptance:

- The task table shows the primary PRD association for each task.
- Tasks without PRD association are visible and marked as unlinked scope.

## 15. Verification Plan

- Unit test plan parsing with `prd_refs`.
- Frontend task table renders derived task metadata.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    client = client_with_db(tmp_path)
    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})

    response = client.get(f"/api/projects/{created.json()['id']}/tasks")

    assert response.status_code == 200
    task = response.json()["milestones"][0]["tasks"][0]
    assert task["user_story"].startswith("As a project manager reviewing delivery scope")
    assert task["scope"] == "Trace Tasks Back to PRDs"
    assert "The task table shows the primary PRD association" in task["acceptance_criteria"]
    assert "Unit test plan parsing with `prd_refs`." in task["verification_method"]
