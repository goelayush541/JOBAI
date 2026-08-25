import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP, Date, ForeignKey, Numeric, String, Text, JSON
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDType
from app.config import get_settings

settings = get_settings()
USE_POSTGRES = settings.DATABASE_URL.startswith("postgresql")

if USE_POSTGRES:
    from sqlalchemy.dialects.postgresql import JSONB as JSONType
else:
    JSONType = JSON


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    pending_analysis = "pending_analysis"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"
    withdrawn = "withdrawn"


class Application(Base):
    __tablename__ = "applications"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.user_id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("jobs.job_id"), nullable=False
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("resumes.resume_id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SAEnum("applied", "pending_analysis", "interview", "offer", "rejected", "withdrawn",
               name="application_status"),
        default="applied",
    )
    relevance_score: Mapped[float | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    applied_date: Mapped[datetime | None] = mapped_column(
        Date, nullable=True
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
    status_history = relationship(
        "ApplicationStatusHistory", back_populates="application",
        cascade="all, delete-orphan",
    )
    ai_insights = relationship(
        "AIInsight", back_populates="application", cascade="all, delete-orphan"
    )
    reminders = relationship(
        "Reminder", back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    history_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("applications.application_id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SAEnum("applied", "pending_analysis", "interview", "offer", "rejected", "withdrawn",
               name="application_status_history_status"),
    )
    changed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC)
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    application = relationship("Application", back_populates="status_history")


class AIInsight(Base):
    __tablename__ = "ai_insights"

    insight_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("applications.application_id"), nullable=False
    )
    matched_skills: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    missing_skills: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    tailored_suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC)
    )

    application = relationship("Application", back_populates="ai_insights")
