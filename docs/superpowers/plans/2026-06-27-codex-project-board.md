# Codex Project Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v0.1 product defined in `docs/product/01-codex-project-board-prd.md`: a local web dashboard that shows Codex-driven project progress, recent activity, risks, and next action from `agentpm.yaml`, local Codex session/token data, and Git state.

**Architecture:** Create a FastAPI backend and React frontend in this empty workspace. The backend reads local files and SQLite databases, stores project registrations in an app SQLite database, and exposes briefing APIs. The frontend renders a briefing-first project dashboard.

**Tech Stack:** Python 3, FastAPI, SQLite, PyYAML, pytest, React, TypeScript, Vite, lightweight CSS.

---

## File Structure

- Create `backend/app/main.py`: FastAPI app and route registration.
- Create `backend/app/database.py`: app SQLite connection and schema setup.
- Create `backend/app/models.py`: Pydantic response/request models.
- Create `backend/app/projects.py`: project registry service.
- Create `backend/app/plan_parser.py`: `agentpm.yaml` parser and progress calculator.
- Create `backend/app/codex_reader.py`: local Codex thread/session/token reader.
- Create `backend/app/git_reader.py`: Git state reader.
- Create `backend/app/briefing.py`: combines plan, Codex, Git, and alerts.
- Create `backend/app/status_rules.py`: PRD-defined briefing status priority and alert thresholds.
- Create `backend/tests/`: focused backend tests.
- Create `frontend/`: Vite React app with dashboard UI.
- Create `agentpm.yaml`: plan file for this project itself.
- Create `README.md`: setup and run instructions.

## Task 1: Backend Skeleton

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/database.py`
- Create: `backend/tests/test_health.py`

- [ ] Create the backend package and dependency file.

```toml
[project]
name = "codex-project-board-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn>=0.30.0",
  "pydantic>=2.8.0",
  "pyyaml>=6.0.0"
]

[project.optional-dependencies]
test = [
  "pytest>=8.2.0",
  "httpx>=0.27.0"
]
```

- [ ] Implement app database initialization.

```python
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
    conn.commit()
```

- [ ] Implement the health endpoint.

```python
from fastapi import FastAPI

app = FastAPI(title="Codex Project Board")

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] Add a failing then passing health test.

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health() -> None:
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] Run `cd backend && python -m pytest`.

Expected result: tests pass.

## Task 2: Project Registry

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/projects.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_projects.py`

- [ ] Add project models.

```python
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    path: str

class Project(BaseModel):
    id: str
    name: str
    path: str
    has_plan: bool
    is_git_repo: bool
```

- [ ] Implement deterministic project IDs, path validation, and CRUD helpers.

```python
from pathlib import Path
import re
import sqlite3
from fastapi import HTTPException
from .models import Project, ProjectCreate

def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"

def has_plan_file(path: str) -> bool:
    return (Path(path) / "agentpm.yaml").exists()

def is_git_repo(path: str) -> bool:
    return (Path(path) / ".git").exists()

def validate_project_create(data: ProjectCreate) -> None:
    if not data.name.strip():
        raise HTTPException(status_code=422, detail="Project name is required")
    if not data.path.strip():
        raise HTTPException(status_code=422, detail="Project path is required")
    if not Path(data.path).exists():
        raise HTTPException(status_code=422, detail="Project path does not exist")

def create_project(conn: sqlite3.Connection, data: ProjectCreate) -> Project:
    validate_project_create(data)
    project_id = slugify(data.name)
    conn.execute(
        "INSERT OR REPLACE INTO projects (id, name, path, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        (project_id, data.name.strip(), str(Path(data.path).resolve())),
    )
    conn.commit()
    path = str(Path(data.path).resolve())
    return Project(id=project_id, name=data.name.strip(), path=path, has_plan=has_plan_file(path), is_git_repo=is_git_repo(path))

def list_projects(conn: sqlite3.Connection) -> list[Project]:
    rows = conn.execute("SELECT id, name, path FROM projects ORDER BY name").fetchall()
    return [
        Project(
            id=row["id"],
            name=row["name"],
            path=row["path"],
            has_plan=has_plan_file(row["path"]),
            is_git_repo=is_git_repo(row["path"]),
        )
        for row in rows
    ]

