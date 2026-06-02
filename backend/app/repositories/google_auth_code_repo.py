"""
Google Auth Code Repository.
Handles creation, lookup, and deletion of one-time auth codes.
"""
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.google_auth_code import GoogleAuthCode

CODE_TTL_SECONDS = 60  # Code is valid for 60 seconds


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    is_new_user: bool,
) -> GoogleAuthCode:
    """Creates a short-lived one-time auth code for the given user."""
    code = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=CODE_TTL_SECONDS)

    db_code = GoogleAuthCode(
        user_id=user_id,
        code=code,
        is_new_user=is_new_user,
        expires_at=expires_at,
    )
    session.add(db_code)
    await session.commit()
    await session.refresh(db_code)
    return db_code


async def get_by_code(
    session: AsyncSession, code: str
) -> Optional[GoogleAuthCode]:
    """Fetches an auth code record by its code string."""
    result = await session.execute(
        select(GoogleAuthCode).where(GoogleAuthCode.code == code)
    )
    return result.scalars().first()


async def delete_by_id(session: AsyncSession, code_id: uuid.UUID) -> None:
    """Deletes an auth code by its primary key (after successful use)."""
    await session.execute(
        delete(GoogleAuthCode).where(GoogleAuthCode.id == code_id)
    )
    await session.commit()


async def delete_expired(session: AsyncSession) -> None:
    """Cleanup task — removes all expired codes (run periodically)."""
    now = datetime.now(timezone.utc)
    await session.execute(
        delete(GoogleAuthCode).where(GoogleAuthCode.expires_at < now)
    )
    await session.commit()
