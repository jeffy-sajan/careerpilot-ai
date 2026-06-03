import asyncio
from app.database.session import async_session_factory
from sqlalchemy import select
from app.models.resume import Resume

async def main():
    async with async_session_factory() as session:
        result = await session.execute(select(Resume))
        resumes = result.scalars().all()
        for r in resumes:
            print(f'{r.id} - {r.status} - user: {r.user_id}')

if __name__ == '__main__':
    asyncio.run(main())
