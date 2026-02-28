from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_permission
from models.database import get_db
from models.user import User
from schemas.prompt import PromptVersionCreate, PromptVersionResponse, PromptListResponse
from repositories import prompt_repository

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.post("", response_model=PromptVersionResponse, status_code=201)
async def create_prompt(
    data: PromptVersionCreate,
    current_user: User = Depends(require_permission("prompts", "create")),
    db: Session = Depends(get_db),
):
    """Create a new prompt version. Requires 'prompts/create' permission."""
    prompt = prompt_repository.create_prompt_version(
        db,
        analysis_type=data.analysis_type,
        version=data.version,
        system_prompt=data.system_prompt,
        is_active=data.is_active,
    )

    if data.is_active:
        prompt = prompt_repository.set_active_prompt(db, data.analysis_type, prompt.id)
    return prompt


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    analysis_type: str | None = None,
    current_user: User = Depends(require_permission("prompts", "view")),
    db: Session = Depends(get_db),
):
    """List all prompt versions. Requires 'prompts/view' permission."""
    if analysis_type:
        prompts = prompt_repository.get_prompts_by_type(db, analysis_type)
    else:
        prompts = prompt_repository.get_all_prompts(db)
    return {"prompts": prompts, "total": len(prompts)}


@router.put("/{prompt_id}/activate", response_model=PromptVersionResponse)
async def activate_prompt(
    prompt_id: str,
    analysis_type: str,
    current_user: User = Depends(require_permission("prompts", "update")),
    db: Session = Depends(get_db),
):
    """Set a specific prompt as active for its analysis type. Requires 'prompts/update'."""
    prompt = prompt_repository.set_active_prompt(db, analysis_type, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found.",
        )
    return prompt
