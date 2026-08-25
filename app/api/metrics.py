import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.application import Application, ApplicationStatusHistory
from app.models.reminder import Reminder
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/metrics", tags=["Metrics"])
logger = logging.getLogger(__name__)


@router.get("/")
async def get_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    apps_result = await db.execute(
        select(Application).where(Application.user_id == current_user.user_id)
    )
    applications = apps_result.scalars().all()

    total_apps = len(applications)
    active_apps = sum(1 for a in applications if a.status in ("applied", "interview"))

    weekly_apps_result = await db.execute(
        select(func.count(Application.application_id)).where(
            Application.user_id == current_user.user_id,
            Application.last_updated_at >= week_ago,
        )
    )
    weekly_updates = weekly_apps_result.scalar() or 0

    scores = [float(a.relevance_score) for a in applications if a.relevance_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    high_match_count = sum(1 for s in scores if s >= 70)

    offers = sum(1 for a in applications if a.status == "offer")
    rejections = sum(1 for a in applications if a.status == "rejected")
    conversion_rate = round((offers / (offers + rejections) * 100) if (offers + rejections) > 0 else 0, 1)

    reminders_result = await db.execute(
        select(Reminder).where(Reminder.user_id == current_user.user_id)
    )
    all_reminders = reminders_result.scalars().all()
    sent_reminders = sum(1 for r in all_reminders if r.status == "sent")
    pending_reminders = sum(1 for r in all_reminders if r.status == "pending")
    total_reminders = len(all_reminders)

    history_result = await db.execute(
        select(ApplicationStatusHistory)
        .join(Application, ApplicationStatusHistory.application_id == Application.application_id)
        .where(
            Application.user_id == current_user.user_id,
            ApplicationStatusHistory.changed_at >= week_ago,
        )
    )
    weekly_history = history_result.scalars().all()

    status_changes = len(weekly_history)
    interview_count = sum(1 for h in weekly_history if h.status == "interview")

    return {
        "period": {
            "week_start": week_ago.isoformat(),
            "month_start": month_ago.isoformat(),
        },
        "application_metrics": {
            "total_applications": total_apps,
            "active_applications": active_apps,
            "weekly_updates": weekly_updates,
        },
        "match_quality": {
            "average_relevance_score": avg_score,
            "high_match_count": high_match_count,
            "total_scored": len(scores),
        },
        "outcome_metrics": {
            "offers": offers,
            "rejections": rejections,
            "conversion_rate": conversion_rate,
        },
        "reminder_metrics": {
            "total_reminders": total_reminders,
            "sent_reminders": sent_reminders,
            "pending_reminders": pending_reminders,
            "follow_up_rate": round((sent_reminders / total_reminders * 100) if total_reminders > 0 else 0, 1),
        },
        "activity_metrics": {
            "weekly_status_changes": status_changes,
            "weekly_interviews": interview_count,
        },
    }
