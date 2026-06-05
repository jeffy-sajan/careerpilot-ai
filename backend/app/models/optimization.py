"""
Optimization Models.
"""

import uuid

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import OptimizationStatus, OptimizationType


class OptimizationRun(Base, TimestampMixin):
    __tablename__ = "optimization_runs"

    __table_args__ = (Index("ix_optimization_runs_resume_job", "resume_id", "job_description_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Metadata for the generation
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    suggestions: Mapped[list["ResumeOptimization"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<OptimizationRun(id={self.id}, resume_id={self.resume_id})>"


class ResumeOptimization(Base, TimestampMixin):
    __tablename__ = "resume_optimizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    optimization_type: Mapped[OptimizationType] = mapped_column(
        Enum(OptimizationType, name="optimizationtype"), nullable=False
    )
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_text: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[OptimizationStatus] = mapped_column(
        Enum(OptimizationStatus, name="optimizationstatus"), nullable=False, default=OptimizationStatus.PENDING
    )

    # Relationships
    run: Mapped["OptimizationRun"] = relationship(back_populates="suggestions")

    def __repr__(self) -> str:
        return f"<ResumeOptimization(id={self.id}, type='{self.optimization_type}', status='{self.status}')>"
