from fastapi import APIRouter

from app.api.v1 import health, auth, google_auth

api_router = APIRouter()

# Mount API routers
api_router.include_router(health.router, prefix="/health", tags=["Health Check"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(google_auth.router, prefix="/auth/google", tags=["Google OAuth"])
