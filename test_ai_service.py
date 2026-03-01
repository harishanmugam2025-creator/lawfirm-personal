
import asyncio
import httpx
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from config import settings
from services.legal_research_service import _generate_research_summary

async def test_ai():
    print(f"Testing AI service with URL: {settings.OLLAMA_URL}")
    print(f"GROQ_API_KEY present: {bool(settings.GROQ_API_KEY)}")
    
    try:
        # Simple test query
        summary = await _generate_research_summary("What is GDPR?", [])
        print("\nAI Response received successfully!")
        print("-" * 20)
        print(summary[:200] + "...")
        print("-" * 20)
        return True
    except Exception as e:
        print(f"\nAI Test Failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_ai())
