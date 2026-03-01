import json
import logging
from typing import List, Optional, Any
from sqlalchemy.orm import Session
import httpx

from config import settings
from repositories import legal_research_repository
from schemas.legal_research import SearchQueryRequest, SearchResultResponse, CaseResponse

logger = logging.getLogger(__name__)

OLLAMA_URL = getattr(settings, "OLLAMA_URL", "https://api.groq.com/openai/v1/chat/completions")
MODEL_NAME = "llama-3.1-8b-instant"
INFERENCE_TIMEOUT = 60.0

async def perform_legal_research(db: Session, user_id: str, req: SearchQueryRequest) -> SearchResultResponse:
    """Execute search and generate AI summary of results."""
    # 1. Log the query
    legal_research_repository.save_research_query(db, user_id, req)
    
    # 2. Search cases
    cases = legal_research_repository.search_cases(db, req)
    
    # 3. Generate AI Summary (Always generate, even if 0 cases found locally)
    ai_summary = await _generate_research_summary(req.query, cases)
    
    case_responses = [CaseResponse.model_validate(c) for c in cases]
    return SearchResultResponse(
        cases=case_responses,
        ai_summary=ai_summary,
        total=len(cases)
    )

async def _generate_research_summary(query: str, cases: List[Any]) -> str:
    """Use Groq to summarize the search results in context of the query."""
    serialized_cases = ""
    for c in cases[:3]: # Summarize top 3
        serialized_cases += f"Case: {c.title}\nRuling: {c.key_ruling}\nSummary: {c.summary}\n\n"

    cases_header = "Here are the most relevant cases found in our local database:\n"
    prompt = f"""You are a professional legal research assistant.
The user searched for: "{query}"

{cases_header + serialized_cases if serialized_cases else "No specific cases matching this query were found in our internal database."}

Please provide a concise (2-3 paragraph) synthesis. 
If cases were provided above, explain how they relate to the search query.
If no cases were provided, provide a general legal overview of the topic based on your knowledge, but clearly state that no specific local precedents were matched.
Do not invent specific case names if not provided; only use provided info for specific citations or speak in general legal terms.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    api_key = getattr(settings, "GROQ_API_KEY", None)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        logger.warning("GROQ_API_KEY not found in settings. AI summary may fail.")

    try:
        async with httpx.AsyncClient(timeout=INFERENCE_TIMEOUT) as client:
            response = await client.post(OLLAMA_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Failed to generate research summary: {e}")
        return "AI analysis service is currently unavailable. Please review the case details below."
