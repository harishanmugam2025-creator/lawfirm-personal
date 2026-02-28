"""
RBAC API Routes — Role & Permission management.
IT Admin can edit; all authenticated users can view.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_permission
from models.database import get_db
from models.user import User
from schemas.rbac import (
    RolesListResponse,
    RolePermissionsResponse,
    BulkPermissionUpdate,
)
from services import rbac_service, audit_service

router = APIRouter(prefix="/rbac", tags=["RBAC Policies"])


@router.get("/roles", response_model=RolesListResponse)
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all roles. Any authenticated user can view."""
    return rbac_service.list_roles(db)


@router.get("/permissions")
async def list_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all permissions grouped by module."""
    return rbac_service.list_permissions_grouped(db)


@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get permission matrix for a specific role."""
    return rbac_service.get_role_permissions(db, role_id)


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: str,
    data: BulkPermissionUpdate,
    current_user: User = Depends(require_permission("system_config", "manage")),
    db: Session = Depends(get_db),
):
    """Update permissions for a role. IT Admin only."""
    result = rbac_service.update_role_permissions(
        db, role_id, data, current_user.id
    )

    # Build change summary for audit
    changes = {
        p.permission_id: p.allowed for p in data.permissions
    }

    audit_service.log_action(
        db,
        user=current_user,
        resource="rbac",
        action="update_role_permissions",
        resource_id=role_id,
        opa_input={
            "role": current_user.role,
            "resource": "system_config",
            "action": "manage",
        },
        opa_decision={"allow": True},
        metadata={
            "target_role": result["role"].name,
            "permissions_changed": len(changes),
        },
    )
    return result
