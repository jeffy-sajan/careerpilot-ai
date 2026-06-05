"""
Job Description Schemas.

Request and Response Pydantic models for the /api/v1/jobs endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class JobDescriptionCreate(BaseModel):
    """
    Payload to create a new Job Description.
    The user pastes the full job posting text, gives it a title,
    and optionally names the company.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Job title or role name (e.g. 'Senior Backend Engineer')",
    )
    company: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Company name (optional)",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Full job description text pasted from the job posting",
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class JobDescriptionResponse(BaseModel):
    """
    Full response for a single Job Description.
    Returned on POST (create) and GET /{id} (detail).
    """

    id: UUID
    user_id: UUID
    title: str
    company: Optional[str]
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionListResponse(BaseModel):
    """
    Lightweight response used for the list endpoint (GET /jobs).
    Excludes the full description text to keep list payloads small.
    """

    id: UUID
    user_id: UUID
    title: str
    company: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
