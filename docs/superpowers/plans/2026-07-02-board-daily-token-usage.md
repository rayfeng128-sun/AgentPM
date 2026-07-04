# Board Daily Token Usage Reconstruction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Board daily token usage metric so the chart shows true per-day token growth reconstructed from rollout history instead of placing full session totals on a single day.

**Architecture:** Extend the Codex rollout reader to extract cumulative token snapshots with timestamps, then derive per-day deltas from those snapshots inside the backend analytics layer. Keep the frontend chart structure intact where possible, but update its empty and partial-state messaging to reflect reconstructed daily history rather than session-dated totals.

**Tech Stack:** FastAPI, Pydantic, pytest, React, TypeScript, Node test runner, CSS

---

## File Structure

- Modify: `backend/app/models.py`
  Add snapshot-level backend models only if needed to pass typed daily reconstruction data through existing analytics helpers.
- Modify: `backend/app/codex_reader.py`
  Parse rollout `token_count` timeline snapshots with timestamps and expose them on loaded sessions.
- Modify: `backend/app/task_analytics.py`
  Reconstruct per-day token deltas from cumulative snapshots and build project/task daily chart data.
- Modify: `backend/tests/test_codex_reader.py`
  Cover rollout snapshot extraction, timestamp parsing, and fallback behavior for incomplete timelines.
- Modify: `backend/tests/test_task_analytics.py`
  Cover multi-day reconstruction, same-day cumulative deltas, partial-data exclusion, and shared attribution in daily views.
- Modify: `backend/tests/test_briefing.py`
  Cover real briefing payload output for rollout-backed multi-day daily history.
- Modify: `frontend/src/App.tsx`
  Keep the Board chart component, but align copy and assumptions with the reconstructed daily dataset.
- Modify: `frontend/src/lib/boardDailyTokenUsage.ts`
  Keep frontend shaping logic compatible with the updated backend payload and partial-data notes.
- Modify: `frontend/src/lib/boardDailyTokenUsage.test.mjs`
  Cover frontend handling for reconstructed multi-day data and new partial-data notes.
- Modify: `references/Harness/changes/2026-07-02/board-low-fi-prototype-design/change.md`
  Record that the daily usage metric was corrected from session-date placement to daily reconstruction.

## Task 1: Add Failing Reader Tests For Rollout Token Snapshots

**Files:**
- Modify: `backend/tests/test_codex_reader.py`
- Test: `backend/tests/test_codex_reader.py`

- [ ] **Step 1: Write the failing snapshot extraction tests**

Add these tests to `backend/tests/test_codex_reader.py`:

```python
def test_rollout_session_reads_token_snapshots_with_timestamps(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-snapshots.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-28T10:00:00.000Z","type":"session_meta","payload":{"session_id":"session-i","id":"session-i","cwd":"/tmp/project-i","model":"gpt-5.5","title":"Snapshot Session"}}
{"timestamp":"2026-06-28T10:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":20,"reasoning_output_tokens":0,"total_tokens":120}}}}
{"timestamp":"2026-06-29T09:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":250,"cached_input_tokens":0,"output_tokens":50,"reasoning_output_tokens":0,"total_tokens":300}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert [snapshot.total_tokens for snapshot in session.token_snapshots] == [120, 300]
    assert len(session.token_snapshots) == 2


def test_rollout_session_skips_token_snapshot_without_timestamp(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-missing-snapshot-time.jsonl"
    rollout.write_text(
        """
{"timestamp":"2026-06-28T10:00:00.000Z","type":"session_meta","payload":{"session_id":"session-j","id":"session-j","cwd":"/tmp/project-j","model":"gpt-5.5","title":"Missing Snapshot Time Session"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":20,"reasoning_output_tokens":0,"total_tokens":120}}}}
""".strip(),
        encoding="utf-8",
    )

    session = read_rollout_session(rollout)

    assert session is not None
    assert session.token_snapshots == []
```

- [ ] **Step 2: Run the reader tests to verify they fail**

Run: `cd backend && ./.venv/bin/python -m pytest tests/test_codex_reader.py -v`

Expected: `FAIL` because `CodexSession` does not yet expose `token_snapshots`.

- [ ] **Step 3: Add snapshot models to the backend types**

Update `backend/app/models.py` by inserting:

```python
class TokenSnapshot(BaseModel):
    timestamp_ms: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_tokens: int
```

Then extend `CodexSession`:

```python
class CodexSession(BaseModel):
    id: str
    title: str
    cwd: str
    model: str | None = None
    model_provider: str | None = None
    tokens_used: int = 0
    updated_at_ms: int | None = None
    rollout_path: str | None = None
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    token_snapshots: list[TokenSnapshot] = Field(default_factory=list)
```

