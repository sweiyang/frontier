"""Agents: /projects/{project}/agents."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from api.deps.project import (
    ProjectAccessContext,
    require_project_member,
    verify_project_admin_or_owner,
)
from api.schema import AgentCreate, AgentUpdate
from core.approval import create_change_request, is_approval_required
from core.approval.version_service import create_agent_version
from core.db import db_project
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/projects/{project_name}/agents", tags=["agents"])


@router.get("")
async def list_agents(
    project_name: str,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """List all agents for a project."""
    # ctx.project is guaranteed to exist and user is verified as member
    agents = await run_in_threadpool(db_project.list_agents_for_project, ctx.project["id"])
    return JSONResponse({"agents": agents})


@router.post("")
async def create_agent(
    project_name: str,
    request: AgentCreate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Create a new agent for a project."""
    if not ctx.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    verify_project_admin_or_owner(ctx.project, ctx.user.user_id, ctx.user.ad_groups)

    payload = {
        "name": request.name,
        "endpoint": request.endpoint,
        "connection_type": request.connection_type,
        "is_default": request.is_default,
        "extras": request.extras,
        "auth": request.auth,
        "icon": _process_icon(request.icon) if request.icon else None,
        "is_artefact": request.is_artefact,
        "approval_required": request.approval_required,
    }

    if await run_in_threadpool(is_approval_required, ctx.project["id"], agent_data=payload):
        cr = await run_in_threadpool(
            create_change_request,
            project_id=ctx.project["id"],
            request_type="create",
            payload=payload,
            requested_by=ctx.user.user_id,
        )
        return JSONResponse(
            {
                "status": "pending_approval",
                "change_request": cr,
                "message": "Agent creation requires approval",
            }
        )

    agent = await run_in_threadpool(
        db_project.create_agent,
        project_id=ctx.project["id"],
        name=payload["name"],
        endpoint=payload["endpoint"],
        connection_type=payload["connection_type"],
        is_default=payload["is_default"],
        extras=payload["extras"],
        auth=payload["auth"],
        icon=payload["icon"],
        is_artefact=payload["is_artefact"],
        description=payload.get("description"),
        approval_required=payload.get("approval_required", False),
    )

    await run_in_threadpool(create_agent_version, agent["id"], ctx.user.user_id)

    return JSONResponse(agent)


@router.put("/{agent_id}")
async def update_agent(
    project_name: str,
    agent_id: int,
    request: AgentUpdate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Update an agent."""
    if not ctx.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    verify_project_admin_or_owner(ctx.project, ctx.user.user_id, ctx.user.ad_groups)

    agent = await run_in_threadpool(db_project.get_agent_by_id, agent_id)
    if not agent or agent["project_id"] != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")

    payload = {
        "name": request.name,
        "endpoint": request.endpoint,
        "connection_type": request.connection_type,
        "is_default": request.is_default,
        "extras": request.extras,
        "auth": request.auth,
        "icon": _process_icon(request.icon) if request.icon else None,
        "is_artefact": request.is_artefact,
        "description": request.description,
        "approval_required": request.approval_required,
    }

    # Check existing agent's approval_required field
    needs_approval = await run_in_threadpool(is_approval_required, ctx.project["id"], agent_data=agent)
    logger.info(f"Agent update - needs_approval: {needs_approval}, project_id: {ctx.project['id']}, agent_id: {agent_id}")

    if needs_approval:
        # Create change request and return - DO NOT update agent
        cr = await run_in_threadpool(
            create_change_request,
            project_id=ctx.project["id"],
            request_type="update",
            payload=payload,
            requested_by=ctx.user.user_id,
            agent_id=agent_id,
        )
        logger.info(f"Change request created: {cr['id']}, returning pending_approval response")
        return JSONResponse(
            {
                "status": "pending_approval",
                "change_request": cr,
                "message": "Agent update requires approval",
            }
        )

    # Only reach here if approval is NOT required
    logger.info(f"No approval required, updating agent directly")
    await run_in_threadpool(create_agent_version, agent_id, ctx.user.user_id)

    updated_agent = await run_in_threadpool(
        db_project.update_agent,
        agent_id=agent_id,
        name=payload["name"],
        endpoint=payload["endpoint"],
        connection_type=payload["connection_type"],
        is_default=payload["is_default"],
        extras=payload["extras"],
        auth=payload["auth"],
        icon=payload["icon"],
        is_artefact=payload["is_artefact"],
        description=payload.get("description"),
        approval_required=payload.get("approval_required"),
    )
    return JSONResponse(updated_agent)


@router.delete("/{agent_id}")
async def delete_agent(
    project_name: str,
    agent_id: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Delete an agent."""
    if not ctx.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    verify_project_admin_or_owner(ctx.project, ctx.user.user_id, ctx.user.ad_groups)

    agent = await run_in_threadpool(db_project.get_agent_by_id, agent_id)
    if not agent or agent["project_id"] != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")

    if await run_in_threadpool(is_approval_required, ctx.project["id"], agent_data=agent):
        cr = await run_in_threadpool(
            create_change_request,
            project_id=ctx.project["id"],
            request_type="delete",
            payload={"agent_id": agent_id, "agent_name": agent["name"]},
            requested_by=ctx.user.user_id,
            agent_id=agent_id,
        )
        return JSONResponse(
            {
                "status": "pending_approval",
                "change_request": cr,
                "message": "Agent deletion requires approval",
            }
        )

    await run_in_threadpool(create_agent_version, agent_id, ctx.user.user_id)

    await run_in_threadpool(db_project.delete_agent, agent_id)
    return JSONResponse({"success": True})


def _process_icon(icon_data: str) -> str:
    """Validate and pass through icon data for database storage.

    Accepts base64 data URLs (stored directly in DB) or plain URLs.
    """
    if not icon_data:
        return icon_data
    # Base64 data URL — store directly in DB
    if icon_data.startswith("data:image"):
        return icon_data
    # Existing URL path (e.g. /uploads/...) — keep as-is
    return icon_data
