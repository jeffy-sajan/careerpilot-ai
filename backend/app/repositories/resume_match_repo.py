"""
Resume Match Repository.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_match import ResumeMatch


async def create_or_update(
    session: AsyncSession,
    resume_id: uuid.UUID,
    job_description_id: uuid.UUID,
    match_score: float,
    matched_skills: list[str],
    missing_skills: list[str],
    missing_keywords: list[str],
    suggestions: list[str],
) -> ResumeMatch:
    """
    Creates a new match record or updates an existing one if it already exists
    for the given resume and job description.
    """
    result = await session.execute(
        select(ResumeMatch).where(
            ResumeMatch.resume_id == resume_id,
            ResumeMatch.job_description_id == job_description_id,
        )
    )
    match = result.scalars().first()

    if match:
        match.match_score = match_score
        match.matched_skills = matched_skills
        match.missing_skills = missing_skills
        match.missing_keywords = missing_keywords
        match.suggestions = suggestions
    else:
        match = ResumeMatch(
            resume_id=resume_id,
            job_description_id=job_description_id,
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            missing_keywords=missing_keywords,
            suggestions=suggestions,
        )
        session.add(match)

    await session.commit()
    await session.refresh(match)
    return match


async def get_match(
    session: AsyncSession,
    resume_id: uuid.UUID,
    job_description_id: uuid.UUID,
) -> Optional[ResumeMatch]:
    """Fetches a specific match."""
    result = await session.execute(
        select(ResumeMatch).where(
            ResumeMatch.resume_id == resume_id,
            ResumeMatch.job_description_id == job_description_id,
        )
    )
    return result.scalars().first()
