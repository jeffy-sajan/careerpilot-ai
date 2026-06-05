"""
Authentication Service.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import send_reset_password_email
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    get_password_hash,
    verify_password,
    verify_password_reset_token,
)
from app.models.user import User
from app.repositories import refresh_token_repo, user_repo
from app.schemas.auth import Token
from app.schemas.user import UserCreate


def _hash_token(token: str) -> str:
    """Creates a fast SHA256 hash for secure database lookup of high-entropy tokens."""
    return hashlib.sha256(token.encode()).hexdigest()


async def register(session: AsyncSession, user_in: UserCreate) -> User:
    """Registers a new user if the email is not already taken."""
    existing_user = await user_repo.get_by_email(session, user_in.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists.")
    return await user_repo.create(session, user_in)


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    """Authenticates a user by email and password."""
    user = await user_repo.get_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return user


async def create_tokens(session: AsyncSession, user_id: uuid.UUID) -> tuple[Token, str]:
    """Creates a new access and refresh token pair."""
    # 1. Create Access Token
    access_token = create_access_token(subject=str(user_id))

    # 2. Create Refresh Token (High entropy random string)
    refresh_token = secrets.token_urlsafe(32)
    refresh_token_hash = _hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # 3. Store refresh token hash in DB
    await refresh_token_repo.create(
        session=session, user_id=user_id, token_hash=refresh_token_hash, expires_at=expires_at
    )

    token_response = Token(access_token=access_token, token_type="bearer")
    return token_response, refresh_token


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> tuple[Token, str]:
    """Validates the refresh token and issues a new token pair."""
    token_hash = _hash_token(refresh_token)
    db_token = await refresh_token_repo.get_by_hash(session, token_hash)

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Make sure expires_at is timezone aware for comparison
    now = datetime.now(timezone.utc)
    # Convert db_token.expires_at to UTC if it's naive (some DB drivers return naive UTC)
    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        await refresh_token_repo.revoke(session, db_token.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Revoke the old token (Refresh Token Rotation)
    await refresh_token_repo.revoke(session, db_token.id)

    # Issue a new pair
    return await create_tokens(session, db_token.user_id)


async def request_password_reset(session: AsyncSession, email: str) -> None:
    """
    Checks if a user exists with the given email, and if so,
    generates a reset token and simulates sending an email.
    """
    user = await user_repo.get_by_email(session, email)
    if not user:
        # Prevent user enumeration by silently returning
        return

    reset_token = create_password_reset_token(email)

    # Send the email using SMTP
    await send_reset_password_email(email_to=email, token=reset_token)


async def reset_password(session: AsyncSession, token: str, new_password: str) -> None:
    """
    Verifies the reset token, updates the user's password, and revokes all active sessions.
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token.")

    user = await user_repo.get_by_email(session, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Hash the new password and update the user record
    new_hashed_password = get_password_hash(new_password)
    user.password_hash = new_hashed_password
    session.add(user)

    # Revoke all active refresh tokens for this user so old sessions are terminated
    await refresh_token_repo.revoke_all_for_user(session, user.id)

    await session.commit()