def get_project(conn: sqlite3.Connection, project_id: str) -> Project | None:
    row = conn.execute("SELECT id, name, path FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
        return None
    return Project(
        id=row["id"],
        name=row["name"],
        path=row["path"],
        has_plan=has_plan_file(row["path"]),
        is_git_repo=is_git_repo(row["path"]),
    )
```

- [ ] Wire project routes in `main.py`.

```python
from fastapi import FastAPI, HTTPException
from .database import connect, init_db
from .models import Project, ProjectCreate
from .projects import create_project, get_project, list_projects

app = FastAPI(title="Codex Project Board")

@app.on_event("startup")
def startup() -> None:
    with connect() as conn:
        init_db(conn)

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/api/projects", response_model=list[Project])
def api_list_projects() -> list[Project]:
    with connect() as conn:
        init_db(conn)
        return list_projects(conn)

@app.post("/api/projects", response_model=Project)
def api_create_project(data: ProjectCreate) -> Project:
    with connect() as conn:
        init_db(conn)
        return create_project(conn, data)

@app.get("/api/projects/{project_id}", response_model=Project)
def api_get_project(project_id: str) -> Project:
    with connect() as conn:
        init_db(conn)
        project = get_project(conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

- [ ] Test project creation, validation, duplicate path replacement, and listing with a temporary database.

Expected behavior: a created project appears in the list; empty name/path and nonexistent path return 422; paths without Git are allowed; `has_plan` and `is_git_repo` reflect the local path.

## Task 3: Plan Parser

**Files:**
- Create: `backend/app/plan_parser.py`
- Modify: `backend/app/models.py`
- Create: `backend/tests/test_plan_parser.py`

- [ ] Add progress models.

```python
from pydantic import BaseModel, Field

class TaskItem(BaseModel):
    id: str
    title: str
    status: str

class Milestone(BaseModel):
    id: str
    title: str
    tasks: list[TaskItem]

class ProgressSummary(BaseModel):
    done: int | None
    total: int | None
    blocked: int | None
    percent: int | None

class PlanLoadResult(BaseModel):
    milestones: list[Milestone]
    missing: bool = False
    invalid: bool = False
    warnings: list[str] = Field(default_factory=list)
```

- [ ] Parse `agentpm.yaml`.

```python
from pathlib import Path
import yaml
from .models import Milestone, PlanLoadResult, ProgressSummary, TaskItem

VALID_STATUSES = {"todo", "doing", "done", "blocked"}

def load_plan(project_path: str) -> PlanLoadResult:
    plan_path = Path(project_path) / "agentpm.yaml"
    if not plan_path.exists():
        return PlanLoadResult(milestones=[], missing=True)
    try:
        data = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return PlanLoadResult(milestones=[], invalid=True, warnings=["agentpm.yaml could not be parsed"])

    milestones = []
    warnings = []
    for milestone in data.get("milestones", []):
        tasks = []
        for task in milestone.get("tasks", []):
            status = task.get("status", "todo")
            if status not in VALID_STATUSES:
                warnings.append(f"Unknown task status for {task.get('id', 'unknown')}: {status}")
                status = "todo"
            tasks.append(TaskItem(id=str(task["id"]), title=str(task["title"]), status=status))
        milestones.append(Milestone(id=str(milestone["id"]), title=str(milestone["title"]), tasks=tasks))
    return PlanLoadResult(milestones=milestones, warnings=warnings)

def calculate_progress(plan: PlanLoadResult) -> ProgressSummary:
    if plan.missing or plan.invalid:
        return ProgressSummary(done=None, total=None, blocked=None, percent=None)
    milestones = plan.milestones
    tasks = [task for milestone in milestones for task in milestone.tasks]
    total = len(tasks)
    done = len([task for task in tasks if task.status == "done"])
    blocked = len([task for task in tasks if task.status == "blocked"])
    percent = 0 if total == 0 else round(done / total * 100)
    return ProgressSummary(done=done, total=total, blocked=blocked, percent=percent)
```

- [ ] Test missing plan, invalid YAML, valid plan, and invalid status fallback.

Expected behavior: missing or invalid plan returns unavailable progress (`None` fields) plus warning state; invalid status becomes `todo` and creates a warning.

## Task 4: Codex Reader

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/app/codex_reader.py`
- Create: `backend/tests/test_codex_reader.py`

- [ ] Add session and token models.

```python
from pydantic import BaseModel

class CodexSession(BaseModel):
    id: str
    title: str
    cwd: str
    model: str | None
    tokens_used: int
    updated_at_ms: int | None
    rollout_path: str | None

class TokenSummary(BaseModel):
    total: int | None
    recent_session: int | None
    unavailable: bool = False
```

- [ ] Read sessions from Codex `state_5.sqlite`.

```python
from pathlib import Path
import sqlite3
from .models import CodexSession, TokenSummary

DEFAULT_CODEX_STATE_DB = Path.home() / ".codex" / "sqlite" / "state_5.sqlite"

def codex_state_available(db_path: Path = DEFAULT_CODEX_STATE_DB) -> bool:
    return db_path.exists()

def read_sessions_for_path(project_path: str, db_path: Path = DEFAULT_CODEX_STATE_DB) -> list[CodexSession]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, title, cwd, model, tokens_used, updated_at_ms, rollout_path
        FROM threads
        WHERE cwd = ?
        ORDER BY updated_at_ms DESC
        LIMIT 50
        """,
        (project_path,),
    ).fetchall()
    conn.close()
    return [
        CodexSession(
            id=row["id"],
            title=row["title"],
            cwd=row["cwd"],
            model=row["model"],
            tokens_used=row["tokens_used"],
            updated_at_ms=row["updated_at_ms"],
            rollout_path=row["rollout_path"],
        )
        for row in rows
    ]

def summarize_tokens(sessions: list[CodexSession], unavailable: bool = False) -> TokenSummary:
    if unavailable:
        return TokenSummary(total=None, recent_session=None, unavailable=True)
    total = sum(session.tokens_used for session in sessions)
    recent_session = sessions[0].tokens_used if sessions else 0
    return TokenSummary(total=total, recent_session=recent_session)
```

- [ ] Test with a temporary SQLite database containing a minimal `threads` table, and test missing Codex DB.

Expected behavior: only sessions matching the project path are returned and tokens are summed; missing Codex DB sets `TokenSummary.unavailable=true` in the briefing instead of producing a server error. Do not expose raw transcript text in API responses.

## Task 5: Git Reader

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/app/git_reader.py`
- Create: `backend/tests/test_git_reader.py`

- [ ] Add Git model.

```python
from pydantic import BaseModel, Field

class GitState(BaseModel):
    is_repo: bool
    branch: str | None
    dirty_files: int
    latest_commit: str | None
    dirty_file_names: list[str] = Field(default_factory=list)
    unavailable: bool = False
```

- [ ] Implement Git state reader.

```python
from pathlib import Path
import subprocess
from .models import GitState

def run_git(project_path: str, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", project_path, *args],
            check=True,
            text=True,
            capture_output=True,
            timeout=3,
        )
        return result.stdout.strip()
    except Exception:
        return None

def read_git_state(project_path: str) -> GitState:
    if not (Path(project_path) / ".git").exists():
        return GitState(is_repo=False, branch=None, dirty_files=0, latest_commit=None, dirty_file_names=[])
    branch = run_git(project_path, ["branch", "--show-current"])
    status = run_git(project_path, ["status", "--porcelain"]) or ""
    latest = run_git(project_path, ["rev-parse", "--short", "HEAD"])
    dirty_files = len([line for line in status.splitlines() if line.strip()])
    dirty_file_names = [line[3:] for line in status.splitlines() if len(line) > 3]
    return GitState(is_repo=True, branch=branch or None, dirty_files=dirty_files, latest_commit=latest, dirty_file_names=dirty_file_names)
```

- [ ] Test non-Git path returns `is_repo=false`.

Expected behavior: no exception is raised for non-Git paths.

## Task 6: Briefing API

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/app/briefing.py`
- Create: `backend/app/status_rules.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_briefing.py`
- Create: `backend/tests/test_status_rules.py`

- [ ] Add briefing models.

```python
from pydantic import BaseModel

class BriefingText(BaseModel):
    status: str
    summary: str
    next_action: str

class Alert(BaseModel):
    level: str
    message: str

class TestState(BaseModel):
    status: str = "unknown"
    confidence: str = "low"

class BriefingResponse(BaseModel):
    project: Project
    progress: ProgressSummary
    briefing: BriefingText
    tokens: TokenSummary
    git: GitState
    test: TestState
    alerts: list[Alert]
```

- [ ] Implement PRD status and alert rules.

```python
from datetime import datetime, timezone
from .models import Alert, CodexSession, GitState, PlanLoadResult, ProgressSummary, TestState, TokenSummary

RECENT_ACTIVITY_HOURS = 48

def is_recent_session(sessions: list[CodexSession], now_ms: int | None = None) -> bool:
    updated_values = [session.updated_at_ms for session in sessions if session.updated_at_ms is not None]
    if not updated_values:
        return False
    latest = max(updated_values)
    now = now_ms or int(datetime.now(timezone.utc).timestamp() * 1000)
    return now - latest <= RECENT_ACTIVITY_HOURS * 60 * 60 * 1000

def token_spike_alert(sessions: list[CodexSession]) -> Alert | None:
    if len(sessions) < 6:
        return None
    recent = sessions[0].tokens_used
    previous = [session.tokens_used for session in sessions[1:6]]
    average = sum(previous) / len(previous)
    if average > 0 and recent > average * 2:
        return Alert(level="info", message="Recent session token usage is more than 2x the previous five-session average.")
    return None

def calculate_status(
    plan: PlanLoadResult,
    progress: ProgressSummary,
    sessions: list[CodexSession],
    git: GitState,
    test: TestState,
) -> str:
    if plan.missing or plan.invalid:
        return "missing_plan"
    if progress.blocked and progress.blocked > 0:
        return "blocked"
    if test.status == "failing":
        return "tests_failing"
    if is_recent_session(sessions) or git.dirty_files > 0:
        return "active"
    if sessions or git.latest_commit:
        return "idle"
    return "unknown"

def build_alerts(
    plan: PlanLoadResult,
    progress: ProgressSummary,
    sessions: list[CodexSession],
    tokens: TokenSummary,
    git: GitState,
    test: TestState,
) -> list[Alert]:
    alerts: list[Alert] = []
    if plan.missing:
        alerts.append(Alert(level="warning", message="Project path has no readable agentpm.yaml."))
    if plan.invalid:
        alerts.append(Alert(level="warning", message="agentpm.yaml exists but cannot be parsed."))
    for warning in plan.warnings:
        alerts.append(Alert(level="warning", message=warning))
    if progress.blocked and progress.blocked > 0:
        alerts.append(Alert(level="warning", message=f"{progress.blocked} task is blocked."))
    if test.status == "unknown":
        alerts.append(Alert(level="warning", message="Test state is unknown."))
    if test.status == "failing":
        alerts.append(Alert(level="error", message="Tests are failing."))
    spike = token_spike_alert(sessions)
    if spike:
        alerts.append(spike)
    if tokens.unavailable:
        alerts.append(Alert(level="warning", message="Local Codex state is unavailable."))
    if not git.is_repo or git.unavailable:
        alerts.append(Alert(level="info", message="Git state is unavailable for this project path."))
    return alerts
```

- [ ] Implement deterministic briefing generation.

```python
from .codex_reader import codex_state_available, read_sessions_for_path, summarize_tokens
from .git_reader import read_git_state
from .models import BriefingResponse, BriefingText, Project, TestState
from .plan_parser import calculate_progress, load_plan
from .status_rules import build_alerts, calculate_status

def build_briefing(project: Project) -> BriefingResponse:
    plan = load_plan(project.path)
    progress = calculate_progress(plan)
    sessions = read_sessions_for_path(project.path)
    tokens = summarize_tokens(sessions, unavailable=not codex_state_available())
    git = read_git_state(project.path)
    test = TestState(status="unknown", confidence="low")
    status = calculate_status(plan=plan, progress=progress, sessions=sessions, git=git, test=test)
    alerts = build_alerts(plan=plan, progress=progress, sessions=sessions, tokens=tokens, git=git, test=test)

    if progress.total is None:
        summary = f"{project.name} has no usable plan data yet."
    else:
        summary = f"{project.name} is {progress.percent}% complete with {progress.done}/{progress.total} tasks done."

    next_action_by_status = {
        "missing_plan": "Create or fix agentpm.yaml with milestones and tasks.",
        "blocked": "Resolve the blocked task before starting new work.",
        "tests_failing": "Run or inspect the relevant test suite before continuing feature work.",
        "active": "Review the current dirty files or latest Codex session and continue the active task.",
        "idle": "Review the plan and choose the next todo task.",
        "unknown": "Check local Codex, Git, and plan availability.",
    }

    return BriefingResponse(
        project=project,
        progress=progress,
        briefing=BriefingText(status=status, summary=summary, next_action=next_action_by_status[status]),
        tokens=tokens,
        git=git,
        test=test,
        alerts=alerts,
    )
```

- [ ] Add route `GET /api/projects/{project_id}/briefing`.

Expected behavior: registered project returns a full briefing response; unknown project returns 404; missing plan, unavailable Codex data, and non-Git paths are represented in the payload rather than returning 500.

- [ ] Test status priority and alert thresholds.

Expected behavior: status priority follows the PRD order: `missing_plan`, `blocked`, `tests_failing`, `active`, `idle`, `unknown`; token spike alert appears when the most recent session uses more than 2x the average of the previous five sessions.

## Task 7: Frontend App

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`

- [ ] Scaffold a Vite React TypeScript app.

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest",
    "lucide-react": "latest"
  },
  "devDependencies": {}
}
```

- [ ] Implement the briefing-first UI.

The first screen must include:

- Left project sidebar.
- Add-project form with name and absolute path fields.
- Top cards for progress, tokens, and Git/test state.
- Main briefing card with status, summary, and next action.
- Recent sessions table.
- Alerts panel.
- Loading, empty, no-selection, validation-error, backend-unavailable, missing-plan, invalid-plan, non-Git, Codex-unavailable, token-unavailable, and unknown-test states.

Use these client-side status labels exactly where applicable:

```ts
type BriefingStatus = "active" | "idle" | "blocked" | "tests_failing" | "missing_plan" | "unknown";
type AlertLevel = "info" | "warning" | "error";
```

- [ ] Use compact dashboard styling, not a marketing landing page.

Expected behavior: user can open the app and immediately inspect a project briefing; missing local signals produce visible states instead of blank cards.

## Task 8: Seed Current Project Plan

**Files:**
- Create: `agentpm.yaml`
- Create: `README.md`

- [ ] Add `agentpm.yaml` for this dashboard project.

```yaml
project:
  name: AgentPM
  path: /Users/ray/BaiduNetDisk/Project/AgentPM

milestones:
  - id: v0.1
    title: Local project board MVP
    tasks:
      - id: backend-skeleton
        title: Build FastAPI backend skeleton
        status: todo
      - id: project-registry
        title: Register and list local projects
        status: todo
      - id: plan-parser
        title: Parse agentpm.yaml and calculate progress
        status: todo
      - id: codex-reader
        title: Read Codex local sessions and token usage
        status: todo
      - id: git-reader
        title: Read project Git state
        status: todo
      - id: briefing-api
        title: Combine signals into project briefing API
        status: todo
      - id: frontend-dashboard
        title: Build briefing-first React dashboard
        status: todo
```

- [ ] Add README run instructions.

Expected behavior: a developer can install backend/frontend dependencies and run the local dashboard.

## Task 9: Verification

**Files:**
- Modify as needed only for fixes found by tests.

- [ ] Run backend tests.

```bash
cd backend
python -m pytest
```

Expected result: all backend tests pass.

- [ ] Run frontend build.

```bash
cd frontend
npm run build
```

Expected result: production build succeeds.

- [ ] Run PRD smoke checks.

Manual checks:

- Register a path with `agentpm.yaml`; progress and percent render.
- Register a path without `agentpm.yaml`; `missing_plan` status and warning render.
- Register a non-Git path; Git unavailable info alert renders without breaking the briefing.
- Temporarily point the backend to a missing Codex DB; Codex unavailable warning renders and transcripts are not shown.
- Create fixture sessions where the newest session is more than 2x the previous five-session average; token spike info alert renders.

- [ ] Start both services.

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm run dev
```

Expected result: dashboard opens and can fetch project briefing data from the backend.

## Assumptions

- v0.1 is local-only and does not need authentication.
- The first implementation can use the local app database at `~/.agentpm/agentpm.sqlite`.
- Cost estimates are deferred; token counts are enough for v0.1.
- Test status is displayed as unknown unless a later task adds explicit test-result ingestion.
- The dashboard reads metadata and summaries, not full Codex transcripts by default.
