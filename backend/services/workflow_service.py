"""Workflow business logic — validation, CRUD orchestration."""

import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories import workflow_repository
from schemas.workflow import WorkflowCreate, WorkflowUpdate
from services import audit_service

# Valid node types for the compliance workflow builder
VALID_NODE_TYPES = {
    "document_upload",
    "extract_text",
    "analyze_gdpr",
    "analyze_ccpa",
    "score_compliance",
}


def _validate_workflow(nodes: list[dict], edges: list[dict]) -> None:
    """Run structural validation on a workflow graph.

    Raises HTTPException(422) on validation failure.
    """
    errors: list[str] = []

    node_ids = {n["id"] for n in nodes}

    # Check all edge endpoints reference existing nodes
    for edge in edges:
        if edge["source"] not in node_ids:
            errors.append(f"Edge '{edge['id']}' references unknown source '{edge['source']}'")
        if edge["target"] not in node_ids:
            errors.append(f"Edge '{edge['id']}' references unknown target '{edge['target']}'")

    # Validate node types
    for node in nodes:
        node_type = node.get("type", "")
        if node_type and node_type not in VALID_NODE_TYPES:
            errors.append(f"Node '{node['id']}' has unknown type '{node_type}'")

    # An analysis node should ideally have an incoming edge (needs text input)
    analysis_types = {"analyze_gdpr", "analyze_ccpa", "score_compliance"}
    targets = {e["target"] for e in edges}
    for node in nodes:
        if node.get("type") in analysis_types and node["id"] not in targets:
            errors.append(
                f"Analysis node '{node['id']}' ({node.get('type')}) has no incoming connection"
            )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"validation_errors": errors},
        )


def create_workflow(db: Session, data: WorkflowCreate, user_id: str):
    """Create and persist a new workflow after validation."""
    nodes_dicts = [n.model_dump() for n in data.nodes]
    edges_dicts = [e.model_dump() for e in data.edges]

    _validate_workflow(nodes_dicts, edges_dicts)

    wf = workflow_repository.create_workflow(
        db,
        name=data.name,
        description=data.description,
        nodes_json=json.dumps(nodes_dicts),
        edges_json=json.dumps(edges_dicts),
        created_by=user_id,
    )
    audit_service.log_action(
        db,
        user_id=user_id,
        resource="workflow",
        action="workflow_created",
        module="Workflow Management",
        resource_id=wf.id,
        metadata={"name": wf.name}
    )
    return wf


def list_workflows(db: Session, user_id: str, *, can_view_all: bool = False):
    """List workflows. Partners/admins see all; others see their own."""
    if can_view_all:
        wfs = workflow_repository.get_all_workflows(db)
    else:
        wfs = workflow_repository.get_workflows_for_user(db, user_id)
    return {"workflows": wfs, "total": len(wfs)}


def get_workflow(
    db: Session, workflow_id: str, user_id: str, *, can_view_all: bool = False
):
    """Fetch a single workflow by ID with ownership check."""
    wf = workflow_repository.get_workflow_by_id(db, workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )
    if not can_view_all and wf.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )
    return wf


def update_workflow(
    db: Session,
    workflow_id: str,
    data: WorkflowUpdate,
    user_id: str,
    *,
    can_manage_all: bool = False,
):
    """Update an existing workflow. Only the creator (or manager) can update."""
    wf = workflow_repository.get_workflow_by_id(db, workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )
    
    if not can_manage_all and wf.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    update_kwargs = {}
    if data.name is not None:
        update_kwargs["name"] = data.name
    if data.description is not None:
        update_kwargs["description"] = data.description
    if data.is_active is not None:
        update_kwargs["is_active"] = data.is_active
    if data.nodes is not None:
        nodes_dicts = [n.model_dump() for n in data.nodes]
        edges_dicts = (
            [e.model_dump() for e in data.edges]
            if data.edges is not None
            else wf.edges
        )
        _validate_workflow(nodes_dicts, edges_dicts)
        update_kwargs["nodes_json"] = json.dumps(nodes_dicts)
    if data.edges is not None:
        edges_dicts = [e.model_dump() for e in data.edges]
        update_kwargs["edges_json"] = json.dumps(edges_dicts)

    updated_wf = workflow_repository.update_workflow(db, wf, **update_kwargs)

    audit_service.log_action(
        db,
        user_id=user_id,
        resource="workflow",
        action="workflow_updated",
        module="Workflow Management",
        resource_id=workflow_id,
        metadata={"updated_fields": list(update_kwargs.keys())}
    )
    return updated_wf


def delete_workflow(db: Session, workflow_id: str, user_id: str, *, can_manage_all: bool = False):
    """Delete a workflow. Only the creator (or manager) can delete."""
    wf = workflow_repository.get_workflow_by_id(db, workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )
    
    if not can_manage_all and wf.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )
    workflow_repository.delete_workflow(db, wf)

    audit_service.log_action(
        db,
        user_id=user_id,
        resource="workflow",
        action="workflow_deleted",
        module="Workflow Management",
        resource_id=workflow_id,
        metadata={"name": wf.name}
    )
