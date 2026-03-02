"""
User Management Service — IT Admin only operations.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from services import audit_service
from repositories import user_repository
from schemas.auth import AdminUserCreate, AdminUserUpdate
from services.auth_service import hash_password
from services.email_service import email_service
from models.legal_research import SavedCase, ResearchQuery
from models.document import Document
from models.lawfirm_case import LawfirmCase
from models.lawfirm_task import LawfirmTask
from models.timesheet import Timesheet
from models.workflow import Workflow
from models.execution import WorkflowExecution
from models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


def list_users(db: Session) -> dict:
    """List all users in the system."""
    users = user_repository.get_all_users(db)
    return {"users": users, "total": len(users)}


def admin_create_user(db: Session, data: AdminUserCreate, created_by: str):
    """
    Admin creates a new user with an assigned role.
    Users cannot choose their own role during registration.
    """
    existing = user_repository.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    hashed = hash_password(data.password)
    user = user_repository.create_user_admin(
        db,
        name=data.name,
        email=data.email,
        hashed_password=hashed,
        role=data.role.value,
    )

    logger.info(
        "Admin %s created user %s (%s) with role %s",
        created_by, user.id, user.email, user.role,
    )

    audit_service.log_action(
        db,
        user_id=created_by,
        resource="user",
        action="user_created",
        module="User Management",
        resource_id=user.id,
        metadata={"email": user.email, "role": user.role}
    )

    # Send welcome email with credentials
    email_service.send_welcome_email(user.email, data.password, user.role)

    return user


def admin_update_user(db: Session, user_id: str, data: AdminUserUpdate, updated_by: str):
    """
    Admin updates a user's name, role, or resets their password.
    """
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    updates = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.role is not None:
        updates["role"] = data.role.value
    if data.password is not None:
        updates["hashed_password"] = hash_password(data.password)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )

    user = user_repository.update_user(db, user, **updates)

    logger.info(
        "Admin %s updated user %s — fields: %s",
        updated_by, user_id, list(updates.keys()),
    )

    audit_service.log_action(
        db,
        user_id=updated_by,
        resource="user",
        action="user_updated",
        module="User Management",
        resource_id=user_id,
        metadata={"fields": list(updates.keys())}
    )
    return user


def admin_deactivate_user(db: Session, user_id: str, deactivated_by: str):
    """Deactivate a user account. IT Admin cannot deactivate themselves."""
    if user_id == deactivated_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account.",
        )

    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deactivated.",
        )

    user = user_repository.deactivate_user(db, user)

    logger.info("Admin %s deactivated user %s (%s)", deactivated_by, user_id, user.email)

    audit_service.log_action(
        db,
        user_id=deactivated_by,
        resource="user",
        action="user_deactivated",
        module="User Management",
        resource_id=user_id,
        metadata={"email": user.email}
    )
    return user


def admin_activate_user(db: Session, user_id: str, activated_by: str):
    """Activate a user account."""
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active.",
        )

    user = user_repository.activate_user(db, user)

    logger.info("Admin %s activated user %s (%s)", activated_by, user_id, user.email)

    audit_service.log_action(
        db,
        user_id=activated_by,
        resource="user",
        action="user_activated",
        module="User Management",
        resource_id=user_id,
        metadata={"email": user.email}
    )
    return user


def admin_delete_user(db: Session, user_id: str, deleted_by: str):
    """Permanently delete a user account. IT Admin cannot delete themselves."""
    if user_id == deleted_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account.",
        )

    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user_email = user.email
    
    # Manually delete related records to support databases without CASCADE constraints
    try:
        db.query(SavedCase).filter(SavedCase.user_id == user_id).delete()
        db.query(ResearchQuery).filter(ResearchQuery.user_id == user_id).delete()
        db.query(Document).filter(Document.uploaded_by == user_id).delete()
        db.query(LawfirmCase).filter(LawfirmCase.assigned_to == user_id).delete()
        db.query(LawfirmTask).filter(LawfirmTask.assigned_to == user_id).delete()
        db.query(Timesheet).filter(Timesheet.user_id == user_id).delete()
        db.query(WorkflowExecution).filter(WorkflowExecution.triggered_by == user_id).delete()
        db.query(Workflow).filter(Workflow.created_by == user_id).delete()
        db.query(AnalysisResult).filter(AnalysisResult.analyzed_by == user_id).delete()
        
        db.commit() # Commit deletions before deleting the user
    except Exception as e:
        db.rollback()
        logger.error("Failed to delete related records for user %s: %s", user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clean up user data: {str(e)}"
        )

    user_repository.delete_user(db, user)

    logger.info("Admin %s deleted user %s (%s)", deleted_by, user_id, user_email)

    audit_service.log_action(
        db,
        user_id=deleted_by,
        resource="user",
        action="user_deleted",
        module="User Management",
        resource_id=user_id,
        metadata={"email": user_email}
    )
