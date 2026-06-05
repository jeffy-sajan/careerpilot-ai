import pytest

from app.services.match_service import MatchService


@pytest.fixture
def match_service():
    return MatchService()


def test_extract_skills(match_service):
    text = "We are looking for someone with experience in Python, FastAPI, and Amazon Web Services. A background in machine learning is a plus."
    skills = match_service._extract_skills(text)

    assert "Python" in skills
    assert "FastAPI" in skills
    assert "AWS" in skills  # "amazon web services" maps to AWS
    assert "Machine Learning" in skills


def test_extract_keywords_stemming(match_service):
    # The stemming should convert "managing", "managed", "manage" into the same root.
    # It also ignores stopwords.
    text = "Managing a team of developers. Managed several projects. Ability to manage expectations."
    keywords = match_service._extract_keywords(text, top_n=5)

    # "manag" is the Snowball stem for managing/managed/manage
    assert "manag" in keywords


def test_calculate_match_perfect(match_service):
    jd_text = "Required: Python, React, AWS. Looking for strong leadership."
    res_text = "I have 5 years using Python, React, and AWS. Demonstrated strong leadership."

    score, matched_skills, missing_skills, missing_keywords, suggestions = match_service.calculate_match(
        res_text, jd_text
    )

    # Should find at least 3 skills
    assert len(matched_skills) >= 3
    assert len(missing_skills) == 0
    # Score should be at least 65
    assert score >= 65


def test_calculate_match_no_skills_in_jd(match_service):
    jd_text = "Looking for a hard worker to manage operations and drive growth."
    res_text = "I am a hard worker who manages operations and drives massive growth."

    score, matched_skills, missing_skills, missing_keywords, suggestions = match_service.calculate_match(
        res_text, jd_text
    )

    # 0 skills in JD, so score is 100% based on keywords. They should match well.
    assert score > 50
    assert len(missing_skills) == 0


def test_calculate_match_poor_match(match_service):
    jd_text = "Required: Python, React, AWS, Docker, Kubernetes."
    res_text = "I am a Ruby on Rails developer. I know HTML and CSS."

    score, matched_skills, missing_skills, missing_keywords, suggestions = match_service.calculate_match(
        res_text, jd_text
    )

    assert score < 20
    assert len(missing_skills) == 5
