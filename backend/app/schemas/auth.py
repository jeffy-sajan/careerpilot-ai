"""
Authentication Pydantic Schemas.

Defines the shape of data coming IN (requests) and going OUT (responses)
for all authentication-related API operations (login, token refresh).
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

    The refresh token is a high-entropy random string (not a JWT).
    It is stored as a SHA-256 hash in the database.
    """

    refresh_token: str = Field(
        min_length=10,
        description="The opaque refresh token received during login.",
        examples=["dGhpcyBpcyBhIHNhbXBsZSByZWZyZXNoIHRva2Vu"],
    )


# ─────────────────────────────────────────────────────────────
# Response Schemas  (data the API sends BACK to the client)
# ─────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """
    Token pair returned after a successful login or token refresh.
    Used by: POST /login (200), POST /refresh (200)

    - access_token  → Short-lived JWT (default: 15 min). Use this on every
                      protected API request in the Authorization header.
    - refresh_token → Long-lived opaque token (default: 7 days). Use ONLY
                      to obtain a new access_token when the current one expires.
    - token_type    → Always "bearer". Tells the client how to send the token.
    """

    access_token: str  = Field(description="Short-lived JWT for API authorization.")
    refresh_token: str = Field(description="Long-lived opaque token for silent re-authentication.")
    token_type: str    = Field(default="bearer", description="Token scheme, always 'bearer'.")


# ─────────────────────────────────────────────────────────────
# Internal Aliases  (keep backward-compat with router / service)
# ─────────────────────────────────────────────────────────────

# The router and service were written using 'LoginRequest', 'RefreshRequest',
# and 'Token'. These aliases maintain compatibility without touching those files.
LoginRequest  = UserLoginRequest
RefreshRequest = RefreshTokenRequest
Token          = TokenResponse
