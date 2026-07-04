from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from app.main import app
from app.models import CodexSession, TaskTokenSession, TaskTokenUsageItem, TokenSnapshot
from app.plan_parser import load_plan
from app.task_analytics import build_daily_token_usage, build_task_token_usage


def create_codex_db(path: Path, project_path: str) -> None:
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
    rows = [
        ("s-direct", "Direct task work", project_path, "gpt-5.5", 1000, 300, None),
        ("s-shared", "Shared implementation", project_path, "gpt-5.4-mini", 500, 200, None),
        ("s-foreign", "Foreign cwd task", "/different/project", "gpt", 700, 100, None),
        ("s-multi", "Multi model task", project_path, "DeepSeek", 300, 150, None),
        ("s-multi-2", "Multi model task 2", project_path, "gpt-5.5", 250, 140, None),
        ("s-unknown", "Unknown model task", project_path, None, 150, 130, None),
    ]
    conn.executemany("INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()


def write_plan(project_dir: Path) -> None:
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: direct
        title: Direct task
        status: doing
        prd_refs:
          - PRD-1
        codex_sessions:
          - s-direct
          - missing-session
        token_budget: 900
      - id: shared-a
        title: Shared A
        status: todo
        prd_refs:
          - PRD-2
        codex_sessions:
          - s-shared
        token_budget: 200
      - id: shared-b
        title: Shared B
        status: blocked
        prd_refs: []
        codex_sessions:
          - s-shared
      - id: no-links
        title: No links
        status: todo
      - id: multi-model
        title: Multi model
        status: doing
        prd_refs:
          - PRD-3
        codex_sessions:
          - s-multi-2
          - s-multi
      - id: unknown-model
        title: Unknown model
        status: doing
        prd_refs:
          - PRD-4
        codex_sessions:
          - s-unknown
""",
        encoding="utf-8",
    )


def test_task_token_usage_covers_direct_shared_none_and_missing(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    write_plan(project_dir)
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)
    tasks = {task.task_id: task for task in usage.tasks}

    assert tasks["direct"].attribution == "direct"
    assert tasks["direct"].total_tokens == 1000
    assert tasks["direct"].model_label == "gpt-5.5"
    assert tasks["direct"].models == ["gpt-5.5"]
    assert tasks["direct"].missing_sessions == ["missing-session"]
    assert tasks["shared-a"].attribution == "shared"
    assert tasks["shared-a"].model_label == "gpt-5.4-mini"
    assert tasks["shared-b"].attribution == "shared"
    assert tasks["no-links"].attribution == "none"
    assert tasks["no-links"].total_tokens == 0
    assert tasks["no-links"].model_label == "No model"
    assert tasks["multi-model"].model_label == "Multiple models"
    assert tasks["multi-model"].models == ["DeepSeek", "gpt-5.5"]
    assert tasks["unknown-model"].model_label == "Unknown model"
    assert tasks["unknown-model"].models == []
    assert any("Missing linked session missing-session" in alert.message for alert in usage.alerts)
    assert any("shared attribution" in alert.message for alert in usage.alerts)
    assert any("exceeded its token budget" in alert.message for alert in usage.alerts)
    assert any(alert.level == "error" and "heavily exceeded" in alert.message for alert in usage.alerts)


def test_task_token_usage_marks_unavailable_when_codex_state_missing(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    write_plan(project_dir)

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), tmp_path / "missing.sqlite")

    assert {task.attribution for task in usage.tasks if task.codex_sessions} == {"unavailable"}
    assert all(task.total_tokens is None for task in usage.tasks if task.codex_sessions)
    assert all(task.model_label == "Token data unavailable" for task in usage.tasks if task.codex_sessions)
    assert any("Token data unavailable" in alert.message for alert in usage.alerts)


def test_task_token_usage_uses_rollout_breakdown_and_session_id_lookup(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: direct
        title: Direct task
        status: doing
        prd_refs:
          - PRD-1
        codex_sessions:
          - s-direct
      - id: foreign
        title: Foreign cwd task
        status: todo
        prd_refs:
          - PRD-2
        codex_sessions:
          - s-foreign
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))
    rollout = tmp_path / "direct-rollout.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-15T15:39:11.109Z","type":"session_meta","payload":{"id":"s-direct"}}
{"timestamp":"2026-06-15T15:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":40,"output_tokens":20,"reasoning_output_tokens":5,"total_tokens":120}}}}
""".strip(),
        encoding="utf-8",
    )
    conn = sqlite3.connect(codex_db)
    conn.execute("UPDATE threads SET rollout_path = ? WHERE id = ?", (str(rollout), "s-direct"))
    conn.commit()
    conn.close()

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)
    tasks = {task.task_id: task for task in usage.tasks}

    assert tasks["direct"].total_tokens == 120
    assert tasks["direct"].input_tokens == 100
    assert tasks["direct"].cached_input_tokens == 40
    assert tasks["direct"].output_tokens == 20
    assert tasks["direct"].reasoning_output_tokens == 5
    assert tasks["foreign"].total_tokens == 700
    assert tasks["foreign"].sessions[0].title == "Foreign cwd task"


