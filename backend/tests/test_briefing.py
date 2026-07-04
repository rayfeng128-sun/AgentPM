from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from app.main import app


def make_codex_db(path: Path, project_path: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE threads (
            id TEXT,
            title TEXT,
            cwd TEXT,
            model TEXT,
            tokens_used INTEGER,
            updated_at_ms INTEGER,
            rollout_path TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("s1", "Recent work", project_path, "gpt", 42, 4102444800000, "/tmp/rollout.jsonl"),
    )
    conn.commit()
    conn.close()


def test_briefing_endpoint_returns_prd_shape(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: mvp
    title: MVP
    tasks:
      - id: backend
        title: Backend
        status: done
      - id: frontend
        title: Frontend
        status: todo
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    make_codex_db(codex_db, str(project_dir.resolve()))
    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.codex_db_path = codex_db
    client = TestClient(app)

    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})
    response = client.get(f"/api/projects/{created.json()['id']}/briefing")

    assert response.status_code == 200
    payload = response.json()
    assert payload["progress"]["done"] == 1
    assert payload["progress"]["total"] == 2
    assert payload["tokens"]["total"] == 42
    assert payload["sessions"][0]["title"] == "Recent work"
    assert payload["briefing"]["status"] == "active"
    assert "summary" in payload["briefing"]


def test_briefing_includes_daily_token_usage_shape(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: analytics
    title: Analytics
    tasks:
      - id: linked
        title: Linked task
        status: doing
        prd_refs:
          - PRD-1
        codex_sessions:
          - s1
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    make_codex_db(codex_db, str(project_dir.resolve()))
    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.codex_db_path = codex_db
    client = TestClient(app)

    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})
    response = client.get(f"/api/projects/{created.json()['id']}/briefing")

    assert response.status_code == 200
    payload = response.json()
    assert "daily_token_usage" in payload
    assert payload["daily_token_usage"]["default_mode"] == "project_total"
    assert payload["daily_token_usage"]["has_task_links"] is True
    assert "project_days" in payload["daily_token_usage"]
    assert "tasks" in payload["daily_token_usage"]
    assert "notes" in payload["daily_token_usage"]


def test_missing_plan_is_payload_state_not_500(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.codex_db_path = tmp_path / "missing-codex.sqlite"
    client = TestClient(app)

    created = client.post("/api/projects", json={"name": "No Plan", "path": str(project_dir)})
    response = client.get(f"/api/projects/{created.json()['id']}/briefing")

    assert response.status_code == 200
    payload = response.json()
    assert payload["briefing"]["status"] == "missing_plan"
    assert payload["progress"]["total"] is None
    assert payload["tokens"]["unavailable"] is True


def test_root_redirects_to_frontend_dashboard(tmp_path: Path) -> None:
    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.codex_db_path = tmp_path / "missing-codex.sqlite"
    client = TestClient(app)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://127.0.0.1:18080/"


def test_briefing_uses_reconstructed_daily_history_when_project_session_list_is_empty(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: analytics
    title: Analytics
    tasks:
      - id: linked
        title: Linked task
        status: doing
        codex_sessions:
          - linked-session
""",
        encoding="utf-8",
    )
    codex_root = tmp_path / ".codex"
    sqlite_dir = codex_root / "sqlite"
    sqlite_dir.mkdir(parents=True)
    codex_db = sqlite_dir / "state_5.sqlite"
    make_codex_db(codex_db, "/different/project")
    rollout_dir = codex_root / "sessions" / "2026" / "06" / "30"
    rollout_dir.mkdir(parents=True)
    (rollout_dir / "rollout-2026-06-30T00-00-39-linked-session.jsonl").write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"linked-session","id":"linked-session","cwd":"/another/path","model":"gpt-5.5","title":"Linked Session"}}
{"timestamp":"2026-06-29T16:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":120,"cached_input_tokens":40,"output_tokens":24,"reasoning_output_tokens":6,"total_tokens":150}}}}
{"timestamp":"2026-06-30T09:15:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":220,"cached_input_tokens":70,"output_tokens":42,"reasoning_output_tokens":10,"total_tokens":260}}}}
{"timestamp":"2026-06-30T18:20:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":300,"cached_input_tokens":100,"output_tokens":60,"reasoning_output_tokens":15,"total_tokens":360}}}}
""".strip(),
        encoding="utf-8",
    )
    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.codex_db_path = codex_db
    client = TestClient(app)

    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})
    response = client.get(f"/api/projects/{created.json()['id']}/briefing")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sessions"] == []
    assert payload["tokens"]["total"] == 360
    assert payload["tokens"]["unavailable"] is False
    assert payload["daily_token_usage"]["project_days"] == [
        {"date": "2026-06-29", "tokens": 150, "models": [{"model_key": "gpt-5.5", "model_label": "gpt-5.5", "tokens": 150}]},
        {"date": "2026-06-30", "tokens": 210, "models": [{"model_key": "gpt-5.5", "model_label": "gpt-5.5", "tokens": 210}]},
    ]
    assert payload["daily_token_usage"]["tasks"] == [
        {
            "task_id": "linked",
            "task_title": "Linked task",
            "status": "doing",
            "attribution": "direct",
            "days": [
                {"date": "2026-06-29", "tokens": 150, "attribution": "direct"},
                {"date": "2026-06-30", "tokens": 210, "attribution": "direct"},
            ],
        }
    ]
    assert payload["daily_token_usage"]["has_partial_data"] is False


def test_briefing_daily_project_total_uses_project_sessions_and_local_timezone(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: analytics
    title: Analytics
    tasks:
      - id: linked
        title: Linked task
        status: doing
        codex_sessions:
          - s1
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    make_codex_db(codex_db, str(project_dir.resolve()))
    today_rollout = tmp_path / "today-rollout.jsonl"
    today_rollout.write_text(
        """
{"timestamp":"2026-07-02T01:00:00.000Z","type":"session_meta","payload":{"session_id":"today-session","id":"today-session","cwd":"REPLACE_ME","model":"gpt-5.5","title":"Today Session"}}
{"timestamp":"2026-07-02T01:00:05.000Z","type":"turn_context","payload":{"timezone":"Asia/Shanghai"}}
{"timestamp":"2026-07-02T02:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":150,"cached_input_tokens":25,"output_tokens":40,"reasoning_output_tokens":15,"total_tokens":230}}}}
""".strip().replace("REPLACE_ME", str(project_dir.resolve())),
        encoding="utf-8",
    )
    conn = sqlite3.connect(codex_db)
    conn.execute(
        "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("today-session", "Today Session", str(project_dir.resolve()), "gpt-5.5", 230, 1751421600000, str(today_rollout)),
    )
    conn.commit()
    conn.close()
    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.codex_db_path = codex_db
    client = TestClient(app)

    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})
    response = client.get(f"/api/projects/{created.json()['id']}/briefing")

    assert response.status_code == 200
    payload = response.json()
    assert payload["daily_token_usage"]["project_days"] == [
        {"date": "2026-07-02", "tokens": 230, "models": [{"model_key": "gpt-5.5", "model_label": "gpt-5.5", "tokens": 230}]},
    ]
    assert payload["daily_token_usage"]["tasks"] == [
        {
            "task_id": "linked",
            "task_title": "Linked task",
            "status": "doing",
            "attribution": "direct",
            "days": [],
        }
    ]
    assert payload["daily_token_usage"]["has_partial_data"] is True
