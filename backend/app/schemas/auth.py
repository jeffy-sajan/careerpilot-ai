"""
Authentication Pydantic Schemas.

Defines the shape of data coming IN (requests) and going OUT (responses)
for all authentication-related API operations (login, token refresh, Google OAuth).
"""

from pydantic import BaseModel, EmailStr, Field

# ─────────────────────────────────────────────────────────────
# Request Schemas  (data the CLIENT sends TO the API)
# ─────────────────────────────────────────────────────────────


class UserLoginRequest(BaseModel):
    """
    Payload required to authenticate and receive a token pair.
    Used by: POST /api/v1/auth/login
    """

    email: EmailStr = Field(
        description="The registered email address.",
        examples=["jane.doe@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="The account password.",
        examples=["Str0ng!Pass"],
    )


class RefreshTokenRequest(BaseModel):
    """
    Payload required to exchange a refresh token for a new token pair.
    Used by: POST /api/v1/auth/refresh
    """

    refresh_token: str = Field(
        min_length=10,
        description="The opaque refresh token received during login.",
        examples=["dGhpcyBpcyBhIHNhbXBsZSByZWZyZXNoIHRva2Vu"],
    )


class GoogleExchangeRequest(BaseModel):
    """
    Payload to exchange a short-lived Google one-time code for a JWT pair.
    Used by: POST /api/v1/auth/google/exchange

    The frontend receives the code as a URL query param after the Google OAuth
    callback, then immediately sends it here to get tokens without exposing
    a JWT in the URL.
    """

    code: str = Field(
        min_length=10,
        description="The one-time auth code from the Google callback redirect.",
    )


class ForgotPasswordRequest(BaseModel):
    """
    Payload to request a password reset email/link.
    """

    email: EmailStr = Field(description="The registered email address.")


class ResetPasswordRequest(BaseModel):
    """
    Payload to finalize a password reset with the new password.
    """

    token: str = Field(description="The short-lived reset token.")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="The new account password.",
    )


# ─────────────────────────────────────────────────────────────
# Response Schemas  (data the API sends BACK to the client)
# ─────────────────────────────────────────────────────────────


class TokenResponse(BaseModel):
    """
    Token pair returned after a successful login or token refresh.
    Used by: POST /login (200), POST /refresh (200), POST /google/exchange (200)
    """

    access_token: str = Field(description="Short-lived JWT for API authorization.")
    token_type: str = Field(default="bearer", description="Token scheme, always 'bearer'.")


# ─────────────────────────────────────────────────────────────
# Internal Aliases  (backward-compat with router / service)
# ─────────────────────────────────────────────────────────────
LoginRequest = UserLoginRequest
RefreshRequest = RefreshTokenRequest
Token = TokenResponse
