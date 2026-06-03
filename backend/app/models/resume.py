"""
Resume Model.
"""
import uuid
from sqlalchemy import ForeignKey, String, Text, Enum, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import ResumeStatus

class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    __table_args__ = (
        Index("ix_resumes_created_at", "created_at"),
        Index("ix_resumes_user_id_status", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # New fields for upload and parsing lifecycle
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus, name="resumestatus"),
        nullable=False,
        default=ResumeStatus.UPLOADED
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsing_engine_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="resumes")
    analyses: Mapped[list["ResumeAnalysis"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", lazy="selectin"
    )
    matches: Mapped[list["ResumeMatch"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, original_file_name='{self.original_file_name}', status='{self.status}')>"

