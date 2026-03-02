from models.database import Base
from models.user import User
from models.otp import OTP
from models.rbac import Role, Permission, RolePermission
from models.document import Document
from models.workflow import Workflow
from models.execution import WorkflowExecution, ExecutionStep
from models.legal_research import LegalCase, ResearchQuery, SavedCase
from models.audit import AuditLog
from models.timesheet import Timesheet
from models.lawfirm_case import LawfirmCase
from models.lawfirm_task import LawfirmTask
from models.analysis import AnalysisResult
from models.prompt import PromptVersion
from models.client import Client
from models.billing import Billing

# List all models for easy access and to ensure registration
__all__ = [
    "Base",
    "User",
    "OTP",
    "Role",
    "Permission",
    "RolePermission",
    "Document",
    "Workflow",
    "WorkflowExecution",
    "ExecutionStep",
    "LegalCase",
    "ResearchQuery",
    "SavedCase",
    "AuditLog",
    "Timesheet",
    "LawfirmCase",
    "LawfirmTask",
    "AnalysisResult",
    "PromptVersion",
    "Client",
    "Billing",
]
