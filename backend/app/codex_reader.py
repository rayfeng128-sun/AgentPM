from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Iterable

from .models import CodexSession, TokenSnapshot, TokenSummary

DEFAULT_CODEX_STATE_DB = Path.home() / ".codex" / "sqlite" / "state_5.sqlite"


def codex_state_available(db_path: Path = DEFAULT_CODEX_STATE_DB) -> bool:
    return db_path.exists()


def read_sessions_for_path(project_path: str, db_path: Path = DEFAULT_CODEX_STATE_DB) -> list[CodexSession]:
    rows = read_thread_rows_for_path(project_path, db_path=db_path)
    sessions = [session_from_row(row) for row in rows]
    if sessions:
        return sessions
    return read_rollout_sessions_for_path(project_path, db_path=db_path)


def read_sessions_by_ids(session_ids: Iterable[str], db_path: Path = DEFAULT_CODEX_STATE_DB) -> list[CodexSession]:
    session_ids = [session_id for session_id in session_ids if session_id]
    if not session_ids or not db_path.exists():
        return []
    placeholders = ", ".join("?" for _ in session_ids)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT id, title, cwd, model, tokens_used, updated_at_ms, rollout_path
            FROM threads
            WHERE id IN ({placeholders})
            """,
            session_ids,
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    row_by_id = {str(row["id"]): row for row in rows}
    sessions = [session_from_row(row_by_id[session_id]) for session_id in session_ids if session_id in row_by_id]
    missing_ids = [session_id for session_id in session_ids if session_id not in row_by_id]
    if not missing_ids:
        return sessions
    fallback_by_id = {session.id: session for session in read_rollout_sessions(db_path=db_path)}
    sessions.extend(fallback_by_id[session_id] for session_id in missing_ids if session_id in fallback_by_id)
    return sessions


def read_thread_rows_for_path(project_path: str, db_path: Path) -> list[sqlite3.Row]:
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """
            SELECT id, title, cwd, model, tokens_used, updated_at_ms, rollout_path
            FROM threads
            WHERE cwd = ?
            ORDER BY updated_at_ms DESC
            LIMIT 50
            """,
            (project_path,),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def read_rollout_sessions_for_path(project_path: str, db_path: Path = DEFAULT_CODEX_STATE_DB) -> list[CodexSession]:
    return [session for session in read_rollout_sessions(db_path=db_path) if session.cwd == project_path]


def read_rollout_sessions(db_path: Path = DEFAULT_CODEX_STATE_DB) -> list[CodexSession]:
    codex_root = codex_root_for_db_path(db_path)
    if codex_root is None:
        return []

    sessions: list[CodexSession] = []
    seen_ids: set[str] = set()
    rollout_dirs = [codex_root / "sessions", codex_root / "archived_sessions"]
    for rollout_dir in rollout_dirs:
        if not rollout_dir.exists():
            continue
        for path in sorted(rollout_dir.rglob("rollout-*.jsonl"), reverse=True):
            session = read_rollout_session(path)
            if session is None or session.id in seen_ids:
                continue
            seen_ids.add(session.id)
            sessions.append(session)
    return sorted(sessions, key=lambda session: session.updated_at_ms or 0, reverse=True)


def read_rollout_session(path: Path) -> CodexSession | None:
    meta: dict[str, object] | None = None
    breakdown: dict[str, int] | None = None
    seen_models: list[str] = []
    seen_model_providers: list[str] = []
    seen_timezone: str | None = None
    token_snapshots: list[TokenSnapshot] = []
    session_meta_timestamp_ms: int | None = None
    latest_timestamp_ms: int | None = None
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event_timestamp_ms = parse_timestamp_ms(event.get("timestamp"))
                if event_timestamp_ms is not None:
                    latest_timestamp_ms = event_timestamp_ms
                if event.get("type") == "session_meta":
                    meta = event.get("payload") or {}
                    session_meta_timestamp_ms = parse_timestamp_ms(meta.get("timestamp"))
                    continue
                if event.get("type") == "turn_context":
                    payload = event.get("payload") or {}
                    push_unique_string(seen_models, payload.get("model"))
                    push_unique_string(seen_model_providers, payload.get("model_provider"))
                    if seen_timezone is None and isinstance(payload.get("timezone"), str) and payload.get("timezone").strip():
                        seen_timezone = str(payload.get("timezone")).strip()
                    continue
                if event.get("type") != "event_msg":
                    continue
                payload = event.get("payload") or {}
                if payload.get("type") == "token_count":
                    usage = read_token_usage(payload)
                    breakdown = usage
                    if event_timestamp_ms is not None:
                        token_snapshots.append(TokenSnapshot(timestamp_ms=event_timestamp_ms, **usage))
    except OSError:
        return None

    if not meta:
        return None

    session_id = str(meta.get("session_id") or meta.get("id") or "")
    cwd = str(meta.get("cwd") or "")
    if not session_id or not cwd:
        return None

    token_snapshots.sort(key=lambda snapshot: snapshot.timestamp_ms)
    latest_snapshot = token_snapshots[-1] if token_snapshots else None
    if latest_snapshot is not None:
        breakdown = snapshot_usage(latest_snapshot)
        latest_timestamp_ms = latest_snapshot.timestamp_ms

    return CodexSession(
        id=session_id,
        title=str(meta.get("title") or meta.get("thread_name") or "Untitled Codex session"),
        cwd=cwd,
        model=model_from_rollout(meta, seen_models),
        model_provider=model_provider_from_rollout(meta, seen_model_providers),
        tokens_used=int((breakdown or {}).get("total_tokens") or 0),
        updated_at_ms=latest_timestamp_ms or session_meta_timestamp_ms,
        rollout_path=str(path),
        input_tokens=optional_int(breakdown, "input_tokens"),
        cached_input_tokens=optional_int(breakdown, "cached_input_tokens"),
        output_tokens=optional_int(breakdown, "output_tokens"),
        reasoning_output_tokens=optional_int(breakdown, "reasoning_output_tokens"),
        token_snapshots=token_snapshots,
        timezone=seen_timezone,
    )


def session_from_row(row: sqlite3.Row) -> CodexSession:
    rollout_session = read_rollout_session(Path(row["rollout_path"])) if row["rollout_path"] else None
    breakdown = snapshot_usage(rollout_session.token_snapshots[-1]) if rollout_session and rollout_session.token_snapshots else None
    if breakdown is None and rollout_session is not None:
        breakdown = {
            "input_tokens": rollout_session.input_tokens or 0,
            "cached_input_tokens": rollout_session.cached_input_tokens or 0,
            "output_tokens": rollout_session.output_tokens or 0,
            "reasoning_output_tokens": rollout_session.reasoning_output_tokens or 0,
            "total_tokens": rollout_session.tokens_used,
        }
    if breakdown is None:
        breakdown = read_rollout_token_usage(row["rollout_path"])
    tokens_used = int(row["tokens_used"] or 0)
    if breakdown is not None:
        tokens_used = int(breakdown.get("total_tokens") or tokens_used)

    return CodexSession(
        id=str(row["id"]),
        title=str(row["title"] or "Untitled Codex session"),
        cwd=str(row["cwd"]),
        model=row["model"] or (rollout_session.model if rollout_session is not None else None),
        model_provider=rollout_session.model_provider if rollout_session is not None else None,
        tokens_used=tokens_used,
        updated_at_ms=(rollout_session.updated_at_ms if rollout_session and rollout_session.updated_at_ms is not None else row["updated_at_ms"]),
        rollout_path=row["rollout_path"],
        input_tokens=optional_int(breakdown, "input_tokens"),
        cached_input_tokens=optional_int(breakdown, "cached_input_tokens"),
        output_tokens=optional_int(breakdown, "output_tokens"),
        reasoning_output_tokens=optional_int(breakdown, "reasoning_output_tokens"),
        token_snapshots=rollout_session.token_snapshots if rollout_session is not None else [],
        timezone=rollout_session.timezone if rollout_session is not None else None,
    )


def read_rollout_token_usage(rollout_path: str | None) -> dict[str, int] | None:
    if not rollout_path:
        return None
    path = Path(rollout_path)
    if not path.exists():
        return None

    latest_usage: dict[str, int] | None = None
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") != "event_msg":
                    continue
                payload = event.get("payload") or {}
                if payload.get("type") != "token_count":
                    continue
                latest_usage = read_token_usage(payload)
    except OSError:
        return None
    return latest_usage


def codex_root_for_db_path(db_path: Path) -> Path | None:
    if db_path.parent.name == "sqlite":
        return db_path.parent.parent
    if db_path.parent.exists():
        return db_path.parent
    return None


def optional_int(usage: dict[str, int] | None, key: str) -> int | None:
    if usage is None:
        return None
    return int(usage[key])


def read_token_usage(payload: dict[str, object]) -> dict[str, int]:
    usage = ((payload.get("info") or {}).get("total_token_usage")) or {}
    return {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "cached_input_tokens": int(usage.get("cached_input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "reasoning_output_tokens": int(usage.get("reasoning_output_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }


def snapshot_usage(snapshot: TokenSnapshot) -> dict[str, int]:
    return {
        "input_tokens": snapshot.input_tokens,
        "cached_input_tokens": snapshot.cached_input_tokens,
        "output_tokens": snapshot.output_tokens,
        "reasoning_output_tokens": snapshot.reasoning_output_tokens,
        "total_tokens": snapshot.total_tokens,
    }


def parse_timestamp_ms(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    else:
        parsed = parsed.astimezone(UTC)
    return int(parsed.timestamp() * 1000)


def model_from_meta(meta: dict[str, object]) -> str | None:
    for key in ("model", "model_name", "model_slug", "model_id"):
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def model_from_rollout(meta: dict[str, object], seen_models: list[str]) -> str | None:
    direct = model_from_meta(meta)
    if direct:
        return direct
    if len(seen_models) == 1:
        return seen_models[0]
    return None


def model_provider_from_rollout(meta: dict[str, object], seen_model_providers: list[str]) -> str | None:
    value = meta.get("model_provider")
    if isinstance(value, str) and value.strip():
        return value.strip()
    if len(seen_model_providers) == 1:
        return seen_model_providers[0]
    return None


def push_unique_string(values: list[str], candidate: object) -> None:
    if not isinstance(candidate, str):
        return
    normalized = candidate.strip()
    if not normalized or normalized in values:
        return
    values.append(normalized)


def summarize_tokens(sessions: list[CodexSession], unavailable: bool = False) -> TokenSummary:
    if unavailable:
        return TokenSummary(total=None, recent_session=None, unavailable=True)
    total = sum(session.tokens_used for session in sessions)
    recent_session = sessions[0].tokens_used if sessions else 0
    return TokenSummary(total=total, recent_session=recent_session)