- [ ] **Step 4: Parse rollout token snapshots in the reader**

Update `backend/app/codex_reader.py` so `read_rollout_session()` accumulates snapshot entries while still preserving the latest aggregate breakdown:

```python
snapshots: list[TokenSnapshot] = []
...
if payload.get("type") == "token_count":
    usage = ((payload.get("info") or {}).get("total_token_usage")) or {}
    breakdown = {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "cached_input_tokens": int(usage.get("cached_input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "reasoning_output_tokens": int(usage.get("reasoning_output_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }
    if event_timestamp_ms is not None:
        snapshots.append(
            TokenSnapshot(
                timestamp_ms=event_timestamp_ms,
                input_tokens=breakdown["input_tokens"],
                cached_input_tokens=breakdown["cached_input_tokens"],
                output_tokens=breakdown["output_tokens"],
                reasoning_output_tokens=breakdown["reasoning_output_tokens"],
                total_tokens=breakdown["total_tokens"],
            )
        )
```

Then pass the snapshots into `CodexSession(...)`:

```python
token_snapshots=snapshots,
```

- [ ] **Step 5: Re-run the reader tests to verify they pass**

Run: `cd backend && ./.venv/bin/python -m pytest tests/test_codex_reader.py -v`

Expected: `PASS`

- [ ] **Step 6: Commit the reader groundwork**

```bash
git add backend/app/models.py backend/app/codex_reader.py backend/tests/test_codex_reader.py
git commit -m "feat: parse rollout token snapshots"
```

## Task 2: Add Failing Analytics Tests For True Multi-Day Reconstruction

**Files:**
- Modify: `backend/tests/test_task_analytics.py`
- Test: `backend/tests/test_task_analytics.py`

- [ ] **Step 1: Write the failing analytics tests**

Add these tests to `backend/tests/test_task_analytics.py`:

```python
def test_task_token_usage_reconstructs_project_days_from_rollout_snapshots(tmp_path: Path) -> None:
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
          - session-k
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
    (rollout_dir / "rollout-session-k.jsonl").write_text(
        """
{"timestamp":"2026-06-28T10:00:00.000Z","type":"session_meta","payload":{"session_id":"session-k","id":"session-k","cwd":"/tmp/other-path","model":"gpt-5.5","title":"Linked Session"}}
{"timestamp":"2026-06-28T10:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":20,"reasoning_output_tokens":0,"total_tokens":120}}}}
{"timestamp":"2026-06-29T09:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":250,"cached_input_tokens":0,"output_tokens":50,"reasoning_output_tokens":0,"total_tokens":300}}}}
{"timestamp":"2026-06-29T16:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":300,"cached_input_tokens":0,"output_tokens":60,"reasoning_output_tokens":0,"total_tokens":360}}}}
""".strip(),
        encoding="utf-8",
    )

    usage = build_task_token_usage("demo", load_plan(str(project_dir)), str(project_dir.resolve()), codex_db)

    assert usage.daily_token_usage is not None
    assert usage.daily_token_usage.project_days == [
        {"date": "2026-06-28", "tokens": 120},
        {"date": "2026-06-29", "tokens": 240},
    ]


def test_task_token_usage_marks_partial_when_only_final_total_exists(tmp_path: Path) -> None:
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
    assert usage.daily_token_usage.has_partial_data is True
    assert any("reconstructed into daily history" in note for note in usage.daily_token_usage.notes)
```

- [ ] **Step 2: Run the analytics tests to verify they fail**

Run: `cd backend && ./.venv/bin/python -m pytest tests/test_task_analytics.py -v`

Expected: `FAIL` because daily analytics still bucket full session totals by one date.

- [ ] **Step 3: Add a small helper that reconstructs per-day deltas**

In `backend/app/task_analytics.py`, add:

```python
def build_session_daily_deltas(session: CodexSession) -> dict[str, int]:
    if not session.token_snapshots:
        return {}

    ordered = sorted(session.token_snapshots, key=lambda snapshot: snapshot.timestamp_ms)
    previous_total = 0
    per_day: dict[str, int] = {}
    for snapshot in ordered:
        delta = snapshot.total_tokens - previous_total
        previous_total = snapshot.total_tokens
        if delta <= 0:
            continue
        date = day_key(snapshot.timestamp_ms)
        if date is None:
            continue
        per_day[date] = per_day.get(date, 0) + delta
    return per_day
```

- [ ] **Step 4: Replace session-date bucketting with delta reconstruction**

Update `build_daily_token_usage()` in `backend/app/task_analytics.py`:

