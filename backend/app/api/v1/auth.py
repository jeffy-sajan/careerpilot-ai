"""
Authentication Router.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, get_current_user
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, RefreshRequest, Token
from app.services import auth_service
from app.models.user import User

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
