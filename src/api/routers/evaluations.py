"""Verified evaluations: /projects/{project_name}/evaluations."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.deps.auth import get_current_user
from api.deps.project import get_project_or_404, verify_project_admin_or_owner
from core.auth.jwt import CurrentUser
from core.db import db_project
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/projects/{project_name}/evaluations", tags=["evaluations"])


class EvaluationCreate(BaseModel):
    """Request body for submitting a verified evaluation."""

    agent_id: Optional[int] = None
    conversation_id: Optional[int] = None
    prompt: str
    answer: str


@router.post("")
async def submit_evaluation(
    project_name: str,
    body: EvaluationCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Save a verified prompt/answer pair."""
    await run_in_threadpool(get_project_or_404, project_name)
    try:
        entry = await run_in_threadpool(
            db_project.save_evaluation,
            project_name=project_name,
            agent_id=body.agent_id,
            conversation_id=body.conversation_id,
            prompt=body.prompt,
            answer=body.answer,
            user_id=current_user.user_id,
            username=current_user.username,
        )
        return JSONResponse(entry)
    except Exception as e:
        logger.opt(exception=True).error("Failed to save evaluation for project '{}'", project_name)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_evaluations(
    project_name: str,
    agent_id: Optional[int] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get all verified evaluations for a project. Owner/admin only."""
    project = await run_in_threadpool(get_project_or_404, project_name)
    verify_project_admin_or_owner(project, current_user.user_id, current_user.ad_groups)
    entries = await run_in_threadpool(db_project.get_project_evaluations, project_name, agent_id)
    return JSONResponse({"evaluations": entries})


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    project_name: str,
    evaluation_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a single evaluation entry. Owner/admin only."""
    project = await run_in_threadpool(get_project_or_404, project_name)
    verify_project_admin_or_owner(project, current_user.user_id, current_user.ad_groups)
    try:
        await run_in_threadpool(db_project.delete_evaluation, evaluation_id, project_name)
        return JSONResponse({"status": "deleted"})
    except ValueError:
        raise HTTPException(status_code=404, detail="Evaluation not found")
