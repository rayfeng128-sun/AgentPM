# AgentPM Structured Data Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local collector and persistence layer that normalizes AgentPM project data into a stable dashboard contract with provenance, confidence, and refresh support.

**Architecture:** Add a structured data model plus SQLite-backed storage, then collect from `agentpm.yaml`, PRDs, and optional `PLANS.md` into normalized project snapshots. Expose those snapshots through the existing FastAPI backend, keep legacy task and token endpoints working during the transition, and let the frontend read field states and provenance from the new API.

**Tech Stack:** Python 3.11+, SQLite, FastAPI, Pydantic, PyYAML, pytest, React, TypeScript, Vite

---

## File Structure

- Modify: `backend/app/database.py`
  Add structured persistence tables to the existing app database initialization.
- Create: `backend/app/structured_models.py`
  Define normalized snapshot, task, field, source, and collection-run models.
- Create: `backend/app/structured_store.py`
  Hold SQLite read/write helpers for collection runs and the latest project snapshot.
- Create: `backend/app/structured_collect.py`
  Read `agentpm.yaml`, PRDs, and optional `PLANS.md`, then normalize them into structured records.
- Create: `backend/app/structured_service.py`
  Orchestrate refresh, snapshot loading, and compatibility helpers for the API layer.
- Modify: `backend/app/prd_reader.py`
  Keep only safe local PRD document reading and anchor resolution helpers.
- Modify: `backend/app/plan_parser.py`
  Expose any parsing helpers needed by the collector without forcing the API to parse Markdown directly.
- Modify: `backend/app/task_analytics.py`
  Switch task rows and token aggregation to the persisted structured snapshot.
- Modify: `backend/app/briefing.py`
  Pull structured task state into the briefing response without re-reading Markdown on every request.
- Modify: `backend/app/main.py`
  Add snapshot and refresh routes, then point existing task endpoints at the structured service.
- Modify: `frontend/src/App.tsx`
  Render field state badges, provenance chips, and refresh/status affordances from the structured response.
- Modify: `frontend/src/styles.css`
  Add compact styles for provenance chips, state pills, and collection warnings.
- Create: `backend/tests/test_structured_store.py`
  Cover database schema creation and snapshot persistence behavior.
- Create: `backend/tests/test_structured_collect.py`
  Cover normalization from `agentpm.yaml`, PRDs, and optional `PLANS.md`.
- Create: `backend/tests/test_structured_service.py`
  Cover refresh orchestration and snapshot loading from the service layer.
- Create: `backend/tests/test_structured_api.py`
  Cover the new snapshot and refresh endpoints plus compatibility for the dashboard routes.
- Modify: `backend/tests/test_task_analytics.py`
  Update token/task assertions to use the structured snapshot contract.
- Modify: `backend/tests/test_briefing.py`
  Update briefing assertions so task state and warnings come from persisted structured data.
- Modify: `docs/README.md`
  Link this plan in the Superpowers artifacts list.
- Modify: `references/Harness/changes/2026-07-05/structured-project-data-persistence/change.md`
  Record that the implementation plan now exists and is part of the documented slice.

## Task 1: Define The Structured Snapshot And Store It In SQLite

**Files:**
- Create: `backend/app/structured_models.py`
- Modify: `backend/app/database.py`
- Create: `backend/app/structured_store.py`
- Create: `backend/tests/test_structured_store.py`

- [ ] **Step 1: Write the failing schema tests**

Add tests like these to `backend/tests/test_structured_store.py`:

```python
from pathlib import Path

from app.database import connect, init_db


def test_init_db_creates_structured_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "agentpm.sqlite"
    with connect(db_path) as conn:
        init_db(conn)
        table_names = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }

    assert {"projects", "collection_runs", "source_documents", "structured_tasks"}.issubset(table_names)


def test_store_and_load_latest_snapshot_round_trips(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: Run the schema tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_structured_store.py -v`

Expected: `FAIL` because the structured tables and store helpers do not exist yet.

- [ ] **Step 3: Add the structured models and SQLite tables**

Create `backend/app/structured_models.py` with these core types:

```python
from enum import Enum
from pydantic import BaseModel, Field


class FieldState(str, Enum):
    explicit = "explicit"
    inferred = "inferred"
    needs_review = "needs_review"
    missing = "missing"
    unavailable = "unavailable"


class SourceRef(BaseModel):
    source_type: str
    path_or_id: str | None = None
    locator: str | None = None


class StructuredFieldValue(BaseModel):
    value: str | None = None
    state: FieldState = FieldState.missing
    source: SourceRef | None = None
    confidence: float | None = None


class StructuredTask(BaseModel):
    task_key: str
    title: str
    status: str
    milestone_id: str | None = None
    milestone_title: str | None = None
    user_story: StructuredFieldValue = Field(default_factory=StructuredFieldValue)
    scope: StructuredFieldValue = Field(default_factory=StructuredFieldValue)
    acceptance_criteria: StructuredFieldValue = Field(default_factory=StructuredFieldValue)
    verification_method: StructuredFieldValue = Field(default_factory=StructuredFieldValue)
    prd_refs: list[str] = Field(default_factory=list)
    codex_sessions: list[str] = Field(default_factory=list)
    token_budget: int | None = None


class StructuredProjectSnapshot(BaseModel):
    project_id: str
    collected_at: str
    warnings: list[str] = Field(default_factory=list)
    tasks: list[StructuredTask] = Field(default_factory=list)
```

