"""RBAC members: /projects/{project}/members."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.auth import get_current_user
from api.deps.project import get_project_or_404, verify_project_owner
from api.schema import MemberCreate, MemberUpdate
from core.auth.jwt import CurrentUser
from core.db import db_project

router = APIRouter(prefix="/projects/{project_name}/members", tags=["rbac-members"])


@router.get("")
async def list_members(
    project_name: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all members (LAN IDs) for a project."""
    project = get_project_or_404(project_name)
    members = db_project.list_project_members_with_roles(project["id"])
    return JSONResponse({"members": members})


@router.post("")
async def add_member(
    project_name: str,
    request: MemberCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add a member by LAN ID (username) to a project."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    member = db_project.add_member_by_username(
        project_id=project["id"],
        username=request.username,
        role=request.role,
    )
    if not member:
        raise HTTPException(status_code=400, detail="Failed to add member")

    if request.agent_ids is not None:
        db_project.set_member_agent_permissions(project["id"], member["user_id"], request.agent_ids)
        member["agent_ids"] = request.agent_ids
    else:
        member["agent_ids"] = []

    return JSONResponse(member)


@router.put("/{user_id}")
async def update_member(
    project_name: str,
    user_id: int,
    request: MemberUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update a member's role and/or agent permissions."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    if request.role is not None:
        updated_member = db_project.update_member_role(project["id"], user_id, request.role)
        if not updated_member:
            raise HTTPException(
                status_code=404, detail="Member not found or cannot modify owner"
            )
    else:
        members = db_project.list_project_members_with_roles(project["id"])
        updated_member = next((m for m in members if m["user_id"] == user_id), None)
        if not updated_member:
            raise HTTPException(status_code=404, detail="Member not found")

    if request.agent_ids is not None:
        db_project.set_member_agent_permissions(project["id"], user_id, request.agent_ids)
        updated_member["agent_ids"] = request.agent_ids
    else:
        updated_member["agent_ids"] = db_project.get_member_agent_permissions(
            project["id"], user_id
        )

    return JSONResponse(updated_member)


@router.delete("/{user_id}")
async def remove_member(
    project_name: str,
    user_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Remove a member from a project."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)

    success = db_project.remove_member_by_id(project["id"], user_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Member not found or cannot remove owner"
        )

    return JSONResponse({"success": True})
