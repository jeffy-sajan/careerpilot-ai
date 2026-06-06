"""
Authentication Router.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    Token,
)
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_async_session)):
    """Register a new user."""
    return await auth_service.register(db, user_in)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request, response: Response, body: LoginRequest, db: AsyncSession = Depends(get_async_session)
):
    """Authenticate and receive access and refresh tokens."""
    from app.core.config import settings

    user = await auth_service.authenticate(db, body.email, body.password)
    token_response, refresh_token_str = await auth_service.create_tokens(db, user.id)

    response.set_cookie(
        key="careerpilot_rt",
        value=refresh_token_str,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="none" if settings.ENVIRONMENT == "production" else "lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return token_response


@router.post("/refresh", response_model=Token)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_async_session)):
    """Use a refresh token from HttpOnly cookie to get a new access token."""
    from app.core.config import settings

    refresh_token = request.cookies.get("careerpilot_rt")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    token_response, new_refresh_token_str = await auth_service.refresh_tokens(db, refresh_token)

    response.set_cookie(
        key="careerpilot_rt",
        value=new_refresh_token_str,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="none" if settings.ENVIRONMENT == "production" else "lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return token_response


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """Clear the refresh token cookie."""
    from app.core.config import settings
    response.delete_cookie(
        key="careerpilot_rt",
        samesite="none" if settings.ENVIRONMENT == "production" else "lax"
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_async_session)):
    """
    Request a password reset email.
    """
    await auth_service.request_password_reset(db, body.email)
    return {"message": "Password reset link has been sent to your email."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_async_session)):
    """
    Reset a user's password using the token sent to their email.
    """
    await auth_service.reset_password(db, request.token, request.new_password)
    return {"message": "Password successfully reset."}
