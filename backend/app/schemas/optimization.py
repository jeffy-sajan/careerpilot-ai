from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import OptimizationStatus, OptimizationType


class OptimizationResponse(BaseModel):
    """
    Schema for a single optimization suggestion.
    Used to return the suggested rewrite and its reasoning to the client.
    """
    id: UUID
    run_id: UUID
    optimization_type: OptimizationType
    section: str
    original_text: str
    suggested_text: str
    reasoning: str
    status: OptimizationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OptimizationRunResponse(BaseModel):
    """
    Schema representing a single session/run of optimization generation.
    Groups multiple optimization suggestions together.
    """
    id: UUID
    resume_id: UUID
    job_description_id: UUID | None
    model_name: str
    prompt_version: str
    created_at: datetime
    updated_at: datetime
    suggestions: list[OptimizationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OptimizationListResponse(BaseModel):
    """
    Schema for listing multiple optimization suggestions.
    Typically used when fetching all pending/accepted suggestions for a specific resume.
    """
    optimizations: list[OptimizationResponse]
    total_count: int


class UpdateOptimizationStatusRequest(BaseModel):
    """
    Schema for updating the status of an optimization.
    Used by the client to accept or reject an AI suggestion.
    """
    status: OptimizationStatus


class PromptResponse(BaseModel):
    """
    Returns the assembled AI prompt and metadata so the frontend
    can call the Gemini API directly with the user's own API key.
    """
    prompt: str
    model_name: str
    response_schema: dict


class SaveOptimizationsRequest(BaseModel):
    """
    Accepts raw suggestion dicts from a client-side Gemini call
    and persists them as an OptimizationRun in the database.
    """
    model_name: str = "gemini-2.5-flash"
    prompt_version: str = "v1.0-byok"
    suggestions: list[dict]