def test_task_token_usage_builds_daily_project_and_task_series(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: direct
        title: Direct task
        status: doing
        prd_refs:
          - PRD-1
        codex_sessions:
          - s-direct
      - id: shared-a
        title: Shared A
        status: todo
        prd_refs:
          - PRD-2
        codex_sessions:
          - s-shared
      - id: shared-b
        title: Shared B
        status: blocked
        codex_sessions:
          - s-shared
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))
    direct_rollout = tmp_path / "direct-daily.jsonl"
    direct_rollout.write_text(
        """
{"timestamp":"2026-06-15T09:00:00.000Z","type":"session_meta","payload":{"id":"s-direct","session_id":"s-direct","cwd":"REPLACE_ME","title":"Direct task work"}}
{"timestamp":"2026-06-15T09:10:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":60,"cached_input_tokens":20,"output_tokens":15,"reasoning_output_tokens":5,"total_tokens":100}}}}
""".strip().replace("REPLACE_ME", str(project_dir.resolve())),
        encoding="utf-8",
    )
    shared_rollout = tmp_path / "shared-daily.jsonl"
    shared_rollout.write_text(
        """
{"timestamp":"2026-06-16T11:00:00.000Z","type":"session_meta","payload":{"id":"s-shared","session_id":"s-shared","cwd":"REPLACE_ME","title":"Shared implementation"}}
{"timestamp":"2026-06-16T11:30:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":120,"cached_input_tokens":40,"output_tokens":30,"reasoning_output_tokens":10,"total_tokens":200}}}}
""".strip().replace("REPLACE_ME", str(project_dir.resolve())),
        encoding="utf-8",
    )
    conn = sqlite3.connect(codex_db)
    conn.execute("UPDATE threads SET rollout_path = ? WHERE id = ?", (str(direct_rollout), "s-direct"))
    conn.execute("UPDATE threads SET rollout_path = ? WHERE id = ?", (str(shared_rollout), "s-shared"))
    conn.commit()
    conn.close()

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)

    assert usage.daily_token_usage is not None
    assert usage.daily_token_usage.default_mode == "project_total"
    assert usage.daily_token_usage.has_task_links is True
    assert [(day.date, day.tokens) for day in usage.daily_token_usage.project_days] == [
        ("2026-06-15", 100),
        ("2026-06-16", 200),
    ]
    assert [
        (day.date, [(segment.model_label, segment.tokens) for segment in day.models])
        for day in usage.daily_token_usage.project_days
    ] == [
        ("2026-06-15", [("gpt-5.5", 100)]),
        ("2026-06-16", [("gpt-5.4-mini", 200)]),
    ]
    assert any(task.task_id == "direct" for task in usage.daily_token_usage.tasks)
    assert any(task.attribution == "shared" for task in usage.daily_token_usage.tasks)


