"""
FastAPI Dependencies.
"""
import uuid
from typing import AsyncGenerator
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.core.config import settings
from app.database.session import get_async_session
from app.models.user import User
from app.repositories import user_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current authenticated user.
    Decodes the JWT, extracts the user ID, and fetches from the database.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user_uuid = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user = await user_repo.get_by_id(db, user_id=user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
