"""
Optimization API Routes.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.database.session import get_async_session
from app.models.user import User
from app.repositories import optimization_repo, resume_match_repo, resume_repo
from app.schemas.optimization import (
    OptimizationListResponse,
    OptimizationResponse,
    OptimizationRunResponse,
    PromptResponse,
    SaveOptimizationsRequest,
    UpdateOptimizationStatusRequest,
)
from app.services.ats_service import ats_service
from app.services.optimization_service import GEMINI_RESPONSE_SCHEMA, optimization_generator_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: fetch ATS + JD context for a resume
# ---------------------------------------------------------------------------

async def _fetch_analysis_context(
    db: AsyncSession,
    resume_id: uuid.UUID,
    user_id: uuid.UUID,
    job_id: uuid.UUID | None,
):
    """
    Shared helper that loads ATS analysis and JD match data for a resume.
    Used by both the platform-key generation endpoint and the BYOK prompt endpoint.
    """
    ats_analysis = None
    jd_match = None

    # Fetch ATS analysis
    try:
        analysis_record = await ats_service.get_analysis(db, resume_id, user_id)
        if analysis_record:
            ats_analysis = {"suggestions": getattr(analysis_record, "missing_formatting", [])}
    except HTTPException:
        pass

    # Fetch JD match if job_id provided
    if job_id:
        match_record = await resume_match_repo.get_match(db, resume_id, job_id)
        if match_record:
            jd_match = {
                "missing_skills": match_record.missing_skills,
                "missing_keywords": match_record.missing_keywords
            }

    return ats_analysis, jd_match


# ---------------------------------------------------------------------------
# POST /resumes/{resume_id}/optimize  — Platform key generation (existing)
# ---------------------------------------------------------------------------

@router.post(
    "/resumes/{resume_id}/optimize",
    response_model=OptimizationRunResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resume Optimizations"]
)
@limiter.limit("5/minute")
async def generate_resume_optimizations(
    request: Request,
    resume_id: uuid.UUID,
    job_id: uuid.UUID | None = Query(None, description="Optional job description ID to optimize against"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Generates new optimization suggestions for a resume using the platform's
    Gemini API key.
    """
    resume = await resume_repo.get_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    ats_analysis, jd_match = await _fetch_analysis_context(db, resume_id, current_user.id, job_id)

    try:
        suggestions_raw = await optimization_generator_service.generate_suggestions(
            resume_text=resume.raw_text,
            ats_analysis=ats_analysis,
            jd_match_results=jd_match
        )
    except Exception as e:
        logger.error(f"Error generating optimizations: {e}", exc_info=True)
        error_msg = str(e)
        if "503" in error_msg or "temporary" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "CareerPilot AI quota is currently exhausted. "
                    "You can try again later or use your own Gemini API key."
                )
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to generate optimizations: {error_msg}"
        )

    run = await optimization_repo.create_many(
        session=db,
        resume_id=resume_id,
        job_id=job_id,
        model_name=optimization_generator_service.model_name,
        prompt_version=optimization_generator_service.prompt_version,
        suggestions=suggestions_raw
    )
    
    return run


# ---------------------------------------------------------------------------
# GET /resumes/{resume_id}/optimize/prompt  — BYOK prompt endpoint (new)
# ---------------------------------------------------------------------------

@router.get(
    "/resumes/{resume_id}/optimize/prompt",
    response_model=PromptResponse,
    tags=["Resume Optimizations"]
)
async def get_optimization_prompt(
    resume_id: uuid.UUID,
    job_id: uuid.UUID | None = Query(None, description="Optional job description ID to optimize against"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the assembled AI prompt and JSON schema so the frontend can call
    the Gemini API directly using the user's own API key.

    The user's API key never touches this server.
    """
    resume = await resume_repo.get_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.raw_text:
        raise HTTPException(status_code=400, detail="Resume text not yet parsed or is empty.")

    ats_analysis, jd_match = await _fetch_analysis_context(db, resume_id, current_user.id, job_id)

    prompt = optimization_generator_service.build_prompt(
        resume_text=resume.raw_text,
        ats_analysis=ats_analysis,
        jd_match_results=jd_match
    )

    return PromptResponse(
        prompt=prompt,
        model_name=optimization_generator_service.model_name,
        response_schema=GEMINI_RESPONSE_SCHEMA,
    )


# ---------------------------------------------------------------------------
# POST /resumes/{resume_id}/optimize/save  — BYOK save endpoint (new)
# ---------------------------------------------------------------------------

@router.post(
    "/resumes/{resume_id}/optimize/save",
    response_model=OptimizationRunResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resume Optimizations"]
)
async def save_byok_optimizations(
    resume_id: uuid.UUID,
    body: SaveOptimizationsRequest,
    job_id: uuid.UUID | None = Query(None, description="Optional job description ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Persists optimization suggestions that were generated client-side
    (via the user's own Gemini API key) into the database.

    The user's API key is never sent to this endpoint.
    """
    resume = await resume_repo.get_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not body.suggestions:
        raise HTTPException(status_code=400, detail="No suggestions provided.")

    run = await optimization_repo.create_many(
        session=db,
        resume_id=resume_id,
        job_id=job_id,
        model_name=body.model_name,
        prompt_version=body.prompt_version,
        suggestions=body.suggestions,
    )

    return run


# ---------------------------------------------------------------------------
# GET /resumes/{resume_id}/optimizations  — List (existing)
# ---------------------------------------------------------------------------

@router.get(
    "/resumes/{resume_id}/optimizations",
    response_model=OptimizationListResponse,
    tags=["Resume Optimizations"]
)
async def list_resume_optimizations(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all optimizations generated for a resume.
    """
    resume = await resume_repo.get_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    optimizations = await optimization_repo.get_for_resume(db, resume_id)
    return OptimizationListResponse(optimizations=list(optimizations), total_count=len(optimizations))


# ---------------------------------------------------------------------------
# PATCH /optimizations/{optimization_id}/status  — Update status (existing)
# ---------------------------------------------------------------------------

@router.patch(
    "/optimizations/{optimization_id}/status",
    response_model=OptimizationResponse,
    tags=["Resume Optimizations"]
)
async def update_optimization_status(
    optimization_id: uuid.UUID,
    request: UpdateOptimizationStatusRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Updates the status (e.g. ACCEPTED, REJECTED) of a specific optimization suggestion.
    """
    opt = await optimization_repo.update_status(
        session=db, 
        optimization_id=optimization_id, 
        status=request.status,
        user_id=current_user.id
    )
    if not opt:
        raise HTTPException(status_code=404, detail="Optimization not found")
    return opt