def test_task_token_usage_reconstructs_daily_history_from_rollout_snapshots(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: linked-a
        title: Linked A
        status: doing
        codex_sessions:
          - s-direct
      - id: linked-b
        title: Linked B
        status: blocked
        codex_sessions:
          - s-direct
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))
    rollout = tmp_path / "rollout-linked.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-15T09:00:00.000Z","type":"session_meta","payload":{"id":"s-rollout","session_id":"s-rollout","cwd":"REPLACE_ME","title":"Linked rollout session"}}
{"timestamp":"2026-06-15T09:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":60,"cached_input_tokens":10,"output_tokens":20,"reasoning_output_tokens":10,"total_tokens":100}}}}
{"timestamp":"2026-06-16T10:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":90,"cached_input_tokens":20,"output_tokens":30,"reasoning_output_tokens":10,"total_tokens":150}}}}
{"timestamp":"2026-06-16T18:30:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":150,"cached_input_tokens":30,"output_tokens":50,"reasoning_output_tokens":20,"total_tokens":250}}}}
{"timestamp":"2026-06-17T08:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":180,"cached_input_tokens":40,"output_tokens":70,"reasoning_output_tokens":20,"total_tokens":300}}}}
    """.strip().replace("REPLACE_ME", str(project_dir.resolve())),
        encoding="utf-8",
    )
    conn = sqlite3.connect(codex_db)
    conn.execute("UPDATE threads SET rollout_path = ?, tokens_used = ?, updated_at_ms = ? WHERE id = ?", (str(rollout), 300, 0, "s-direct"))
    conn.commit()
    conn.close()

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)

    assert usage.daily_token_usage is not None
    assert [(day.date, day.tokens) for day in usage.daily_token_usage.project_days] == [
        ("2026-06-15", 100),
        ("2026-06-16", 150),
        ("2026-06-17", 50),
    ]
    task_days = {task.task_id: [(day.date, day.tokens) for day in task.days] for task in usage.daily_token_usage.tasks}
    assert task_days["linked-a"] == [("2026-06-15", 100), ("2026-06-16", 150), ("2026-06-17", 50)]
    assert task_days["linked-b"] == [("2026-06-15", 100), ("2026-06-16", 150), ("2026-06-17", 50)]
    assert usage.daily_token_usage.has_partial_data is False
    assert usage.daily_token_usage.notes == []


def test_task_token_usage_uses_project_sessions_for_project_total_and_local_session_timezone(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: linked
        title: Linked task
        status: doing
        codex_sessions:
          - s-direct
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))

    linked_rollout = tmp_path / "linked-rollout.jsonl"
    linked_rollout.write_text(
        """
{"timestamp":"2026-06-29T15:55:00.000Z","type":"session_meta","payload":{"id":"s-direct","session_id":"s-direct","cwd":"REPLACE_ME","title":"Linked session"}}
{"timestamp":"2026-06-29T15:55:10.000Z","type":"turn_context","payload":{"timezone":"Asia/Shanghai"}}
{"timestamp":"2026-06-29T16:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":60,"cached_input_tokens":10,"output_tokens":20,"reasoning_output_tokens":10,"total_tokens":100}}}}
""".strip().replace("REPLACE_ME", str(project_dir.resolve())),
        encoding="utf-8",
    )
    unlinked_rollout = tmp_path / "unlinked-rollout.jsonl"
    unlinked_rollout.write_text(
        """
{"timestamp":"2026-07-02T01:00:00.000Z","type":"session_meta","payload":{"id":"s-today","session_id":"s-today","cwd":"REPLACE_ME","title":"Today session"}}
{"timestamp":"2026-07-02T01:00:05.000Z","type":"turn_context","payload":{"timezone":"Asia/Shanghai"}}
{"timestamp":"2026-07-02T02:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":150,"cached_input_tokens":25,"output_tokens":40,"reasoning_output_tokens":15,"total_tokens":230}}}}
""".strip().replace("REPLACE_ME", str(project_dir.resolve())),
        encoding="utf-8",
    )

    conn = sqlite3.connect(codex_db)
    conn.execute("UPDATE threads SET rollout_path = ?, tokens_used = ?, updated_at_ms = ? WHERE id = ?", (str(linked_rollout), 100, 0, "s-direct"))
    conn.execute(
        "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("s-today", "Today session", str(project_dir.resolve()), "gpt-5.5", 230, 1751421600000, str(unlinked_rollout)),
    )
    conn.commit()
    conn.close()

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)

    assert usage.daily_token_usage is not None
    assert [(day.date, day.tokens) for day in usage.daily_token_usage.project_days] == [
        ("2026-06-30", 100),
        ("2026-07-02", 230),
    ]
    assert [
        (day.date, [(segment.model_label, segment.tokens) for segment in day.models])
        for day in usage.daily_token_usage.project_days
    ] == [
        ("2026-06-30", [("gpt-5.5", 100)]),
        ("2026-07-02", [("gpt-5.5", 230)]),
    ]
    assert [(day.date, day.tokens) for day in usage.daily_token_usage.tasks[0].days] == [("2026-06-30", 100)]


def test_daily_project_totals_group_multiple_models_within_a_day() -> None:
    usage = build_daily_token_usage(
        [],
        project_sessions=[
            CodexSession(
                id="s-alpha",
                title="Alpha",
                cwd="/tmp/project",
                model="gpt-5.5",
                tokens_used=120,
                token_snapshots=[
                    TokenSnapshot(
                        timestamp_ms=1751529600000,
                        input_tokens=40,
                        cached_input_tokens=10,
                        output_tokens=15,
                        reasoning_output_tokens=5,
                        total_tokens=70,
                    ),
                    TokenSnapshot(
                        timestamp_ms=1751533200000,
                        input_tokens=65,
                        cached_input_tokens=15,
                        output_tokens=25,
                        reasoning_output_tokens=15,
                        total_tokens=120,
                    ),
                ],
            ),
            CodexSession(
                id="s-beta",
                title="Beta",
                cwd="/tmp/project",
                model="DeepSeek",
                tokens_used=90,
                token_snapshots=[
                    TokenSnapshot(
                        timestamp_ms=1751531400000,
                        input_tokens=30,
                        cached_input_tokens=5,
                        output_tokens=10,
                        reasoning_output_tokens=5,
                        total_tokens=50,
                    ),
                    TokenSnapshot(
                        timestamp_ms=1751535000000,
                        input_tokens=55,
                        cached_input_tokens=10,
                        output_tokens=15,
                        reasoning_output_tokens=10,
                        total_tokens=90,
                    ),
                ],
            ),
        ],
    )

    assert [(day.date, day.tokens) for day in usage.project_days] == [("2025-07-03", 210)]
    assert [(segment.model_label, segment.tokens) for segment in usage.project_days[0].models] == [
        ("gpt-5.5", 120),
        ("DeepSeek", 90),
    ]


def test_task_token_usage_marks_partial_when_rollout_counters_reset(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: linked
        title: Linked task
        status: doing
        codex_sessions:
          - s-direct
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))
    rollout = tmp_path / "rollout-reset.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-15T09:00:00.000Z","type":"session_meta","payload":{"id":"s-direct","session_id":"s-direct","cwd":"REPLACE_ME","title":"Reset session"}}
{"timestamp":"2026-06-15T09:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":60,"cached_input_tokens":10,"output_tokens":20,"reasoning_output_tokens":10,"total_tokens":100}}}}
{"timestamp":"2026-06-16T10:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":30,"cached_input_tokens":5,"output_tokens":10,"reasoning_output_tokens":5,"total_tokens":50}}}}
""".strip().replace("REPLACE_ME", str(project_dir.resolve())),
        encoding="utf-8",
    )
    conn = sqlite3.connect(codex_db)
    conn.execute("UPDATE threads SET rollout_path = ?, tokens_used = ? WHERE id = ?", (str(rollout), 50, "s-direct"))
    conn.commit()
    conn.close()

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)

    assert usage.daily_token_usage is not None
    assert usage.daily_token_usage.project_days == []
    assert usage.daily_token_usage.tasks[0].days == []
    assert usage.daily_token_usage.has_partial_data is True
    assert any("reconstructed from cumulative snapshots" in note for note in usage.daily_token_usage.notes)


