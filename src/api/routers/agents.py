"""Agents: /projects/{project}/agents."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.project import require_project_member, verify_project_owner, ProjectAccessContext
from api.schema import AgentCreate, AgentUpdate
from core.db import db_project

router = APIRouter(prefix="/projects/{project_name}/agents", tags=["agents"])


@router.get("")
async def list_agents(
    project_name: str,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """List all agents for a project."""
    # ctx.project is guaranteed to exist and user is verified as member
    agents = db_project.list_agents_for_project(ctx.project["id"])
    return JSONResponse({"agents": agents})


@router.post("")
async def create_agent(
    project_name: str,
    request: AgentCreate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Create a new agent for a project."""
    verify_project_owner(ctx.project, ctx.user.user_id if ctx.user else None)

    agent = db_project.create_agent(
        project_id=ctx.project["id"],
        name=request.name,
        endpoint=request.endpoint,
        connection_type=request.connection_type,
        is_default=request.is_default,
        extras=request.extras,
        auth=request.auth,
        icon=_process_icon(request.icon) if request.icon else None,
    )
    return JSONResponse(agent)


@router.put("/{agent_id}")
async def update_agent(
    project_name: str,
    agent_id: int,
    request: AgentUpdate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Update an agent."""
    verify_project_owner(ctx.project, ctx.user.user_id if ctx.user else None)

    agent = db_project.get_agent_by_id(agent_id)
    if not agent or agent["project_id"] != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")

    updated_agent = db_project.update_agent(
        agent_id=agent_id,
        name=request.name,
        endpoint=request.endpoint,
        connection_type=request.connection_type,
        is_default=request.is_default,
        extras=request.extras,
        auth=request.auth,
        icon=_process_icon(request.icon) if request.icon else None,
    )
    return JSONResponse(updated_agent)


@router.delete("/{agent_id}")
async def delete_agent(
    project_name: str,
    agent_id: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Delete an agent."""
    verify_project_owner(ctx.project, ctx.user.user_id if ctx.user else None)

    agent = db_project.get_agent_by_id(agent_id)
    if not agent or agent["project_id"] != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_project.delete_agent(agent_id)
    return JSONResponse({"success": True})


def _process_icon(icon_data: str) -> str:
    """Process base64 icon data and save to file."""
    import base64
    import os
    import uuid
    import re

    if not icon_data or not icon_data.startswith("data:image"):
        return icon_data

    try:
        # Extract format and data
        match = re.search(r"data:image/(.*?);base64,(.*)", icon_data)
        if not match:
            return icon_data

        ext = match.group(1)
        data = match.group(2)
        
        # Map common extensions
        if ext == "jpeg":
            ext = "jpg"
        elif ext == "svg+xml":
            ext = "svg"

        # Generate filename
        filename = f"agent_{uuid.uuid4()}.{ext}"
        
        # Define uploads path (relative to this file -> ../../data/uploads)
        # Verify this matches the main.py mount logic
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        uploads_dir = os.path.join(base_dir, "data", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        file_path = os.path.join(uploads_dir, filename)

        # Write file
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(data))

        # Return publicly accessible URL
        return f"/uploads/{filename}"

    except Exception as e:
        print(f"Error processing icon: {e}")
        return icon_data  # Fallback to original string if error