```python
for task in tasks:
    day_totals: dict[str, int] = {}
    for session in task.sessions:
        if session.missing or session.tokens is None:
            continue
        session_deltas = build_session_daily_deltas(
            CodexSession(
                id=session.id,
                title=session.title or "Untitled Codex session",
                cwd="",
                tokens_used=session.tokens or 0,
                updated_at_ms=session.updated_at_ms,
                token_snapshots=session.token_snapshots,
            )
        )
        if not session_deltas:
            has_partial_data = True
            continue
        for date, tokens in session_deltas.items():
            project_totals[date] = project_totals.get(date, 0) + tokens
            day_totals[date] = day_totals.get(date, 0) + tokens
```

Also update `TaskTokenSession` in `backend/app/models.py` to carry snapshots:

```python
class TaskTokenSession(BaseModel):
    ...
    token_snapshots: list[TokenSnapshot] = Field(default_factory=list)
```

And make sure `build_task_token_usage()` forwards:

```python
token_snapshots=session.token_snapshots,
```

- [ ] **Step 5: Re-run the analytics tests to verify they pass**

Run: `cd backend && ./.venv/bin/python -m pytest tests/test_task_analytics.py -v`

Expected: `PASS`

- [ ] **Step 6: Commit the analytics behavior change**

```bash
git add backend/app/models.py backend/app/task_analytics.py backend/tests/test_task_analytics.py
git commit -m "feat: reconstruct daily token usage from rollout history"
```

## Task 3: Verify Briefing Payload Behavior End To End

**Files:**
- Modify: `backend/tests/test_briefing.py`
- Test: `backend/tests/test_briefing.py`

- [ ] **Step 1: Write the failing end-to-end briefing test**

Add this test to `backend/tests/test_briefing.py`:

```python
def test_briefing_uses_reconstructed_daily_token_history(tmp_path: Path) -> None:
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
    (rollout_dir / "rollout-linked-session.jsonl").write_text(
        """
{"timestamp":"2026-06-28T10:00:00.000Z","type":"session_meta","payload":{"session_id":"linked-session","id":"linked-session","cwd":"/another/path","model":"gpt-5.5","title":"Linked Session"}}
{"timestamp":"2026-06-28T10:05:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":20,"reasoning_output_tokens":0,"total_tokens":120}}}}
{"timestamp":"2026-06-29T09:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":250,"cached_input_tokens":0,"output_tokens":50,"reasoning_output_tokens":0,"total_tokens":300}}}}
{"timestamp":"2026-06-29T16:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":300,"cached_input_tokens":0,"output_tokens":60,"reasoning_output_tokens":0,"total_tokens":360}}}}
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
    assert payload["daily_token_usage"]["project_days"] == [
        {"date": "2026-06-28", "tokens": 120},
        {"date": "2026-06-29", "tokens": 240},
    ]
    assert payload["daily_token_usage"]["has_partial_data"] is False
```

- [ ] **Step 2: Run the briefing tests to verify they fail or remain incomplete**

Run: `cd backend && ./.venv/bin/python -m pytest tests/test_briefing.py -v`

Expected: `FAIL` until the reconstructed data path is flowing through the briefing payload.

- [ ] **Step 3: Ensure briefing wiring keeps using the analytics output directly**

In `backend/app/briefing.py`, make sure the same `task_token_usage.daily_token_usage` is forwarded into the response:

```python
return BriefingResponse(
    ...
    task_token_usage=task_token_usage,
    daily_token_usage=task_token_usage.daily_token_usage,
)
```

If this already exists, do not refactor it further. Keep the change scoped to verification that the reconstructed backend output reaches the API unchanged.

- [ ] **Step 4: Re-run the briefing tests to verify they pass**

Run: `cd backend && ./.venv/bin/python -m pytest tests/test_briefing.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit the API verification**

```bash
git add backend/tests/test_briefing.py backend/app/briefing.py
git commit -m "test: verify reconstructed daily token history in briefing"
```

## Task 4: Align Frontend Messaging And Data Shaping With Reconstructed History

**Files:**
- Modify: `frontend/src/lib/boardDailyTokenUsage.ts`
- Modify: `frontend/src/lib/boardDailyTokenUsage.test.mjs`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write the failing frontend data-shaping tests**

Add these tests to `frontend/src/lib/boardDailyTokenUsage.test.mjs`:

```javascript
test("uses reconstructed project days without collapsing to one label", () => {
  const model = buildDailyChartModel({
    defaultMode: "project_total",
    projectDays: [
      { date: "2026-06-28", tokens: 120 },
      { date: "2026-06-29", tokens: 240 },
    ],
    tasks: [],
    notes: [],
    hasPartialData: false,
    hasTaskLinks: true,
  }, "project_total", null);

  assert.deepEqual(model.bars.map((bar) => bar.label), ["Jun 28", "Jun 29"]);
  assert.deepEqual(model.bars.map((bar) => bar.value), [120, 240]);
});


