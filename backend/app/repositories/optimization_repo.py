"""
Optimization Repository.
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import OptimizationStatus
from app.models.optimization import OptimizationRun, ResumeOptimization
from app.models.resume import Resume


async def create_many(
    session: AsyncSession,
    resume_id: uuid.UUID,
    job_id: Optional[uuid.UUID],
    model_name: str,
    prompt_version: str,
    suggestions: list[dict],
) -> OptimizationRun:
    """
    Creates an OptimizationRun and multiple associated ResumeOptimizations.
    """
    run = OptimizationRun(
        resume_id=resume_id,
        job_description_id=job_id,
        model_name=model_name,
        prompt_version=prompt_version,
    )
    session.add(run)
    await session.flush()  # Get run.id before adding suggestions

    for opt_data in suggestions:
        opt = ResumeOptimization(
            run_id=run.id,
            optimization_type=opt_data["optimization_type"],
            section=opt_data["section"],
            original_text=opt_data["original_text"],
            suggested_text=opt_data["suggested_text"],
            reasoning=opt_data["reasoning"],
            status=OptimizationStatus.PENDING,
        )
        session.add(opt)
    
    await session.commit()
    
    # Reload with selectinload to ensure suggestions relationship is populated
    result = await session.execute(
        select(OptimizationRun)
        .options(selectinload(OptimizationRun.suggestions))
        .where(OptimizationRun.id == run.id)
    )
    return result.scalars().first()


async def get_for_resume(
    session: AsyncSession,
    resume_id: uuid.UUID,
) -> Sequence[ResumeOptimization]:
    """
    Gets all optimization suggestions for a specific resume across all runs.
    """
    result = await session.execute(
        select(ResumeOptimization)
        .join(OptimizationRun, OptimizationRun.id == ResumeOptimization.run_id)
        .where(OptimizationRun.resume_id == resume_id)
        .order_by(ResumeOptimization.created_at.desc())
    )
    return result.scalars().all()


async def update_status(
    session: AsyncSession,
    optimization_id: uuid.UUID,
    status: OptimizationStatus,
    user_id: uuid.UUID,
) -> Optional[ResumeOptimization]:
    """
    Updates the status of a specific optimization suggestion.
    Enforces user ownership.
    """
    result = await session.execute(
        select(ResumeOptimization)
        .join(OptimizationRun, OptimizationRun.id == ResumeOptimization.run_id)
        .join(Resume, Resume.id == OptimizationRun.resume_id)
        .where(
            ResumeOptimization.id == optimization_id,
            Resume.user_id == user_id
        )
    )
    opt = result.scalars().first()
    
    if opt:
        opt.status = status
        await session.commit()
        await session.refresh(opt)
        return opt
    return None
