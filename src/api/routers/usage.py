"""Project usage: /projects/{project}/usage."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
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
    project = await run_in_threadpool(get_project_or_404, project_name)

    projects = await run_in_threadpool(db_project.list_projects_for_user, current_user.user_id, current_user.ad_groups)
    if not any(p["project_id"] == project["project_id"] for p in projects):
        raise HTTPException(status_code=403, detail="Access denied to this project")

    usage_stats = await run_in_threadpool(db_project.get_project_usage_by_agent, project_name)
    return JSONResponse(usage_stats)


@router.get("/details")
async def get_project_usage_details(
    project_name: str,
    agent_id: Optional[int] = Query(None),
    month: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get per-user usage details filtered by agent and month."""
    project = await run_in_threadpool(get_project_or_404, project_name)
    project_id = project["project_id"]

    # Verify access
    projects = await run_in_threadpool(db_project.list_projects_for_user, current_user.user_id, current_user.ad_groups)
    if not any(p["project_id"] == project_id for p in projects):
        raise HTTPException(status_code=403, detail="Access denied to this project")

    # Determine accessible agents based on role
    role = await run_in_threadpool(db_project.get_user_role_in_project, current_user.user_id, project_id)

    all_agents = await run_in_threadpool(db_project.list_agents_for_project, project["id"])

    if role in ("owner", "admin"):
        accessible_agents = [{"id": a["id"], "name": a["name"]} for a in all_agents]
    else:
        allowed_ids = await run_in_threadpool(
            db_project.get_accessible_agent_ids_for_user,
            project["id"],
            current_user.user_id,
            current_user.ad_groups,
        )
        if allowed_ids:
            accessible_agents = [{"id": a["id"], "name": a["name"]} for a in all_agents if a["id"] in allowed_ids]
        else:
            # No specific permissions set — grant access to all agents
            accessible_agents = [{"id": a["id"], "name": a["name"]} for a in all_agents]

    # Validate requested agent_id is accessible
    accessible_ids = {a["id"] for a in accessible_agents}
    if agent_id and agent_id not in accessible_ids:
        raise HTTPException(status_code=403, detail="Access denied to this agent")

    # Fetch per-user usage
    usage = await run_in_threadpool(db_project.get_project_usage_by_user, project_name, agent_id, month)

    return JSONResponse(
        {
            "accessible_agents": accessible_agents,
            "users": usage["users"],
            "months": usage["months"],
        }
    )
