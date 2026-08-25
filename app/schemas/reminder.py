from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReminderCreate(BaseModel):
    application_id: UUID
    reminder_type: str
    channel: str = "in_app"
    message: str | None = None
    scheduled_at: datetime


class ReminderResponse(BaseModel):
    reminder_id: UUID
    application_id: UUID
    reminder_type: str
    channel: str
    message: str | None
    scheduled_at: datetime
    sent_at: datetime | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
