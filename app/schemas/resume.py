from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ResumeResponse(BaseModel):
    resume_id: UUID
    file_name: str
    file_url: str
    is_active: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True
