from enum import Enum
from typing import Any

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
    warnings: list[str] = Field(default_factory=list)


class StructuredMilestone(BaseModel):
    milestone_id: str
    title: str
    tasks: list[StructuredTask] = Field(default_factory=list)


class StructuredProjectSnapshot(BaseModel):
    project_id: str
    collected_at: str
    status: str = "complete"
    warnings: list[str] = Field(default_factory=list)
    milestones: list[StructuredMilestone] = Field(default_factory=list)

    def as_task_rows(self) -> list[StructuredTask]:
        return [task for milestone in self.milestones for task in milestone.tasks]


class CollectionRun(BaseModel):
    id: str
    project_id: str
    started_at: str
    finished_at: str | None = None
    status: str
    warnings: list[str] = Field(default_factory=list)
    snapshot: StructuredProjectSnapshot | None = None


class StructuredTaskRecord(BaseModel):
    project_id: str
    task_key: str
    run_id: str
    milestone_id: str | None = None
    milestone_title: str | None = None
    title: str
    status: str
    token_budget: int | None = None
    task_json: dict[str, Any] = Field(default_factory=dict)
