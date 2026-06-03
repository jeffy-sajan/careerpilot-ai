import uuid

import pytest
from fastapi import HTTPException

from app.models.enums import ResumeStatus
from app.models.resume import Resume
from app.schemas.user import UserCreate
from app.services import auth_service
from app.services.ats_service import ATSService


@pytest.fixture
async def sample_user(db_session):
    user_in = UserCreate(
        name="ATS Rule Test User",
        email="ats.rule.test@example.com",
        password="secret1Password"
    )
    user = await auth_service.register(db_session, user_in)
    return user

@pytest.fixture
async def perfect_resume(db_session, sample_user):
    text = (
        "john.doe@example.com 555-123-4567 linkedin.com/in/johndoe\n"
        "Skills: Python, React, SQL\n"
        "Education: University of Technology, B.S. Computer Science\n"
        "Experience:\n"
        "- Developed a microservices architecture that increased performance by 40%\n"
        "- Managed a team of 15 engineers and streamlined deployments\n"
        "- Created an automated testing pipeline, reducing bugs by 30%\n"
    ) + ("This is some extra text to make sure the word count is over 150 words. " * 15)
    resume = Resume(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        file_name="perfect.pdf",
        file_url="http://example.com/perfect.pdf",
        original_file_name="perfect.pdf",
        storage_path="resumes/perfect.pdf",
        content_type="application/pdf",
        file_size_bytes=1000,
        status=ResumeStatus.COMPLETED,
        raw_text=text,
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    return resume

@pytest.fixture
async def weak_resume(db_session, sample_user):
    text = "Just a very short text with nothing in it."
    resume = Resume(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        file_name="weak.pdf",
        file_url="http://example.com/weak.pdf",
        original_file_name="weak.pdf",
        storage_path="resumes/weak.pdf",
        content_type="application/pdf",
        file_size_bytes=500,
        status=ResumeStatus.COMPLETED,
        raw_text=text,
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    return resume

@pytest.mark.asyncio
async def test_ats_analysis_perfect_resume(db_session, sample_user, perfect_resume):
    service = ATSService()
    analysis = await service.analyze_resume(db_session, perfect_resume.id, sample_user.id)
    
    assert analysis.id is not None
    assert analysis.ats_score == 100.0
    assert any("email" in s.lower() for s in analysis.strengths)
    assert len(analysis.weaknesses) == 0
    
    # Retrieve analysis
    fetched = await service.get_analysis(db_session, perfect_resume.id, sample_user.id)
    assert fetched.ats_score == 100.0

@pytest.mark.asyncio
async def test_ats_analysis_weak_resume(db_session, sample_user, weak_resume):
    service = ATSService()
    analysis = await service.analyze_resume(db_session, weak_resume.id, sample_user.id)
    
    # Missing email(-10), phone(-10), linkedin(-5), skills(-15), education(-10), experience(-15), metrics(-10), length(-10), bullets(-10), verbs(-5) = 100 - 100 = 0
    assert analysis.ats_score == 0.0
    assert len(analysis.strengths) == 0
    assert len(analysis.weaknesses) > 0

@pytest.mark.asyncio
async def test_ats_analysis_resume_not_found(db_session, sample_user):
    service = ATSService()
    with pytest.raises(HTTPException) as exc:
        await service.analyze_resume(db_session, uuid.uuid4(), sample_user.id)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_ats_analysis_no_raw_text(db_session, sample_user):
    resume = Resume(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        file_name="empty.pdf",
        file_url="http://example.com/empty.pdf",
        original_file_name="empty.pdf",
        storage_path="resumes/empty.pdf",
        content_type="application/pdf",
        file_size_bytes=1000,
        status=ResumeStatus.PROCESSING,
        raw_text=None,
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    
    service = ATSService()
    with pytest.raises(HTTPException) as exc:
        await service.analyze_resume(db_session, resume.id, sample_user.id)
    assert exc.value.status_code == 400

