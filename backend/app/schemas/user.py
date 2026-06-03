"""
User Pydantic Schemas.

Defines the shape of data coming IN (requests) and going OUT (responses)
for all user-related API operations.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ─────────────────────────────────────────────────────────────
# Request Schemas  (data the CLIENT sends TO the API)
# ─────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    """
    Payload required to create a new user account.
    Used by: POST /api/v1/auth/register
    """

    name: str = Field(
        min_length=2,
        max_length=100,
        description="The user's full display name.",
        examples=["Jane Doe"],
    )
    email: EmailStr = Field(
        description="A valid, unique email address.",
        examples=["jane.doe@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Account password. Minimum 8 characters.",
        examples=["Str0ng!Pass"],
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Strips surrounding whitespace and rejects blank/whitespace-only names."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Name must not be blank or contain only whitespace.")
        return stripped

    @field_validator("password")
    @classmethod
    def password_must_have_complexity(cls, v: str) -> str:
        """
        Enforces that the password contains at least one digit
        and at least one letter — a lightweight complexity check.
        """
        has_letter = any(c.isalpha() for c in v)
        has_digit  = any(c.isdigit() for c in v)
        if not has_letter or not has_digit:
            raise ValueError(
                "Password must contain at least one letter and one digit."
            )
        return v


# ─────────────────────────────────────────────────────────────
# Response Schemas  (data the API sends BACK to the client)
# ─────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """
    Public user profile returned by the API.
    Sensitive fields (password_hash, etc.) are deliberately excluded.
    Used by: POST /register (201), GET /me (200)
    """

    id: uuid.UUID = Field(description="The user's unique identifier (UUID v4).")
    name: str     = Field(description="The user's display name.")
    email: EmailStr = Field(description="The user's email address.")
    avatar_url: Optional[str] = Field(default=None, description="Profile picture URL (Google users only).")
    auth_provider: str = Field(default="email", description="How the user authenticates: 'email' | 'google' | 'both'.")
    created_at: datetime = Field(description="Timestamp when the account was created (UTC).")
    updated_at: datetime = Field(description="Timestamp of the last profile update (UTC).")

    # Tells Pydantic to read values from SQLAlchemy ORM model attributes,
    # not just plain dictionaries.
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────
# Internal Aliases  (keep backward-compat with router / service)
# ─────────────────────────────────────────────────────────────

# The router and service were written using 'UserCreate'.
# This alias means we don't have to touch those files.
UserCreate = UserRegisterRequest
