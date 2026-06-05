import re
import uuid

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis


class KeywordItem(BaseModel):
    keyword: str = Field(description="The detected keyword or skill")
    category: str = Field(description="The category of the keyword (e.g., Hard skill, Soft skill, Methodology)")


class GeminiATSAnalysisSchema(BaseModel):
    ats_score: float = Field(description="ATS score from 0 to 100")
    strengths: list[str] = Field(description="List of strong points in the resume")
    weaknesses: list[str] = Field(description="List of weak points or missing sections")
    recommendations: list[str] = Field(description="Actionable recommendations to improve the resume")
    keyword_analysis: list[KeywordItem] = Field(description="List of detected keywords and their categories")


class ATSService:
    def __init__(self):
        # We no longer rely on Gemini for V1, we use a deterministic rule-based engine.
        pass

    def _analyze_text(self, text: str) -> dict:
        """
        Rule-based ATS analysis engine.
        Scores based on heuristics and structural checks.
        """
        score = 100
        strengths = []
        weaknesses = []
        recommendations = []

        # Clean text of common PDF extraction artifacts (like zero-width spaces)
        clean_text = text.replace("\u200b", "").replace("\xa0", " ")
        text_lower = clean_text.lower()

        # 1. Check Email
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        if re.search(email_pattern, clean_text):
            strengths.append("Contact information (email) is present.")
        else:
            score -= 10
            weaknesses.append("Missing email address.")
            recommendations.append("Add a professional email address for contact.")

        # 2. Check Phone
        phone_pattern = r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        if re.search(phone_pattern, clean_text):
            strengths.append("Contact information (phone number) is present.")
        else:
            score -= 10
            weaknesses.append("Missing phone number.")
            recommendations.append("Add a phone number so recruiters can reach you easily.")

        # 3. Check LinkedIn
        if "linkedin.com" in text_lower:
            strengths.append("Professional profile (LinkedIn) included.")
        else:
            score -= 5
            weaknesses.append("Missing LinkedIn profile link.")
            recommendations.append("Include a link to your LinkedIn profile to provide more professional context.")

        # 4. Skills Section
        if "skills" in text_lower or "technologies" in text_lower:
            strengths.append("Dedicated Skills section detected.")
        else:
            score -= 15
            weaknesses.append("Skills section not clearly defined.")
            recommendations.append("Add a distinct 'Skills' section listing your technical and soft skills.")

        # 5. Education Section
        if "education" in text_lower or "university" in text_lower or "degree" in text_lower:
            strengths.append("Education section is clearly defined.")
        else:
            score -= 10
            weaknesses.append("Education details missing or unclear.")
            recommendations.append("Include your highest degree and institution name.")

        # 6. Experience Section
        if "experience" in text_lower or "employment" in text_lower or "work history" in text_lower:
            strengths.append("Professional experience section detected.")
        else:
            score -= 15
            weaknesses.append("Work experience section missing.")
            recommendations.append("Add a 'Work Experience' section detailing your past roles.")

        # 7. Quantifiable Metrics (Numbers and Percentages)
        # Look for digits, percentages, or money symbols which often indicate quantifiable achievements
        metrics_pattern = r"(\d{2,}%|\$\d+|\d+x|\b\d{2,}\b)"
        if len(re.findall(metrics_pattern, clean_text)) > 3:
            strengths.append("Excellent use of quantifiable metrics (numbers/percentages) to show impact.")
        else:
            score -= 10
            weaknesses.append("Lack of quantifiable achievements.")
            recommendations.append(
                "Use numbers, percentages, or dollar amounts to quantify your impact (e.g., 'Increased sales by 20%')."
            )

        # 8. Word Count
        word_count = len(clean_text.split())
        if word_count < 150:
            score -= 10
            weaknesses.append("Resume is too short (under 150 words).")
            recommendations.append("Expand on your experience with more detailed descriptions.")
        elif word_count > 1000:
            score -= 5
            weaknesses.append("Resume might be too long (over 1000 words).")
            recommendations.append("Consider condensing your resume to highlight the most relevant points.")

        # 9. Bullet Points
        if "•" in clean_text or "-" in clean_text or "*" in clean_text:
            strengths.append("Good use of bullet points for readability.")
        else:
            score -= 10
            weaknesses.append("Lack of bullet points makes it hard to scan.")
            recommendations.append("Use bullet points rather than long paragraphs for experience descriptions.")

        # 10. Action Verbs
        action_verbs = [
            "managed",
            "developed",
            "led",
            "created",
            "designed",
            "implemented",
            "increased",
            "reduced",
            "optimized",
            "streamlined",
            "spearheaded",
        ]
        found_verbs = [v for v in action_verbs if v in text_lower]
        if len(found_verbs) >= 3:
            strengths.append(f"Strong action verbs used (e.g., {', '.join(found_verbs[:3])}).")
        else:
            score -= 5
            weaknesses.append("Experience descriptions lack strong action verbs.")
            recommendations.append(
                "Start your bullet points with strong action verbs (e.g., Developed, Managed, Optimized)."
            )

        # Ensure score is within bounds
        score = max(0, min(100, score))

        return {
            "ats_score": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "keyword_analysis": {"Rule-Based": "Engine active", "ATS Check": "Heuristics"},
        }

    async def generate_analysis(self, raw_text: str) -> dict:
        """
        Wraps the rule-based analyzer.
        """
        try:
            return self._analyze_text(raw_text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate ATS analysis: {str(e)}")

    async def analyze_resume(self, session: AsyncSession, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeAnalysis:
        """
        Analyzes a resume and saves the results to the database.
        """
        result = await session.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
        resume = result.scalars().first()

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        if not resume.raw_text:
            raise HTTPException(status_code=400, detail="Resume text not yet parsed or is empty.")

        # Check if analysis already exists
        result = await session.execute(select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id))
        existing_analysis = result.scalars().first()

        if existing_analysis:
            # We overwrite or return existing, for V1 we can delete existing and create new, or just return existing
            # Returning existing so we don't spam. To force re-analysis, one would delete the old analysis.
            return existing_analysis

        # Generate the analysis
        analysis_data = await self.generate_analysis(resume.raw_text)

        # Create and save new analysis
        new_analysis = ResumeAnalysis(
            resume_id=resume.id,
            ats_score=analysis_data["ats_score"],
            strengths=analysis_data["strengths"],
            weaknesses=analysis_data["weaknesses"],
            recommendations=analysis_data["recommendations"],
            keyword_analysis=analysis_data["keyword_analysis"],
        )
        session.add(new_analysis)

        resume.parsed_data = {"ats_analyzed": True}

        await session.commit()
        await session.refresh(new_analysis)
        return new_analysis

    async def get_analysis(self, session: AsyncSession, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeAnalysis:
        """
        Fetches an existing analysis.
        """
        result = await session.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
        if not result.scalars().first():
            raise HTTPException(status_code=404, detail="Resume not found")

        result = await session.execute(select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id))
        analysis = result.scalars().first()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found for this resume.")

        return analysis


ats_service = ATSService()
