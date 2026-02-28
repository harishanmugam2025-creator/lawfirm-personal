from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_permission
from models.database import get_db
from models.user import User
from schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
)
from services import workflow_service, opa_service, execution_service, audit_service
from schemas.execution import ExecutionResponse

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    current_user: User = Depends(require_permission("workflows", "create")),
    db: Session = Depends(get_db),
):
    """Create a new compliance workflow. Requires 'workflows/create' permission."""
    workflow = workflow_service.create_workflow(db, data, current_user.id)
    
    audit_service.log_action(
        db,
        user=current_user,
        resource="workflows",
        action="create",
        resource_id=workflow.id,
        metadata={"name": workflow.name}
    )
    return workflow


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List workflows. Partners/admins see all; others see only their own."""
    can_view_all = await opa_service.check_permission(
        current_user.role, "workflows", "view_all"
    )
    audit_service.log_action(
        db,
        user=current_user,
        resource="workflows",
        action="view_all" if can_view_all else "view_own",
        opa_input={
            "role": current_user.role,
            "resource": "workflows",
            "action": "view_all",
        },
        opa_decision={"allow": bool(can_view_all)},
    )
    return workflow_service.list_workflows(db, current_user.id, can_view_all=can_view_all)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific workflow by ID."""
    can_view_all = await opa_service.check_permission(
        current_user.role, "workflows", "view_all"
    )
    audit_service.log_action(
        db,
        user=current_user,
        resource="workflows",
        action="view_all" if can_view_all else "view_own",
        resource_id=workflow_id,
        opa_input={
            "role": current_user.role,
            "resource": "workflows",
            "action": "view_all",
        },
        opa_decision={"allow": bool(can_view_all)},
    )
    return workflow_service.get_workflow(
        db, workflow_id, current_user.id, can_view_all=can_view_all
    )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    data: WorkflowUpdate,
    current_user: User = Depends(require_permission("workflows", "create")),
    db: Session = Depends(get_db),
):
    """Update an existing workflow. Only the creator can update."""
    workflow = workflow_service.update_workflow(db, workflow_id, data, current_user.id)
    
    audit_service.log_action(
        db,
        user=current_user,
        resource="workflows",
        action="edit",
        resource_id=workflow_id,
        metadata={"name_changed": data.name is not None}
    )
    return workflow


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(require_permission("workflows", "delete")),
    db: Session = Depends(get_db),
):
    """Delete a workflow. Requires 'workflows/delete' permission."""
    workflow_service.delete_workflow(db, workflow_id, current_user.id)
    
    audit_service.log_action(
        db,
        user=current_user,
        resource="workflows",
        action="delete",
        resource_id=workflow_id
    )


@router.post("/{workflow_id}/execute", response_model=ExecutionResponse, status_code=201)
async def execute_workflow(
    workflow_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("workflows", "execute")),
    db: Session = Depends(get_db),
):
    """Execute a workflow by uploading a PDF through the workflow engine."""
    result = await execution_service.execute_workflow(db, workflow_id, file, current_user.id)
    
    audit_service.log_action(
        db,
        user=current_user,
        resource="workflows",
        action="execute",
        resource_id=workflow_id,
        metadata={"filename": file.filename}
    )
    execution = result["execution"]
    steps = result["steps"]
    return {
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "document_id": execution.document_id,
        "status": execution.status,
        "triggered_by": execution.triggered_by,
        "started_at": execution.started_at,
        "finished_at": execution.finished_at,
        "error_message": execution.error_message,
        "created_at": execution.created_at,
        "steps": steps,
    }
