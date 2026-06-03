"""
Resume Repository.
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ResumeStatus
from app.models.resume import Resume


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    original_file_name: str,
    storage_path: str,
    content_type: str,
    file_size_bytes: int,
    status: ResumeStatus = ResumeStatus.UPLOADED,
) -> Resume:
    """
    Creates a new resume record in the database.
    """
    resume = Resume(
        user_id=user_id,
        original_file_name=original_file_name,
        storage_path=storage_path,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        status=status,
        # Populate legacy fields to satisfy existing NOT NULL constraints 
        # (until they are officially dropped in a future cleanup)
        file_name=original_file_name,
        file_url=storage_path,
    )
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


async def get_by_id(
    session: AsyncSession, 
    resume_id: uuid.UUID, 
    user_id: uuid.UUID
) -> Optional[Resume]:
    """
    Fetches a specific resume by ID. 
    Enforces user ownership.
    """
    result = await session.execute(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id
        )
    )
    return result.scalars().first()


async def get_all_for_user(
    session: AsyncSession, 
    user_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100
) -> Sequence[Resume]:
    """
    Fetches all resumes for a specific user, sorted by creation date (newest first).
    Supports pagination via skip and limit.
    """
    result = await session.execute(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def delete(
    session: AsyncSession, 
    resume_id: uuid.UUID, 
    user_id: uuid.UUID
) -> bool:
    """
    Deletes a specific resume by ID.
    Enforces user ownership.
    Returns True if a row was deleted, False otherwise.
    """
    result = await session.execute(
        sqlalchemy_delete(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id
        )
    )
    await session.commit()
    return result.rowcount > 0
