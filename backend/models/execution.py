import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy import Enum as SAEnum
from sqlalchemy.types import JSON

from models.database import Base


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)

    status = Column(
        SAEnum(
            "queued",
            "running",
            "succeeded",
            "failed",
            name="workflow_execution_status",
        ),
        nullable=False,
        default="queued",
    )

    triggered_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ExecutionStep(Base):
    __tablename__ = "execution_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(
        String,
        ForeignKey("workflow_executions.id"),
        nullable=False,
        index=True,
    )

    node_id = Column(String, nullable=False)
    node_type = Column(String, nullable=False)

    status = Column(
        SAEnum(
            "queued",
            "running",
            "succeeded",
            "failed",
            name="execution_step_status",
        ),
        nullable=False,
        default="queued",
    )

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)

    latency_seconds = Column(Float, nullable=True)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
