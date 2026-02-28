from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from models.database import get_db
from models.user import User
from repositories import execution_repository
from schemas.execution import ExecutionResponse, ExecutionListResponse
from services import opa_service, audit_service

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    execution = execution_repository.get_execution_by_id(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found.",
        )

    can_view_all = await opa_service.check_permission(
        current_user.role, "workflows", "view_all"
    )
    if not can_view_all and execution.triggered_by != current_user.id:
        audit_service.log_action(
            db,
            user=current_user,
            resource="executions",
            action="view_denied",
            resource_id=execution_id,
            opa_input={
                "role": current_user.role,
                "resource": "workflows",
                "action": "view_all",
            },
            opa_decision={"allow": False},
            metadata={"reason": "not_owner"},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found.",
        )

    steps = execution_repository.list_steps_for_execution(db, execution.id)
    audit_service.log_action(
        db,
        user=current_user,
        resource="executions",
        action="view",
        resource_id=execution_id,
        opa_input={
            "role": current_user.role,
            "resource": "workflows",
            "action": "view_all",
        },
        opa_decision={"allow": bool(can_view_all)},
    )
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


@router.get("/workflow/{workflow_id}", response_model=ExecutionListResponse)
async def list_executions_for_workflow(
    workflow_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Basic permission gate (fine-grained checks can be expanded later)
    allowed = await opa_service.check_permission(current_user.role, "workflows", "view_own")
    if not allowed:
        audit_service.log_action(
            db,
            user=current_user,
            resource="executions",
            action="list_denied",
            resource_id=workflow_id,
            opa_input={
                "role": current_user.role,
                "resource": "workflows",
                "action": "view_own",
            },
            opa_decision={"allow": False},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: workflows/view_own",
        )

    executions = execution_repository.list_executions_for_workflow(db, workflow_id, limit=limit)
    can_view_all = await opa_service.check_permission(
        current_user.role, "workflows", "view_all"
    )

    if not can_view_all:
        executions = [e for e in executions if e.triggered_by == current_user.id]

    audit_service.log_action(
        db,
        user=current_user,
        resource="executions",
        action="list",
        resource_id=workflow_id,
        opa_input={
            "role": current_user.role,
            "resource": "workflows",
            "action": "view_all",
        },
        opa_decision={"allow": bool(can_view_all)},
        metadata={"limit": limit},
    )
    return {"executions": executions, "total": len(executions)}
