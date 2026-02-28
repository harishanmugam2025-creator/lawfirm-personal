from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from models.database import get_db
from models.user import User
from repositories import audit_repository
from schemas.audit import AuditLogListResponse
from services import opa_service

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    limit: int = 50,
    offset: int = 0,
    resource: str | None = None,
    module: str | None = None,
    action: str | None = None,
    resource_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    can_view_all = await opa_service.check_permission(
        current_user.role, "audit_logs", "view_all"
    )
    can_view_own = await opa_service.check_permission(
        current_user.role, "audit_logs", "view_own"
    )

    if not can_view_all and not can_view_own:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: audit_logs/view_own",
        )

    logs = audit_repository.list_audit_logs(
        db,
        user_id=None if can_view_all else current_user.id,
        resource=resource,
        module=module,
        action=action,
        resource_id=resource_id,
        limit=limit,
        offset=offset,
    )
    return {"logs": logs, "total": len(logs)}
