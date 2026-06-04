import json
import logging
from typing import Any

import httpx
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured Output Schema (used by both backend and frontend Gemini calls)
# ---------------------------------------------------------------------------

class LLMSuggestion(BaseModel):
    section: str = Field(description="The section of the resume (e.g., 'Summary', 'Experience', 'Skills').")
    original_text: str = Field(description="The exact original text from the resume being improved.")
    suggested_text: str = Field(description="The rewritten text incorporating the improvements.")
    reasoning: str = Field(description="Why this change is suggested and what impact it has.")
    optimization_type: str = Field(
        description=(
            "Type of optimization: KEYWORD, BULLET_REWRITE, SKILL_ADDITION, "
            "SUMMARY_IMPROVEMENT, or ATS_FIX."
        )
    )


class LLMOptimizationResult(BaseModel):
    suggestions: list[LLMSuggestion]


# ---------------------------------------------------------------------------
# JSON Schema for Gemini Structured Output (exported for the /prompt endpoint)
# ---------------------------------------------------------------------------

GEMINI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string"},
                    "original_text": {"type": "string"},
                    "suggested_text": {"type": "string"},
                    "reasoning": {"type": "string"},
                    "optimization_type": {
                        "type": "string",
                        "enum": ["KEYWORD", "BULLET_REWRITE", "SKILL_ADDITION", "SUMMARY_IMPROVEMENT", "ATS_FIX"]
                    }
                },
                "required": ["section", "original_text", "suggested_text", "reasoning", "optimization_type"]
            }
        }
    },
    "required": ["suggestions"]
}


class OptimizationGeneratorService:
    def __init__(self):
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self.prompt_version = "v1.0"
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def build_prompt(
        self,
        resume_text: str,
        ats_analysis: dict[str, Any] | None,
        jd_match_results: dict[str, Any] | None
    ) -> str:
        """
        Assembles the optimization prompt from resume text and analysis data.
        This method is deterministic and has no side effects — it can be safely
        called by the /prompt endpoint without triggering any API calls.
        """
        # Build context
        context_parts = []
        if ats_analysis:
            suggestions = ats_analysis.get("suggestions", [])
            context_parts.append(f"ATS Analysis Suggestions (General Resume Health): {suggestions}")

        if jd_match_results:
            missing_skills = jd_match_results.get("missing_skills", [])
            missing_keywords = jd_match_results.get("missing_keywords", [])
            context_parts.append(
                f"Job Description Match Gaps (Target Job Specific):\n"
                f"- Missing Skills: {missing_skills}\n"
                f"- Missing Keywords: {missing_keywords}"
            )

        context_str = "\n".join(context_parts)

        prompt = (
            "You are an Expert Technical Recruiter and ATS Optimization Specialist.\n\n"
            "I am providing you with a candidate's resume text, and analysis of gaps "
            "they have either generally (ATS Analysis) or specifically for a target job "
            "(Job Description Match).\n\n"
            f"{context_str}\n\n"
            "Resume Text:\n"
            f"{resume_text}\n\n"
            "Your task is to provide actionable, section-by-section improvements. "
            "Do NOT rewrite the entire resume as a single block.\n"
            "Provide a list of specific suggestions. For each suggestion, "
            "provide the original text, the suggested text, the section it belongs to, "
            "reasoning, and the type of optimization.\n"
            "Make sure the suggested text naturally incorporates missing skills and keywords "
            "where appropriate without lying or hallucinating experiences.\n"
            "Focus heavily on action-oriented language, metrics, and incorporating the "
            "missing skills and keywords provided in the gaps analysis."
        )

        return prompt

    async def _generate_via_openrouter(self, prompt: str) -> list[dict[str, Any]]:
        """
        Fallback generator using OpenRouter.
        """
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API key is not configured.")

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "CareerPilot AI",
            "Content-Type": "application/json"
        }
        
        # We specify JSON output via prompt and system instruction.
        data = {
            "model": "meta-llama/llama-3-70b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You must respond with ONLY valid JSON matching this schema: "
                        + json.dumps(GEMINI_RESPONSE_SCHEMA)
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=data, timeout=30.0)
            
            if resp.status_code != 200:
                raise Exception(f"OpenRouter API failed: {resp.status_code} - {resp.text}")
                
            resp_data = resp.json()
            content = resp_data["choices"][0]["message"]["content"]
            
            try:
                parsed = json.loads(content)
                return parsed.get("suggestions", [])
            except json.JSONDecodeError:
                raise Exception("Failed to parse OpenRouter response as JSON.")

    async def generate_suggestions(
        self,
        resume_text: str,
        ats_analysis: dict[str, Any] | None,
        jd_match_results: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """
        Generates structured optimization suggestions.
        Tier 1: Gemini via platform key
        Tier 2: OpenRouter via platform key
        Tier 3: Propagate 503 to trigger BYOK on frontend
        """
        prompt = self.build_prompt(resume_text, ats_analysis, jd_match_results)

        # Tier 1: Try Gemini
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=LLMOptimizationResult,
                        temperature=0.7,
                    ),
                )
                data = json.loads(response.text)
                return data.get("suggestions", [])
            except Exception as e:
                logger.warning(f"Tier 1 (Gemini) failed: {e}")
                # If it's a quota or 503 error, proceed to fallback.
                # If it's something else (like an auth error for our own key), we should still probably fallback.
        else:
            logger.warning("Tier 1 (Gemini) skipped: No API key configured.")

        # Tier 2: Try OpenRouter
        logger.info("Attempting Tier 2 (OpenRouter) fallback...")
        try:
            return await self._generate_via_openrouter(prompt)
        except Exception as e:
            logger.error(f"Tier 2 (OpenRouter) failed: {e}")
            # If both failed, we raise a 503 to signal the frontend to offer BYOK
            raise Exception("503 Service Unavailable (Both Gemini and OpenRouter failed)")


optimization_generator_service = OptimizationGeneratorService()
