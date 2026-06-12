import pytest
from app.services.ats_feedback_generator import ats_feedback_generator

def test_perfect_resume_feedback():
    formatting = {
        "has_email": True, "has_phone": True, "has_linkedin": True, "word_count": 500,
        "has_bullets": True, "has_summary": True, "has_consistent_dates": True, "has_portfolio_links": True
    }
    quality = {
        "experience": {"details": {"entry_count": 3, "action_verbs_found": ["A", "B", "C", "D"], "metrics_count": 3, "good_bullet_ratio": 0.8}},
        "skills": {"details": {"skill_count": 12, "categorized_entries": 3}},
        "projects": {"details": {"project_count": 2, "technologies_mentioned": ["A", "B", "C"], "avg_words_per_project": 20}},
        "education": {"details": {"degrees_found": ["B.S."], "institution_signals": ["Univ"]}}
    }
    res = ats_feedback_generator.generate(formatting, quality)
    assert len(res["weaknesses"]) == 0
    assert len(res["strengths"]) > 0

def test_weak_resume_feedback():
    formatting = {"word_count": 100}
    quality = {"experience": {}, "skills": {}, "projects": {}, "education": {}}
    res = ats_feedback_generator.generate(formatting, quality)
    assert len(res["weaknesses"]) > 5

def test_edge_cases():
    pass
