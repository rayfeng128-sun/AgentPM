from pathlib import Path
import sqlite3

from app.database import connect, init_db
from app.structured_models import FieldState, SourceRef, StructuredFieldValue, StructuredMilestone, StructuredProjectSnapshot, StructuredTask
from app.structured_store import load_latest_snapshot, save_snapshot


def make_snapshot() -> StructuredProjectSnapshot:
    return StructuredProjectSnapshot(
        project_id="demo",
        collected_at="2026-07-05T00:00:00+00:00",
        warnings=["warn"],
        milestones=[
            StructuredMilestone(
                milestone_id="m1",
                title="Milestone",
                tasks=[
                    StructuredTask(
                        task_key="task-1",
                        title="Task 1",
                        status="doing",
                        user_story=StructuredFieldValue(
                            value="As a user, I can test persistence",
                            state=FieldState.explicit,
                            source=SourceRef(source_type="agentpm.yaml", path_or_id="agentpm.yaml", locator="tasks.task-1.user_story"),
                            confidence=1.0,
                        ),
                        scope=StructuredFieldValue(value="Scope", state=FieldState.inferred),
                        acceptance_criteria=StructuredFieldValue(value="Done", state=FieldState.needs_review),
                        verification_method=StructuredFieldValue(value="pytest", state=FieldState.missing),
                        prd_refs=["docs/product/05-structured-project-data-prd.md"],
                        codex_sessions=["s1"],
                        token_budget=123,
                    )
                ],
            )
        ],
    )


def test_init_db_creates_structured_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "agentpm.sqlite"
    with connect(db_path) as conn:
        init_db(conn)
        table_names = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}

    assert {"projects", "collection_runs", "structured_tasks"}.issubset(table_names)


def test_store_and_load_latest_snapshot_round_trips(tmp_path: Path) -> None:
    db_path = tmp_path / "agentpm.sqlite"
    snapshot = make_snapshot()
    with connect(db_path) as conn:
        init_db(conn)
        saved = save_snapshot(conn, snapshot)
        loaded = load_latest_snapshot(conn, snapshot.project_id)

    assert saved.project_id == snapshot.project_id
    assert saved.snapshot is not None
    assert loaded == snapshot
