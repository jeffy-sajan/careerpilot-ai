"""
User Repository.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Fetch a user by email."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Fetch a user by their ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_by_google_id(session: AsyncSession, google_id: str) -> Optional[User]:
    """Fetch a user by their Google ID (for returning Google sign-in users)."""
    result = await session.execute(select(User).where(User.google_id == google_id))
    return result.scalars().first()


async def create(session: AsyncSession, user_in: UserCreate) -> User:
    """Create a new user with hashed password."""
    user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=get_password_hash(user_in.password),
        auth_provider="email",
        email_verified=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_google_user(
    session: AsyncSession,
    google_id: str,
    email: str,
    name: str,
    avatar_url: Optional[str],
) -> tuple[User, bool]:
    """
    Finds or creates a user from Google OAuth data.
    Returns (user, is_new_user).

    Decision tree:
    1. Look up by google_id → returning Google user (update profile, return)
    2. Look up by email → existing email/password user (raise conflict)
    3. Neither found → create new Google user
    """
    # 1. Returning Google user
    existing_by_google = await get_by_google_id(session, google_id)
    if existing_by_google:
        # Update name/avatar in case they changed on Google
        existing_by_google.name = name
        existing_by_google.avatar_url = avatar_url
        await session.commit()
        await session.refresh(existing_by_google)
        return existing_by_google, False

    # 2. Email already registered with password — block and inform
    existing_by_email = await get_by_email(session, email)
    if existing_by_email:
        # Re-raise as a specific exception the router can catch and convert to
        # a redirect with ?error=account_exists_with_different_provider
        raise ValueError(f"account_exists_with_different_provider:{email}")

    # 3. Brand new Google user — create account
    new_user = User(
        email=email,
        name=name,
        password_hash=None,  # Google users have no password
        google_id=google_id,
        avatar_url=avatar_url,
        email_verified=True,  # Google guarantees email is verified
        auth_provider="google",
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user, True
