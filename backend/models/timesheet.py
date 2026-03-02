import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float

from models.database import Base

class Timesheet(Base):
    __tablename__ = "timesheets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(String, ForeignKey("lawfirm_cases.id"), nullable=False)
    hours = Column(Float, nullable=False)
    revenue_generated = Column(Float, nullable=False, default=0.0) # Calculated based on hours * rate
    billable = Column(Integer, default=1) # 1 for True, 0 for False (for broader compatibility)
    month = Column(String, nullable=False) # e.g., 'Feb 2026' or '2026-02'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