def test_task_token_usage_marks_partial_when_final_snapshot_disagrees_with_session_total() -> None:
    usage = build_daily_token_usage(
        [
            TaskTokenUsageItem(
                task_id="linked",
                task_title="Linked task",
                status="doing",
                total_tokens=175,
                attribution="direct",
                codex_sessions=["s-direct"],
                sessions=[
                    TaskTokenSession(
                        id="s-direct",
                        title="Mismatch session",
                        tokens=175,
                        token_snapshots=[
                            TokenSnapshot(
                                timestamp_ms=1749978300000,
                                input_tokens=60,
                                cached_input_tokens=10,
                                output_tokens=20,
                                reasoning_output_tokens=10,
                                total_tokens=100,
                            ),
                            TokenSnapshot(
                                timestamp_ms=1750068000000,
                                input_tokens=90,
                                cached_input_tokens=20,
                                output_tokens=30,
                                reasoning_output_tokens=10,
                                total_tokens=150,
                            ),
                        ],
                        source="codex_state_db",
                    )
                ],
            )
        ]
    )

    assert usage.project_days == []
    assert usage.tasks[0].days == []
    assert usage.has_partial_data is True
    assert any("reconstructed from cumulative snapshots" in note for note in usage.notes)


def test_task_token_usage_marks_daily_history_partial_when_only_final_total_exists(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: linked
        title: Linked task
        status: doing
        codex_sessions:
          - s-direct
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)

    assert usage.daily_token_usage is not None
    assert usage.daily_token_usage.project_days == []
    assert usage.daily_token_usage.tasks[0].days == []
    assert usage.daily_token_usage.has_partial_data is True
    assert any("reconstructed from cumulative snapshots" in note for note in usage.daily_token_usage.notes)


