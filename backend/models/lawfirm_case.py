import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from models.database import Base

class LawfirmCase(Base):
    __tablename__ = "lawfirm_cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    assigned_to = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(SAEnum("open", "closed", "on_hold", "under_review", "in_litigation", "pending_documents", "delayed", name="case_status"), default="open")
    case_type = Column(String, default="Civil")  # e.g., Civil, Criminal, Corporate
    jurisdiction = Column(String, nullable=True)
    risk_level = Column(SAEnum("low", "medium", "high", name="risk_level"), default="low")
    risk_reason = Column(String, nullable=True)
    outcome = Column(SAEnum("success", "settled", "dismissed", "failed", name="case_outcome"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # Relationships can be defined if needed, though mostly using raw foreign keys for analytics
