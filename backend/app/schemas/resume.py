from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Validation Constants
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


class ResumeBase(BaseModel):
    """Base fields shared across all Resume responses."""

    id: UUID
    user_id: UUID
    original_file_name: str
    content_type: str
    file_size_bytes: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(ResumeBase):
    """Returned immediately after a user uploads a file."""

    message: str = Field(
        default="Resume uploaded successfully and is queued for parsing.", description="Status message for the frontend"
    )


class ResumeResponse(ResumeBase):
    """Detailed response for a single resume."""

    file_url: str
    raw_text: Optional[str] = None
    parsed_data: Optional[dict] = None
    error_message: Optional[str] = None


class ResumeListResponse(ResumeBase):
    """Lightweight schema used for returning a list of resumes (Dashboard view)."""

    file_url: str


class ResumeAnalysisResponse(BaseModel):
    id: UUID
    resume_id: UUID
    ats_score: float
    strengths: list[str] | None
    weaknesses: list[str] | None
    recommendations: list[str] | None
    keyword_analysis: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeMatchResponse(BaseModel):
    id: UUID
    resume_id: UUID
    job_description_id: UUID
    match_score: float
    matched_skills: list[str] | None
    missing_skills: list[str] | None
    missing_keywords: list[str] | None
    suggestions: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