test("preserves reconstructed-history partial note", () => {
  const model = buildDailyChartModel({
    defaultMode: "project_total",
    projectDays: [],
    tasks: [],
    notes: ["Some session totals could not be reconstructed into daily history."],
    hasPartialData: true,
    hasTaskLinks: true,
  }, "project_total", null);

  assert.equal(model.note, "Some session totals could not be reconstructed into daily history.");
});
```

- [ ] **Step 2: Run the frontend tests to verify the current copy or assumptions fail**

Run: `cd frontend && npm run test`

Expected: `FAIL` if old note strings or shaping assumptions still expect session-date bucketting.

- [ ] **Step 3: Update frontend helper and copy**

In `frontend/src/lib/boardDailyTokenUsage.ts`, keep the existing chart model structure but update note handling and labels so reconstructed daily data is treated as the primary source of truth. The helper should preserve backend-provided note text directly instead of rewriting it.

Use this pattern for note resolution:

```ts
const note = daily.notes[0] ?? null;
```

Do not add frontend-side reconstruction logic. The frontend should only render the backend-provided daily dataset.

- [ ] **Step 4: Update the Board chart and empty-state copy**

In `frontend/src/App.tsx`, update any remaining strings that imply `session day` placement. Use wording aligned with the spec:

```ts
"Some session totals could not be reconstructed into daily history."
```

Keep the existing SVG column chart structure and only adjust copy and assumptions needed for the new metric.

- [ ] **Step 5: Run frontend tests and build**

Run: `cd frontend && npm run test`

Expected: `PASS`

Run: `cd frontend && npm run build`

Expected: `PASS`

- [ ] **Step 6: Commit the frontend alignment**

```bash
git add frontend/src/lib/boardDailyTokenUsage.ts frontend/src/lib/boardDailyTokenUsage.test.mjs frontend/src/App.tsx frontend/src/styles.css
git commit -m "feat: align board chart with reconstructed daily usage"
```

## Task 5: Record The Change And Run Final Verification

**Files:**
- Modify: `references/Harness/changes/2026-07-02/board-low-fi-prototype-design/change.md`
- Test: `backend/tests/test_codex_reader.py`
- Test: `backend/tests/test_task_analytics.py`
- Test: `backend/tests/test_briefing.py`

- [ ] **Step 1: Update the lightweight change record**

Add this line under scope in `references/Harness/changes/2026-07-02/board-low-fi-prototype-design/change.md`:

```md
- Correct Board daily token usage to use reconstructed per-day rollout deltas instead of assigning full session totals to one day.
```

- [ ] **Step 2: Run the focused backend verification**

Run: `cd backend && ./.venv/bin/python -m pytest tests/test_codex_reader.py tests/test_task_analytics.py tests/test_briefing.py -v`

Expected: `PASS`

- [ ] **Step 3: Run the full backend suite**

Run: `cd backend && ./.venv/bin/python -m pytest`

Expected: `PASS`

- [ ] **Step 4: Rebuild the frontend production bundle**

Run: `cd frontend && npm run build`

Expected: `PASS`

- [ ] **Step 5: Rebuild Docker for the smoke check**

Run: `docker compose up --build -d`

Expected: backend and frontend containers restart cleanly.

- [ ] **Step 6: Verify the live briefing payload**

Run: `docker compose exec -T backend python -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/projects/agentpm/briefing')); print(json.dumps({'project_days': data['daily_token_usage']['project_days'][:7], 'has_partial_data': data['daily_token_usage']['has_partial_data'], 'notes': data['daily_token_usage']['notes']}, ensure_ascii=False))"`

Expected: multiple dated daily bars appear when rollout history contains multiple days, and `has_partial_data` is only `true` for sessions without reconstructable history.

- [ ] **Step 7: Commit the verification and record update**

```bash
git add references/Harness/changes/2026-07-02/board-low-fi-prototype-design/change.md
git commit -m "docs: record reconstructed daily token usage change"
```

## Self-Review

- Spec coverage:
  - True daily incremental reconstruction is covered in Tasks 1-3.
  - Excluding incomplete timelines from the daily chart is covered in Tasks 2 and 4.
  - Shared attribution and task-oriented daily views remain covered by Task 2.
  - Frontend rendering and messaging remain covered by Task 4.
  - Verification and governance are covered by Task 5.
- Placeholder scan:
  - Removed generic “handle edge cases” wording and replaced it with explicit tests for missing timestamps, incomplete timelines, and cumulative snapshots.
- Type consistency:
  - `TokenSnapshot`, `token_snapshots`, `build_session_daily_deltas`, `project_days`, and `has_partial_data` are used consistently across reader, analytics, API, and frontend plan steps.
