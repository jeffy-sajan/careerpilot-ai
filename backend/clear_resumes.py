import asyncio
from app.database.session import async_session_factory
from sqlalchemy import delete
from app.models.resume import Resume

async def main():
    async with async_session_factory() as session:
        await session.execute(delete(Resume))
        await session.commit()
        print('Resumes deleted.')

if __name__ == '__main__':
    asyncio.run(main())
