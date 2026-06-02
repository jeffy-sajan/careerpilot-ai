"""
User Repository.
"""
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Fetch a user by email."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Fetch a user by their ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def create(session: AsyncSession, user_in: UserCreate) -> User:
    """Create a new user with hashed password."""
    user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=get_password_hash(user_in.password)
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
