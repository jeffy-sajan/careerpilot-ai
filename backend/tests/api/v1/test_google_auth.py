from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.api.v1.google_auth import oauth


@pytest.mark.asyncio
async def test_authorize_redirect(client: AsyncClient):
    # Call the authorize endpoint
    # Authlib will generate a RedirectResponse to Google
    resp = await client.get("/api/v1/auth/google/authorize", follow_redirects=False)
    assert resp.status_code == 302
    assert "accounts.google.com" in resp.headers["location"]


@pytest.mark.asyncio
async def test_callback_success(client: AsyncClient):
    # Mock the authorize_access_token method to return a dummy token with userinfo
    mock_token = {
        "userinfo": {
            "sub": "1234567890",
            "email": "google.user@example.com",
            "name": "Google User",
            "picture": "http://example.com/pic.jpg",
        }
    }
    with patch.object(oauth.google, "authorize_access_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_token

        # We need a fake session cookie because Authlib checks state,
        # but in our mock we might just bypass that if authorize_access_token handles it.
        # Calling the callback
        resp = await client.get("/api/v1/auth/google/callback?code=fakecode&state=fakestate", follow_redirects=False)

        # It should redirect to frontend callback
        assert resp.status_code in (302, 307)
        assert "/auth/google/callback" in resp.headers["location"]
        assert "code=" in resp.headers["location"]

        # Extract the code from the redirect URL
        loc = resp.headers["location"]
        code = loc.split("code=")[1].split("&")[0]

        # Exchange the code
        exchange_resp = await client.post("/api/v1/auth/google/exchange", json={"code": code})
        assert exchange_resp.status_code == 200
        tokens = exchange_resp.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_callback_no_userinfo(client: AsyncClient):
    mock_token = {}
    with patch.object(oauth.google, "authorize_access_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_token
        resp = await client.get("/api/v1/auth/google/callback?code=fakecode", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert "error=google_auth_failed" in resp.headers["location"]


@pytest.mark.asyncio
async def test_callback_oauth_error(client: AsyncClient):
    from authlib.integrations.starlette_client import OAuthError

    with patch.object(oauth.google, "authorize_access_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.side_effect = OAuthError("invalid_request", "state mismatch")
        resp = await client.get("/api/v1/auth/google/callback?code=fakecode", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert "error=google_auth_failed" in resp.headers["location"]


@pytest.mark.asyncio
async def test_exchange_invalid_code(client: AsyncClient):
    exchange_resp = await client.post("/api/v1/auth/google/exchange", json={"code": "invalidcode"})
    assert exchange_resp.status_code == 400


@pytest.mark.asyncio
async def test_exchange_expired_code(client: AsyncClient, db_session):
    import datetime

    from app.repositories import google_auth_code_repo, user_repo
    from app.schemas.user import UserCreate

    # Create user
    user = await user_repo.create(db_session, UserCreate(name="User", email="u@x.com", password="Password123"))

    # Create expired code manually
    auth_code = await google_auth_code_repo.create(db_session, user.id, True)
    auth_code.expires_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=10)
    db_session.add(auth_code)
    await db_session.commit()

    exchange_resp = await client.post("/api/v1/auth/google/exchange", json={"code": auth_code.code})
    assert exchange_resp.status_code == 400
    assert "expired" in exchange_resp.json()["detail"]
