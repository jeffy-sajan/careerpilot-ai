import re
import uuid

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.services.resume_classifier_service import resume_classifier
from app.services.resume_section_extractor import resume_section_extractor
from app.services.section_quality_scorer import SKILL_CATEGORIES


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
        Combines contact/formatting checks (40 pts) with section-quality
        evaluation (60 pts) via SectionQualityScorer.
        """
        from app.services.section_quality_scorer import section_quality_scorer
        from app.services.ats_feedback_generator import ats_feedback_generator

        formatting_score = 40  # max 40 pts for contact + formatting
        formatting_details = {}

        # Clean text of common PDF extraction artifacts
        clean_text = text.replace("\u200b", "").replace("\xa0", " ")
        text_lower = clean_text.lower()

        # ── Contact & Formatting Checks (max 40) ───────────────────────────

        # 1. Email (5 pts)
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        formatting_details["has_email"] = bool(re.search(email_pattern, clean_text))
        if not formatting_details["has_email"]:
            formatting_score -= 5

        # 2. Phone (5 pts)
        phone_pattern = r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        formatting_details["has_phone"] = bool(re.search(phone_pattern, clean_text))
        if not formatting_details["has_phone"]:
            formatting_score -= 5

        # 3. LinkedIn (5 pts)
        formatting_details["has_linkedin"] = "linkedin.com" in text_lower
        if not formatting_details["has_linkedin"]:
            formatting_score -= 5

        # 4. Word Count (5 pts)
        word_count = len(clean_text.split())
        formatting_details["word_count"] = word_count
        if word_count < 150:
            formatting_score -= 5
        elif word_count > 1000:
            formatting_score -= 3

        # 5. Bullet Points (5 pts)
        formatting_details["has_bullets"] = any(char in clean_text for char in ["•", "-", "*"])
        if not formatting_details["has_bullets"]:
            formatting_score -= 5

        # 6. Summary / Objective (5 pts)
        summary_keywords = [r"\bsummary\b", r"\bobjective\b", r"\bprofile\b", r"\babout me\b"]
        formatting_details["has_summary"] = any(re.search(kw, text_lower) for kw in summary_keywords)
        if not formatting_details["has_summary"]:
            formatting_score -= 5

        # 7. Consistent formatting (5 pts) — dates pattern
        date_pattern = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{4}\b|\b\d{4}\s*[-–—]\s*(?:\d{4}|present|current)\b"
        date_matches = re.findall(date_pattern, clean_text, re.IGNORECASE)
        formatting_details["has_consistent_dates"] = len(date_matches) >= 2
        if not formatting_details["has_consistent_dates"]:
            formatting_score -= 3

        # 8. Professional links — GitHub, portfolio (5 pts)
        formatting_details["has_portfolio_links"] = any(link in text_lower for link in ["github.com", "portfolio", "gitlab.com"])
        if not formatting_details["has_portfolio_links"]:
            formatting_score -= 2

        formatting_score = max(0, formatting_score)

        # ── Section Quality Evaluation (max 60) ────────────────────────────

        structured = resume_section_extractor.extract(text)
        quality = section_quality_scorer.evaluate(structured)
        quality_dict = quality.to_dict()

        # ── Feedback Generation ────────────────────────────────────────────
        feedback = ats_feedback_generator.generate(
            formatting_details=formatting_details,
            quality_details=quality_dict["breakdown"],
        )

        strengths = feedback["strengths"]
        weaknesses = feedback["weaknesses"]
        recommendations = feedback["recommendations"]

        # ── Final Score ────────────────────────────────────────────────────
        total_score = formatting_score + quality.total_score
        total_score = max(0, min(100, total_score))

        # Build keyword analysis with detected skills
        keyword_analysis: dict[str, str] = {}
        for skill in structured.get("skills", []):
            # Split comma-separated skills
            for s in re.split(r"[,|;]", skill):
                s = s.strip()
                if s:
                    category = self._categorize_skill(s)
                    keyword_analysis[s] = category

        # Also detect skills mentioned in experience
        exp_text_lower = " ".join(structured.get("experience", [])).lower()
        for cat_name, cat_skills in SKILL_CATEGORIES.items():
            for sk in cat_skills:
                if sk not in keyword_analysis:
                    # Use negative lookbehinds/lookaheads for word characters 
                    # to prevent partial matches like "r" in "experience".
                    # We use (?<!\w) instead of \b to properly handle skills ending in symbols like "c++"
                    pattern = r'(?<!\w)' + re.escape(sk.lower()) + r'(?!\w)'
                    if re.search(pattern, exp_text_lower):
                        keyword_analysis[sk] = f"Hard skill ({cat_name})"

        return {
            "ats_score": total_score,
            "formatting_score": formatting_score,
            "section_quality": quality.to_dict(),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "keyword_analysis": keyword_analysis,
        }

    @staticmethod
    def _categorize_skill(skill: str) -> str:
        """Categorize a single skill string."""
        from app.services.section_quality_scorer import SKILL_CATEGORIES
        skill_lower = skill.lower().strip()
        for cat_name, cat_skills in SKILL_CATEGORIES.items():
            if skill_lower in cat_skills:
                return f"Hard skill ({cat_name})"
        # Check for soft skills
        soft_skills = {
            "leadership", "communication", "teamwork", "problem-solving",
            "collaboration", "time management", "adaptability", "creativity",
            "critical thinking", "attention to detail", "work ethic",
        }
        if skill_lower in soft_skills:
            return "Soft skill"
        return "Skill"

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
            # For development/testing, we want to re-analyze to use the latest engine logic
            await session.delete(existing_analysis)
            await session.commit()

        # ── Resume Validation Layer ──────────────────────────────────────────
        classification = resume_classifier.classify(resume.raw_text)

        if not classification.is_resume:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "The uploaded document does not appear to be a resume.",
                    "is_resume": False,
                    "confidence": classification.confidence,
                    "detected_sections": classification.detected_sections,
                    "missing_sections": classification.missing_sections,
                },
            )
        # ────────────────────────────────────────────────────────────────────

        # Generate the analysis
        analysis_data = await self.generate_analysis(resume.raw_text)

        # Apply confidence penalty for borderline documents
        if classification.confidence < 70:
            penalty_factor = classification.confidence / 100.0
            analysis_data["ats_score"] = int(analysis_data["ats_score"] * penalty_factor)
            
            # Insert this specific warning at the top of the weaknesses list
            penalty_msg = f"ATS match score was penalized because the document confidence is low ({classification.confidence}%)."
            if penalty_msg not in analysis_data["weaknesses"]:
                analysis_data["weaknesses"].insert(0, penalty_msg)

        # Create and save new analysis
        new_analysis = ResumeAnalysis(
            resume_id=resume.id,
            ats_score=analysis_data["ats_score"],
            strengths=analysis_data["strengths"],
            weaknesses=analysis_data["weaknesses"],
            recommendations=analysis_data["recommendations"],
            keyword_analysis={
                **analysis_data["keyword_analysis"],
                "resume_validation": {
                    "confidence": classification.confidence,
                    "detected_sections": classification.detected_sections,
                    "missing_sections": classification.missing_sections,
                    **(  # include warning if in the 40-69 grey zone
                        {"warning": classification.warning}
                        if classification.warning
                        else {}
                    ),
                },
                "section_quality": analysis_data["section_quality"],
                "formatting_score": analysis_data["formatting_score"],
            },
        )
        session.add(new_analysis)

        # Extract structured sections (already computed inside _analyze_text,
        # but we call again here for storage — it's cheap and deterministic)
        structured_data = resume_section_extractor.extract(resume.raw_text)
        
        # Merge with existing parsed_data or create new
        existing_data = resume.parsed_data or {}
        resume.parsed_data = {
            **existing_data,
            "ats_analyzed": True,
            "structured_sections": structured_data
        }

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
