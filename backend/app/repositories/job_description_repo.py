"""
Job Description Repository.

Provides async CRUD operations against the job_descriptions table.
All write operations bake in user ownership enforcement so the service
layer never has to remember to do it manually.
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    description: str,
    company: Optional[str] = None,
) -> JobDescription:
    """
    Persists a new Job Description for the given user.
    """
    jd = JobDescription(
        user_id=user_id,
        title=title,
        company=company,
        description=description,
    )
    session.add(jd)
    await session.commit()
    await session.refresh(jd)
    return jd


async def get_by_id(
    session: AsyncSession,
    jd_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[JobDescription]:
    """
    Fetches a single Job Description by ID.
    Enforces user ownership — returns None if the record belongs to
    a different user, making it indistinguishable from a missing record.
    """
    result = await session.execute(
        select(JobDescription).where(
            JobDescription.id == jd_id,
            JobDescription.user_id == user_id,
        )
    )
    return result.scalars().first()


async def get_all_for_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[JobDescription]:
    """
    Returns all Job Descriptions belonging to the user,
    sorted by creation date (newest first).
    Supports pagination via skip / limit.
    """
    result = await session.execute(
        select(JobDescription)
        .where(JobDescription.user_id == user_id)
        .order_by(JobDescription.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def delete(
    session: AsyncSession,
    jd_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Deletes a Job Description by ID.
    Enforces user ownership at the query level so a user can never
    delete another user's record.
    Returns True if a row was deleted, False if the record was not found.
    """
    result = await session.execute(
        sqlalchemy_delete(JobDescription).where(
            JobDescription.id == jd_id,
            JobDescription.user_id == user_id,
        )
    )
    await session.commit()
    return result.rowcount > 0
