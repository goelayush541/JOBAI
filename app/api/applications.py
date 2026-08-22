import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.application import AIInsight, Application, ApplicationStatusHistory
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationResponse,
    ApplicationStatusUpdate,
    StatusHistoryResponse,
)
from app.services.auth import get_current_user
from app.services.gemini import gemini_service

router = APIRouter(prefix="/applications", tags=["Applications"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_result = await db.execute(
        select(Job).where(
            Job.job_id == payload.job_id,
            Job.user_id == current_user.user_id,
        )
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume_result = await db.execute(
        select(Resume).where(
            Resume.resume_id == payload.resume_id,
            Resume.user_id == current_user.user_id,
        )
    )
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    existing = await db.execute(
        select(Application).where(
            Application.user_id == current_user.user_id,
            Application.job_id == payload.job_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Application already exists for this job")

    application = Application(
        user_id=current_user.user_id,
        job_id=payload.job_id,
        resume_id=payload.resume_id,
        status="applied",
        applied_date=datetime.now(UTC).date(),
    )
    db.add(application)
    await db.flush()

    history_entry = ApplicationStatusHistory(
        application_id=application.application_id,
        status="applied",
        notes="Application created",
    )
    db.add(history_entry)

    if resume.parsed_text and job.job_description:
        try:
            analysis = await gemini_service.analyze_resume_job_fit(
                resume.parsed_text, job.job_description
            )
            application.relevance_score = analysis.get("relevance_score")
            insight = AIInsight(
                application_id=application.application_id,
                matched_skills=analysis.get("matched_skills"),
                missing_skills=analysis.get("missing_skills"),
                tailored_suggestions=analysis.get("tailored_suggestions"),
            )
            db.add(insight)
        except Exception as exc:
            logger.warning("Gemini analysis failed: %s", exc)

    await db.commit()
    await db.refresh(application)
    return application


@router.get("/", response_model=list[ApplicationResponse])
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(Application.user_id == current_user.user_id)
    )
    return [ApplicationResponse.model_validate(a) for a in result.scalars().all()]


@router.get("/{application_id}", response_model=ApplicationDetailResponse)
async def get_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.job),
            selectinload(Application.ai_insights),
        )
        .where(
            Application.application_id == UUID(application_id),
            Application.user_id == current_user.user_id,
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    insight = application.ai_insights[0] if application.ai_insights else None
    score = float(application.relevance_score) if application.relevance_score else None
    return ApplicationDetailResponse(
        application_id=application.application_id,
        user_id=application.user_id,
        job_id=application.job_id,
        resume_id=application.resume_id,
        status=application.status,
        relevance_score=score,
        applied_date=application.applied_date,
        last_updated_at=application.last_updated_at,
        job_title=application.job.job_title if application.job else None,
        company_name=application.job.company_name if application.job else None,
        matched_skills=insight.matched_skills if insight else None,
        missing_skills=insight.missing_skills if insight else None,
        tailored_suggestions=insight.tailored_suggestions if insight else None,
    )


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    valid_statuses = {"applied", "interview", "offer", "rejected", "withdrawn"}
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")

    result = await db.execute(
        select(Application).where(
            Application.application_id == UUID(application_id),
            Application.user_id == current_user.user_id,
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = payload.status
    application.last_updated_at = datetime.now(UTC)

    history_entry = ApplicationStatusHistory(
        application_id=application.application_id,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(history_entry)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/{application_id}/history", response_model=list[StatusHistoryResponse])
async def get_status_history(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(
            Application.application_id == UUID(application_id),
            Application.user_id == current_user.user_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")

    history_result = await db.execute(
        select(ApplicationStatusHistory)
        .where(ApplicationStatusHistory.application_id == UUID(application_id))
        .order_by(ApplicationStatusHistory.changed_at)
    )
    return [StatusHistoryResponse.model_validate(h) for h in history_result.scalars().all()]


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(
            Application.application_id == UUID(application_id),
            Application.user_id == current_user.user_id,
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(application)
    await db.commit()
