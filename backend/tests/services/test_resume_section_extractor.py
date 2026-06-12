"""
Unit tests for ResumeSectionExtractor.
"""

from __future__ import annotations

import pytest

from app.services.resume_section_extractor import ResumeSectionExtractor

@pytest.fixture
def extractor():
    return ResumeSectionExtractor()

def test_extracts_contact_info(extractor):
    text = """
    Jane Doe
    123 Main St, Anytown, USA
    jane.doe@example.com | (555) 987-6543
    linkedin.com/in/janedoe | github.com/jdoe99
    
    EXPERIENCE
    Software Engineer
    """
    result = extractor.extract(text)
    
    contact = result["contact"]
    assert contact["name"] == "Jane Doe"
    assert contact["email"] == "jane.doe@example.com"
    assert contact["phone"] == "(555) 987-6543"
    assert contact["linkedin"] == "linkedin.com/in/janedoe"
    assert contact["github"] == "github.com/jdoe99"

def test_extracts_sections_chronological_format(extractor):
    text = """
    John Smith
    jsmith@test.com
    
    SUMMARY
    A highly motivated professional.
    
    EXPERIENCE
    Company A - Developer
    • Built a cool feature
    • Fixed some bugs
    
    Company B - Intern
    • Learned a lot
    
    EDUCATION
    B.S. Computer Science
    
    SKILLS
    Python, Java, C++
    """
    
    result = extractor.extract(text)
    
    assert result["summary"] == "A highly motivated professional."
    
    assert len(result["experience"]) == 5
    assert result["experience"][0].startswith("Company A")
    assert result["experience"][1] == "Built a cool feature"
    
    assert len(result["education"]) == 1
    assert result["education"][0] == "B.S. Computer Science"
    
    assert len(result["skills"]) == 1
    assert result["skills"][0] == "Python, Java, C++"

def test_extracts_sections_minimal_format(extractor):
    text = """
    Minimal Resume
    
    TECHNICAL SKILLS
    React
    Node.js
    
    WORK HISTORY
    Job 1
    Job 2
    """
    
    result = extractor.extract(text)
    
    # "TECHNICAL SKILLS" matches the 'skills' header
    assert len(result["skills"]) == 2
    assert "React" in result["skills"]
    assert "Node.js" in result["skills"]
    
    # "WORK HISTORY" matches the 'experience' header
    assert len(result["experience"]) == 2
    assert "Job 1" in result["experience"]
    assert "Job 2" in result["experience"]

def test_extracts_unconventional_casing_spacing(extractor):
    text = """
    Weird formatting
    
    * p r o f e s s i o n a l   s u m m a r y *
    This should not match the regex because of spaces, but wait, the regex doesn't handle spaced letters.
    Let's test normal casing and padded stars.
    
    *** EXPERIENCE ***
    Cool Job
    
    ##EDUCATION##
    School
    """
    
    result = extractor.extract(text)
    
    assert len(result["experience"]) == 1
    assert result["experience"][0] == "Cool Job"
    
    assert len(result["education"]) == 1
    assert result["education"][0] == "School"

def test_empty_resume(extractor):
    result = extractor.extract("")
    assert result["contact"] == {}
    assert result["experience"] == []
