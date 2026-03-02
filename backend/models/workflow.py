import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean

from models.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True, default="")
    # React Flow nodes & edges stored as JSON strings
    nodes_json = Column(Text, nullable=False, default="[]")
    edges_json = Column(Text, nullable=False, default="[]")
    created_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def nodes(self):
        return json.loads(self.nodes_json) if self.nodes_json else []

    @property
    def edges(self):
        return json.loads(self.edges_json) if self.edges_json else []
