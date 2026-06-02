"""
Resume Analysis Model.
"""
import uuid
from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

class ResumeAnalysis(Base, TimestampMixin):
    __tablename__ = "resume_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    ats_score: Mapped[float] = mapped_column(Float, nullable=False)
    strengths: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    weaknesses: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    keyword_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    resume: Mapped["Resume"] = relationship(back_populates="analyses")

    def __repr__(self) -> str:
        return f"<ResumeAnalysis(id={self.id}, resume_id={self.resume_id}, ats_score={self.ats_score})>"
