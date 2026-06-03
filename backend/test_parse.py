import asyncio
from app.database.session import async_session_factory
from sqlalchemy import select
from app.models.resume import Resume
from app.services.resume_service import ResumeService
from app.core.storage import LocalStorageProvider
import traceback

async def main():
    try:
        async with async_session_factory() as session:
            # Get the most recent resume
            result = await session.execute(select(Resume).order_by(Resume.created_at.desc()).limit(1))
            resume = result.scalars().first()
            if not resume:
                print('No resume found')
                return
            
            print(f'Found resume: {resume.id} for user {resume.user_id}')
            
            service = ResumeService(storage_provider=LocalStorageProvider())
            await service.parse_resume_task(resume.id, resume.user_id)
            print('Parse task completed')
            
            # check status
            await session.refresh(resume)
            print(f'Status: {resume.status}')
            print(f'Error message: {resume.error_message}')
    except Exception as e:
        print('Exception caught!')
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