Extend `backend/app/database.py` so `init_db()` also creates these tables:

```python
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS collection_runs (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT NOT NULL,
        warnings_json TEXT NOT NULL DEFAULT '[]'
    )
    """
)
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS structured_tasks (
        project_id TEXT NOT NULL,
        task_key TEXT NOT NULL,
        run_id TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        milestone_id TEXT,
        milestone_title TEXT,
        token_budget INTEGER,
        PRIMARY KEY (project_id, task_key)
    )
    """
)
```

Create `backend/app/structured_store.py` with helpers to save and load the latest snapshot:

```python
def save_snapshot(conn: sqlite3.Connection, snapshot: StructuredProjectSnapshot) -> None:
    ...


def load_latest_snapshot(conn: sqlite3.Connection, project_id: str) -> StructuredProjectSnapshot | None:
    ...
```

- [ ] **Step 4: Re-run the schema tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_structured_store.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit the store layer**

```bash
git add backend/app/database.py backend/app/structured_models.py backend/app/structured_store.py backend/tests/test_structured_store.py
git commit -m "feat: add structured project data store"
```

## Task 2: Normalize Project Sources Into Structured Tasks

**Files:**
- Create: `backend/app/structured_collect.py`
- Modify: `backend/app/prd_reader.py`
- Modify: `backend/app/plan_parser.py`
- Create: `backend/tests/test_structured_collect.py`

- [ ] **Step 1: Write the failing collector tests**

Add tests like these to `backend/tests/test_structured_collect.py`:

```python
from pathlib import Path

from app.structured_collect import collect_project_snapshot
from app.structured_models import FieldState


def test_collect_snapshot_prefers_explicit_yaml_values(tmp_path: Path) -> None:
    ...


def test_collect_snapshot_uses_prd_fallback_when_yaml_field_missing(tmp_path: Path) -> None:
    ...


def test_collect_snapshot_treats_missing_plans_md_as_non_fatal(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: Run the collector tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_structured_collect.py -v`

Expected: `FAIL` because `app.structured_collect` does not exist yet.

- [ ] **Step 3: Implement deterministic normalization with provenance**

Create `backend/app/structured_collect.py` with a single public entry point:

```python
def collect_project_snapshot(project_path: Path, project_id: str) -> StructuredProjectSnapshot:
    ...
```

Use this resolution order when populating each task field:

```text
explicit agentpm.yaml value
anchored PRD section
structured PLANS.md section
missing
```

Keep the field metadata explicit in the output:

```python
StructuredFieldValue(
    value="As a PM...",
    state=FieldState.explicit,
    source=SourceRef(source_type="agentpm.yaml", path_or_id="agentpm.yaml", locator="task.user_story"),
    confidence=1.0,
)
```

Move the current PRD fallback logic out of `backend/app/prd_reader.py` and into the collector so `prd_reader.py` stays focused on safe local document reads.

- [ ] **Step 4: Re-run the collector tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_structured_collect.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit the collector layer**

```bash
git add backend/app/structured_collect.py backend/app/prd_reader.py backend/app/plan_parser.py backend/tests/test_structured_collect.py
git commit -m "feat: normalize project sources into structured tasks"
```

## Task 3: Expose Snapshot And Refresh APIs

**Files:**
- Create: `backend/app/structured_service.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/task_analytics.py`
- Modify: `backend/app/briefing.py`
- Create: `backend/tests/test_structured_api.py`

- [ ] **Step 1: Write the failing API tests**

Add tests like these to `backend/tests/test_structured_api.py`:

```python
from fastapi.testclient import TestClient


def test_refresh_endpoint_persists_snapshot(tmp_path: Path) -> None:
    ...


def test_tasks_endpoint_reads_persisted_snapshot(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: Run the API tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_structured_api.py -v`

Expected: `FAIL` because the snapshot and refresh routes do not exist yet.

- [ ] **Step 3: Wire the structured service into the FastAPI app**

Create `backend/app/structured_service.py` with orchestration helpers:

```python
def refresh_project_snapshot(conn: sqlite3.Connection, project: Project) -> StructuredProjectSnapshot:
    ...


def load_project_snapshot(conn: sqlite3.Connection, project_id: str) -> StructuredProjectSnapshot | None:
    ...
```

Add these routes in `backend/app/main.py`:

```python
@app.get("/api/projects/{project_id}/structured-state", response_model=StructuredProjectSnapshot)
def api_project_structured_state(project_id: str) -> StructuredProjectSnapshot:
    ...


@app.post("/api/projects/{project_id}/structured-refresh", response_model=StructuredProjectSnapshot)
def api_refresh_project_structured_state(project_id: str) -> StructuredProjectSnapshot:
    ...
```

