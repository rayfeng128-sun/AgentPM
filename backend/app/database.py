from pathlib import Path
import sqlite3

APP_DB = Path.home() / ".agentpm" / "agentpm.sqlite"


def connect(db_path: Path = APP_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS collection_runs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            warnings_json TEXT NOT NULL DEFAULT '[]',
            snapshot_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS structured_tasks (
            project_id TEXT NOT NULL,
            task_key TEXT NOT NULL,
            run_id TEXT NOT NULL,
            milestone_id TEXT,
            milestone_title TEXT,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            token_budget INTEGER,
            task_json TEXT NOT NULL,
            PRIMARY KEY (project_id, task_key)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_collection_runs_project_started
        ON collection_runs (project_id, started_at DESC)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_structured_tasks_project_run
        ON structured_tasks (project_id, run_id)
        """
    )
    conn.commit()
