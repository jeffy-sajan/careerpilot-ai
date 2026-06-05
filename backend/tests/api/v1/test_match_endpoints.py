import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.user import User


async def _register_and_login(client: AsyncClient, email: str) -> str:
    """Registers a user and returns a valid Bearer token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Match Test User",
            "email": email,
            "password": "testPassword123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "testPassword123",
        },
    )
    return login_resp.json()["access_token"]


@pytest.fixture
async def test_user_and_token(client: AsyncClient, db_session: AsyncSession):
    email = f"user_{uuid.uuid4()}@example.com"
    token = await _register_and_login(client, email)
    # Fetch user from DB to get ID
    from sqlalchemy import select

    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    return user, token


@pytest.fixture
async def sample_resume(db_session: AsyncSession, test_user_and_token) -> Resume:
    """Creates a sample resume with enough text to bypass edge-case filters."""
    user, _ = test_user_and_token
    resume = Resume(
        user_id=user.id,
        file_name="test_resume.pdf",
        original_file_name="test_resume.pdf",
        storage_path="/tmp/test_resume.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        file_url="/tmp/test_resume.pdf",
        raw_text="I am a highly skilled senior engineer. I have over 5 years of experience using Python, FastAPI, and PostgreSQL. I have managed a large team of developers and driven product growth. "
        * 3,  # Duplicate to ensure > 30 words
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    return resume


@pytest.fixture
async def sample_jd(db_session: AsyncSession, test_user_and_token) -> JobDescription:
    """Creates a sample job description with enough text to bypass edge-case filters."""
    user, _ = test_user_and_token
    jd = JobDescription(
        user_id=user.id,
        title="Senior Backend Engineer",
        company="Acme Corp",
        description="We are seeking a senior backend engineer. You must have strong experience with Python and PostgreSQL. You will be managing a team of developers and driving product growth. "
        * 3,  # Duplicate to ensure > 30 words
    )
    db_session.add(jd)
    await db_session.commit()
    await db_session.refresh(jd)
    return jd


@pytest.mark.asyncio
async def test_generate_match_success(
    client: AsyncClient,
    sample_resume: Resume,
    sample_jd: JobDescription,
    test_user_and_token,
):
    """Test generating a match between a valid resume and JD."""
    _, token = test_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(f"/api/v1/resumes/{sample_resume.id}/match/{sample_jd.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "match_score" in data
    assert "matched_skills" in data
    assert "missing_skills" in data

    # Python and PostgreSQL should be matched
    assert "Python" in data["matched_skills"]
    assert "PostgreSQL" in data["matched_skills"]


@pytest.mark.asyncio
async def test_generate_match_insufficient_text(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user_and_token,
    sample_jd: JobDescription,
):
    """Test the edge case guardrail when resume text is too short."""
    user, token = test_user_and_token
    headers = {"Authorization": f"Bearer {token}"}

    short_resume = Resume(
        user_id=user.id,
        file_name="short.pdf",
        original_file_name="short.pdf",
        storage_path="/tmp/short.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        file_url="/tmp/short.pdf",
        raw_text="Too short. Just a few words.",
    )
    db_session.add(short_resume)
    await db_session.commit()
    await db_session.refresh(short_resume)

    response = await client.post(f"/api/v1/resumes/{short_resume.id}/match/{sample_jd.id}", headers=headers)
    assert response.status_code == 400
    assert "Insufficient text" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_match_ownership_validation(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_jd: JobDescription,
    test_user_and_token,
):
    """Test that a user cannot match a resume they don't own."""
    user, token = test_user_and_token
    headers = {"Authorization": f"Bearer {token}"}

    # Create a resume owned by a DIFFERENT user
    other_email = f"other_{uuid.uuid4()}@example.com"
    await _register_and_login(client, other_email)

    from sqlalchemy import select

    from app.models.user import User

    result = await db_session.execute(select(User).where(User.email == other_email))
    other_user = result.scalars().first()
    other_user_id = other_user.id

    other_resume = Resume(
        user_id=other_user_id,
        file_name="other.pdf",
        original_file_name="other.pdf",
        storage_path="/tmp/other.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        file_url="/tmp/other.pdf",
        raw_text="This is someone else's resume text, it has a lot of words so it passes the length check. " * 5,
    )
    db_session.add(other_resume)
    await db_session.commit()
    await db_session.refresh(other_resume)

    # Attempting to match it with the current user's token should 404
    response = await client.post(f"/api/v1/resumes/{other_resume.id}/match/{sample_jd.id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_existing_match(
    client: AsyncClient,
    sample_resume: Resume,
    sample_jd: JobDescription,
    test_user_and_token,
):
    """Test retrieving an already generated match."""
    _, token = test_user_and_token
    headers = {"Authorization": f"Bearer {token}"}

    # First generate it
    await client.post(f"/api/v1/resumes/{sample_resume.id}/match/{sample_jd.id}", headers=headers)

    # Then get it
    response = await client.get(f"/api/v1/resumes/{sample_resume.id}/match/{sample_jd.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["match_score"] > 0
