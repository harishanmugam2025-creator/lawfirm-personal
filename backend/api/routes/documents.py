from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_permission
from models.database import get_db
from models.user import User
from schemas.document import DocumentResponse, DocumentListResponse
from services import document_service, opa_service, audit_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("documents", "upload")),
    db: Session = Depends(get_db),
):
    """Upload a PDF document. Extracts text automatically."""
    doc = await document_service.upload_document(db, file, current_user.id)
    
    audit_service.log_action(
        db,
        user=current_user,
        resource="documents",
        action="upload",
        resource_id=doc.id,
        metadata={"filename": file.filename}
    )
    return doc


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List documents. Partners/admins see all; others see only their own."""
    can_view_all = await opa_service.check_permission(
        current_user.role, "documents", "view_all"
    )
    audit_service.log_action(
        db,
        user=current_user,
        resource="documents",
        action="view_all" if can_view_all else "view_own",
        opa_input={
            "role": current_user.role,
            "resource": "documents",
            "action": "list_all",
        },
        opa_decision={"allow": bool(can_view_all)},
    )
    return document_service.list_documents(db, current_user.id, can_list_all=can_view_all)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details and extracted text of a specific document."""
    can_view_all = await opa_service.check_permission(
        current_user.role, "documents", "view_all"
    )
    audit_service.log_action(
        db,
        user=current_user,
        resource="documents",
        action="view_all" if can_view_all else "view_own",
        resource_id=document_id,
        opa_input={
            "role": current_user.role,
            "resource": "documents",
            "action": "view_all",
        },
        opa_decision={"allow": bool(can_view_all)},
    )
    return document_service.get_document(
        db, document_id, current_user.id, can_access_any=can_view_all
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document (file + database record)."""
    can_delete_any = await opa_service.check_permission(
        current_user.role, "documents", "delete_any"
    )
    audit_service.log_action(
        db,
        user=current_user,
        resource="documents",
        action="delete_any" if can_delete_any else "delete_own",
        resource_id=document_id,
        opa_input={
            "role": current_user.role,
            "resource": "documents",
            "action": "delete_any",
        },
        opa_decision={"allow": bool(can_delete_any)},
    )
    document_service.delete_document(
        db, document_id, current_user.id, can_access_any=can_delete_any
    )
