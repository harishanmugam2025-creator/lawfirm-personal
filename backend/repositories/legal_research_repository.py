from sqlalchemy.orm import Session
from models.legal_research import LegalCase, ResearchQuery, SavedCase
from schemas.legal_research import CaseCreate, SearchQueryRequest
from typing import List, Optional

def create_case(db: Session, case_data: CaseCreate) -> LegalCase:
    db_case = LegalCase(**case_data.model_dump())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

def search_cases(db: Session, req: SearchQueryRequest) -> List[LegalCase]:
    query = db.query(LegalCase)
    
    if req.jurisdiction and req.jurisdiction != "All Regions":
        query = query.filter(LegalCase.jurisdiction == req.jurisdiction)
    if req.year:
        query = query.filter(LegalCase.year == req.year)
    if req.regulation and req.regulation != "All Regulations":
        query = query.filter(LegalCase.regulation == req.regulation)
    
    # Match mult-word queries by checking if ANY of the words exist in the fields
    if req.query:
        from sqlalchemy import or_
        terms = [t.strip() for t in req.query.split() if t.strip()]
        if terms:
            conditions = []
            for term in terms:
                search_term = f"%{term}%"
                conditions.append(LegalCase.title.ilike(search_term))
                conditions.append(LegalCase.summary.ilike(search_term))
                conditions.append(LegalCase.full_text.ilike(search_term))
            query = query.filter(or_(*conditions))
    
    return query.all()

def save_research_query(db: Session, user_id: str, req: SearchQueryRequest):
    db_query = ResearchQuery(
        user_id=user_id,
        query_text=req.query,
        filters={"jurisdiction": req.jurisdiction, "year": req.year, "regulation": req.regulation}
    )
    db.add(db_query)
    db.commit()

def get_research_history(db: Session, user_id: str) -> List[ResearchQuery]:
    return db.query(ResearchQuery).filter(ResearchQuery.user_id == user_id).order_by(ResearchQuery.timestamp.desc()).all()

def save_case(db: Session, user_id: str, case_id: str, notes: Optional[str] = None):
    db_saved = SavedCase(user_id=user_id, case_id=case_id, notes=notes)
    db.add(db_saved)
    db.commit()
    return db_saved
