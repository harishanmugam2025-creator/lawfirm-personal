"""
Compliance Analysis API Routes
POST /analyze-document  — Trigger GDPR/CCPA analysis on an existing document.
GET  /analysis/{document_id} — Retrieve the latest compliance result for a document.
"""

import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_permission
from models.database import get_db
from models.user import User
from repositories import analysis_repository, document_repository
from schemas.analysis import ComplianceAnalysisResponse
from services import ollama_service, compliance_scoring, pdf_extractor
from services import opa_service, audit_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Compliance Analysis"])


@router.post("/analyze-document", response_model=ComplianceAnalysisResponse, status_code=201)
async def analyze_document(
    document_id: str,
    workflow_id: str | None = None,
    current_user: User = Depends(require_permission("documents", "view_own")),
    db: Session = Depends(get_db),
):
    """
    Trigger a full GDPR/CCPA compliance analysis on an existing uploaded document.

    Workflow:
    1. Fetch the document from the database.
    2. Extract text (use stored text or re-extract from disk).
    3. Send text to Ollama for AI analysis.
    4. Apply the compliance scoring engine.
    5. Persist results in the database.
    6. Return the compliance report.
    """
    # 1. Verify the user can access this document
    can_view_all = await opa_service.check_permission(
        current_user.role, "documents", "view_all"
    )
    doc = document_repository.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    if not can_view_all and doc.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # 2. Get the document text
    doc_text = doc.extracted_text
    if not doc_text:
        # Try re-extracting from disk
        try:
            doc_text = pdf_extractor.extract_text_from_pdf(doc.disk_path)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot extract text from document: {exc}",
            )

    # Log the analysis start
    logger.info("Starting compliance analysis for document %s (%s)", doc.id, doc.filename)
    audit_service.log_action(
        db,
        user=current_user,
        resource="compliance_analysis",
        action="analyze",
        resource_id=doc.id,
        opa_input={"role": current_user.role, "resource": "documents", "action": "view_own"},
        opa_decision={"allow": True},
    )

    # 3. Send to Ollama for AI analysis
    start_time = time.monotonic()
    ai_result = await ollama_service.analyze_document_compliance(doc_text)
    
    # 4. Apply the compliance scoring engine
    scored_result = compliance_scoring.calculate_compliance_score(ai_result)
    latency = time.monotonic() - start_time

    logger.info(
        "Compliance analysis complete for %s — Score: %d, GDPR: %s, CCPA: %s (%.2fs)",
        doc.filename, scored_result["score"], scored_result["gdpr_status"],
        scored_result["ccpa_status"], latency,
    )

    # 5. Persist the result
    result = analysis_repository.create_compliance_result(
        db,
        document_id=doc.id,
        analyzed_by=current_user.id,
        compliance_data=scored_result,
        latency_seconds=latency,
        workflow_id=workflow_id,
    )

    # Track processing metric
    from services.metrics_service import DOCUMENTS_PROCESSED
    DOCUMENTS_PROCESSED.inc()

    # 6. Return response
    return ComplianceAnalysisResponse(
        id=result.id,
        document_id=result.document_id,
        workflow_id=result.workflow_id,
        document_name=doc.filename,
        gdpr_status=result.gdpr_status,
        ccpa_status=result.ccpa_status,
        score=result.score,
        detected_sections=json.loads(result.detected_sections) if result.detected_sections else [],
        missing_sections=json.loads(result.missing_sections) if result.missing_sections else [],
        ai_suggestions=json.loads(result.ai_suggestions) if result.ai_suggestions else [],
        analyzed_by=result.analyzed_by,
        created_at=result.created_at,
    )


@router.get("/analysis/{document_id}", response_model=ComplianceAnalysisResponse)
async def get_analysis(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch the latest compliance analysis result for a document."""
    # Verify access
    can_view_all = await opa_service.check_permission(
        current_user.role, "documents", "view_all"
    )
    doc = document_repository.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    if not can_view_all and doc.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Fetch the latest compliance result
    result = analysis_repository.get_latest_compliance_for_document(db, document_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No compliance analysis found for this document.",
        )

    return ComplianceAnalysisResponse(
        id=result.id,
        document_id=result.document_id,
        workflow_id=result.workflow_id,
        document_name=doc.filename,
        gdpr_status=result.gdpr_status or "FAIL",
        ccpa_status=result.ccpa_status or "FAIL",
        score=result.score or 0,
        detected_sections=json.loads(result.detected_sections) if result.detected_sections else [],
        missing_sections=json.loads(result.missing_sections) if result.missing_sections else [],
        ai_suggestions=json.loads(result.ai_suggestions) if result.ai_suggestions else [],
        analyzed_by=result.analyzed_by,
        created_at=result.created_at,
    )
