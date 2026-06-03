"""
Authentication Service.
"""
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from app.schemas.user import UserCreate
from app.schemas.auth import Token
from app.models.user import User
from app.repositories import user_repo, refresh_token_repo

def _hash_token(token: str) -> str:
    """Creates a fast SHA256 hash for secure database lookup of high-entropy tokens."""
    return hashlib.sha256(token.encode()).hexdigest()

async def register(session: AsyncSession, user_in: UserCreate) -> User:
    """Registers a new user if the email is not already taken."""
    existing_user = await user_repo.get_by_email(session, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )
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

async def create_tokens(session: AsyncSession, user_id: uuid.UUID) -> Token:
    """Creates a new access and refresh token pair."""
    # 1. Create Access Token
    access_token = create_access_token(subject=str(user_id))
    
    # 2. Create Refresh Token (High entropy random string)
    refresh_token = secrets.token_urlsafe(32)
    refresh_token_hash = _hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # 3. Store refresh token hash in DB
    await refresh_token_repo.create(
        session=session,
        user_id=user_id,
        token_hash=refresh_token_hash,
        expires_at=expires_at
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

async def refresh_tokens(session: AsyncSession, refresh_token: str) -> Token:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address."
        )
        
    reset_token = create_password_reset_token(email)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    # Simulate sending an email (in production, integrate with SendGrid/SMTP)
    print("\n" + "="*50)
    print("PASSWORD RESET REQUESTED")
    print(f"To: {email}")
    print(f"Click the link below to reset your password:\n{reset_url}")
    print("="*50 + "\n")

async def reset_password(session: AsyncSession, token: str, new_password: str) -> None:
    """
    Verifies the reset token, updates the user's password, and revokes all active sessions.
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )
        
    user = await user_repo.get_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
        
    # Hash the new password and update the user record
    new_hashed_password = get_password_hash(new_password)
    user.password_hash = new_hashed_password
    session.add(user)
    
    # Revoke all active refresh tokens for this user so old sessions are terminated
    await refresh_token_repo.revoke_all_for_user(session, user.id)
    
    await session.commit()

