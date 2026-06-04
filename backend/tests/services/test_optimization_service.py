import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.optimization_service import OptimizationGeneratorService


@pytest.fixture
def mock_genai_client():
    with patch("app.services.optimization_service.genai.Client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.mark.asyncio
async def test_generate_suggestions(mock_genai_client):
    service = OptimizationGeneratorService()
    service.client = mock_genai_client
    
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "suggestions": [
            {
                "section": "Experience",
                "original_text": "Did stuff",
                "suggested_text": "Did stuff well",
                "reasoning": "More descriptive",
                "optimization_type": "BULLET_REWRITE"
            }
        ]
    })
    
    mock_genai_client.models.generate_content.return_value = mock_response
    
    resume_text = "Experience: Did stuff"
    ats_analysis = {"suggestions": ["Add metrics"]}
    jd_match_results = {"missing_skills": ["Python"], "missing_keywords": ["backend"]}
    
    suggestions = await service.generate_suggestions(resume_text, ats_analysis, jd_match_results)
    
    assert len(suggestions) == 1
    assert suggestions[0]["section"] == "Experience"
    assert suggestions[0]["suggested_text"] == "Did stuff well"
    
    # Check that client was called with correct context
    mock_genai_client.models.generate_content.assert_called_once()
    call_args = mock_genai_client.models.generate_content.call_args
    assert "Add metrics" in call_args.kwargs["contents"]
    assert "Python" in call_args.kwargs["contents"]
