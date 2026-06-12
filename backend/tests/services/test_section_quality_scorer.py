"""
Unit tests for SectionQualityScorer.
"""

from __future__ import annotations

import pytest

from app.services.section_quality_scorer import SectionQualityScorer


@pytest.fixture
def scorer():
    return SectionQualityScorer()


# ═══════════════════════════════════════════════════════════════════════════
# Experience Scoring
# ═══════════════════════════════════════════════════════════════════════════

class TestExperienceScoring:
    def test_empty_experience(self, scorer):
        result = scorer.score_experience([])
        assert result.score == 0
        assert result.max_score == 25
        assert result.details["entry_count"] == 0

    def test_strong_experience(self, scorer):
        entries = [
            "Senior Software Engineer at Acme Corp",
            "Developed a microservices architecture that reduced latency by 40%",
            "Led a team of 5 engineers to deliver a $2M project on time",
            "Managed CI/CD pipelines serving 100+ deployments per week",
            "Implemented automated testing framework increasing code coverage by 30%",
            "Optimized database queries reducing response time by 60%",
        ]
        result = scorer.score_experience(entries)
        assert result.score >= 20, f"Strong experience should score ≥20, got {result.score}"
        assert result.details["entry_count"] == 6
        assert len(result.details["action_verbs_found"]) >= 3
        assert result.details["metrics_count"] >= 3

    def test_weak_experience_no_verbs_no_metrics(self, scorer):
        entries = [
            "Job at company",
            "Stuff",
        ]
        result = scorer.score_experience(entries)
        assert result.score < 10
        assert len(result.details["action_verbs_found"]) == 0

    def test_bullet_quality_scoring(self, scorer):
        # Good bullets: 8-30 words each
        good_entries = [
            "Designed and implemented a distributed caching layer that improved API response times by 45%",
            "Led migration of legacy monolith to microservices architecture serving 10M daily requests",
            "Collaborated with product team to define and deliver three major feature releases",
        ]
        result = scorer.score_experience(good_entries)
        assert result.details["good_bullet_ratio"] >= 0.6

    def test_action_verb_variety(self, scorer):
        entries = [
            "Developed the backend API using Python and FastAPI",
            "Managed deployment infrastructure on AWS",
            "Optimized SQL queries for better performance",
            "Led the frontend team in a React migration project",
            "Designed the database schema for the new product",
        ]
        result = scorer.score_experience(entries)
        assert len(result.details["action_verbs_found"]) >= 4


# ═══════════════════════════════════════════════════════════════════════════
# Skills Scoring
# ═══════════════════════════════════════════════════════════════════════════

class TestSkillsScoring:
    def test_empty_skills(self, scorer):
        result = scorer.score_skills([])
        assert result.score == 0
        assert result.max_score == 15
        assert result.details["skill_count"] == 0

    def test_diverse_skills(self, scorer):
        skills = [
            "Python, JavaScript, TypeScript",
            "React, Django, FastAPI",
            "PostgreSQL, Redis, MongoDB",
            "Docker, AWS, Kubernetes",
            "Git, Jira, Figma",
        ]
        result = scorer.score_skills(skills)
        assert result.score >= 10
        assert len(result.details["categories_covered"]) >= 3

    def test_single_category_skills(self, scorer):
        skills = ["Python, Java, C++, JavaScript"]
        result = scorer.score_skills(skills)
        assert "languages" in result.details["categories_covered"]
        assert len(result.details["categories_covered"]) == 1

    def test_categorized_skills_bonus(self, scorer):
        """Skills organized with colons should get a categorization bonus."""
        skills = [
            "Languages: Python, JavaScript, TypeScript",
            "Frameworks: React, Django",
            "Databases: PostgreSQL, Redis",
        ]
        result = scorer.score_skills(skills)
        assert result.details["categorized_entries"] >= 2

    def test_many_skills_high_count_score(self, scorer):
        skills = [
            "Python, Java, JavaScript, TypeScript, Go",
            "React, Angular, Vue, Django",
        ]
        result = scorer.score_skills(skills)
        assert result.details["skill_count"] >= 8


