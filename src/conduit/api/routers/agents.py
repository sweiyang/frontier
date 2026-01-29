"""Agents: /projects/{project}/agents."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from conduit.api.deps.auth import get_current_user
from conduit.api.deps.project import get_project_or_404, verify_project_owner
from conduit.api.schema import AgentCreate, AgentUpdate
from conduit.core.auth.jwt import CurrentUser
from conduit.core.db import db_project

router = APIRouter(prefix="/projects/{project_name}/agents", tags=["agents"])


@router.get("")
async def list_agents(
    project_name: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all agents for a project."""
    project = get_project_or_404(project_name)
    agents = db_project.list_agents_for_project(project["id"])
    return JSONResponse({"agents": agents})


@router.post("")
async def create_agent(
    project_name: str,
    request: AgentCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new agent for a project."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    agent = db_project.create_agent(
        project_id=project["id"],
        name=request.name,
        endpoint=request.endpoint,
        connection_type=request.connection_type,
        is_default=request.is_default,
        extras=request.extras,
        auth=request.auth,
    )
    return JSONResponse(agent)


@router.put("/{agent_id}")
async def update_agent(
    project_name: str,
    agent_id: int,
    request: AgentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an agent."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    agent = db_project.get_agent_by_id(agent_id)
    if not agent or agent["project_id"] != project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")

    updated_agent = db_project.update_agent(
        agent_id=agent_id,
        name=request.name,
        endpoint=request.endpoint,
        connection_type=request.connection_type,
        is_default=request.is_default,
        extras=request.extras,
        auth=request.auth,
    )
    return JSONResponse(updated_agent)


@router.delete("/{agent_id}")
async def delete_agent(
    project_name: str,
    agent_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an agent."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    agent = db_project.get_agent_by_id(agent_id)
    if not agent or agent["project_id"] != project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_project.delete_agent(agent_id)
    return JSONResponse({"success": True})
