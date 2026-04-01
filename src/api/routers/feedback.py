"""Message feedback: /projects/{project_name}/feedback."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.deps.auth import get_current_user
from api.deps.project import get_project_or_404, verify_project_admin_or_owner
from core.auth.jwt import CurrentUser
from core.db import db_project
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/projects/{project_name}/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    agent_id: Optional[int] = None
    utterance: Optional[str] = None
    feedback_type: str  # "good" or "bad"
    comments: Optional[str] = None


@router.post("")
async def submit_feedback(
    project_name: str,
    body: FeedbackCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Submit good/bad feedback for an assistant message."""
    get_project_or_404(project_name)
    if body.feedback_type not in ("good", "bad"):
        return JSONResponse(status_code=400, content={"detail": "feedback_type must be 'good' or 'bad'"})
    try:
        entry = db_project.save_feedback(
            project_name=project_name,
            agent_id=body.agent_id,
            user_id=current_user.user_id,
            username=current_user.username,
            utterance=body.utterance,
            feedback_type=body.feedback_type,
            comments=body.comments,
        )
        return JSONResponse(entry)
    except Exception as e:
        logger.opt(exception=True).error("Failed to save feedback for project '{}'", project_name)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_feedback(
    project_name: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get all feedback for a project. Owner/admin only."""
    project = get_project_or_404(project_name)
    verify_project_admin_or_owner(project, current_user.user_id, current_user.ad_groups)
    entries = db_project.get_project_feedback(project_name)
    return JSONResponse({"feedback": entries})
