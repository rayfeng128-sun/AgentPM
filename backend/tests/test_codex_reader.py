from datetime import UTC, datetime
from pathlib import Path
import sqlite3

from app.codex_reader import codex_state_available, read_rollout_session, read_sessions_by_ids, read_sessions_for_path, summarize_tokens


def create_codex_db(path: Path) -> None:
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
        ("a", "Session A", "/tmp/project-a", "gpt", 10, 200, "/tmp/a.jsonl"),
    )
    conn.execute(
        "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("b", "Session B", "/tmp/project-b", "gpt", 20, 100, "/tmp/b.jsonl"),
    )
    conn.commit()
    conn.close()


def test_reads_sessions_for_matching_path(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    create_codex_db(db)

    sessions = read_sessions_for_path("/tmp/project-a", db_path=db)
    tokens = summarize_tokens(sessions)

    assert [session.id for session in sessions] == ["a"]
    assert tokens.total == 10
    assert tokens.recent_session == 10
    assert tokens.unavailable is False


def test_missing_codex_db_marks_tokens_unavailable(tmp_path: Path) -> None:
    missing = tmp_path / "missing.sqlite"

    assert codex_state_available(missing) is False
    assert read_sessions_for_path("/tmp/project-a", db_path=missing) == []
    assert summarize_tokens([], unavailable=True).model_dump() == {
        "total": None,
        "recent_session": None,
        "unavailable": True,
    }


def test_reads_sessions_by_id_and_prefers_rollout_token_breakdown(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    create_codex_db(db)
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-15T15:39:11.109Z","type":"session_meta","payload":{"id":"a"}}
{"timestamp":"2026-06-15T15:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":341516,"cached_input_tokens":266880,"output_tokens":5297,"reasoning_output_tokens":1963,"total_tokens":346813}}}}
""".strip(),
        encoding="utf-8",
    )

    conn = sqlite3.connect(db)
    conn.execute("UPDATE threads SET rollout_path = ? WHERE id = ?", (str(rollout), "a"))
    conn.commit()
    conn.close()

    sessions = read_sessions_by_ids(["a"], db_path=db)

    assert [session.id for session in sessions] == ["a"]
    assert sessions[0].tokens_used == 346813
    assert sessions[0].input_tokens == 341516
    assert sessions[0].cached_input_tokens == 266880
    assert sessions[0].output_tokens == 5297
    assert sessions[0].reasoning_output_tokens == 1963


def test_reads_sessions_for_matching_path_from_rollout_fallback(tmp_path: Path) -> None:
    codex_root = tmp_path / ".codex"
    sqlite_dir = codex_root / "sqlite"
    sqlite_dir.mkdir(parents=True)
    db = sqlite_dir / "state_5.sqlite"
    create_codex_db(db)
    rollout_dir = codex_root / "sessions" / "2026" / "06" / "30"
    rollout_dir.mkdir(parents=True)
    rollout = rollout_dir / "rollout-2026-06-30T00-00-39-session-c.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-c","id":"session-c","cwd":"/tmp/project-c","model":"gpt-5.5","title":"Rollout Session","rollout_path":"/tmp/rollout-session-c.jsonl"}}
{"timestamp":"2026-06-29T16:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":50,"output_tokens":20,"reasoning_output_tokens":5,"total_tokens":120}}}}
""".strip(),
        encoding="utf-8",
    )

    sessions = read_sessions_for_path("/tmp/project-c", db_path=db)

    assert [session.id for session in sessions] == ["session-c"]
    assert sessions[0].title == "Rollout Session"
    assert sessions[0].tokens_used == 120
    assert sessions[0].input_tokens == 100
    assert sessions[0].updated_at_ms == int(datetime(2026, 6, 29, 16, 40, 27, 693000, tzinfo=UTC).timestamp() * 1000)


