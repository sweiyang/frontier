"""Project usage: /projects/{project}/usage."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.auth import get_current_user
from api.deps.project import get_project_or_404
from core.auth.jwt import CurrentUser
from core.db import db_project

router = APIRouter(prefix="/projects/{project_name}/usage", tags=["usage"])


@router.get("")
async def get_project_usage(
    project_name: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get usage statistics for a project grouped by agent."""
    project = get_project_or_404(project_name)

    projects = db_project.list_projects_for_user(
        current_user.user_id, current_user.ad_groups
    )
    if not any(p["project_id"] == project["project_id"] for p in projects):
        raise HTTPException(status_code=403, detail="Access denied to this project")

    usage_stats = db_project.get_project_usage_by_agent(project_name)
    return JSONResponse(usage_stats)
