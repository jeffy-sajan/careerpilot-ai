import asyncio
import sys
import logging
from sqlalchemy import select
from app.database.session import async_session_factory
from app.services.ats_service import ATSService
from app.models.resume import Resume

logging.basicConfig(level=logging.INFO)

async def main():
    service = ATSService()
    async with async_session_factory() as session:
        try:
            result = await session.execute(select(Resume).where(Resume.raw_text.isnot(None)))
            resume = result.scalars().first()
            if not resume:
                print("No resume found with raw_text")
                return
            
            print(f"Testing ATSService with resume {resume.id}...")
            # We bypass analyze_resume wrapper to just test generate_analysis
            analysis = await service.generate_analysis(resume.raw_text)
            print("Success! Score:", analysis.get("ats_score"))
        except Exception as e:
            print("ERROR CAUGHT:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
