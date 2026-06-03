import pytest
import uuid
from io import BytesIO
from unittest.mock import patch, MagicMock
from fastapi import UploadFile, BackgroundTasks
from app.services.resume_service import ResumeService
from app.core.storage import LocalStorageProvider
from app.repositories import resume_repo
from app.models.enums import ResumeStatus
from app.schemas.user import UserCreate
from app.services import auth_service
import app.core.parsers

@pytest.fixture
def temp_storage(tmp_path):
    return LocalStorageProvider(base_dir=str(tmp_path))

@pytest.fixture
def resume_service(temp_storage):
    return ResumeService(storage_provider=temp_storage)

@pytest.fixture
async def sample_user(db_session):
    user_in = UserCreate(
        name="Parser Test User",
        email="parser.test@example.com",
        password="secret1Password"
    )
    user = await auth_service.register(db_session, user_in)
    return user

# Context manager mock to yield the test's db_session instead of creating a new connection
class MockSessionContext:
    def __init__(self, session):
        self.session = session
    async def __aenter__(self):
        return self.session
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Do not close the shared test session
        pass

@pytest.mark.asyncio
async def test_pdf_parsing_success(db_session, sample_user, resume_service, temp_storage):
    # 1. Prepare dummy file
    content = b"%PDF-1.4 dummy pdf content"
    file_name = "test_resume.pdf"
    
    upload_file = UploadFile(
        file=BytesIO(content),
        filename=file_name,
        headers={"content-type": "application/pdf"}
    )
    
    # Mock PyMuPDF page and doc
    mock_page = MagicMock()
    mock_page.get_text.return_value = "John Doe\nSoftware Engineer\nPython & FastAPI expert."
    mock_doc = MagicMock()
    mock_doc.__iter__.return_value = [mock_page]
    mock_doc.is_encrypted = False
    
    bg_tasks = BackgroundTasks()
    
    # Patch async_session_factory to share the test transaction, and patch fitz.open
    with patch("app.database.session.async_session_factory", return_value=MockSessionContext(db_session)), \
         patch("app.core.parsers.fitz.open", return_value=mock_doc) as mock_fitz_open:
         
        resume = await resume_service.upload_resume(
            session=db_session,
            user_id=sample_user.id,
            file=upload_file,
            background_tasks=bg_tasks
        )
        
        assert resume.status == ResumeStatus.UPLOADED
        
        # Execute background tasks synchronously
        await bg_tasks()
        
        # Refresh session to fetch updated DB fields
        await db_session.refresh(resume)
        
        # Verify success status transitions and raw_text mapping
        assert resume.status == ResumeStatus.COMPLETED
        assert "John Doe" in resume.raw_text
        assert "FastAPI expert" in resume.raw_text
        assert resume.parsing_engine_version == "v1-python"
        assert resume.error_message is None
        
        mock_fitz_open.assert_called_once()


@pytest.mark.asyncio
async def test_docx_parsing_success(db_session, sample_user, resume_service, temp_storage):
    # 1. Prepare dummy file
    content = b"dummy docx zip content"
    file_name = "test_resume.docx"
    
    upload_file = UploadFile(
        file=BytesIO(content),
        filename=file_name,
        headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    )
    
    # Mock Document
    mock_para = MagicMock()
    mock_para.text = "Jane Smith\nData Scientist\nMachine Learning Specialist."
    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para]
    mock_doc.tables = []
    
    bg_tasks = BackgroundTasks()
    
    with patch("app.database.session.async_session_factory", return_value=MockSessionContext(db_session)), \
         patch("app.core.parsers.Document", return_value=mock_doc) as mock_docx_document:
         
        resume = await resume_service.upload_resume(
            session=db_session,
            user_id=sample_user.id,
            file=upload_file,
            background_tasks=bg_tasks
        )
        
        await bg_tasks()
        await db_session.refresh(resume)
        
        assert resume.status == ResumeStatus.COMPLETED
        assert "Jane Smith" in resume.raw_text
        assert "Machine Learning" in resume.raw_text
        assert resume.parsing_engine_version == "v1-python"
        assert resume.error_message is None
        
        mock_docx_document.assert_called_once()


@pytest.mark.asyncio
async def test_parsing_failure_corrupted_pdf(db_session, sample_user, resume_service, temp_storage):
    content = b"corrupt binary"
    file_name = "corrupt.pdf"
    
    upload_file = UploadFile(
        file=BytesIO(content),
        filename=file_name,
        headers={"content-type": "application/pdf"}
    )
    
    bg_tasks = BackgroundTasks()
    
    with patch("app.database.session.async_session_factory", return_value=MockSessionContext(db_session)), \
         patch("app.core.parsers.fitz.open", side_effect=Exception("Failed to open or parse PDF file")):
         
        resume = await resume_service.upload_resume(
            session=db_session,
            user_id=sample_user.id,
            file=upload_file,
            background_tasks=bg_tasks
        )
        
        await bg_tasks()
        await db_session.refresh(resume)
        
        assert resume.status == ResumeStatus.FAILED
        assert "Failed to open or parse PDF file" in resume.error_message
        assert resume.raw_text is None


@pytest.mark.asyncio
async def test_parsing_failure_empty_extracted_text(db_session, sample_user, resume_service, temp_storage):
    content = b"scanned content"
    file_name = "scanned.pdf"
    
    upload_file = UploadFile(
        file=BytesIO(content),
        filename=file_name,
        headers={"content-type": "application/pdf"}
    )
    
    mock_page = MagicMock()
    mock_page.get_text.return_value = "   \n   "  # Whitespace only
    mock_doc = MagicMock()
    mock_doc.__iter__.return_value = [mock_page]
    mock_doc.is_encrypted = False
    
    bg_tasks = BackgroundTasks()
    
    with patch("app.database.session.async_session_factory", return_value=MockSessionContext(db_session)), \
         patch("app.core.parsers.fitz.open", return_value=mock_doc):
         
        resume = await resume_service.upload_resume(
            session=db_session,
            user_id=sample_user.id,
            file=upload_file,
            background_tasks=bg_tasks
        )
        
        await bg_tasks()
        await db_session.refresh(resume)
        
        assert resume.status == ResumeStatus.FAILED
        assert "No extractable text found" in resume.error_message
        assert resume.raw_text is None
