import calendar
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_async_session
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.schemas.job_application import (
    ApplicationMetricsResponse,
    DashboardInsightResponse,
    JobApplicationCreate,
    JobApplicationListResponse,
    JobApplicationResponse,
    JobApplicationUpdate,
)
from app.services.job_application_service import job_application_service

router = APIRouter()


@router.post("", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED, tags=["Job Applications"])
async def create_application(
    body: JobApplicationCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new tracked job application."""
    return await job_application_service.create_application(
        db, user_id=current_user.id, data=body.model_dump(exclude_unset=True)
    )


@router.get("/metrics", response_model=ApplicationMetricsResponse, tags=["Job Applications"])
async def get_application_metrics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve funnel and pipeline metrics for the user's job applications."""
    applications = await job_application_service.get_user_applications(db, current_user.id)

    total = len(applications)
    if total == 0:
        return ApplicationMetricsResponse(
            total_applications=0,
            active_applications=0,
            total_interviews=0,
            total_offers=0,
            interview_rate=0.0,
            offer_rate=0.0,
        )

    # Active applications
    active = sum(
        1
        for app in applications
        if app.status in {ApplicationStatus.APPLIED, ApplicationStatus.ASSESSMENT, ApplicationStatus.INTERVIEW}
    )

    applied_count = sum(1 for app in applications if app.status != ApplicationStatus.SAVED)

    def reached_interview(app):
        if app.status in {ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER}:
            return True
        return any(h.new_status == ApplicationStatus.INTERVIEW.value for h in app.status_history)

    def reached_offer(app):
        if app.status == ApplicationStatus.OFFER:
            return True
        return any(h.new_status == ApplicationStatus.OFFER.value for h in app.status_history)

    interviews = sum(1 for app in applications if reached_interview(app))
    offers = sum(1 for app in applications if reached_offer(app))

    interview_rate = (interviews / applied_count * 100) if applied_count > 0 else 0.0
    offer_rate = (offers / applied_count * 100) if applied_count > 0 else 0.0

    today = datetime.now(timezone.utc)

    # 1. Monthly Trend
    monthly_trend = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        month_name = calendar.month_abbr[m]
        count = sum(1 for app in applications if app.application_date.year == y and app.application_date.month == m)
        monthly_trend.append({"m": month_name, "v": count})

    # Calculate MoM growth rate
    mom_growth_rate = 0.0
    if len(monthly_trend) >= 2:
        v_curr = monthly_trend[-1]["v"]
        v_prev = monthly_trend[-2]["v"]
        if v_prev > 0:
            mom_growth_rate = round(((v_curr - v_prev) / v_prev) * 100, 1)
        elif v_prev == 0 and v_curr > 0:
            mom_growth_rate = 100.0

    # 2. Role Response Rates
    role_families = {"Product": 0, "Design": 0, "Eng": 0, "Strategy": 0, "DX": 0}
    role_applied = {"Product": 0, "Design": 0, "Eng": 0, "Strategy": 0, "DX": 0}

    def get_role_family(title: str) -> str:
        t = title.lower()
        if "product" in t or "manager" in t:
            return "Product"
        if "design" in t or "ux" in t or "ui" in t:
            return "Design"
        if "engineer" in t or "developer" in t or "software" in t:
            return "Eng"
        if "dx" in t or "developer experience" in t or "devrel" in t:
            return "DX"
        return "Strategy"

    for app in applications:
        if app.status != ApplicationStatus.SAVED:
            fam = get_role_family(app.job_title)
            role_applied[fam] += 1
            if reached_interview(app):
                role_families[fam] += 1

    role_response_rates = []
    for k in role_families.keys():
        rate = int((role_families[k] / role_applied[k] * 100)) if role_applied[k] > 0 else 0
        role_response_rates.append({"k": k, "v": rate})

    # 3. Upcoming Interviews
    upcoming = [app for app in applications if app.next_interview_date and app.next_interview_date > today]
    upcoming.sort(key=lambda x: x.next_interview_date)
    upcoming_interviews = []
    for app in upcoming[:5]:
        d = app.next_interview_date.strftime("%a %d")
        t = app.company_name
        time_str = app.next_interview_date.strftime("%H:%M")
        upcoming_interviews.append({"d": d, "t": t, "time": time_str})

    # 4. Recent Activity
    activities = []
    for app in applications:
        activities.append(
            {
                "timestamp": app.created_at,
                "icon": "PlusCircle",
                "title": f"Applied to {app.company_name} — {app.job_title}",
                "time": "",
                "tag": "Pipeline",
            }
        )
        for history in app.status_history:
            activities.append(
                {
                    "timestamp": history.changed_at,
                    "icon": (
                        "Send"
                        if history.new_status == ApplicationStatus.INTERVIEW.value
                        else "Trophy"
                        if history.new_status == ApplicationStatus.OFFER.value
                        else "FileText"
                    ),
                    "title": f"Application updated · {app.company_name} · moved to {history.new_status.title()}",
                    "time": "",
                    "tag": "Pipeline",
                }
            )

    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activity = []

    def time_ago(dt: datetime) -> str:
        delta = today - dt
        if delta.days > 0:
            if delta.days == 1:
                return "Yesterday"
            return f"{delta.days} days ago"
        elif delta.seconds >= 3600:
            h = delta.seconds // 3600
            return f"{h} hr ago"
        elif delta.seconds >= 60:
            m = delta.seconds // 60
            return f"{m} min ago"
        return "Just now"

    for act in activities[:5]:
        recent_activity.append(
            {"icon": act["icon"], "title": act["title"], "time": time_ago(act["timestamp"]), "tag": act["tag"]}
        )

    return ApplicationMetricsResponse(
        total_applications=total,
        active_applications=active,
        total_interviews=interviews,
        total_offers=offers,
        interview_rate=round(interview_rate, 1),
        offer_rate=round(offer_rate, 1),
        mom_growth_rate=mom_growth_rate,
        monthly_trend=monthly_trend,
        role_response_rates=role_response_rates,
        upcoming_interviews=upcoming_interviews,
        recent_activity=recent_activity,
    )


@router.get("/insights", response_model=DashboardInsightResponse, tags=["Job Applications"])
async def get_application_insights(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Generate AI insights based on the user's application metrics."""
    metrics = await get_application_metrics(db=db, current_user=current_user)

    from app.services.optimization_service import optimization_generator_service

    insight = await optimization_generator_service.generate_dashboard_insight(metrics.model_dump())

    return DashboardInsightResponse(**insight)


@router.get("", response_model=JobApplicationListResponse, tags=["Job Applications"])
async def list_applications(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all job applications for the current user."""
    applications = await job_application_service.get_user_applications(db, current_user.id)
    return JobApplicationListResponse(applications=list(applications))


@router.get("/{application_id}", response_model=JobApplicationResponse, tags=["Job Applications"])
async def get_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a specific job application."""
    return await job_application_service.get_application(db, application_id, current_user.id)


@router.patch("/{application_id}", response_model=JobApplicationResponse, tags=["Job Applications"])
async def update_application(
    application_id: uuid.UUID,
    body: JobApplicationUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Update a specific job application."""
    return await job_application_service.update_application(
        db, application_id, body.model_dump(exclude_unset=True), current_user.id
    )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Job Applications"])
async def delete_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a job application."""
    await job_application_service.delete_application(db, application_id, current_user.id)
