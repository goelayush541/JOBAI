from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.application import Application
from app.models.reminder import Reminder
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    apps_result = await db.execute(
        select(Application).where(Application.user_id == current_user.user_id)
    )
    applications = apps_result.scalars().all()

    total = len(applications)
    by_status = {}
    scores = []
    for app in applications:
        by_status[app.status] = by_status.get(app.status, 0) + 1
        if app.relevance_score is not None:
            scores.append(float(app.relevance_score))

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    reminders_result = await db.execute(
        select(Reminder).where(
            Reminder.user_id == current_user.user_id,
            Reminder.status == "pending",
        )
    )
    pending_reminders = reminders_result.scalars().all()

    return {
        "total_applications": total,
        "status_breakdown": by_status,
        "average_relevance_score": avg_score,
        "pending_reminders": len(pending_reminders),
        "reminders": [
            {
                "reminder_id": str(r.reminder_id),
                "reminder_type": r.reminder_type,
                "scheduled_at": r.scheduled_at.isoformat(),
                "message": r.message,
            }
            for r in pending_reminders
        ],
    }
