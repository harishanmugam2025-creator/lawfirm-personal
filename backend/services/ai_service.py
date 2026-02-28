import json
import logging
from typing import Any

import httpx
from fastapi import HTTPException

from config import settings

logger = logging.getLogger(__name__)

# Default to local Ollama. In production, this points to the isolated AI pod.
OLLAMA_URL = getattr(settings, "OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = "mistral"
INFERENCE_TIMEOUT = 30.0  # Strict 30s timeout per governance


async def analyze_compliance(system_prompt: str, document_text: str) -> dict[str, Any]:
    """
    Call Mistral 7B via Ollama to analyze the document text against the provided rules.
    Enforces a structured JSON response to build the Reasoning Path.
    """
    # The prompt explicitly asks for the 3 required reasoning fields
    full_prompt = f"""
{system_prompt}

Analyze the following document text and return ONLY a valid JSON object with EXACTLY these three keys:
- "rules_triggered": A string explaining which rules were violated or "None" if fully compliant.
- "confidence_score": A float between 0.0 and 1.0 representing your certainty.
- "source_text": A short string quoting the most relevant part of the document used for this decision.

DOCUMENT TEXT:
{document_text}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for deterministic analysis
        }
    }

    headers = {}
    api_key = getattr(settings, "OLLAMA_API_KEY", None)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=INFERENCE_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate", 
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            response_text = data.get("response", "{}")
            
            try:
                # Parse the guaranteed JSON
                result_json = json.loads(response_text)
                
                # Ensure the required keys exist, providing fallbacks if the LLM hallucinated
                return {
                    "rules_triggered": str(result_json.get("rules_triggered", "Parsing failed: missing rules_triggered")),
                    "confidence_score": float(result_json.get("confidence_score", 0.0)),
                    "source_text": str(result_json.get("source_text", "Parsing failed: missing source_text"))[:500],
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse Ollama output as JSON: %s", response_text)
                return _graceful_degradation("AI returned invalid JSON format.")

    except httpx.TimeoutException:
        logger.error("Ollama inference timed out after %ss", INFERENCE_TIMEOUT)
        return _graceful_degradation("AI inference timeout (exceeded 30s limit).")
    except httpx.RequestError as exc:
        logger.error("Failed to connect to Ollama at %s: %s", OLLAMA_URL, exc)
        return _graceful_degradation("AI service reachable. Operating in degraded mode.")
    except Exception as exc:
        logger.exception("Unexpected error during AI analysis: %s", exc)
        return _graceful_degradation("Unexpected AI service failure.")


def _graceful_degradation(reason: str) -> dict[str, Any]:
    """Return a highly-confident failure result rather than crashing the request."""
    return {
        "rules_triggered": f"SYSTEM FAILURE: {reason}",
        "confidence_score": 0.0,
        "source_text": "N/A - Analysis could not be completed.",
    }
