from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    path: str


class Project(BaseModel):
    id: str
    name: str
    path: str
    has_plan: bool
    is_git_repo: bool


class DirectoryOption(BaseModel):
    name: str
    path: str


class DirectoryRoot(BaseModel):
    label: str
    path: str


class DirectoryBrowseResponse(BaseModel):
    current_path: str | None
    parent_path: str | None
    roots: list[DirectoryRoot] = Field(default_factory=list)
    directories: list[DirectoryOption] = Field(default_factory=list)


class TaskItem(BaseModel):
    id: str
    title: str
    status: str
    assignee: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    session_note: str | None = None
    user_story: str | None = None
    scope: str | None = None
    acceptance_criteria: str | None = None
    verification_method: str | None = None
    prd_refs: list[str] = Field(default_factory=list)
    codex_sessions: list[str] = Field(default_factory=list)
    token_budget: int | None = None


class ProgressSummary(BaseModel):
    done: int | None
    total: int | None
    blocked: int | None
    percent: int | None


class Milestone(BaseModel):
    id: str
    title: str
    progress: ProgressSummary | None = None
    tasks: list[TaskItem]


class PlanLoadResult(BaseModel):
    milestones: list[Milestone]
    missing: bool = False
    invalid: bool = False
    warnings: list[str] = Field(default_factory=list)


class TokenSnapshot(BaseModel):
    timestamp_ms: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_tokens: int


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
    timezone: str | None = None


class TokenSummary(BaseModel):
    total: int | None
    recent_session: int | None
    unavailable: bool = False


class GitState(BaseModel):
    is_repo: bool
    branch: str | None
    dirty_files: int
    latest_commit: str | None
    dirty_file_names: list[str] = Field(default_factory=list)
    unavailable: bool = False


class TestState(BaseModel):
    status: str = "unknown"
    confidence: str = "low"


class BriefingText(BaseModel):
    status: str
    summary: str
    next_action: str


class Alert(BaseModel):
    level: str
    message: str


class TaskPlanResponse(BaseModel):
    project_id: str
    progress: ProgressSummary
    milestones: list[Milestone]
    alerts: list[Alert]


class PrdDocumentResponse(BaseModel):
    ref: str
    path: str
    anchor: str | None = None
    title: str | None = None
    content: str = ""
    unavailable: bool = False


class TaskTokenSession(BaseModel):
    id: str
    title: str | None = None
    model: str | None = None
    model_provider: str | None = None
    updated_at_ms: int | None = None
    tokens: int | None = None
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    token_snapshots: list[TokenSnapshot] = Field(default_factory=list)
    timezone: str | None = None
    source: str
    missing: bool = False


class TaskTokenUsageItem(BaseModel):
    task_id: str
    task_title: str
    status: str
    prd_refs: list[str] = Field(default_factory=list)
    codex_sessions: list[str] = Field(default_factory=list)
    total_tokens: int | None
    model_label: str = "No model"
    models: list[str] = Field(default_factory=list)
    model_providers: list[str] = Field(default_factory=list)
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    token_budget: int | None = None
    attribution: str
    sessions: list[TaskTokenSession] = Field(default_factory=list)
    missing_sessions: list[str] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)


class TaskTokenUsageResponse(BaseModel):
    project_id: str
    tasks: list[TaskTokenUsageItem]
    alerts: list[Alert]
    daily_token_usage: DailyTokenUsageResponse | None = None


class DailyTokenTaskDay(BaseModel):
    date: str
    tokens: int
    attribution: str


class DailyTokenModelSegment(BaseModel):
    model_key: str
    model_label: str
    tokens: int


class DailyTokenProjectDay(BaseModel):
    date: str
    tokens: int
    models: list[DailyTokenModelSegment] = Field(default_factory=list)


class DailyTokenTaskSeries(BaseModel):
    task_id: str
    task_title: str
    status: str
    attribution: str
    days: list[DailyTokenTaskDay] = Field(default_factory=list)


class DailyTokenUsageResponse(BaseModel):
    default_mode: str = "project_total"
    project_days: list[DailyTokenProjectDay] = Field(default_factory=list)
    tasks: list[DailyTokenTaskSeries] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    has_partial_data: bool = False
    has_task_links: bool = False


class BriefingResponse(BaseModel):
    project: Project
    progress: ProgressSummary
    briefing: BriefingText
    tokens: TokenSummary
    git: GitState
    test: TestState
    sessions: list[CodexSession]
    alerts: list[Alert]
    task_plan: TaskPlanResponse | None = None
    task_token_usage: TaskTokenUsageResponse | None = None
    daily_token_usage: DailyTokenUsageResponse | None = None
