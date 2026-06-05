import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_application import JobApplication
from app.repositories.job_application_repo import job_application_repo


class JobApplicationService:
    async def create_application(self, db: AsyncSession, user_id: uuid.UUID, data: dict) -> JobApplication:
        return await job_application_repo.create(db, user_id=user_id, **data)

    async def get_application(self, db: AsyncSession, application_id: uuid.UUID, user_id: uuid.UUID) -> JobApplication:
        application = await job_application_repo.get_by_id(db, application_id, user_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found",
            )
        return application

    async def get_user_applications(self, db: AsyncSession, user_id: uuid.UUID) -> Sequence[JobApplication]:
        return await job_application_repo.get_for_user(db, user_id)

    async def update_application(
        self, db: AsyncSession, application_id: uuid.UUID, update_data: dict, user_id: uuid.UUID
    ) -> JobApplication:
        application = await self.get_application(db, application_id, user_id)
        return await job_application_repo.update(db, application, update_data, user_id)

    async def delete_application(self, db: AsyncSession, application_id: uuid.UUID, user_id: uuid.UUID) -> None:
        application = await self.get_application(db, application_id, user_id)
        await job_application_repo.delete(db, application)


job_application_service = JobApplicationService()
