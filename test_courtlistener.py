import asyncio
import httpx
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from services.legal_research_service import _search_external_cases
from config import settings

async def test_courtlistener():
    token = settings.COURTLISTENER_API_TOKEN
    if not token:
        print("Error: COURTLISTENER_API_TOKEN is not set in environment or .env")
        return
    print(f"Testing CourtListener API with token: {token[:5]}...")
    query = "Amazon GDPR"
    results = await _search_external_cases(query)
    
    print(f"Found {len(results)} results for '{query}'")
    for r in results[:3]:
        print(f"- {r['title']} ({r['year']})")
        print(f"  Summary: {r['summary'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_courtlistener())
