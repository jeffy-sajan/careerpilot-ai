"""
Models Package — Re-exports all models for Alembic auto-detection.
"""

from app.models.activity_log import ActivityLog
from app.models.enums import ApplicationPriority, ApplicationSource, ApplicationStatus
from app.models.google_auth_code import GoogleAuthCode
from app.models.job_application import ApplicationStatusHistory, JobApplication
from app.models.job_description import JobDescription
from app.models.optimization import OptimizationRun, ResumeOptimization
from app.models.refresh_token import RefreshToken
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.resume_match import ResumeMatch
from app.models.user import User

__all__ = [
    "ActivityLog",
    "ApplicationPriority",
    "ApplicationSource",
    "ApplicationStatus",
    "ApplicationStatusHistory",
    "GoogleAuthCode",
    "JobApplication",
    "JobDescription",
    "RefreshToken",
    "Resume",
    "ResumeAnalysis",
    "ResumeMatch",
    "OptimizationRun",
    "ResumeOptimization",
    "User",
]