Update `backend/app/task_analytics.py` so task rows and token summaries read from the latest structured snapshot instead of calling `load_plan(project.path)` directly.

Update `backend/app/briefing.py` so warnings and task status can reflect the persisted structured state when it is available.

- [ ] **Step 4: Re-run the API tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_structured_api.py tests/test_task_analytics.py tests/test_briefing.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit the API wiring**

```bash
git add backend/app/structured_service.py backend/app/main.py backend/app/task_analytics.py backend/app/briefing.py backend/tests/test_structured_api.py backend/tests/test_task_analytics.py backend/tests/test_briefing.py
git commit -m "feat: expose structured project snapshot api"
```

## Task 4: Update The Task Dashboard UI For Field Provenance And Refresh

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend` build

- [ ] **Step 1: Write the frontend type and rendering expectations**

Update the TypeScript types in `frontend/src/App.tsx` to accept structured field metadata:

```ts
type StructuredFieldValue = {
  value: string | null;
  state: "explicit" | "inferred" | "needs_review" | "missing" | "unavailable";
  source: { source_type: string; path_or_id: string | null; locator: string | null } | null;
  confidence: number | null;
};

type StructuredTask = {
  task_key: string;
  title: string;
  status: TaskStatus;
  user_story: StructuredFieldValue;
  scope: StructuredFieldValue;
  acceptance_criteria: StructuredFieldValue;
  verification_method: StructuredFieldValue;
  prd_refs: string[];
  codex_sessions: string[];
  token_budget: number | null;
};
```

- [ ] **Step 2: Run the frontend build to verify the new types fail first**

Run: `cd frontend && npm run build`

Expected: `FAIL` until the structured response fields are wired through the component tree.

- [ ] **Step 3: Render provenance and refresh affordances**

Add compact UI helpers in `frontend/src/App.tsx` for:

```tsx
function fieldStateLabel(state: StructuredFieldValue["state"]) {
  ...
}

function FieldStatePill({ field }: { field: StructuredFieldValue }) {
  ...
}
```

Use them in the task table so each task row shows:

- the field value
- a state badge
- a subtle source chip when the field is inferred or needs review
- a refresh/status affordance for the latest structured collection run

Keep `Not specified` as the fallback only when the field state is `missing`.

Add matching styles in `frontend/src/styles.css` for the new pills, warning banners, and compact provenance text.

- [ ] **Step 4: Re-run the frontend build to verify it passes**

Run: `cd frontend && npm run build`

Expected: `PASS`

- [ ] **Step 5: Commit the UI changes**

```bash
git add frontend/src/App.tsx frontend/src/styles.css
git commit -m "feat: show structured field provenance in task dashboard"
```

## Task 5: Update Documentation And Roll Out The Plan

**Files:**
- Modify: `docs/README.md`
- Modify: `references/Harness/changes/2026-07-05/structured-project-data-persistence/change.md`
- Test: `rg` / plan review

- [ ] **Step 1: Add the plan to the documentation index**

Insert this line into `docs/README.md` under the Superpowers plans list:

```markdown
- [docs/superpowers/plans/2026-07-05-agentpm-structured-data-persistence.md](superpowers/plans/2026-07-05-agentpm-structured-data-persistence.md)
```

- [ ] **Step 2: Link the implementation plan from the Harness change record**

Add the plan file to `references/Harness/changes/2026-07-05/structured-project-data-persistence/change.md` so the change record points at the PRD, design, and implementation plan together.

```markdown
- `docs/superpowers/plans/2026-07-05-agentpm-structured-data-persistence.md`
```

- [ ] **Step 3: Run the documentation sanity check**

Run a repository text scan across the PRD, design, plan, Harness change record, and docs index, then confirm there are no unfinished-work markers or contradictory statements in the documented slice.

- [ ] **Step 4: Commit the documentation rollup**

```bash
git add docs/README.md references/Harness/changes/2026-07-05/structured-project-data-persistence/change.md docs/superpowers/plans/2026-07-05-agentpm-structured-data-persistence.md
git commit -m "docs: add implementation plan for structured project data persistence"
```

## Spec Coverage

- Story 1 and Story 5 from the PRD are covered by Tasks 2, 3, and 4 because they move task data into a stable AgentPM-owned snapshot, keep `PLANS.md` optional, and show normalized states in the dashboard.
- Story 2 is covered by Tasks 1 and 2 because the schema stores source metadata and the collector records provenance for each derived field.
- Story 3 is covered by Task 3 because the service adds refresh and snapshot loading around the persistent collection flow.
- Story 4 is covered by Tasks 1, 2, and 4 because the state model distinguishes `explicit`, `inferred`, `needs_review`, `missing`, and `unavailable`.
- Persistence, error handling, and incremental delivery are covered across Tasks 1 through 5 with focused test-first slices.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-05-agentpm-structured-data-persistence.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
