from fastapi import APIRouter

from app.api.v1 import auth, google_auth, health, jobs, optimizations, resumes

api_router = APIRouter()

# Mount API routers
api_router.include_router(health.router, prefix="/health", tags=["Health Check"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(google_auth.router, prefix="/auth/google", tags=["Google OAuth"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resume Management"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Job Descriptions"])
api_router.include_router(optimizations.router)
