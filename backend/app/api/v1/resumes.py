"""
Resume API Routes.
"""

import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.database.session import get_async_session
from app.models.user import User
from app.schemas.resume import (
    ResumeAnalysisResponse,
    ResumeListResponse,
    ResumeMatchResponse,
    ResumeResponse,
    ResumeUploadResponse,
)
from app.services.ats_service import ats_service
from app.services.match_service import match_service
from app.services.resume_service import ResumeService

router = APIRouter()


# Dependency to inject the service layer
def get_resume_service() -> ResumeService:
    from app.core.config import settings
    
    if settings.STORAGE_PROVIDER == "supabase":
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set when STORAGE_PROVIDER is 'supabase'")
        from app.core.storage import SupabaseStorageProvider
        storage = SupabaseStorageProvider(
            url=settings.SUPABASE_URL,
            key=settings.SUPABASE_SERVICE_KEY,
            bucket=settings.SUPABASE_BUCKET
        )
    else:
        from app.core.storage import LocalStorageProvider
        storage = LocalStorageProvider(base_dir="uploads")
        
    return ResumeService(storage_provider=storage)


@router.post("/", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Uploads a new resume (PDF or DOCX).
    Enforces maximum file size and strictly validates MIME types.
    """
    resume = await resume_service.upload_resume(db, current_user.id, file, background_tasks)
    return resume


@router.get("/", response_model=List[ResumeListResponse])
async def list_resumes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Lists all resumes uploaded by the authenticated user.
    Results are paginated and sorted by upload date (newest first).
    """
    return await resume_service.list_resumes(db, current_user.id, skip, limit)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Retrieves detailed metadata for a specific resume.
    Ensures that a user can only access their own resumes.
    """
    return await resume_service.get_resume(db, resume_id, current_user.id)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Deletes a resume record and its associated physical file.
    Ensures that a user can only delete their own resumes.
    """
    await resume_service.delete_resume(db, resume_id, current_user.id)


@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisResponse)
@limiter.limit("10/hour")
async def analyze_resume(
    request: Request,
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Triggers the ATS analysis for a specific resume.
    """
    return await ats_service.analyze_resume(db, resume_id, current_user.id)


@router.get("/{resume_id}/analysis", response_model=ResumeAnalysisResponse)
async def get_resume_analysis(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches the existing ATS analysis for a resume.
    """
    return await ats_service.get_analysis(db, resume_id, current_user.id)


@router.post("/{resume_id}/match/{job_id}", response_model=ResumeMatchResponse)
async def generate_resume_match(
    resume_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a match score and missing skills analysis between a resume and a job description.
    """
    return await match_service.generate_match(db, resume_id, job_id, current_user.id)


@router.get("/{resume_id}/match/{job_id}", response_model=ResumeMatchResponse)
async def get_resume_match(
    resume_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches an existing match analysis.
    """
    return await match_service.get_match(db, resume_id, job_id, current_user.id)
