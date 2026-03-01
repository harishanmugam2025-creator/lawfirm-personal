import json
from unittest.mock import patch, MagicMock

import httpx
import pytest

from services import ai_service


@pytest.mark.asyncio
async def test_analyze_compliance_success():
    """Test successful JSON parsing from Ollama."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "rules_triggered": "GDPR Article 5 violation",
                        "confidence_score": 0.95,
                        "source_text": "We sell user data without consent."
                    })
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await ai_service.analyze_compliance("System Prompt", "Doc Text")

        assert result["rules_triggered"] == "GDPR Article 5 violation"
        assert result["confidence_score"] == 0.95
        assert "sell user data" in result["source_text"]


@pytest.mark.asyncio
async def test_analyze_compliance_invalid_json():
    """Test graceful degradation when Ollama returns non-JSON text."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "I am an AI and I think this is compliant."
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await ai_service.analyze_compliance("P", "T")

        assert "SYSTEM FAILURE" in result["rules_triggered"]
        assert result["confidence_score"] == 0.0


@pytest.mark.asyncio
async def test_analyze_compliance_timeout():
    """Test fallback logic when httpx raises a TimeoutException."""
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        result = await ai_service.analyze_compliance("P", "T")

        assert "SYSTEM FAILURE" in result["rules_triggered"]
        assert "timeout" in result["rules_triggered"].lower()
        assert result["confidence_score"] == 0.0


@pytest.mark.asyncio
async def test_analyze_compliance_connection_error():
    """Test fallback logic when Ollama is unreachable."""
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection Refused")):
        result = await ai_service.analyze_compliance("P", "T")

        assert "SYSTEM FAILURE" in result["rules_triggered"]
        assert result["confidence_score"] == 0.0
