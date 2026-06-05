import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OptimizationStatus
from app.models.optimization import OptimizationRun, ResumeOptimization
from app.models.resume import Resume
from app.models.user import User


async def _register_and_login(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Opt Test User",
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
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    return user, token


@pytest.fixture
async def sample_resume(db_session: AsyncSession, test_user_and_token) -> Resume:
    user, _ = test_user_and_token
    resume = Resume(
        user_id=user.id,
        file_name="test_opt.pdf",
        original_file_name="test_opt.pdf",
        storage_path="/tmp/test_opt.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        file_url="/tmp/test_opt.pdf",
        raw_text="I am a backend engineer with Python.",
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    return resume


@pytest.mark.asyncio
async def test_generate_resume_optimizations(
    client: AsyncClient,
    test_user_and_token,
    sample_resume: Resume,
):
    _, token = test_user_and_token
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.api.v1.optimizations.optimization_generator_service.generate_suggestions") as mock_gen:
        mock_gen.return_value = [
            {
                "section": "Summary",
                "original_text": "I am a backend engineer",
                "suggested_text": "I am a senior backend engineer",
                "reasoning": "Better adjective",
                "optimization_type": "SUMMARY_IMPROVEMENT",
            }
        ]

        response = await client.post(f"/api/v1/resumes/{sample_resume.id}/optimize", headers=headers)

        print("Response:", response.status_code, response.text)
        assert response.status_code == 201
        data = response.json()
        assert data["resume_id"] == str(sample_resume.id)
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["section"] == "Summary"
        assert data["suggestions"][0]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_update_optimization_status_idor(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user_and_token,
):
    user1, token1 = test_user_and_token
    headers1 = {"Authorization": f"Bearer {token1}"}

    email2 = f"other_{uuid.uuid4()}@example.com"
    await _register_and_login(client, email2)
    result = await db_session.execute(select(User).where(User.email == email2))
    user2 = result.scalars().first()

    resume2 = Resume(
        user_id=user2.id,
        file_name="r2.pdf",
        original_file_name="r2.pdf",
        storage_path="/tmp/r2.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        file_url="/tmp/r2.pdf",
        raw_text="Other resume",
    )
    db_session.add(resume2)
    await db_session.commit()
    await db_session.refresh(resume2)

    run = OptimizationRun(resume_id=resume2.id, model_name="test", prompt_version="v1")
    db_session.add(run)
    await db_session.flush()

    opt = ResumeOptimization(
        run_id=run.id,
        optimization_type="KEYWORD",
        section="Summary",
        original_text="A",
        suggested_text="B",
        reasoning="C",
        status=OptimizationStatus.PENDING,
    )
    db_session.add(opt)
    await db_session.commit()
    await db_session.refresh(opt)

    response = await client.patch(
        f"/api/v1/optimizations/{opt.id}/status", headers=headers1, json={"status": "ACCEPTED"}
    )

    assert response.status_code == 404
