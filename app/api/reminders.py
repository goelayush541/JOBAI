from datetime import UTC, datetime
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.application import Application
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.services.auth import get_current_user
from app.services.reminders import reminder_service

router = APIRouter(prefix="/reminders", tags=["Reminders"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    payload: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app_result = await db.execute(
        select(Application).where(
            Application.application_id == payload.application_id,
            Application.user_id == current_user.user_id,
        )
    )
    if not app_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")

    reminder = Reminder(
        application_id=payload.application_id,
        user_id=current_user.user_id,
        reminder_type=payload.reminder_type,
        channel=payload.channel,
        message=payload.message,
        scheduled_at=payload.scheduled_at,
        status="pending",
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)

    try:
        await reminder_service.schedule_reminder(
            reminder.reminder_id, current_user.user_id, payload.scheduled_at
        )
    except Exception:
        pass

    logger.info(
        "Reminder created: %s for application %s, type=%s, scheduled=%s",
        reminder.reminder_id, payload.application_id,
        payload.reminder_type, payload.scheduled_at,
    )
    return reminder


@router.get("/", response_model=list[ReminderResponse])
async def list_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder).where(Reminder.user_id == current_user.user_id)
    )
    return [ReminderResponse.model_validate(r) for r in result.scalars().all()]


@router.patch("/{reminder_id}/cancel", response_model=ReminderResponse)
async def cancel_reminder(
    reminder_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder).where(
            Reminder.reminder_id == UUID(reminder_id),
            Reminder.user_id == current_user.user_id,
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder.status = "cancelled"
    await db.commit()
    await db.refresh(reminder)
    logger.info("Reminder cancelled: %s", reminder.reminder_id)
    return reminder