def test_reads_session_by_id_from_rollout_fallback_when_sqlite_has_no_row(tmp_path: Path) -> None:
    codex_root = tmp_path / ".codex"
    sqlite_dir = codex_root / "sqlite"
    sqlite_dir.mkdir(parents=True)
    db = sqlite_dir / "state_5.sqlite"
    create_codex_db(db)
    rollout_dir = codex_root / "sessions" / "2026" / "06" / "30"
    rollout_dir.mkdir(parents=True)
    rollout = rollout_dir / "rollout-2026-06-30T00-00-39-session-d.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-d","id":"session-d","cwd":"/tmp/project-d","model":"gpt-5.5","title":"Fallback Session"}}
{"timestamp":"2026-06-29T16:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":200,"cached_input_tokens":80,"output_tokens":40,"reasoning_output_tokens":10,"total_tokens":240}}}}
""".strip(),
        encoding="utf-8",
    )

    sessions = read_sessions_by_ids(["session-d"], db_path=db)

    assert [session.id for session in sessions] == ["session-d"]
    assert sessions[0].cwd == "/tmp/project-d"
    assert sessions[0].tokens_used == 240


def test_reads_model_slug_from_rollout_session_meta(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-model-slug.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-e","id":"session-e","cwd":"/tmp/project-e","model_slug":"gpt-5.5","title":"Model Slug Session"}}
{"timestamp":"2026-06-29T16:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":120,"cached_input_tokens":40,"output_tokens":30,"reasoning_output_tokens":5,"total_tokens":150}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert session.model == "gpt-5.5"
    assert session.tokens_used == 150


def test_rollout_session_without_model_keeps_model_empty(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-provider-only.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-f","id":"session-f","cwd":"/tmp/project-f","model_provider":"openai","title":"Provider Only Session"}}
{"timestamp":"2026-06-29T16:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":90,"cached_input_tokens":20,"output_tokens":10,"reasoning_output_tokens":3,"total_tokens":100}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert session.model is None
    assert session.tokens_used == 100


def test_rollout_session_reads_model_from_turn_context_when_meta_omits_it(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-turn-context-model.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-g","id":"session-g","cwd":"/tmp/project-g","model_provider":"openai","title":"Turn Context Session"}}
{"timestamp":"2026-06-29T16:00:44.296Z","type":"turn_context","payload":{"model":"gpt-5.4","model_provider":"openai"}}
{"timestamp":"2026-06-29T16:40:27.693Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":90,"cached_input_tokens":20,"output_tokens":10,"reasoning_output_tokens":3,"total_tokens":100}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert session.model == "gpt-5.4"
    assert session.model_provider == "openai"
    assert session.tokens_used == 100


def test_rollout_session_uses_session_meta_timestamp_when_no_later_event_timestamp_exists(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-meta-timestamp.jsonl"
    rollout.write_text(
        """
{"type":"session_meta","payload":{"session_id":"session-h","id":"session-h","cwd":"/tmp/project-h","model":"gpt-5.5","title":"Meta Timestamp Session","timestamp":"2026-06-29T16:00:43.296Z"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":90,"cached_input_tokens":20,"output_tokens":10,"reasoning_output_tokens":3,"total_tokens":100}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert session.updated_at_ms == int(datetime(2026, 6, 29, 16, 0, 43, 296000, tzinfo=UTC).timestamp() * 1000)


def test_rollout_session_collects_timestamped_token_snapshots(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-token-snapshots.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-i","id":"session-i","cwd":"/tmp/project-i","model":"gpt-5.5","title":"Snapshot Session"}}
{"timestamp":"2026-06-29T16:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":10,"cached_input_tokens":2,"output_tokens":3,"reasoning_output_tokens":1,"total_tokens":13}}}}
{"timestamp":"2026-06-29T16:10:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":20,"cached_input_tokens":4,"output_tokens":6,"reasoning_output_tokens":2,"total_tokens":26}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert [snapshot.timestamp_ms for snapshot in session.token_snapshots] == [
        int(datetime(2026, 6, 29, 16, 5, 0, tzinfo=UTC).timestamp() * 1000),
        int(datetime(2026, 6, 29, 16, 10, 0, tzinfo=UTC).timestamp() * 1000),
    ]
    assert [snapshot.total_tokens for snapshot in session.token_snapshots] == [13, 26]
    assert session.tokens_used == 26
    assert session.input_tokens == 20
    assert session.cached_input_tokens == 4
    assert session.output_tokens == 6
    assert session.reasoning_output_tokens == 2


