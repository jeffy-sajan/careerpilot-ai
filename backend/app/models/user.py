"""
User Model.
"""
import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

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

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
