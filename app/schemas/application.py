from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApplicationCreate(BaseModel):
    job_id: UUID
    resume_id: UUID


class ApplicationStatusUpdate(BaseModel):
    status: str
    notes: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: UUID
    user_id: UUID
    job_id: UUID
    resume_id: UUID
    status: str
    relevance_score: float | None = None
    applied_date: date | None = None
    last_updated_at: datetime


class ApplicationDetailResponse(ApplicationResponse):
    job_title: str | None = None
    company_name: str | None = None
    matched_skills: list | dict | None = None
    missing_skills: list | dict | None = None
    tailored_suggestions: str | None = None


class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: UUID
    status: str
    changed_at: datetime
    notes: str | None
