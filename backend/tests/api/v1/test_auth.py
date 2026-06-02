import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "name": "API User",
        "email": "api.user@example.com",
        "password": "api1Password"
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "api.user@example.com"
    assert "password_hash" not in data

@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {
        "name": "API User",
        "email": "api.dup@example.com",
        "password": "api1Password"
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login_and_me(client: AsyncClient):
    payload = {
        "name": "Login User",
        "email": "api.login@example.com",
        "password": "login1Password"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "api.login@example.com",
        "password": "login1Password"
    })
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    # Get Me
    me_resp = await client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "api.login@example.com"

@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh(client: AsyncClient):
    payload = {
        "name": "Refresh User",
        "email": "api.refresh@example.com",
        "password": "login1Password"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "api.refresh@example.com",
        "password": "login1Password"
    })
    refresh_token = login_resp.json()["refresh_token"]
    
    # Refresh
    ref_resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert ref_resp.status_code == 200
    assert "access_token" in ref_resp.json()

@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient):
    # Register user
    payload = {
        "name": "Forgot User",
        "email": "api.forgot@example.com",
        "password": "login1Password"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    # Valid email
    resp = await client.post("/api/v1/auth/forgot-password", json={
        "email": "api.forgot@example.com"
    })
    assert resp.status_code == 202
    
    # Invalid email
    resp_invalid = await client.post("/api/v1/auth/forgot-password", json={
        "email": "nonexistent@example.com"
    })
    assert resp_invalid.status_code == 404

@pytest.mark.asyncio
async def test_reset_password(client: AsyncClient, capsys):
    payload = {
        "name": "Reset User",
        "email": "api.reset@example.com",
        "password": "login1Password"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    await client.post("/api/v1/auth/forgot-password", json={
        "email": "api.reset@example.com"
    })
    
    captured = capsys.readouterr()
    token_line = [line for line in captured.out.split('\n') if "?token=" in line][0]
    token = token_line.split("?token=")[1]
    
    resp = await client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "newpassword123"
    })
    assert resp.status_code == 200
