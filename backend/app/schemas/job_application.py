import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApplicationPriority, ApplicationStatus


class ApplicationStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    old_status: str | None
    new_status: str
    changed_at: datetime
    changed_by: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


class JobApplicationBase(BaseModel):
    resume_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    company_name: str = Field(..., max_length=255)
    job_title: str = Field(..., max_length=255)
    job_url: str | None = Field(default=None, max_length=1000)
    source: str | None = Field(default=None, max_length=255)
    status: ApplicationStatus = ApplicationStatus.SAVED
    priority: ApplicationPriority = ApplicationPriority.MEDIUM
    application_date: datetime
    next_interview_date: datetime | None = None
    notes: str | None = Field(default=None, max_length=5000)


class JobApplicationCreate(JobApplicationBase):
    pass


class JobApplicationUpdate(BaseModel):
    resume_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    company_name: str | None = Field(default=None, max_length=255)
    job_title: str | None = Field(default=None, max_length=255)
    job_url: str | None = Field(default=None, max_length=1000)
    source: str | None = Field(default=None, max_length=255)
    status: ApplicationStatus | None = None
    priority: ApplicationPriority | None = None
    application_date: datetime | None = None
    next_interview_date: datetime | None = None
    notes: str | None = Field(default=None, max_length=5000)


class JobApplicationResponse(JobApplicationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    status_history: list[ApplicationStatusHistoryResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class JobApplicationListResponse(BaseModel):
    applications: list[JobApplicationResponse]


class MonthlyTrend(BaseModel):
    m: str
    v: int


class RecentActivity(BaseModel):
    icon: str
    title: str
    time: str
    tag: str


class RecommendedAction(BaseModel):
    action: str
    impact: str


class DashboardInsightResponse(BaseModel):
    insight_text: str
    recommended_actions: list[RecommendedAction]


class RoleResponseRate(BaseModel):
    k: str
    v: int


class UpcomingInterview(BaseModel):
    d: str
    t: str
    time: str


class ApplicationMetricsResponse(BaseModel):
    total_applications: int
    active_applications: int
    total_interviews: int
    total_offers: int
    interview_rate: float
    offer_rate: float
    mom_growth_rate: float
    monthly_trend: list[MonthlyTrend] = Field(default_factory=list)
    recent_activity: list[RecentActivity] = Field(default_factory=list)
    role_response_rates: list[RoleResponseRate] = Field(default_factory=list)
    upcoming_interviews: list[UpcomingInterview] = Field(default_factory=list)
