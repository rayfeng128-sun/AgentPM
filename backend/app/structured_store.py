from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from .structured_models import CollectionRun, StructuredProjectSnapshot, StructuredTask


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def snapshot_to_json(snapshot: StructuredProjectSnapshot) -> str:
    return snapshot.model_dump_json()


def snapshot_from_json(payload: str) -> StructuredProjectSnapshot:
    return StructuredProjectSnapshot.model_validate_json(payload)


def save_snapshot(conn: sqlite3.Connection, snapshot: StructuredProjectSnapshot) -> CollectionRun:
    run_id = uuid.uuid4().hex
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO collection_runs (
            id, project_id, started_at, finished_at, status, warnings_json, snapshot_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            snapshot.project_id,
            now,
            snapshot.collected_at,
            snapshot.status,
            json.dumps(snapshot.warnings, ensure_ascii=False),
            snapshot_to_json(snapshot),
        ),
    )
    conn.execute("DELETE FROM structured_tasks WHERE project_id = ?", (snapshot.project_id,))

    for milestone in snapshot.milestones:
        for task in milestone.tasks:
            conn.execute(
                """
                INSERT OR REPLACE INTO structured_tasks (
                    project_id,
                    task_key,
                    run_id,
                    milestone_id,
                    milestone_title,
                    title,
                    status,
                    token_budget,
                    task_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.project_id,
                    task.task_key,
                    run_id,
                    task.milestone_id,
                    task.milestone_title,
                    task.title,
                    task.status,
                    task.token_budget,
                    task.model_dump_json(),
                ),
            )

    conn.execute(
        """
        UPDATE collection_runs
        SET finished_at = ?, status = ?, warnings_json = ?, snapshot_json = ?
        WHERE id = ?
        """,
        (snapshot.collected_at, snapshot.status, json.dumps(snapshot.warnings, ensure_ascii=False), snapshot_to_json(snapshot), run_id),
    )
    conn.commit()

    return CollectionRun(
        id=run_id,
        project_id=snapshot.project_id,
        started_at=now,
        finished_at=snapshot.collected_at,
        status=snapshot.status,
        warnings=snapshot.warnings,
        snapshot=snapshot,
    )


def load_latest_snapshot(conn: sqlite3.Connection, project_id: str) -> StructuredProjectSnapshot | None:
    row = conn.execute(
        """
        SELECT snapshot_json
        FROM collection_runs
        WHERE project_id = ?
        ORDER BY COALESCE(finished_at, started_at) DESC, started_at DESC
        LIMIT 1
        """,
        (project_id,),
    ).fetchone()
    if row is None:
        return None
    payload = row["snapshot_json"] if isinstance(row, sqlite3.Row) else row[0]
    if not payload:
        return None
    return snapshot_from_json(payload)
