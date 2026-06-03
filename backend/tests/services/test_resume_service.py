from io import BytesIO

import pytest
from fastapi import BackgroundTasks, HTTPException, UploadFile

from app.core.storage import LocalStorageProvider
from app.models.enums import ResumeStatus
from app.schemas.user import UserCreate
from app.services import auth_service
from app.services.resume_service import ResumeService


@pytest.fixture
def temp_storage(tmp_path):
    return LocalStorageProvider(base_dir=str(tmp_path))

@pytest.fixture
def resume_service(temp_storage):
    return ResumeService(storage_provider=temp_storage)

@pytest.fixture
async def sample_user(db_session):
    user_in = UserCreate(
        name="Resume Service User",
        email="resume.service@example.com",
        password="secret1Password"
    )
    user = await auth_service.register(db_session, user_in)
    return user

@pytest.mark.asyncio
async def test_upload_and_delete_resume(db_session, sample_user, resume_service, temp_storage):
    # 1. Prepare dummy file
    content = b"%PDF-1.4 dummy pdf content"
    file_name = "test_resume.pdf"
    
    # Simulate FastAPI UploadFile
    upload_file = UploadFile(
        file=BytesIO(content),
        filename=file_name,
        headers={"content-type": "application/pdf"}
    )
    # FastAPI sets size on read or we can set it
    
    # 2. Upload
    bg_tasks = BackgroundTasks()
    resume = await resume_service.upload_resume(db_session, sample_user.id, upload_file, bg_tasks)
    
    assert resume.id is not None
    assert resume.user_id == sample_user.id
    assert resume.original_file_name == file_name
    assert resume.content_type == "application/pdf"
    assert resume.file_size_bytes == len(content)
    assert resume.status == ResumeStatus.UPLOADED
    assert resume.storage_path.startswith("resumes/")
    
    # Verify file exists on physical storage
    assert await temp_storage.file_exists(resume.storage_path) is True

    # 3. List Resumes
    resumes = await resume_service.list_resumes(db_session, sample_user.id)
    assert len(resumes) == 1
    assert resumes[0].id == resume.id

    # 4. Get Resume
    fetched = await resume_service.get_resume(db_session, resume.id, sample_user.id)
    assert fetched.id == resume.id

    # 5. Delete Resume
    await resume_service.delete_resume(db_session, resume.id, sample_user.id)

    # Verify deleted from DB
    with pytest.raises(HTTPException) as exc:
        await resume_service.get_resume(db_session, resume.id, sample_user.id)
    assert exc.value.status_code == 404

    # Verify deleted from physical storage
    assert await temp_storage.file_exists(resume.storage_path) is False
