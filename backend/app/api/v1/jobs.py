"""
Job Description API Routes.

All endpoints are JWT-protected via the `get_current_user` dependency.
User ownership is enforced in the service layer — the router only handles
HTTP concerns (status codes, request/response serialisation).
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_async_session
from app.models.user import User
from app.schemas.job_description import (
    JobDescriptionCreate,
    JobDescriptionListResponse,
    JobDescriptionResponse,
)
from app.services.job_description_service import job_description_service

router = APIRouter()


@router.post("/", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_description(
    payload: JobDescriptionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    **Save a new Job Description.**

    The client pastes the full job posting text and gives it a title.
    The resulting record is immediately ready to be used for Resume Matching.

    **Request flow:**
    `Client` → JWT validated → `JobDescriptionService.create` → `job_description_repo.create`
    → row inserted → ORM object refreshed → serialised → `HTTP 201`
    """
    return await job_description_service.create(db, current_user.id, payload)


@router.get("/", response_model=List[JobDescriptionListResponse])
async def list_job_descriptions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    **List all saved Job Descriptions for the authenticated user.**

    Returns a lightweight list (no full description text) sorted by
    creation date, newest first. Supports pagination via `skip` and `limit`.

    **Request flow:**
    `Client` → JWT validated → `JobDescriptionService.list` → `job_description_repo.get_all_for_user`
    → paginated SELECT → list serialised → `HTTP 200`
    """
    return await job_description_service.list(db, current_user.id, skip, limit)


@router.get("/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    jd_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    **Retrieve a single Job Description by ID.**

    Returns the full record including the description text.
    Returns `404` if the ID does not exist **or** belongs to a different user
    (ownership is never leaked via a 403).

    **Request flow:**
    `Client` → JWT validated → `JobDescriptionService.get` → `job_description_repo.get_by_id`
    → `WHERE id = ? AND user_id = ?` → ORM object or `404` → serialised → `HTTP 200`
    """
    return await job_description_service.get(db, jd_id, current_user.id)


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_description(
    jd_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    **Delete a Job Description by ID.**

    Also cascades to any associated `ResumeMatch` records via the
    `ON DELETE CASCADE` foreign key constraint — no orphans are left.
    Returns `404` if the record does not exist or belongs to another user.

    **Request flow:**
    `Client` → JWT validated → `JobDescriptionService.delete` → `job_description_repo.delete`
    → `DELETE WHERE id = ? AND user_id = ?` → `HTTP 204` (or `404` if not found)
    """
    await job_description_service.delete(db, jd_id, current_user.id)
