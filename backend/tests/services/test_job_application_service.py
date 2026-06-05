import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.enums import ApplicationPriority, ApplicationStatus
from app.schemas.job_application import JobApplicationCreate, JobApplicationUpdate
from app.schemas.user import UserCreate
from app.services import auth_service
from app.services.job_application_service import job_application_service


@pytest.fixture
async def sample_user(db_session):
    user_in = UserCreate(name="Job Tracker User", email="job.tracker@example.com", password="secret1Password")
    user = await auth_service.register(db_session, user_in)
    return user


@pytest.mark.asyncio
async def test_create_application(db_session, sample_user):
    create_data = JobApplicationCreate(
        company_name="Google",
        job_title="Software Engineer",
        job_url="https://careers.google.com",
        source="LinkedIn",
        status=ApplicationStatus.APPLIED,
        priority=ApplicationPriority.HIGH,
        application_date=datetime.now(timezone.utc),
        notes="Applied via referral.",
    )

    app = await job_application_service.create_application(
        db=db_session, user_id=sample_user.id, data=create_data.model_dump(exclude_unset=True)
    )

    assert app.company_name == "Google"
    assert app.job_title == "Software Engineer"
    assert app.user_id == sample_user.id


@pytest.mark.asyncio
async def test_get_application_success(db_session, sample_user):
    create_data = JobApplicationCreate(
        company_name="Meta", job_title="Backend Engineer", application_date=datetime.now(timezone.utc)
    )
    app = await job_application_service.create_application(
        db_session, sample_user.id, create_data.model_dump(exclude_unset=True)
    )

    fetched = await job_application_service.get_application(db_session, app.id, sample_user.id)
    assert fetched.id == app.id
    assert fetched.company_name == "Meta"


@pytest.mark.asyncio
async def test_get_application_not_found(db_session, sample_user):
    with pytest.raises(HTTPException) as exc:
        await job_application_service.get_application(db_session, uuid.uuid4(), sample_user.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_application(db_session, sample_user):
    create_data = JobApplicationCreate(
        company_name="Apple", job_title="Systems Engineer", application_date=datetime.now(timezone.utc)
    )
    app = await job_application_service.create_application(
        db_session, sample_user.id, create_data.model_dump(exclude_unset=True)
    )

    update_data = JobApplicationUpdate(status=ApplicationStatus.INTERVIEW)
    updated = await job_application_service.update_application(
        db_session, app.id, update_data.model_dump(exclude_unset=True), sample_user.id
    )

    assert updated.status == ApplicationStatus.INTERVIEW


@pytest.mark.asyncio
async def test_update_application_not_found(db_session, sample_user):
    update_data = JobApplicationUpdate(status=ApplicationStatus.INTERVIEW)
    with pytest.raises(HTTPException) as exc:
        await job_application_service.update_application(
            db_session, uuid.uuid4(), update_data.model_dump(exclude_unset=True), sample_user.id
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_application(db_session, sample_user):
    create_data = JobApplicationCreate(
        company_name="Amazon", job_title="SDE", application_date=datetime.now(timezone.utc)
    )
    app = await job_application_service.create_application(
        db_session, sample_user.id, create_data.model_dump(exclude_unset=True)
    )

    await job_application_service.delete_application(db_session, app.id, sample_user.id)

    with pytest.raises(HTTPException) as exc:
        await job_application_service.get_application(db_session, app.id, sample_user.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_application_not_found(db_session, sample_user):
    with pytest.raises(HTTPException) as exc:
        await job_application_service.delete_application(db_session, uuid.uuid4(), sample_user.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_user_applications(db_session, sample_user):
    create_data = JobApplicationCreate(
        company_name="Netflix", job_title="UI Engineer", application_date=datetime.now(timezone.utc)
    )
    await job_application_service.create_application(
        db_session, sample_user.id, create_data.model_dump(exclude_unset=True)
    )

    apps = await job_application_service.get_user_applications(db_session, sample_user.id)
    assert len(apps) >= 1
    assert apps[0].company_name == "Netflix"
