from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from api.dependencies import get_current_user
from models.user import User
from schemas.legal_research import SearchQueryRequest, SearchResultResponse, ResearchQueryResponse, CaseResponse, SavedCaseBase
from services import legal_research_service, audit_service
from repositories import legal_research_repository

router = APIRouter(prefix="/research", tags=["Legal Research"])

@router.post("/search", response_model=SearchResultResponse)
async def search_case_law(
    req: SearchQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for case law and get an AI synthesis of results."""
    result = await legal_research_service.perform_legal_research(db, current_user.id, req)
    
    audit_service.log_action(
        db,
        user=current_user,
        resource="research",
        action="search",
        metadata={"query": req.query, "results_count": result.total}
    )
    
    return result

@router.get("/history", response_model=List[ResearchQueryResponse])
def get_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch the current user's search history."""
    return legal_research_repository.get_research_history(db, current_user.id)

@router.post("/save-case")
def bookmark_case(
    saved_case: SavedCaseBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bookmark a legal case for later review."""
    legal_research_repository.save_case(db, current_user.id, saved_case.case_id, saved_case.notes)
    
    audit_service.log_action(
        db,
        user=current_user,
        resource="research",
        action="save_case",
        resource_id=saved_case.case_id
    )
    
    return {"message": "Case saved successfully"}
