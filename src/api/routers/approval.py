"""API endpoints for approval workflow management."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from api.deps.project import (
    ProjectAccessContext,
    require_project_member,
    verify_project_admin_or_owner,
)
from api.schema import ApprovalActionCreate, ApprovalSettingsUpdate, ApproverCreate
from core.approval import (
    add_approver_by_username,
    approve_change_request,
    get_approval_settings,
    get_change_request,
    is_approval_required,
    list_approvers,
    list_change_requests,
    reject_change_request,
    remove_approver,
    update_approval_settings,
)
from core.approval.version_service import (
    get_agent_version,
    get_agent_versions,
    rollback_agent_to_version,
)
from core.config import get_config
from core.db import db_project

router = APIRouter(tags=["approval"])


@router.get("/approval/environment")
async def get_environment_info():
    """Get approval workflow status."""
    cfg = get_config()
    return JSONResponse(
        {
            "approval_enabled": cfg.approval_enabled,
        }
    )


@router.get("/projects/{project_name}/approvers")
async def get_project_approvers(
    project_name: str,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get list of approvers for a project."""
    approvers = await run_in_threadpool(list_approvers, ctx.project["id"])
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
        ctx.user.ad_groups if ctx.user else None,
    )

    result = await run_in_threadpool(
        add_approver_by_username, ctx.project["id"], body.username, ctx.user.user_id if ctx.user else 0
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Failed to add approver. User may not exist or is already an approver.",
        )

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
        ctx.user.ad_groups if ctx.user else None,
    )

    success = await run_in_threadpool(remove_approver, ctx.project["id"], user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Approver not found")

    return JSONResponse({"success": True})


@router.get("/projects/{project_name}/approval-settings")
async def get_project_approval_settings(
    project_name: str,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get approval settings for a project."""
    settings = await run_in_threadpool(get_approval_settings, ctx.project["id"])
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
        ctx.user.ad_groups if ctx.user else None,
    )

    try:
        settings = await run_in_threadpool(update_approval_settings, ctx.project["id"], body.approval_type)
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
    requests = await run_in_threadpool(list_change_requests, ctx.project["id"], status)
    return JSONResponse({"change_requests": requests})


@router.get("/projects/{project_name}/change-requests/{request_id}")
async def get_change_request_detail(
    project_name: str,
    request_id: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get details of a change request."""
    cr = await run_in_threadpool(get_change_request, request_id)
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
    cr = await run_in_threadpool(get_change_request, request_id)
    if not cr or cr.get("project_id") != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Change request not found")

    result = await run_in_threadpool(approve_change_request, request_id, ctx.user.user_id if ctx.user else 0, body.comment)

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Failed to approve. Request may be already resolved or you already voted.",
        )

    # Handle self-approval error
    if isinstance(result, dict) and result.get("error") == "self_approval":
        raise HTTPException(
            status_code=403,
            detail=result.get("message", "You cannot approve your own change request"),
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
    cr = await run_in_threadpool(get_change_request, request_id)
    if not cr or cr.get("project_id") != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Change request not found")

    if not body.comment:
        raise HTTPException(status_code=400, detail="Comment is required for rejection")

    result = await run_in_threadpool(reject_change_request, request_id, ctx.user.user_id if ctx.user else 0, body.comment)

    if not result:
        raise HTTPException(status_code=400, detail="Failed to reject. Request may be already resolved.")

    return JSONResponse(result)


@router.get("/projects/{project_name}/agents/{agent_id}/versions")
async def get_agent_version_history(
    project_name: str,
    agent_id: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get version history for an agent."""
    versions = await run_in_threadpool(get_agent_versions, agent_id)
    return JSONResponse({"versions": versions})


@router.get("/projects/{project_name}/agents/{agent_id}/versions/{version_number}")
async def get_agent_version_detail(
    project_name: str,
    agent_id: int,
    version_number: int,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get a specific version of an agent."""
    version = await run_in_threadpool(get_agent_version, agent_id, version_number)
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
        ctx.user.ad_groups if ctx.user else None,
    )

    agent = await run_in_threadpool(db_project.get_agent_by_id, agent_id)
    if not agent or agent["project_id"] != ctx.project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")

    if await run_in_threadpool(is_approval_required, ctx.project["id"], agent_data=agent):
        from core.approval import create_change_request

        version = await run_in_threadpool(get_agent_version, agent_id, version_number)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        cr = await run_in_threadpool(
            create_change_request,
            project_id=ctx.project["id"],
            request_type="update",
            requested_by=ctx.user.user_id if ctx.user else 0,
            payload=version["snapshot"],
            agent_id=agent_id,
        )
        return JSONResponse(
            {
                "status": "pending_approval",
                "change_request": cr,
                "message": "Rollback requires approval",
            }
        )

    result = await run_in_threadpool(rollback_agent_to_version, agent_id, version_number, ctx.user.user_id if ctx.user else 0)

    if not result:
        raise HTTPException(status_code=400, detail="Failed to rollback agent")

    return JSONResponse(result)
