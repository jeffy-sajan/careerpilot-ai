"""
API Integration Tests — Job Description Endpoints.

Tests the full HTTP stack: routing → service → repository → database.
Each test registers a fresh user and uses that user's JWT for all requests,
so ownership enforcement is exercised on every authenticated call.
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register_and_login(client: AsyncClient, email: str) -> str:
    """Registers a user and returns a valid Bearer token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "JD Test User",
            "email": email,
            "password": "jd1TestPassword",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "jd1TestPassword",
        },
    )
    return login_resp.json()["access_token"]


JD_PAYLOAD = {
    "title": "Senior Backend Engineer",
    "company": "Acme Corp",
    "description": (
        "We are looking for a Senior Backend Engineer with strong Python, "
        "FastAPI, and PostgreSQL skills. Experience with Docker and AWS is a plus. "
        "You will design scalable microservices and collaborate with a distributed team."
    ),
}


# ---------------------------------------------------------------------------
# POST /api/v1/jobs — Create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_job_description(client: AsyncClient):
    """A valid POST creates the JD and returns HTTP 201 with the full record."""
    token = await _register_and_login(client, "jd.create@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/v1/jobs/", json=JD_PAYLOAD, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == JD_PAYLOAD["title"]
    assert data["company"] == JD_PAYLOAD["company"]
    assert data["description"] == JD_PAYLOAD["description"]
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_job_description_unauthenticated(client: AsyncClient):
    """Creating a JD without a token must return 401."""
    response = await client.post("/api/v1/jobs/", json=JD_PAYLOAD)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_job_description_no_company(client: AsyncClient):
    """Company field is optional — creating without it must succeed."""
    token = await _register_and_login(client, "jd.nocompany@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {**JD_PAYLOAD, "company": None}

    response = await client.post("/api/v1/jobs/", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json()["company"] is None


@pytest.mark.asyncio
async def test_create_job_description_missing_title(client: AsyncClient):
    """Missing required field `title` must return 422 Unprocessable Entity."""
    token = await _register_and_login(client, "jd.badrequest@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {k: v for k, v in JD_PAYLOAD.items() if k != "title"}

    response = await client.post("/api/v1/jobs/", json=payload, headers=headers)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/jobs — List
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_job_descriptions_empty(client: AsyncClient):
    """A new user with no JDs should receive an empty list."""
    token = await _register_and_login(client, "jd.listempty@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/jobs/", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_job_descriptions(client: AsyncClient):
    """A user sees only their own JDs, sorted newest first."""
    token = await _register_and_login(client, "jd.list@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create two JDs
    await client.post("/api/v1/jobs/", json={**JD_PAYLOAD, "title": "JD One"}, headers=headers)
    await client.post("/api/v1/jobs/", json={**JD_PAYLOAD, "title": "JD Two"}, headers=headers)

    response = await client.get("/api/v1/jobs/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Newest first
    assert data[0]["title"] == "JD Two"
    assert data[1]["title"] == "JD One"
    # List response should NOT include the full description text
    assert "description" not in data[0]


@pytest.mark.asyncio
async def test_list_job_descriptions_isolation(client: AsyncClient):
    """User A cannot see User B's job descriptions."""
    token_a = await _register_and_login(client, "jd.usera@example.com")
    token_b = await _register_and_login(client, "jd.userb@example.com")

    # User A creates a JD
    await client.post("/api/v1/jobs/", json=JD_PAYLOAD, headers={"Authorization": f"Bearer {token_a}"})

    # User B's list must be empty
    response = await client.get("/api/v1/jobs/", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /api/v1/jobs/{id} — Detail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_job_description(client: AsyncClient):
    """GET /{id} returns the full record including description text."""
    token = await _register_and_login(client, "jd.get@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/api/v1/jobs/", json=JD_PAYLOAD, headers=headers)
    jd_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/jobs/{jd_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == jd_id
    assert data["description"] == JD_PAYLOAD["description"]


@pytest.mark.asyncio
async def test_get_job_description_not_found(client: AsyncClient):
    """GET with a random UUID returns 404."""
    import uuid

    token = await _register_and_login(client, "jd.get404@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(f"/api/v1/jobs/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_job_description_other_user(client: AsyncClient):
    """User B cannot access User A's JD — returns 404 (not 403, to avoid leaking existence)."""
    token_a = await _register_and_login(client, "jd.own.a@example.com")
    token_b = await _register_and_login(client, "jd.own.b@example.com")

    # User A creates a JD
    create_resp = await client.post("/api/v1/jobs/", json=JD_PAYLOAD, headers={"Authorization": f"Bearer {token_a}"})
    jd_id = create_resp.json()["id"]

    # User B tries to access it
    response = await client.get(f"/api/v1/jobs/{jd_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/jobs/{id} — Delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_job_description(client: AsyncClient):
    """DELETE returns 204 and the JD is no longer accessible."""
    token = await _register_and_login(client, "jd.delete@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/api/v1/jobs/", json=JD_PAYLOAD, headers=headers)
    jd_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/jobs/{jd_id}", headers=headers)
    assert delete_resp.status_code == 204

    # Confirm it's gone
    get_resp = await client.get(f"/api/v1/jobs/{jd_id}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_description_not_found(client: AsyncClient):
    """DELETE on a non-existent ID returns 404."""
    import uuid

    token = await _register_and_login(client, "jd.del404@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.delete(f"/api/v1/jobs/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_description_other_user(client: AsyncClient):
    """User B cannot delete User A's JD — returns 404."""
    token_a = await _register_and_login(client, "jd.dela@example.com")
    token_b = await _register_and_login(client, "jd.delb@example.com")

    create_resp = await client.post("/api/v1/jobs/", json=JD_PAYLOAD, headers={"Authorization": f"Bearer {token_a}"})
    jd_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/jobs/{jd_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 404

    # Confirm User A's JD still exists
    get_resp = await client.get(f"/api/v1/jobs/{jd_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert get_resp.status_code == 200
