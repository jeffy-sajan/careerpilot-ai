"""
Job Application Models.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import ApplicationPriority, ApplicationStatus


class JobApplication(Base, TimestampMixin):
    __tablename__ = "job_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
        default=ApplicationStatus.SAVED,
        index=True,
    )
    priority: Mapped[ApplicationPriority] = mapped_column(
        Enum(ApplicationPriority, name="application_priority"),
        nullable=False,
        default=ApplicationPriority.MEDIUM,
    )

    application_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_interview_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="job_applications")
    status_history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationStatusHistory.changed_at"
    )

    def __repr__(self) -> str:
        return f"<JobApplication(id={self.id}, company='{self.company_name}', status='{self.status}')>"


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )

    old_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)

    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    application: Mapped["JobApplication"] = relationship(back_populates="status_history")
    changed_by_user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return (
            f"<ApplicationStatusHistory(id={self.id}, "
            f"application_id={self.application_id}, new_status='{self.new_status}')>"
        )
