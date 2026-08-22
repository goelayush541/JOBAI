from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobCreate(BaseModel):
    job_title: str
    company_name: str
    job_description: str
    source_url: str | None = None
    location: str | None = None


class JobResponse(BaseModel):
    job_id: UUID
    job_title: str
    company_name: str
    job_description: str
    source_url: str | None
    location: str | None
    created_at: datetime

    class Config:
        from_attributes = True
