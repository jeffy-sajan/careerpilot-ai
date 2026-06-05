import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job_application import ApplicationStatusHistory, JobApplication


class JobApplicationRepository:
    async def get_by_id(
        self, session: AsyncSession, application_id: uuid.UUID, user_id: uuid.UUID
    ) -> JobApplication | None:
        stmt = (
            select(JobApplication)
            .where(JobApplication.id == application_id, JobApplication.user_id == user_id)
            .options(selectinload(JobApplication.status_history))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, user_id: uuid.UUID, **kwargs) -> JobApplication:
        # Create the application
        application = JobApplication(user_id=user_id, **kwargs)
        session.add(application)
        await session.flush()

        # Log initial history
        history = ApplicationStatusHistory(
            application_id=application.id,
            old_status=None,
            new_status=application.status.value,
            changed_at=datetime.now(timezone.utc),
            changed_by=user_id,
        )
        session.add(history)
        await session.commit()

        # Return fully loaded application with status_history
        return await self.get_by_id(session, application.id, user_id)

    async def get_for_user(self, session: AsyncSession, user_id: uuid.UUID) -> Sequence[JobApplication]:
        stmt = (
            select(JobApplication)
            .where(JobApplication.user_id == user_id)
            .options(selectinload(JobApplication.status_history))
            .order_by(JobApplication.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(
        self, session: AsyncSession, application: JobApplication, update_data: dict, user_id: uuid.UUID
    ) -> JobApplication:
        old_status = application.status.value

        for field, value in update_data.items():
            setattr(application, field, value)

        # Log history if status changed
        new_status = application.status.value
        if old_status != new_status:
            history = ApplicationStatusHistory(
                application_id=application.id,
                old_status=old_status,
                new_status=new_status,
                changed_at=datetime.now(timezone.utc),
                changed_by=user_id,
            )
            session.add(history)

        await session.commit()

        # Return fully loaded application with status_history
        return await self.get_by_id(session, application.id, user_id)

    async def delete(self, session: AsyncSession, application: JobApplication) -> None:
        await session.delete(application)
        await session.commit()


job_application_repo = JobApplicationRepository()
