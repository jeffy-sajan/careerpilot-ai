"""
Refresh Token Repository.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken

async def create(
    session: AsyncSession, 
    user_id: uuid.UUID, 
    token_hash: str, 
    expires_at: datetime
) -> RefreshToken:
    """Stores a new refresh token hash."""
    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    session.add(db_token)
    await session.commit()
    await session.refresh(db_token)
    return db_token

async def get_by_hash(session: AsyncSession, token_hash: str) -> Optional[RefreshToken]:
    """Fetches a refresh token record by its hash."""
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalars().first()

async def revoke(session: AsyncSession, token_id: uuid.UUID) -> None:
    """Deletes a refresh token from the database, revoking it."""
    await session.execute(
        delete(RefreshToken).where(RefreshToken.id == token_id)
    )
    await session.commit()

async def revoke_all_for_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Deletes all refresh tokens for a given user."""
    await session.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    await session.commit()
