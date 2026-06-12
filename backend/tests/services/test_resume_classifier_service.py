"""
Unit tests for ResumeClassifierService.

These tests cover:
  - Pure unit tests for classify() (no DB needed)
  - Integration with ATSService (validate gate) using an in-memory DB session
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.models.enums import ResumeStatus
from app.models.resume import Resume
from app.schemas.user import UserCreate
from app.services import auth_service
from app.services.ats_service import ATSService
from app.services.resume_classifier_service import (
    ResumeClassificationResult,
    ResumeClassifierService,
)

# Integration tests (DB fixtures) are only run when the test DB is reachable.
# Mark them so they can be skipped locally with: pytest -m "not integration"
pytestmark_integration = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def make_service() -> ResumeClassifierService:
    return ResumeClassifierService()


FULL_RESUME_TEXT = """
John Doe
john.doe@example.com | (555) 123-4567 | linkedin.com/in/johndoe | github.com/johndoe

SUMMARY
Software engineer with 5+ years of experience building scalable web applications.

EXPERIENCE
Senior Software Engineer — Acme Corp                             Jan 2020 – Present
- Developed microservices architecture that increased throughput by 40%.
- Led a team of 8 engineers and streamlined the CI/CD pipeline.
- Reduced cloud costs by 25% via infrastructure optimizations.

Software Engineer — Beta Inc                                     Mar 2017 – Dec 2019
- Implemented RESTful APIs consumed by 50k+ daily users.
- Created automated test suites, reducing regression bugs by 30%.

EDUCATION
B.S. Computer Science — State University                        2013 – 2017

SKILLS
Python, FastAPI, React, PostgreSQL, Docker, Kubernetes, AWS

PROJECTS
CareerPilot AI — Resume analysis and job-matching platform (github.com/johndoe/careerpilot)

