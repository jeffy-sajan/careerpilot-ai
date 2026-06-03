"""
Authentication Router.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, get_current_user
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
)
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """Register a new user."""
    return await auth_service.register(db, user_in)

@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Authenticate and receive access and refresh tokens."""
    user = await auth_service.authenticate(db, request.email, request.password)
    return await auth_service.create_tokens(db, user.id)

@router.post("/refresh", response_model=Token)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Use a refresh token to get a new access token."""
    return await auth_service.refresh_tokens(db, request.refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get the current authenticated user's profile."""
    return current_user

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Request a password reset email.
    """
    await auth_service.request_password_reset(db, request.email)
    return {"message": "Password reset link has been sent to your email."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Reset a user's password using the token sent to their email.
    """
    await auth_service.reset_password(db, request.token, request.new_password)
    return {"message": "Password successfully reset."}
