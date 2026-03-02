from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from models.database import Base

class LegalCase(Base):
    __tablename__ = "legal_cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    court = Column(String, nullable=False)
    jurisdiction = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    regulation = Column(String, nullable=False)  # e.g., "GDPR", "CCPA"
    summary = Column(Text, nullable=False)
    full_text = Column(Text, nullable=False)
    key_ruling = Column(Text, nullable=True)
    relevance_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ResearchQuery(Base):
    __tablename__ = "research_queries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query_text = Column(String, nullable=False)
    filters = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SavedCase(Base):
    __tablename__ = "saved_cases"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    case_id = Column(String, ForeignKey("legal_cases.id"), primary_key=True)
    notes = Column(Text, nullable=True)
    saved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
