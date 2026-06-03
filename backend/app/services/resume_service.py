"""
Resume Service.
"""
import uuid
from typing import Sequence

from fastapi import BackgroundTasks, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import StorageProvider
from app.models.resume import Resume
from app.repositories import resume_repo
from app.schemas.resume import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_BYTES


class ResumeService:
    def __init__(self, storage_provider: StorageProvider):
        self.storage_provider = storage_provider

    async def upload_resume(
        self, 
        session: AsyncSession, 
        user_id: uuid.UUID, 
        file: UploadFile,
        background_tasks: BackgroundTasks
    ) -> Resume:
        """
        Validates the uploaded file, saves it via the storage provider, 
        and creates a database record. Enqueues a background parsing task.
        Rollbacks physical file on DB failure.
        """
        # 1 & 2. Validate File
        if not file.content_type or file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=415, 
                detail="Unsupported file type. Only PDF and DOCX are allowed."
            )

        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413, 
                detail="File size exceeds the 5MB limit."
            )
            
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty."
            )

        # 3 & 4. Save file via StorageProvider
        try:
            storage_path, file_url = await self.storage_provider.save_file(
                file_bytes=file_bytes, 
                user_id=user_id, 
                original_filename=file.filename or "unknown"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")

        # 5 & 6. Save metadata via repository and handle rollback
        try:
            resume = await resume_repo.create(
                session=session,
                user_id=user_id,
                original_file_name=file.filename or "unknown",
                storage_path=storage_path,
                content_type=file.content_type,
                file_size_bytes=file_size,
            )
            # Trigger background parsing task
            background_tasks.add_task(self.parse_resume_task, resume.id, user_id)
            
            return resume
        except Exception as e:
            # Rollback storage if DB insert fails
            await self.storage_provider.delete_file(storage_path)
            # Re-raise to trigger a 500 response and allow FastAPI to rollback the DB session
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def parse_resume_task(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Background task to perform raw text extraction and update resume parsing state.
        Uses a separate/fresh database session context.
        """
        import tempfile
        from pathlib import Path

        from app.core.parsers import DOCXResumeParser, PDFResumeParser
        from app.database.session import async_session_factory
        from app.models.enums import ResumeStatus

        async with async_session_factory() as session:
            # 1. Fetch resume record
            resume = await resume_repo.get_by_id(session, resume_id, user_id)
            if not resume:
                return  # Was deleted in the meantime

            # 2. Update status to PROCESSING
            resume.status = ResumeStatus.PROCESSING
            await session.commit()
            
            try:
                # 3. Read file bytes from storage provider
                file_bytes = await self.storage_provider.read_file(resume.storage_path)
                
                # 4. Extract text by writing to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(resume.original_file_name).suffix) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = Path(tmp.name)

                try:
                    raw_text = ""
                    if resume.content_type == "application/pdf":
                        parser = PDFResumeParser()
                        raw_text = parser.extract_text(tmp_path)
                    elif resume.content_type == (
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    ):
                        parser = DOCXResumeParser()
                        raw_text = parser.extract_text(tmp_path)
                    else:
                        raise ValueError(f"Unsupported content type for parsing: {resume.content_type}")
                finally:
                    # Clean up temp file
                    if tmp_path.exists():
                        tmp_path.unlink()

                # 5. Check if we extracted any text
                if not raw_text:
                    raise ValueError(
                        "No extractable text found in resume. The document might be scanned or empty."
                    )

                # 6. Save text and update status to COMPLETED
                resume.raw_text = raw_text
                resume.parsing_engine_version = "v1-python"
                resume.status = ResumeStatus.COMPLETED
                resume.error_message = None
                
            except Exception as e:
                # 7. Update status to FAILED and record error message
                resume.status = ResumeStatus.FAILED
                resume.error_message = str(e)
            
            await session.commit()


    async def get_resume(self, session: AsyncSession, resume_id: uuid.UUID, user_id: uuid.UUID) -> Resume:
        """Fetches a specific resume."""
        resume = await resume_repo.get_by_id(session, resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return resume


    async def list_resumes(
        self, session: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Resume]:
        """Fetches all resumes for a user."""
        return await resume_repo.get_all_for_user(session, user_id, skip, limit)


    async def delete_resume(self, session: AsyncSession, resume_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Deletes a resume from database and storage."""
        # Need to fetch it first to get the storage_path and ensure ownership
        resume = await self.get_resume(session, resume_id, user_id)
        
        # Delete from DB first
        success = await resume_repo.delete(session, resume_id, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete resume record")
            
        # Delete from physical storage
        # Even if this fails, the DB record is gone, making it an orphaned file,
        # which is preferable to an orphaned DB record.
        await self.storage_provider.delete_file(resume.storage_path)
