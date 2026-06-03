import asyncio
import uuid
from app.database.session import async_session_factory
from app.repositories import user_repo, resume_repo
from app.models.enums import ResumeStatus
from app.services.resume_service import ResumeService
from app.core.storage import LocalStorageProvider
from app.schemas.user import UserCreate
from fastapi import UploadFile, BackgroundTasks
from io import BytesIO

async def main():
    print("1. Creating local storage provider")
    storage = LocalStorageProvider(base_dir="uploads")
    service = ResumeService(storage_provider=storage)
    
    print("2. Connecting to DB session")
    async with async_session_factory() as session:
        print("3. Creating sample user")
        user_in = UserCreate(
            name="Debug User",
            email=f"debug-{uuid.uuid4().hex[:6]}@example.com",
            password="secret1Password"
        )
        from app.services import auth_service
        user = await auth_service.register(session, user_in)
        print(f"Created user: {user.id}")
        
        print("4. Preparing dummy upload file")
        content = b"%PDF-1.4 dummy pdf content"
        upload_file = UploadFile(
            file=BytesIO(content),
            filename="debug_resume.pdf",
            headers={"content-type": "application/pdf"}
        )
        
        print("5. Uploading resume")
        bg_tasks = BackgroundTasks()
        resume = await service.upload_resume(
            session=session,
            user_id=user.id,
            file=upload_file,
            background_tasks=bg_tasks
        )
        print(f"Uploaded resume ID: {resume.id}, Status: {resume.status}")
        
        print("6. Committing session so other sessions can see the resume")
        await session.commit()
        
        print("7. Running background tasks")
        from unittest.mock import patch, MagicMock
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Hello World PDF parser debug text content."
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        
        with patch("pypdf.PdfReader", return_value=mock_reader):
            await bg_tasks()
            
        print("8. Fetching updated resume status")
        await session.refresh(resume)
        print(f"Final Resume Status: {resume.status}")
        print(f"Raw Text: {resume.raw_text}")
        print(f"Error Message: {resume.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
