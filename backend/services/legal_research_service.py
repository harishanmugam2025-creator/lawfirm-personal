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
    
    # 2. Search local cases
    local_cases = legal_research_repository.search_cases(db, req)
    
    # 3. Search external cases (CourtListener)
    external_cases = []
    if req.query:
        external_cases = await _search_external_cases(req.query)
    
    # 4. Merge results
    all_cases = []
    # Convert local cases to a uniform format if needed, but here we'll just combine
    all_cases.extend(local_cases)
    all_cases.extend(external_cases)
    
    # 5. Generate AI Summary (Always generate, even if 0 cases found)
    ai_summary = await _generate_research_summary(req.query, all_cases)
    
    case_responses = []
    for c in all_cases:
        if hasattr(c, "model_validate"):
            case_responses.append(CaseResponse.model_validate(c))
        else:
            # It's a dict from the external API
            case_responses.append(CaseResponse(**c))

    return SearchResultResponse(
        cases=case_responses,
        ai_summary=ai_summary,
        total=len(case_responses)
    )

async def _search_external_cases(query: str) -> List[dict]:
    """Fetch real-world cases from CourtListener API."""
    token = getattr(settings, "COURTLISTENER_API_TOKEN", None)
    if not token:
        logger.warning("COURTLISTENER_API_TOKEN not found. Skipping external search.")
        return []

    url = "https://www.courtlistener.com/api/v3/search/"
    params = {
        "q": query,
        "type": "o", # 'o' for opinions
        "page_size": 10
    }
    headers = {
        "Authorization": f"Token {token}"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                # Map CourtListener fields to our CaseResponse schema
                results.append({
                    "id": str(item.get("id", "")),
                    "title": item.get("caseName", "Untitled Case"),
                    "court": item.get("court", "Unknown Court"),
                    "jurisdiction": item.get("jurisdiction", "USA"),
                    "year": int(item.get("date_filed", "0001-01-01").split("-")[0]) if item.get("date_filed") else 0,
                    "regulation": "General", # We don't necessarily know which regulation it matches best
                    "summary": item.get("snippet", "No summary available.").replace("<span class=\"highlight\">", "").replace("</span>", ""),
                    "full_text": f"Source: {item.get('absolute_url', '')}",
                    "key_ruling": "Refer to full text for detailed ruling."
                })
            return results
    except Exception as e:
        logger.error(f"CourtListener search failed: {e}")
        return []

async def _generate_research_summary(query: str, cases: List[Any]) -> str:
    """Use Groq to summarize the search results in context of the query."""
    serialized_cases = ""
    # Use top 5 cases for summary if available
    for c in cases[:5]:
        if isinstance(c, dict):
            title = c.get("title")
            ruling = c.get("key_ruling")
            summary = c.get("summary")
        else:
            title = c.title
            ruling = c.key_ruling
            summary = c.summary
            
        serialized_cases += f"Case: {title}\nRuling: {ruling}\nSummary: {summary}\n\n"

    cases_header = "Here are the most relevant cases found:\n"
    prompt = f"""You are a professional legal research assistant.
The user searched for: "{query}"

{cases_header + serialized_cases if serialized_cases else "No specific cases matching this query were found in our internal database or external records."}

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
