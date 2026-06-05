"""
Health check endpoint.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_async_session

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return application health status."""
    return HealthResponse(status="healthy")


@router.get("/db", response_model=HealthResponse)
async def db_health_check(db=Depends(get_async_session)) -> HealthResponse:
    """Verify database connectivity."""
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return HealthResponse(status="healthy")
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database connection failed")
