import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum

from models.database import Base

class LawfirmTask(Base):
    __tablename__ = "lawfirm_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("lawfirm_cases.id"), nullable=False)
    assigned_to = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(SAEnum("pending", "in_progress", "completed", name="task_status"), default="pending")
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
