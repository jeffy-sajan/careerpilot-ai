"""
Match Service.

Implements the V1 Job Description Matching logic.
Calculates a weighted score based on dictionary-matched skills and extracted keywords.
"""
import math
import re
import uuid
from collections import Counter
from typing import Set, Tuple

from fastapi import HTTPException
from nltk.stem import SnowballStemmer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_match import ResumeMatch
from app.repositories import job_description_repo, resume_match_repo, resume_repo

# ---------------------------------------------------------------------------
# V1 Static Dictionaries
# ---------------------------------------------------------------------------

# Common technical and soft skills mapped to their canonical forms
SKILLS_DICT = {
    "python": "Python",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "ruby": "Ruby",
    "go": "Go",
    "rust": "Rust",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "azure": "Azure",
    "git": "Git",
    "ci/cd": "CI/CD",
    "agile": "Agile",
    "scrum": "Scrum",
    "leadership": "Leadership",
    "communication": "Communication",
    "machine learning": "Machine Learning",
    "data analysis": "Data Analysis",
}

# Common words to filter out when extracting general keywords
STOPWORDS = {
    "the", "and", "is", "in", "to", "of", "a", "for", "with", "on", "as", "an",
    "by", "we", "are", "you", "this", "that", "it", "or", "be", "your", "our",
    "will", "have", "at", "from", "can", "all", "not", "but", "what", "how",
    "job", "description", "requirements", "responsibilities", "experience",
    "looking", "seeking", "years", "work", "team", "strong", "good", "excellent",
    "working", "using", "required", "preferred", "plus", "ability", "skills"
}


