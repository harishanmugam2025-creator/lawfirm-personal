import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey

from models.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False, default="application/pdf")
    size_bytes = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=True)
    disk_path = Column(String, nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
