import os
import uuid
import io
from pathlib import Path

import pdfplumber
import boto3
from botocore.client import Config
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config import settings
from repositories import document_repository
from services import audit_service
import logging

logger = logging.getLogger(__name__)

# MinIO Client Initialization
s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

def ensure_bucket_exists():
    try:
        s3_client.head_bucket(Bucket=settings.MINIO_BUCKET)
    except:
        s3_client.create_bucket(Bucket=settings.MINIO_BUCKET)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def upload_document(db: Session, file: UploadFile, user_id: str):
    """Validate, save to MinIO, extract text, and persist metadata."""

    # --- Validate content type ---
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    # --- Read file bytes & enforce size limit ---
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    # --- Save to MinIO or Local Fallback ---
    file_id = str(uuid.uuid4())
    object_key = f"{user_id}/{file_id}.pdf"
    
    try:
        ensure_bucket_exists()
        s3_client.put_object(
            Bucket=settings.MINIO_BUCKET,
            Key=object_key,
            Body=contents,
            ContentType=file.content_type
        )
        storage_type = "minio"
    except Exception as e:
        # Fallback to local storage if MinIO is unavailable (e.g., on Render)
        logger.warning(f"MinIO upload failed, falling back to local storage: {e}")
        local_dir = Path("uploads") / user_id
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / f"{file_id}.pdf"
        with open(local_path, "wb") as f:
            f.write(contents)
        object_key = str(local_path)
        storage_type = "local"

    # --- Extract text with pdfplumber (using memory stream) ---
    extracted_text = ""
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
    except Exception:
        extracted_text = "[Text extraction failed]"

    # --- Persist to database ---
    doc = document_repository.create_document(
        db,
        id=file_id,
        filename=file.filename or "unnamed.pdf",
        content_type=file.content_type,
        size_bytes=len(contents),
        extracted_text=extracted_text.strip() or None,
        disk_path=object_key, # Store S3 key instead of disk path
        uploaded_by=user_id,
    )
    audit_service.log_action(
        db,
        user_id=user_id,
        resource="document",
        action="document_upload",
        module="Document Management",
        resource_id=doc.id,
        metadata={"filename": doc.filename, "size_bytes": doc.size_bytes, "storage": "minio"}
    )
    return doc


def list_documents(db: Session, user_id: str, *, can_list_all: bool = False):
    """Return documents. If *can_list_all* is True, return every document;
    otherwise only those belonging to *user_id*."""
    if can_list_all:
        docs = document_repository.get_all_documents(db)
    else:
        docs = document_repository.get_documents_for_user(db, user_id)
    return {"documents": docs, "total": len(docs)}


def get_document(
    db: Session,
    document_id: str,
    user_id: str,
    *,
    can_access_any: bool = False,
):
    """Get a single document. Ownership is enforced unless *can_access_any*."""
    doc = document_repository.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    if not can_access_any and doc.uploaded_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return doc


def delete_document(
    db: Session,
    document_id: str,
    user_id: str,
    *,
    can_access_any: bool = False,
):
    """Delete a document from MinIO and database."""
    doc = document_repository.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    if not can_access_any and doc.uploaded_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Remove file from MinIO or Local Storage
    try:
        s3_client.delete_object(Bucket=settings.MINIO_BUCKET, Key=doc.disk_path)
    except Exception as e:
        logger.warning(f"S3 Delete Error (might be local file): {e}")
    
    # Also attempt to delete locally if it was saved via fallback
    local_path = Path(doc.disk_path)
    if local_path.exists() and local_path.is_file():
        try:
            local_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete local file: {e}")

    document_repository.delete_document(db, doc)

    audit_service.log_action(
        db,
        user_id=user_id,
        resource="document",
        action="document_delete",
        module="Document Management",
        resource_id=document_id,
        metadata={"filename": doc.filename, "storage": "minio"}
    )
