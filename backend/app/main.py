import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .briefing import build_briefing, token_summary_for_project
from .codex_reader import DEFAULT_CODEX_STATE_DB, read_sessions_for_path
from .database import APP_DB, connect, init_db
from .models import BriefingResponse, CodexSession, DirectoryBrowseResponse, PrdDocumentResponse, Project, ProjectCreate, TaskPlanResponse, TaskTokenUsageResponse, TokenSummary
from .plan_parser import load_plan
from .prd_reader import read_project_prd
from .projects import browse_directories, create_project, delete_project, get_project, list_projects
from .task_analytics import build_task_plan, build_task_token_usage

app = FastAPI(title="Codex Project Board")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:18080",
        "http://127.0.0.1:18080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def app_db_path() -> Path:
    return getattr(app.state, "db_path", APP_DB)


def codex_db_path() -> Path:
    return getattr(app.state, "codex_db_path", DEFAULT_CODEX_STATE_DB)


def browse_roots() -> list[Path]:
    configured = getattr(app.state, "browse_roots", None)
    if configured is not None:
        return [Path(item) for item in configured]

    env_value = os.environ.get("AGENTPM_BROWSE_ROOTS", "")
    roots = [Path(item) for item in env_value.split(os.pathsep) if item.strip()]
    return roots or [Path("/sample-project")]


@app.on_event("startup")
def startup() -> None:
    with connect(app_db_path()) as conn:
        init_db(conn)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="http://127.0.0.1:18080/", status_code=307)


@app.get("/api/projects", response_model=list[Project])
def api_list_projects() -> list[Project]:
    with connect(app_db_path()) as conn:
        init_db(conn)
        return list_projects(conn)


@app.get("/api/directories", response_model=DirectoryBrowseResponse)
def api_browse_directories(path: str | None = None) -> DirectoryBrowseResponse:
    return browse_directories(path, browse_roots())


@app.post("/api/projects", response_model=Project)
def api_create_project(data: ProjectCreate) -> Project:
    with connect(app_db_path()) as conn:
        init_db(conn)
        return create_project(conn, data)


@app.delete("/api/projects/{project_id}", status_code=204)
def api_delete_project(project_id: str) -> Response:
    with connect(app_db_path()) as conn:
        init_db(conn)
        deleted = delete_project(conn, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return Response(status_code=204)


@app.get("/api/projects/{project_id}", response_model=Project)
def api_get_project(project_id: str) -> Project:
    with connect(app_db_path()) as conn:
        init_db(conn)
        project = get_project(conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/api/projects/{project_id}/briefing", response_model=BriefingResponse)
def api_project_briefing(project_id: str) -> BriefingResponse:
    project = api_get_project(project_id)
    return build_briefing(project, codex_db_path=codex_db_path())


@app.get("/api/projects/{project_id}/tasks", response_model=TaskPlanResponse)
def api_project_tasks(project_id: str) -> TaskPlanResponse:
    project = api_get_project(project_id)
    return build_task_plan(project.id, load_plan(project.path), project.path)


@app.get("/api/projects/{project_id}/prd", response_model=PrdDocumentResponse)
def api_project_prd(project_id: str, ref: str) -> PrdDocumentResponse:
    project = api_get_project(project_id)
    return read_project_prd(project.path, ref)


@app.get("/api/projects/{project_id}/task-token-usage", response_model=TaskTokenUsageResponse)
def api_project_task_token_usage(project_id: str) -> TaskTokenUsageResponse:
    project = api_get_project(project_id)
    return build_task_token_usage(project.id, load_plan(project.path), project.path, codex_db_path())


@app.get("/api/projects/{project_id}/sessions", response_model=list[CodexSession])
def api_project_sessions(project_id: str) -> list[CodexSession]:
    project = api_get_project(project_id)
    return read_sessions_for_path(project.path, db_path=codex_db_path())


@app.get("/api/projects/{project_id}/tokens", response_model=TokenSummary)
def api_project_tokens(project_id: str) -> TokenSummary:
    project = api_get_project(project_id)
    return token_summary_for_project(project, codex_db_path=codex_db_path())
