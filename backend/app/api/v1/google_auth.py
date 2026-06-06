"""
Google OAuth 2.0 Router — Phase 6

Endpoints:
  GET  /auth/google/authorize  → Redirects browser to Google consent screen
  GET  /auth/google/callback   → Receives auth code from Google, creates user, redirects frontend
  POST /auth/google/exchange   → Frontend exchanges one-time code for a JWT pair

Security:
  - Google Client Secret never leaves the backend
  - State parameter prevents CSRF on the OAuth flow
  - One-time code pattern prevents JWT exposure in URLs
"""

from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.core.config import settings
from app.core.rate_limit import limiter
from app.repositories import google_auth_code_repo, user_repo
from app.schemas.auth import GoogleExchangeRequest, Token
from app.services import auth_service

router = APIRouter()

# ── Configure the Authlib OAuth client ───────────────────────────────────────
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account",  # Always show account picker
    },
)


@router.get("/authorize")
@limiter.limit("10/minute")
async def google_authorize(request: Request):
    """
    Step 1: Redirect the user's browser to Google's consent screen.
    Authlib automatically generates and stores the `state` parameter
    in the session to prevent CSRF.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Sign-In is not configured on this server.",
        )
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Step 2: Google redirects the user back here with ?code=...&state=...
    - Exchanges the auth code for a Google ID token
    - Decodes the ID token to get the user's profile
    - Finds or creates a user in our database
    - Creates a short-lived one-time code
    - Redirects the frontend to /auth/google/callback?code=<one_time_code>
    """
    frontend_url = settings.FRONTEND_URL

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        # Google denied access or state mismatch (possible CSRF)
        return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed&detail={str(e.error)}")

    # Google's ID token contains verified user info
    user_info = token.get("userinfo")
    if not user_info:
        return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed&detail=no_user_info")

    google_id = user_info.get("sub")  # Google's unique user ID
    email = user_info.get("email")
    name = user_info.get("name") or email.split("@")[0]
    picture = user_info.get("picture")

    try:
        user, is_new_user = await user_repo.get_or_create_google_user(
            session=db,
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=picture,
        )
    except ValueError as e:
        # Email already registered with a different provider
        error_type = str(e).split(":")[0]
        return RedirectResponse(url=f"{frontend_url}/login?error={error_type}")

    # Create a one-time code — frontend will exchange this for a JWT pair
    auth_code = await google_auth_code_repo.create(
        session=db,
        user_id=user.id,
        is_new_user=is_new_user,
    )

    redirect_params = f"code={auth_code.code}&is_new_user={str(is_new_user).lower()}"
    return RedirectResponse(url=f"{frontend_url}/auth/google/callback?{redirect_params}")


@router.post("/exchange", response_model=Token)
@limiter.limit("10/minute")
async def google_exchange(
    request: Request,
    response: Response,
    body: GoogleExchangeRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Step 3: The frontend sends the one-time code here.
    - Validates the code (exists + not expired)
    - Deletes the code immediately (single-use)
    - Returns a full JWT access + refresh token pair
    """
    db_code = await google_auth_code_repo.get_by_code(db, body.code)

    if not db_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used authentication code.",
        )

    # Check expiry
    now = datetime.now(timezone.utc)
    expires_at = db_code.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        await google_auth_code_repo.delete_by_id(db, db_code.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication code has expired. Please sign in again.",
        )

    # Delete the one-time code immediately (prevents replay attacks)
    user_id = db_code.user_id
    await google_auth_code_repo.delete_by_id(db, db_code.id)

    # Issue a normal JWT + refresh token pair
    token_response, refresh_token_str = await auth_service.create_tokens(db, user_id)

    from app.core.config import settings

    response.set_cookie(
        key="careerpilot_rt",
        value=refresh_token_str,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="none" if settings.ENVIRONMENT == "production" else "lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return token_response
