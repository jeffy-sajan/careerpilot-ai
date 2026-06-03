"""
User Model.
"""
import uuid
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Nullable — Google users have no password_hash
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Google OAuth fields (Phase 6) ────────────────────────────────────────
    # Unique ID from Google's identity system. Null for email/password users.
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    # Profile picture URL from Google
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Google guarantees the email is verified. False by default for email/password users
    # until we add an email verification flow.
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Track how the user authenticates: 'email' | 'google' | 'both'
    auth_provider: Mapped[str] = mapped_column(String(20), default="email", nullable=False)

    # Relationships
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    job_applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    job_descriptions: Mapped[list["JobDescription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    google_auth_codes: Mapped[list["GoogleAuthCode"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
