"""
Activity Log Model.
"""
import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base, TimestampMixin

class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, action='{self.action}')>"
