"""
Resume Model.
"""
import uuid
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="resumes")
    analyses: Mapped[list["ResumeAnalysis"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", lazy="selectin"
    )
    matches: Mapped[list["ResumeMatch"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, file_name='{self.file_name}')>"
