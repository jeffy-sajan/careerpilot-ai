"""
Job Application Model.
"""
import uuid
from datetime import date
from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base, TimestampMixin
from app.models.enums import ApplicationSource, ApplicationStatus

class JobApplication(Base, TimestampMixin):
    __tablename__ = "job_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    source: Mapped[ApplicationSource] = mapped_column(
        Enum(ApplicationSource, name="application_source"),
        nullable=False,
        default=ApplicationSource.OTHER,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
        default=ApplicationStatus.SAVED,
        index=True,
    )
    
    application_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="job_applications")

    def __repr__(self) -> str:
        return f"<JobApplication(id={self.id}, company='{self.company}', status='{self.status}')>"