def test_task_token_usage_records_partial_daily_data_when_session_day_missing(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: linked
        title: Linked task
        status: doing
        codex_sessions:
          - s-direct
""",
        encoding="utf-8",
    )
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))
    conn = sqlite3.connect(codex_db)
    conn.execute("UPDATE threads SET updated_at_ms = NULL WHERE id = ?", ("s-direct",))
    conn.commit()
    conn.close()

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)

    assert usage.daily_token_usage is not None
    assert usage.daily_token_usage.project_days == []
    assert usage.daily_token_usage.has_partial_data is True
    assert any("reconstructed from cumulative snapshots" in note for note in usage.daily_token_usage.notes)


def test_tasks_and_task_token_usage_endpoints(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    write_plan(project_dir)
    codex_db = tmp_path / "codex.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))
    app.state.db_path = tmp_path / "agentpm.sqlite"
    app.state.codex_db_path = codex_db
    client = TestClient(app)

    created = client.post("/api/projects", json={"name": "Demo", "path": str(project_dir)})
    project_id = created.json()["id"]
    tasks_response = client.get(f"/api/projects/{project_id}/tasks")
    token_response = client.get(f"/api/projects/{project_id}/task-token-usage")

    assert tasks_response.status_code == 200
    assert token_response.status_code == 200
    assert tasks_response.json()["progress"]["total"] == 6
    assert tasks_response.json()["milestones"][0]["progress"]["blocked"] == 1
    assert tasks_response.json()["milestones"][0]["tasks"][0]["prd_refs"] == ["PRD-1"]
    assert token_response.json()["tasks"][1]["attribution"] == "shared"
    assert token_response.json()["tasks"][0]["model_label"] == "gpt-5.5"


def test_task_token_usage_uses_provider_label_when_model_name_is_missing(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text(
        """
milestones:
  - id: delivery
    title: Delivery
    tasks:
      - id: provider-only
        title: Provider only task
        status: doing
        prd_refs:
          - PRD-1
        codex_sessions:
          - s-provider
""",
        encoding="utf-8",
    )
    codex_root = tmp_path / ".codex"
    sqlite_dir = codex_root / "sqlite"
    sqlite_dir.mkdir(parents=True)
    codex_db = sqlite_dir / "state_5.sqlite"
    create_codex_db(codex_db, str(project_dir.resolve()))
    rollout_dir = codex_root / "sessions" / "2026" / "06" / "30"
    rollout_dir.mkdir(parents=True)
    (rollout_dir / "rollout-provider-only.jsonl").write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"s-provider","id":"s-provider","cwd":"/tmp/project-provider","model_provider":"openai","title":"Provider Session"}}
{"timestamp":"2026-06-29T16:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":300,"cached_input_tokens":100,"output_tokens":60,"reasoning_output_tokens":15,"total_tokens":360}}}}
""".strip(),
        encoding="utf-8",
    )

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)
    task = usage.tasks[0]

    assert task.model_label == "OpenAI model"
    assert task.models == []
    assert task.model_providers == ["openai"]
