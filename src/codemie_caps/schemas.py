from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WorkItemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    item_type: Literal["epic", "story", "task", "bug"] = "story"
    priority: Literal["low", "medium", "high", "critical"] = "medium"


class WorkItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    description: str
    item_type: str
    priority: str
    status: str


class StageSubmission(BaseModel):
    artifact: str = Field(min_length=3, max_length=12000)
    actor: str = Field(default="assistant", min_length=2, max_length=100)


class ReviewDecision(BaseModel):
    decision: Literal["approve", "reject"]
    actor: str = Field(min_length=2, max_length=100)
    note: str = Field(min_length=3, max_length=2000)
    artifact: str | None = Field(default=None, min_length=3, max_length=12000)


class StageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    title: str
    persona: str
    position: int
    status: str
    artifact: str
    reviewed_by: str
    review_note: str
    submitted_at: datetime | None
    reviewed_at: datetime | None


class WorkflowRead(BaseModel):
    run_id: int
    project: str
    status: str
    current_stage: str | None
    stages: list[StageRead]


class AuditRead(BaseModel):
    id: int
    actor: str
    action: str
    entity_type: str
    entity_key: str
    details: str
    created_at: datetime