# ═══════════════════════════════════════════════════════════════════════════
# Projects Scoring
# ═══════════════════════════════════════════════════════════════════════════

class TestProjectsScoring:
    def test_empty_projects(self, scorer):
        result = scorer.score_projects([])
        assert result.score == 0
        assert result.max_score == 12
        assert result.details["project_count"] == 0

    def test_strong_projects(self, scorer):
        projects = [
            "Built a full-stack e-commerce platform using React and Django with PostgreSQL database and Stripe integration",
            "Developed a real-time chat application using WebSockets and deployed on AWS with Docker containerization",
            "Created an ML-powered resume analyzer using Python and scikit-learn that processes natural language text",
        ]
        result = scorer.score_projects(projects)
        assert result.score >= 8
        assert len(result.details["technologies_mentioned"]) >= 2

    def test_brief_projects_low_quality(self, scorer):
        projects = [
            "Todo app",
            "Calculator",
        ]
        result = scorer.score_projects(projects)
        assert result.details["avg_words_per_project"] < 6


# ═══════════════════════════════════════════════════════════════════════════
# Education Scoring
# ═══════════════════════════════════════════════════════════════════════════

class TestEducationScoring:
    def test_empty_education(self, scorer):
        result = scorer.score_education([])
        assert result.score == 0
        assert result.max_score == 8
        assert len(result.details["degrees_found"]) == 0

    def test_strong_education(self, scorer):
        education = [
            "B.S. in Computer Science",
            "Stanford University, 2020",
        ]
        result = scorer.score_education(education)
        assert result.score >= 6
        assert len(result.details["degrees_found"]) >= 1
        assert "university" in result.details["institution_signals"]

    def test_education_no_degree_keyword(self, scorer):
        education = ["Studied programming at a bootcamp"]
        result = scorer.score_education(education)
        assert result.details["degrees_found"] == []

    def test_masters_degree_detection(self, scorer):
        education = ["M.S. Computer Engineering, MIT"]
        result = scorer.score_education(education)
        assert len(result.details["degrees_found"]) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# Full Evaluation
# ═══════════════════════════════════════════════════════════════════════════

class TestFullEvaluation:
    def test_evaluate_returns_all_sections(self, scorer):
        sections = {
            "experience": ["Developed APIs at Google", "Managed a team of 5"],
            "skills": ["Python, Java, React"],
            "projects": ["Built a portfolio site using Next.js and Vercel"],
            "education": ["B.S. Computer Science, University of Michigan"],
        }
        result = scorer.evaluate(sections)
        d = result.to_dict()
        assert "experience_score" in d
        assert "skills_score" in d
        assert "projects_score" in d
        assert "education_score" in d
        assert "total_section_quality_score" in d
        assert d["total_section_quality_score"] == (
            d["experience_score"] + d["skills_score"] + d["projects_score"] + d["education_score"]
        )

    def test_evaluate_empty_sections(self, scorer):
        sections = {
            "experience": [],
            "skills": [],
            "projects": [],
            "education": [],
        }
        result = scorer.evaluate(sections)
        assert result.total_score == 0

    def test_max_total_is_60(self, scorer):
        sections = {
            "experience": [],
            "skills": [],
            "projects": [],
            "education": [],
        }
        result = scorer.evaluate(sections)
        assert result.max_total == 60

    def test_to_dict_has_breakdown(self, scorer):
        sections = {
            "experience": ["Developed features"],
            "skills": ["Python"],
            "projects": [],
            "education": [],
        }
        result = scorer.evaluate(sections)
        d = result.to_dict()
        assert "breakdown" in d
        assert "experience" in d["breakdown"]
        assert "skills" in d["breakdown"]
        assert "projects" in d["breakdown"]
        assert "education" in d["breakdown"]
        # Each breakdown should have score, max_score, strengths, weaknesses, recommendations
        for section_name in ["experience", "skills", "projects", "education"]:
            sec = d["breakdown"][section_name]
            assert "score" in sec
            assert "max_score" in sec
            assert "details" in sec