def test_rollout_session_captures_turn_context_timezone(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-timezone.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-tz","id":"session-tz","cwd":"/tmp/project-tz","model":"gpt-5.5","title":"Timezone Session"}}
{"timestamp":"2026-06-29T16:00:44.000Z","type":"turn_context","payload":{"timezone":"Asia/Shanghai"}}
{"timestamp":"2026-06-29T16:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":10,"cached_input_tokens":2,"output_tokens":3,"reasoning_output_tokens":1,"total_tokens":13}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert session.timezone == "Asia/Shanghai"


def test_rollout_session_skips_token_snapshots_without_usable_timestamp(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-token-snapshots-missing-timestamp.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-j","id":"session-j","cwd":"/tmp/project-j","model":"gpt-5.5","title":"Missing Snapshot Timestamp Session"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":10,"cached_input_tokens":2,"output_tokens":3,"reasoning_output_tokens":1,"total_tokens":13}}}}
{"timestamp":"not-a-timestamp","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":20,"cached_input_tokens":4,"output_tokens":6,"reasoning_output_tokens":2,"total_tokens":26}}}}
{"timestamp":"2026-06-29T16:10:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":30,"cached_input_tokens":6,"output_tokens":9,"reasoning_output_tokens":3,"total_tokens":39}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert len(session.token_snapshots) == 1
    assert session.token_snapshots[0].timestamp_ms == int(datetime(2026, 6, 29, 16, 10, 0, tzinfo=UTC).timestamp() * 1000)
    assert session.token_snapshots[0].total_tokens == 39
    assert session.tokens_used == 39
    assert session.input_tokens == 30
    assert session.cached_input_tokens == 6
    assert session.output_tokens == 9
    assert session.reasoning_output_tokens == 3


def test_sqlite_backed_session_includes_rollout_token_snapshots(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    create_codex_db(db)
    rollout = tmp_path / "rollout-sqlite-snapshots.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"id":"a","cwd":"/tmp/project-a","title":"Session A"}}
{"timestamp":"2026-06-29T16:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":10,"cached_input_tokens":2,"output_tokens":3,"reasoning_output_tokens":1,"total_tokens":13}}}}
{"timestamp":"2026-06-29T16:10:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":20,"cached_input_tokens":4,"output_tokens":6,"reasoning_output_tokens":2,"total_tokens":26}}}}
""".strip(),
        encoding="utf-8",
    )

    conn = sqlite3.connect(db)
    conn.execute("UPDATE threads SET rollout_path = ? WHERE id = ?", (str(rollout), "a"))
    conn.commit()
    conn.close()

    sessions = read_sessions_by_ids(["a"], db_path=db)

    assert len(sessions) == 1
    assert [snapshot.timestamp_ms for snapshot in sessions[0].token_snapshots] == [
        int(datetime(2026, 6, 29, 16, 5, 0, tzinfo=UTC).timestamp() * 1000),
        int(datetime(2026, 6, 29, 16, 10, 0, tzinfo=UTC).timestamp() * 1000),
    ]
    assert [snapshot.total_tokens for snapshot in sessions[0].token_snapshots] == [13, 26]
    assert sessions[0].tokens_used == 26


def test_rollout_session_sorts_out_of_order_token_snapshots_and_uses_latest_timestamped_totals(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-out-of-order-token-snapshots.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-29T16:00:43.296Z","type":"session_meta","payload":{"session_id":"session-k","id":"session-k","cwd":"/tmp/project-k","model":"gpt-5.5","title":"Out Of Order Snapshot Session"}}
{"timestamp":"2026-06-29T16:10:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":30,"cached_input_tokens":6,"output_tokens":9,"reasoning_output_tokens":3,"total_tokens":39}}}}
{"timestamp":"2026-06-29T16:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":10,"cached_input_tokens":2,"output_tokens":3,"reasoning_output_tokens":1,"total_tokens":13}}}}
{"timestamp":"2026-06-29T16:07:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":20,"cached_input_tokens":4,"output_tokens":6,"reasoning_output_tokens":2,"total_tokens":26}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert [snapshot.timestamp_ms for snapshot in session.token_snapshots] == [
        int(datetime(2026, 6, 29, 16, 5, 0, tzinfo=UTC).timestamp() * 1000),
        int(datetime(2026, 6, 29, 16, 7, 0, tzinfo=UTC).timestamp() * 1000),
        int(datetime(2026, 6, 29, 16, 10, 0, tzinfo=UTC).timestamp() * 1000),
    ]
    assert [snapshot.total_tokens for snapshot in session.token_snapshots] == [13, 26, 39]
    assert session.updated_at_ms == int(datetime(2026, 6, 29, 16, 10, 0, tzinfo=UTC).timestamp() * 1000)
    assert session.tokens_used == 39
    assert session.input_tokens == 30
    assert session.cached_input_tokens == 6
    assert session.output_tokens == 9
    assert session.reasoning_output_tokens == 3
