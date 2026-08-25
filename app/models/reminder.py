import uuid
from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDType


class Reminder(Base):
    __tablename__ = "reminders"

    reminder_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("applications.application_id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.user_id"), nullable=False
    )
    reminder_type: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50), default="in_app")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "sent", "cancelled", name="reminder_status"),
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC)
    )

    application = relationship("Application", back_populates="reminders")
    user = relationship("User", back_populates="reminders")