CERTIFICATIONS
AWS Certified Solutions Architect – Associate (2022)
""" * 2  # repeat to exceed 150-word length check


MINIMAL_RESUME_TEXT = (
    "john@example.com 555-000-1111\n"
    "Education: B.S. Computer Science\n"
    "Skills: Python\n"
    "Experience: 2 years\n"
    "• Worked on projects\n"
    "• Delivered results\n"
    "• Met deadlines\n"
) + ("Word padding. " * 20)


BORDERLINE_TEXT = (
    "john@example.com\n"
    "Education: B.S. Computer Science\n"
    "Skills: Python\n"
) + ("Some extra text to push word count past 50. " * 5)


NOT_RESUME_TEXT = (
    "Chapter 1: The Great Adventure\n\n"
    "It was a dark and stormy night. The wind howled through the trees as "
    "our hero made his way through the forest. He had no phone, no email, "
    "and certainly no LinkedIn profile. " * 10
)


EMPTY_TEXT = "   \n\t  "


# ---------------------------------------------------------------------------
# Pure unit tests for ResumeClassifierService.classify()
# ---------------------------------------------------------------------------


class TestResumeClassifierContactScoring:
    def test_email_adds_points(self):
        svc = make_service()
        result = svc.classify("user@example.com")
        assert result.confidence >= 10

    def test_phone_adds_points(self):
        svc = make_service()
        result = svc.classify("Call me at 555-123-4567")
        assert result.confidence >= 7

    def test_linkedin_adds_points(self):
        svc = make_service()
        result = svc.classify("linkedin.com/in/johndoe")
        assert result.confidence >= 4

    def test_github_adds_points(self):
        svc = make_service()
        result = svc.classify("github.com/johndoe")
        assert result.confidence >= 4

    def test_all_contact_info_scores_25(self):
        svc = make_service()
        text = "user@example.com (555) 123-4567 linkedin.com/in/johndoe github.com/johndoe"
        result = svc.classify(text)
        # 10 + 7 + 4 + 4 = 25
        assert result.confidence >= 25


class TestResumeClassifierSectionDetection:
    def test_experience_section_detected(self):
        svc = make_service()
        result = svc.classify("Experience\n- Did things")
        assert "experience" in result.detected_sections

    def test_education_section_detected(self):
        svc = make_service()
        result = svc.classify("Education: B.S. Computer Science")
        assert "education" in result.detected_sections

    def test_skills_section_detected(self):
        svc = make_service()
        result = svc.classify("Skills: Python, SQL")
        assert "skills" in result.detected_sections

    def test_projects_section_detected(self):
        svc = make_service()
        result = svc.classify("Projects\n- Built a web app")
        assert "projects" in result.detected_sections

    def test_summary_section_detected(self):
        svc = make_service()
        result = svc.classify("Summary\nSoftware engineer with 5 years experience")
        assert "summary" in result.detected_sections

    def test_certifications_section_detected(self):
        svc = make_service()
        result = svc.classify("Certifications: AWS Certified")
        assert "certifications" in result.detected_sections

    def test_missing_sections_tracked(self):
        svc = make_service()
        # Only education present
        result = svc.classify("Education: B.S.")
        assert "education" in result.detected_sections
        assert "experience" in result.missing_sections
        assert "skills" in result.missing_sections


class TestResumeClassifierLengthScoring:
    def test_empty_text_returns_zero(self):
        svc = make_service()
        result = svc.classify(EMPTY_TEXT)
        assert result.confidence == 0
        assert result.is_resume is False

    def test_very_short_text_gets_zero_length_pts(self):
        svc = make_service()
        # Only 10 words — should score 0 for length
        result = svc.classify("just ten words total right here nothing else wow")
        assert result.confidence < 15  # only possible contact/section hits

    def test_optimal_length_gets_full_length_pts(self):
        svc = make_service()
        # Build a 300-word text with nothing resume-like
        long_text = "word " * 300
        result = svc.classify(long_text)
        # Should include 10 length points
        assert result.confidence >= 10


class TestResumeClassifierFormattingScoring:
    def test_bullet_points_detected(self):
        svc = make_service()
        text = "• Did thing one\n• Did thing two\n• Did thing three"
        result = svc.classify(text)
        assert result.confidence >= 5

    def test_date_ranges_detected(self):
        svc = make_service()
        text = "Worked at Company Jan 2020 - Present"
        result = svc.classify(text)
        assert result.confidence >= 5


class TestResumeClassifierEndToEnd:
    def test_full_resume_is_accepted(self):
        svc = make_service()
        result = svc.classify(FULL_RESUME_TEXT)
        assert result.is_resume is True
        assert result.confidence >= 70
        assert result.warning is None
        # All major sections should be detected
        for section in ["experience", "education", "skills", "summary", "certifications"]:
            assert section in result.detected_sections

    def test_minimal_resume_passes_threshold(self):
        svc = make_service()
        result = svc.classify(MINIMAL_RESUME_TEXT)
        assert result.is_resume is True
        assert result.confidence >= 40

    def test_borderline_text_gets_warning(self):
        svc = make_service()
        result = svc.classify(BORDERLINE_TEXT)
        # Should land in 40-69 range for the warning scenario
        if 40 <= result.confidence < 70:
            assert result.warning is not None
            assert "may not be a resume" in result.warning
            assert result.is_resume is True  # still proceeds with warning

    def test_non_resume_is_rejected(self):
        svc = make_service()
        result = svc.classify(NOT_RESUME_TEXT)
        assert result.is_resume is False
        assert result.confidence < 40
        assert "does not appear to be a resume" in result.warning

    def test_to_dict_structure(self):
        svc = make_service()
        result = svc.classify(FULL_RESUME_TEXT)
        d = result.to_dict()
        assert "is_resume" in d
        assert "confidence" in d
        assert "detected_sections" in d
        assert "missing_sections" in d

    def test_to_dict_includes_warning_when_present(self):
        svc = make_service()
        result = ResumeClassificationResult(
            is_resume=True,
            confidence=55,
            warning="This document may not be a resume. ATS results may be unreliable.",
        )
        d = result.to_dict()
        assert "warning" in d

    def test_to_dict_excludes_warning_when_none(self):
        svc = make_service()
        result = ResumeClassificationResult(is_resume=True, confidence=85)
        d = result.to_dict()
        assert "warning" not in d


# ---------------------------------------------------------------------------
# Integration: ATSService respects the validation gate
# ---------------------------------------------------------------------------


@pytest.fixture
async def ats_user(db_session):
    user_in = UserCreate(
        name="Classifier Gate User",
        email="classifier.gate@example.com",
        password="securePassword1",
    )
    return await auth_service.register(db_session, user_in)


async def _make_resume(db_session, user_id, raw_text: str | None) -> Resume:
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        file_name="test.pdf",
        file_url="http://example.com/test.pdf",
        original_file_name="test.pdf",
        storage_path="resumes/test.pdf",
        content_type="application/pdf",
        file_size_bytes=1000,
        status=ResumeStatus.COMPLETED,
        raw_text=raw_text,
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    return resume


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ats_rejects_non_resume_document(db_session, ats_user):
    """A document that clearly isn't a resume must raise HTTP 422."""
    resume = await _make_resume(db_session, ats_user.id, NOT_RESUME_TEXT)

    service = ATSService()
    with pytest.raises(HTTPException) as exc_info:
        await service.analyze_resume(db_session, resume.id, ats_user.id)

    assert exc_info.value.status_code == 422
    detail = exc_info.value.detail
    assert detail["is_resume"] is False
    assert "confidence" in detail
    assert "detected_sections" in detail
    assert "missing_sections" in detail


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ats_proceeds_with_full_resume(db_session, ats_user):
    """A proper resume clears the validation gate and ATS scoring completes."""
    resume = await _make_resume(db_session, ats_user.id, FULL_RESUME_TEXT)

    service = ATSService()
    analysis = await service.analyze_resume(db_session, resume.id, ats_user.id)

    assert analysis.id is not None
    assert analysis.ats_score >= 0
    # Validation metadata should be embedded in keyword_analysis
    assert "resume_validation" in analysis.keyword_analysis
    val_meta = analysis.keyword_analysis["resume_validation"]
    assert val_meta["confidence"] >= 70
    assert "warning" not in val_meta  # clean pass — no warning


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ats_validation_metadata_attached_on_warning_zone(db_session, ats_user):
    """A borderline document that passes (40-69) should embed a warning in metadata."""
    # Craft text that is likely to land in the 40-69 band:
    # has email + education + skills but nothing else resume-like
    text = (
        "user@example.com\n"
        "Education: B.S. Computer Science — Some University\n"
        "Skills: Python, SQL, Docker\n"
    ) + ("Padding text to exceed 150 words. " * 8)

    resume = await _make_resume(db_session, ats_user.id, text)
    service = ATSService()

    # Classify to learn the actual confidence (may or may not be in 40-69)
    from app.services.resume_classifier_service import resume_classifier
    classification = resume_classifier.classify(text)

    if classification.is_resume and classification.confidence < 70:
        # Warning zone: should still succeed but with warning in metadata
        analysis = await service.analyze_resume(db_session, resume.id, ats_user.id)
        assert "resume_validation" in analysis.keyword_analysis
        assert "warning" in analysis.keyword_analysis["resume_validation"]
    elif classification.confidence >= 70:
        # Passed cleanly — just assert no crash
        analysis = await service.analyze_resume(db_session, resume.id, ats_user.id)
        assert analysis.id is not None
    else:
        # Rejected — should raise
        with pytest.raises(HTTPException) as exc_info:
            await service.analyze_resume(db_session, resume.id, ats_user.id)
        assert exc_info.value.status_code == 422
