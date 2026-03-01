"""
Ollama Integration Service for GDPR/CCPA Compliance Analysis.
Sends document text to a local Ollama instance and returns structured compliance results.
"""

import json
import logging
from pathlib import Path
from typing import Any

import httpx
import time

from config import settings

logger = logging.getLogger(__name__)

OLLAMA_URL = getattr(settings, "OLLAMA_URL", "https://api.groq.com/openai/v1/chat/completions")
MODEL_NAME = "llama-3.1-8b-instant"
INFERENCE_TIMEOUT = 120.0  # 120s for compliance analysis (longer docs)

# Load the prompt template once at module level
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "gdpr_ccpa_analysis_prompt.md"
_SYSTEM_PROMPT: str | None = None


def _get_system_prompt() -> str:
    """Lazy-load the system prompt from disk."""
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        try:
            _SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Prompt file not found at %s, using inline fallback.", _PROMPT_PATH)
            _SYSTEM_PROMPT = (
                "You are a legal compliance AI. Analyze the document for GDPR and CCPA compliance. "
                "Return ONLY valid JSON with keys: gdpr_status, ccpa_status, score, "
                "detected_sections, missing_sections, ai_suggestions."
            )
    return _SYSTEM_PROMPT


# Default structure returned on failure
_EMPTY_RESULT: dict[str, Any] = {
    "gdpr_status": "FAIL",
    "ccpa_status": "FAIL",
    "score": 0,
    "detected_sections": [],
    "missing_sections": [],
    "ai_suggestions": ["Analysis could not be completed. Please try again."],
}


async def analyze_document_compliance(document_text: str) -> dict[str, Any]:
    """
    Send extracted document text to Groq for GDPR/CCPA compliance analysis.
    """
    from services.metrics_service import AI_INFERENCE_LATENCY
    
    start_time = time.time()
    try:
        system_prompt = _get_system_prompt()

        full_prompt = f"""{system_prompt}

        DOCUMENT TEXT:
        {document_text}
        """

        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": full_prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        api_key = getattr(settings, "GROQ_API_KEY", None)
        if not api_key:
            logger.warning("GROQ_API_KEY is not set. API calls will likely fail.")
        else:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            logger.info("Sending document (%d chars) to Groq for compliance analysis...", len(document_text))
            async with httpx.AsyncClient(timeout=INFERENCE_TIMEOUT) as client:
                response = await client.post(OLLAMA_URL, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                response_text = data["choices"][0]["message"]["content"]

                try:
                    result = json.loads(response_text)
                    normalized = _normalise_result(result)
                    
                    # Track compliance metrics
                    from services.metrics_service import COMPLIANCE_RESULTS
                    COMPLIANCE_RESULTS.labels(framework="gdpr", status=normalized["gdpr_status"]).inc()
                    COMPLIANCE_RESULTS.labels(framework="ccpa", status=normalized["ccpa_status"]).inc()
                    
                    return normalized
                except json.JSONDecodeError:
                    logger.error("Groq returned invalid JSON: %s", response_text)
                    return _error_result("AI model returned an malformed response.")

        except httpx.ReadTimeout:
            logger.error("Groq inference timed out after %d seconds.", INFERENCE_TIMEOUT)
            return _error_result("AI analysis timed out. The document might be too complex.")
        except httpx.HTTPStatusError as exc:
            logger.error("Groq API error: %s", exc)
            return _error_result(f"AI service error: {exc.response.status_code}")
        except Exception as exc:
            logger.exception("Unexpected error during compliance analysis: %s", exc)
            return _error_result(f"Unexpected error: {exc}")
    finally:
        AI_INFERENCE_LATENCY.labels(model=MODEL_NAME, analysis_type="compliance").observe(time.time() - start_time)


def _normalise_result(raw: dict[str, Any]) -> dict[str, Any]:
    """Ensure the AI response has exactly the expected shape."""
    return {
        "gdpr_status": str(raw.get("gdpr_status", "FAIL")).upper(),
        "ccpa_status": str(raw.get("ccpa_status", "FAIL")).upper(),
        "score": _clamp(raw.get("score", 0), 0, 100),
        "detected_sections": _to_str_list(raw.get("detected_sections", [])),
        "missing_sections": _to_str_list(raw.get("missing_sections", [])),
        "ai_suggestions": _to_str_list(raw.get("ai_suggestions", [])),
    }


def _error_result(message: str) -> dict[str, Any]:
    """Return a safe error result without crashing."""
    result = dict(_EMPTY_RESULT)
    result["ai_suggestions"] = [message]
    return result


def _clamp(value, lo, hi):
    """Clamp a numeric value within [lo, hi]."""
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return lo


def _to_str_list(value) -> list[str]:
    """Coerce a value into a list of strings."""
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []
