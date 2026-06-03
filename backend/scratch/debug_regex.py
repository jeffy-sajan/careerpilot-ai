import asyncio
import sys
import logging
from sqlalchemy import select
from app.database.session import async_session_factory
from app.models.resume import Resume

logging.basicConfig(level=logging.INFO)

async def main():
    async with async_session_factory() as session:
        result = await session.execute(select(Resume).where(Resume.raw_text.isnot(None)).order_by(Resume.created_at.desc()))
        resume = result.scalars().first()
        if not resume:
            print("No resume found with raw_text")
            return
        
        print(f"Resume {resume.id} raw text snippet (first 1000 chars):\n")
        print(resume.raw_text[:1000])
        print("\n\nRegex check for email:")
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, resume.raw_text)
        print("Standard Regex Match:", match)
        
        loose_pattern = r'\S+@\S+'
        match_loose = re.search(loose_pattern, resume.raw_text)
        print("Loose Regex Match:", match_loose)
        
        print("Does it contain '@'?", '@' in resume.raw_text)

if __name__ == "__main__":
    asyncio.run(main())
