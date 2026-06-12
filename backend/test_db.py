import asyncio
import json
from sqlalchemy import select
from app.database.session import async_session_factory
from app.models.resume import Resume
from app.services.resume_section_extractor import resume_section_extractor
from app.services.section_quality_scorer import section_quality_scorer
from app.services.ats_feedback_generator import ats_feedback_generator

async def main():
    async with async_session_factory() as session:
        result = await session.execute(select(Resume).order_by(Resume.created_at.desc()).limit(1))
        resume = result.scalars().first()
        
        extracted = resume_section_extractor.extract(resume.raw_text)
        quality = section_quality_scorer.evaluate(extracted)
        quality_dict = quality.to_dict()
        
        print("=== QUALITY SCORES ===")
        print(json.dumps(quality_dict, indent=2))
        
        print("\n=== FEEDBACK GENERATOR ===")
        feedback = ats_feedback_generator.generate(
            formatting_details={},
            quality_details=quality_dict["breakdown"],
        )
        print(json.dumps(feedback, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
