"""
Job Description Service.

Business logic layer sitting between the API router and the repository.
Responsible for ownership validation and raising the correct HTTP errors
so the router stays thin and declarative.
"""

import uuid
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.repositories import job_description_repo
from app.schemas.job_description import JobDescriptionCreate


class JobDescriptionService:
    """
    Encapsulates all business rules for managing Job Descriptions.

    Design decisions:
    - Ownership is enforced at both the repository query level (WHERE user_id = ?)
      AND here in the service layer (404 on None result), giving defence in depth.
    - 404 is returned even when the record exists but belongs to another user —
      leaking 403 would confirm the record exists, which is a privacy issue.
    """

    async def create(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        payload: JobDescriptionCreate,
    ) -> JobDescription:
        """
        Saves a new Job Description for the authenticated user.

        Request flow:
        1. Router receives POST /api/v1/jobs with JWT + JSON body.
        2. `get_current_user` dependency resolves the JWT to a User ORM object.
        3. Router delegates here with (session, user.id, validated payload).
        4. Repository inserts the row, commits, and returns the refreshed ORM object.
        5. Router serialises via JobDescriptionResponse and returns HTTP 201.
        """
        return await job_description_repo.create(
            session=session,
            user_id=user_id,
            title=payload.title,
            company=payload.company,
            description=payload.description,
        )

    async def get(
        self,
        session: AsyncSession,
        jd_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> JobDescription:
        """
        Fetches a single Job Description, asserting ownership.

        Request flow:
        1. Router receives GET /api/v1/jobs/{id} with JWT.
        2. `get_current_user` resolves user.
        3. Router delegates here with (session, jd_id, user.id).
        4. Repository queries WHERE id = ? AND user_id = ?.
        5. If None → 404 raised here (not in the router).
        6. Router serialises via JobDescriptionResponse and returns HTTP 200.
        """
        jd = await job_description_repo.get_by_id(session, jd_id, user_id)
        if not jd:
            raise HTTPException(status_code=404, detail="Job description not found")
        return jd

    async def list(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[JobDescription]:
        """
        Returns all Job Descriptions for the authenticated user.

        Request flow:
        1. Router receives GET /api/v1/jobs with JWT + optional skip/limit query params.
        2. `get_current_user` resolves user.
        3. Router delegates here with (session, user.id, skip, limit).
        4. Repository runs paginated SELECT … ORDER BY created_at DESC.
        5. Router serialises via List[JobDescriptionListResponse] and returns HTTP 200.
        """
        return await job_description_repo.get_all_for_user(
            session=session,
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    async def delete(
        self,
        session: AsyncSession,
        jd_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """
        Deletes a Job Description, asserting ownership.

        Request flow:
        1. Router receives DELETE /api/v1/jobs/{id} with JWT.
        2. `get_current_user` resolves user.
        3. Router delegates here with (session, jd_id, user.id).
        4. Repository executes DELETE WHERE id = ? AND user_id = ?.
        5. If no row was deleted (False returned) → 404 raised here.
        6. Router returns HTTP 204 No Content.

        Note: Cascading deletes on ResumeMatch rows are handled at the
        database level via the ON DELETE CASCADE foreign key constraint,
        so this service does not need to manually clean up match records.
        """
        deleted = await job_description_repo.delete(session, jd_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Job description not found")


# Module-level singleton — mirrors the ats_service pattern in this codebase.
job_description_service = JobDescriptionService()
