"""RBAC groups: /projects/{project}/groups."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.auth import get_current_user
from api.deps.project import get_project_or_404, verify_project_owner
from api.schema import ADGroupCreate, ADGroupUpdate
from core.auth.jwt import CurrentUser
from core.db import db_project

router = APIRouter(prefix="/projects/{project_name}/groups", tags=["rbac-groups"])


@router.get("")
async def list_ad_groups(
    project_name: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all AD groups for a project."""
    project = get_project_or_404(project_name)
    groups = db_project.list_ad_groups_for_project(project["id"])
    return JSONResponse({"groups": groups})


@router.post("")
async def add_ad_group(
    project_name: str,
    request: ADGroupCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add an AD group to a project."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    group = db_project.add_ad_group_to_project(
        project_id=project["id"],
        group_dn=request.group_dn,
        group_name=request.group_name,
        role=request.role,
    )

    if request.agent_ids is not None:
        db_project.set_ad_group_agent_permissions(group["id"], project["id"], request.agent_ids)
        group["agent_ids"] = request.agent_ids
    else:
        group["agent_ids"] = []

    return JSONResponse(group)


@router.put("/{group_id}")
async def update_ad_group(
    project_name: str,
    group_id: int,
    request: ADGroupUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an AD group's role and/or agent permissions."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    if request.role is not None:
        updated_group = db_project.update_ad_group_role(group_id, request.role)
        if not updated_group:
            raise HTTPException(status_code=404, detail="Group not found")
    else:
        groups = db_project.list_ad_groups_for_project(project["id"])
        updated_group = next((g for g in groups if g["id"] == group_id), None)
        if not updated_group:
            raise HTTPException(status_code=404, detail="Group not found")

    if request.agent_ids is not None:
        db_project.set_ad_group_agent_permissions(group_id, project["id"], request.agent_ids)
        updated_group["agent_ids"] = request.agent_ids
    else:
        updated_group["agent_ids"] = db_project.get_ad_group_agent_permissions(group_id)

    return JSONResponse(updated_group)


@router.delete("/{group_id}")
async def remove_ad_group(
    project_name: str,
    group_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Remove an AD group from a project."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    success = db_project.remove_ad_group_from_project(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")

    return JSONResponse({"success": True})
