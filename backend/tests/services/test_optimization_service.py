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
    mock_response.text = json.dumps(
        {
            "suggestions": [
                {
                    "section": "Experience",
                    "original_text": "Did stuff",
                    "suggested_text": "Did stuff well",
                    "reasoning": "More descriptive",
                    "optimization_type": "BULLET_REWRITE",
                }
            ]
        }
    )

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


@pytest.mark.asyncio
async def test_generate_suggestions_bad_json(mock_genai_client):
    service = OptimizationGeneratorService()
    service.client = mock_genai_client

    mock_response = MagicMock()
    mock_response.text = '```json\n{"broken": true\n```'
    mock_genai_client.models.generate_content.return_value = mock_response

    with pytest.raises(Exception):
        await service.generate_suggestions("resume text")


def test_build_prompt():
    service = OptimizationGeneratorService()
    prompt = service.build_prompt("resume", {"suggestions": ["ats"]}, {"missing_skills": ["python"]})
    assert "resume" in prompt
    assert "ats" in prompt
    assert "python" in prompt


@pytest.mark.asyncio
async def test_generate_via_openrouter():
    service = OptimizationGeneratorService()

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": '{"suggestions": [{"section": "Skill"}]}'}}]}
        mock_post.return_value = mock_resp

        # OpenRouter fallback requires an API key in settings
        with patch("app.services.optimization_service.settings.OPENROUTER_API_KEY", "test-key"):
            res = await service._generate_via_openrouter("prompt")
            assert len(res) == 1
            assert res[0]["section"] == "Skill"


@pytest.mark.asyncio
async def test_generate_via_openrouter_bad_json():
    service = OptimizationGeneratorService()

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "bad json"}}]}
        mock_post.return_value = mock_resp

        with patch("app.services.optimization_service.settings.OPENROUTER_API_KEY", "test-key"):
            with pytest.raises(Exception) as exc:
                await service._generate_via_openrouter("prompt")
            assert "Failed to parse OpenRouter response" in str(exc.value)


@pytest.mark.asyncio
async def test_generate_dashboard_insight_success(mock_genai_client):
    service = OptimizationGeneratorService()
    service.client = mock_genai_client

    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {
            "insight_text": "You are doing great!",
            "recommended_actions": [{"action": "Apply to more jobs", "impact": "High"}],
        }
    )

    mock_genai_client.models.generate_content.return_value = mock_response

    metrics = {"applications_this_week": 5}
    insight = await service.generate_dashboard_insight(metrics)

    assert insight["insight_text"] == "You are doing great!"
    assert len(insight["recommended_actions"]) == 1


@pytest.mark.asyncio
async def test_generate_dashboard_insight_fallback_openrouter():
    service = OptimizationGeneratorService()
    # Mock client missing or failing, trigger fallback
    service.client = None

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": '{"insight_text": "Good job fallback!", "recommended_actions": []}'}}]
        }
        mock_post.return_value = mock_resp

        with patch("app.services.optimization_service.settings.OPENROUTER_API_KEY", "test-key"):
            insight = await service.generate_dashboard_insight({"metrics": 1})
            assert insight["insight_text"] == "Good job fallback!"


@pytest.mark.asyncio
async def test_generate_dashboard_insight_fallback_failure():
    service = OptimizationGeneratorService()
    service.client = None

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_post.return_value = mock_resp

        with patch("app.services.optimization_service.settings.OPENROUTER_API_KEY", "test-key"):
            with pytest.raises(Exception) as exc:
                await service.generate_dashboard_insight({"metrics": 1})
            assert "503 Service Unavailable" in str(exc.value)
