"""
GoogleAuthCode Model.

A short-lived, single-use code used to securely pass authentication
from the backend OAuth callback to the frontend without putting a JWT in a URL.

Flow:
  Backend callback → creates GoogleAuthCode (TTL: 60s)
  → Redirects frontend to /auth/google/callback?code=<UUID>
  → Frontend calls POST /auth/google/exchange { code: UUID }
  → Backend validates, deletes code, returns JWT pair
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class GoogleAuthCode(Base, TimestampMixin):
    __tablename__ = "google_auth_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    is_new_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="google_auth_codes")

    def __repr__(self) -> str:
        return f"<GoogleAuthCode(user_id={self.user_id})>"
