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
    user_in = UserCreate(name="ATS Rule Test User", email="ats.rule.test@example.com", password="secret1Password")
    user = await auth_service.register(db_session, user_in)
    return user


@pytest.fixture
async def perfect_resume(db_session, sample_user):
    text = (
        "John Doe\n"
        "john.doe@example.com | 555-123-4567 | linkedin.com/in/johndoe | github.com/johndoe\n\n"
        "Summary:\n"
        "Highly experienced Software Engineer with a proven track record of building scalable web applications and leading engineering teams.\n\n"
        "Skills:\n"
        "Languages: Python, Java, JavaScript, TypeScript, Go, SQL\n"
        "Frameworks: React, Django, FastAPI, Angular, Node.js\n"
        "Tools: Docker, AWS, Kubernetes, Git, PostgreSQL\n\n"
        "Experience:\n"
        "Senior Software Engineer | Google | Jan 2021 - Present\n"
        "- Developed a microservices architecture that increased performance by 40%\n"
        "- Managed a team of 15 engineers and streamlined deployments using Docker\n"
        "- Created an automated testing pipeline, reducing bugs by 30%\n\n"
        "Software Engineer | Microsoft | June 2018 - Dec 2020\n"
        "- Optimized database queries, reducing latency by 25% for millions of users\n"
        "- Spearheaded transition to cloud architecture on AWS saving $50k annually\n"
        "- Mentored 5 junior engineers and established testing guidelines\n\n"
        "Education:\n"
        "University of Technology, B.S. in Computer Science and Bachelor of Science, College of Engineering, 2018\n\n"
        "Projects:\n"
        "Resume Analyzer\n"
        "- Built a full-stack resume analysis application using React and FastAPI with PostgreSQL database to process documents\n"
        "- Deployed the application using Docker containers on AWS with automatic CI/CD pipelines to guarantee uptime\n"
        "E-Commerce Platform\n"
        "- Developed a secure online shopping site using Django and integrated Stripe payments API to handle transactions safely\n"
    )
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
    text = (
        "john.doe@example.com\n"
        "Skills:\n"
        "Experience:\n"
        "Education:\n"
    ) + ("This is some placeholder text to make sure the word count is over 150 words. " * 20)
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

    # Under the new engine, a borderline resume has a very low score and gets penalized
    assert analysis.ats_score < 15.0
    assert len(analysis.strengths) > 0
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