class MatchService:
    def __init__(self):
        self.stemmer = SnowballStemmer("english")

    def _clean_text(self, text: str) -> str:
        """Lowercases and removes punctuation except for common tech symbols (+, #, .)."""
        text = text.lower()
        # Keep letters, numbers, spaces, and specific symbols used in tech (C++, C#, Node.js)
        text = re.sub(r'[^a-z0-9\s\+\#\.\/]', ' ', text)
        return text

    def _extract_skills(self, text: str) -> Set[str]:
        """Scans text for exact matches of our known skill dictionary."""
        found_skills = set()
        clean_text = self._clean_text(text)
        words = [w.strip('.') for w in clean_text.split()]
        
        # Check single words
        for word in words:
            if word in SKILLS_DICT:
                found_skills.add(SKILLS_DICT[word])
                
        # Check two-word phrases (e.g. "amazon web services", "machine learning")
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if phrase in SKILLS_DICT:
                found_skills.add(SKILLS_DICT[phrase])
                
        # Check three-word phrases
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            if phrase in SKILLS_DICT:
                found_skills.add(SKILLS_DICT[phrase])

        return found_skills

    def _extract_keywords(self, text: str, top_n: int = 15) -> Set[str]:
        """Extracts the most frequent non-stopword tokens as keywords, using stemming."""
        clean_text = self._clean_text(text)
        
        words = []
        for w in clean_text.split():
            w = w.strip('.')
            if len(w) > 2 and w not in STOPWORDS and w not in SKILLS_DICT:
                # Stem the word (e.g., managing -> manag)
                stemmed = self.stemmer.stem(w)
                words.append(stemmed)
        
        counter = Counter(words)
        return {word for word, count in counter.most_common(top_n)}

    def calculate_match(self, resume_text: str, jd_text: str) -> Tuple[float, list, list, list, list]:
        """
        Calculates the match score and extracts matched/missing attributes.
        
        Scoring Formula (0-100):
        - Skills account for 65% of the total score.
        - Keywords account for 35% of the total score.
        - Score = ((Matched_Skills / Total_JD_Skills) * 65) + ((Matched_Keywords / Total_JD_Keywords) * 35)
        
        If the JD has no extractable skills, keywords take 100% of the weight.
        If neither can be extracted, defaults to a baseline text-overlap score or 0.
        """
        # 1. Extract from Job Description (The Target)
        jd_skills = self._extract_skills(jd_text)
        jd_keywords = self._extract_keywords(jd_text)

        # 2. Extract from Resume (The Candidate)
        res_skills = self._extract_skills(resume_text)
        # Extract more from resume to increase chance of finding the JD keywords
        res_keywords = self._extract_keywords(resume_text, top_n=50) 

        # 3. Compute Set Intersections and Differences
        matched_skills = jd_skills.intersection(res_skills)
        missing_skills = jd_skills.difference(res_skills)
        
        matched_keywords = jd_keywords.intersection(res_keywords)
        missing_keywords = jd_keywords.difference(res_keywords)

        # 4. Calculate Weighted Score
        skill_score = 0.0
        keyword_score = 0.0

        if len(jd_skills) > 0:
            skill_score = (len(matched_skills) / len(jd_skills)) * 65.0
        
        if len(jd_keywords) > 0:
            keyword_score = (len(matched_keywords) / len(jd_keywords)) * 35.0

        # Adjust weights if the JD was completely lacking skills (e.g. poor job posting)
        if len(jd_skills) == 0 and len(jd_keywords) > 0:
            keyword_score = (len(matched_keywords) / len(jd_keywords)) * 100.0
        
        total_score = math.floor(skill_score + keyword_score)

        # 5. Generate Actionable Suggestions
        suggestions = []
        if missing_skills:
            # We take the top 3 missing skills to avoid overwhelming the user
            top_missing = list(missing_skills)[:3]
            suggestions.append(
                f"Your resume is missing key technical skills explicitly required by the job: "
                f"{', '.join(top_missing)}. "
                "If you have experience with these, add them to your skills section and bullet points."
            )
        
        if missing_keywords:
            suggestions.append(
                "Consider incorporating more industry terminology from the job description to pass ATS keyword filters."
            )
            
        if total_score > 80:
            suggestions.append("Great match! Your resume aligns very well with this position.")

        return total_score, list(matched_skills), list(missing_skills), list(missing_keywords), suggestions

    async def generate_match(
        self,
        session: AsyncSession,
        resume_id: uuid.UUID,
        job_description_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ResumeMatch:
        """
        Orchestrates the matching process by loading documents, running the algorithm,
        and persisting the results.
        """
        # Ensure ownership of both resources
        resume = await resume_repo.get_by_id(session, resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
            
        if not resume.raw_text:
            raise HTTPException(
                status_code=400, 
                detail="Resume text has not been parsed yet. Please wait for processing to complete."
            )

        jd = await job_description_repo.get_by_id(session, job_description_id, user_id)
        if not jd:
            raise HTTPException(status_code=404, detail="Job description not found")

        # Edge Case Validation: Check if there's enough text
        if len(resume.raw_text.split()) < 30:
            raise HTTPException(status_code=400, detail="Insufficient text in resume to perform a reliable match.")
            
        if len(jd.description.split()) < 30:
            raise HTTPException(status_code=400, detail="Job description is too short to perform a reliable match.")

        # Compute Match
        score, matched_skills, missing_skills, missing_keywords, suggestions = self.calculate_match(
            resume_text=resume.raw_text,
            jd_text=jd.description
        )

        # Save to Database
        match = await resume_match_repo.create_or_update(
            session=session,
            resume_id=resume.id,
            job_description_id=jd.id,
            match_score=score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            missing_keywords=missing_keywords,
            suggestions=suggestions,
        )
        
        return match

    async def get_match(
        self,
        session: AsyncSession,
        resume_id: uuid.UUID,
        job_description_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ResumeMatch:
        """Fetches an existing match result."""
        # Validate ownership of the resume first to prevent snooping
        resume = await resume_repo.get_by_id(session, resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        match = await resume_match_repo.get_match(session, resume_id, job_description_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match analysis not found for these documents.")
            
        return match

match_service = MatchService()
