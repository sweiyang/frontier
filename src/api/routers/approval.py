"""API endpoints for approval workflow management."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.project import (
    require_project_member,
    ProjectAccessContext,
    verify_project_admin_or_owner,
)
from api.schema import ApproverCreate, ApprovalSettingsUpdate, ApprovalActionCreate
from core.config import get_config
from core.approval import (
    is_approval_required,
    add_approver_by_username,
    remove_approver,
    list_approvers,
    get_approval_settings,
    update_approval_settings,
    list_change_requests,
    get_change_request,
    approve_change_request,
    reject_change_request,
)
from core.approval.version_service import (
    get_agent_versions,
    get_agent_version,
    rollback_agent_to_version,
)
from core.db import db_project

router = APIRouter(tags=["approval"])


@router.get("/approval/environment")
async def get_environment_info():
    """Get current environment information for approval workflow."""
    cfg = get_config()
    return JSONResponse({
        "environment": cfg.app_env,
        "is_production": cfg.is_production,
        "approval_enabled": cfg.approval_enabled,
    })


@router.get("/projects/{project_name}/approvers")
async def get_project_approvers(
    project_name: str,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get list of approvers for a project."""
    approvers = list_approvers(ctx.project["id"])
    return JSONResponse({"approvers": approvers})


@router.post("/projects/{project_name}/approvers")
async def add_project_approver(
    project_name: str,
    body: ApproverCreate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Add an approver to a project. Only project owner or admin can add approvers."""
    verify_project_admin_or_owner(
        ctx.project,
        ctx.user.user_id if ctx.user else None,
        ctx.user.ad_groups if ctx.user else None
    )

    result = add_approver_by_username(
        ctx.project["id"],
        body.username,
        ctx.user.user_id if ctx.user else 0
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to add approver. User may not exist or is already an approver.")

    return JSONResponse(result)


@router.delete("/projects/{project_name}/approvers/{user_id}")
async def remove_project_approver(
    project_name: str,
    user_id: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Remove an approver from a project. Only project owner or admin can remove approvers."""
    verify_project_admin_or_owner(
        ctx.project,
        ctx.user.user_id if ctx.user else None,
        ctx.user.ad_groups if ctx.user else None
    )

    success = remove_approver(ctx.project["id"], user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Approver not found")

    return JSONResponse({"success": True})


@router.get("/projects/{project_name}/approval-settings")
async def get_project_approval_settings(
    project_name: str,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get approval settings for a project."""
    settings = get_approval_settings(ctx.project["id"])
    return JSONResponse(settings)


@router.put("/projects/{project_name}/approval-settings")
async def update_project_approval_settings(
    project_name: str,
    body: ApprovalSettingsUpdate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Update approval settings for a project. Only project owner or admin can update."""
    verify_project_admin_or_owner(
        ctx.project,
        ctx.user.user_id if ctx.user else None,
        ctx.user.ad_groups if ctx.user else None
    )

    try:
        settings = update_approval_settings(ctx.project["id"], body.approval_type)
        return JSONResponse(settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_name}/change-requests")
async def get_project_change_requests(
    project_name: str,
    status: Optional[str] = None,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get change requests for a project."""
    requests = list_change_requests(ctx.project["id"], status)
    return JSONResponse({"change_requests": requests})


@router.get("/projects/{project_name}/change-requests/{request_id}")
async def get_change_request_detail(
    project_name: str,
    request_id: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get details of a change request."""
    cr = get_change_request(request_id)
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
    # Verify the change request belongs to this project
    if cr.get("project_id") != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Change request not found")
    return JSONResponse(cr)


@router.post("/projects/{project_name}/change-requests/{request_id}/approve")
async def approve_request(
    project_name: str,
    request_id: int,
    body: ApprovalActionCreate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Approve a change request."""
    # Verify the change request belongs to this project
    cr = get_change_request(request_id)
    if not cr or cr.get("project_id") != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Change request not found")

    result = approve_change_request(
        request_id,
        ctx.user.user_id if ctx.user else 0,
        body.comment
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Failed to approve. Request may be already resolved or you already voted."
        )

    # Handle self-approval error
    if isinstance(result, dict) and result.get("error") == "self_approval":
        raise HTTPException(
            status_code=403,
            detail=result.get("message", "You cannot approve your own change request")
        )

    return JSONResponse(result)


@router.post("/projects/{project_name}/change-requests/{request_id}/reject")
async def reject_request(
    project_name: str,
    request_id: int,
    body: ApprovalActionCreate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Reject a change request."""
    # Verify the change request belongs to this project
    cr = get_change_request(request_id)
    if not cr or cr.get("project_id") != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Change request not found")

    if not body.comment:
        raise HTTPException(status_code=400, detail="Comment is required for rejection")

    result = reject_change_request(
        request_id,
        ctx.user.user_id if ctx.user else 0,
        body.comment
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Failed to reject. Request may be already resolved."
        )

    return JSONResponse(result)


@router.get("/projects/{project_name}/agents/{agent_id}/versions")
async def get_agent_version_history(
    project_name: str,
    agent_id: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get version history for an agent."""
    versions = get_agent_versions(agent_id)
    return JSONResponse({"versions": versions})


@router.get("/projects/{project_name}/agents/{agent_id}/versions/{version_number}")
async def get_agent_version_detail(
    project_name: str,
    agent_id: int,
    version_number: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get a specific version of an agent."""
    version = get_agent_version(agent_id, version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return JSONResponse(version)


@router.post("/projects/{project_name}/agents/{agent_id}/rollback/{version_number}")
async def rollback_agent(
    project_name: str,
    agent_id: int,
    version_number: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Rollback an agent to a previous version."""
    verify_project_admin_or_owner(
        ctx.project,
        ctx.user.user_id if ctx.user else None,
        ctx.user.ad_groups if ctx.user else None
    )

    if is_approval_required(ctx.project["id"]):
        from core.approval import create_change_request

        version = get_agent_version(agent_id, version_number)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        cr = create_change_request(
            project_id=ctx.project["id"],
            request_type="update",
            requested_by=ctx.user.user_id if ctx.user else 0,
            payload=version["snapshot"],
            agent_id=agent_id,
        )
        return JSONResponse({
            "status": "pending_approval",
            "change_request": cr,
            "message": "Rollback requires approval in production environment",
        })

    result = rollback_agent_to_version(
        agent_id,
        version_number,
        ctx.user.user_id if ctx.user else 0
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to rollback agent")

    return JSONResponse(result)
