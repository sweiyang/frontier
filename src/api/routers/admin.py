"""API endpoints for platform administration."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.auth import CurrentUser, get_current_user
from api.schema import WorkbenchAccessGrantCreate
from core.config import get_config
from core.db import db_project
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_platform_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependency that ensures the caller is a platform admin (platform_owner)."""
    if current_user.username not in get_config().platform_owners:
        raise HTTPException(status_code=403, detail="Platform admin access required")
    return current_user


@router.get("/projects")
async def list_all_projects(
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """List all projects (platform admin only)."""
    projects = db_project.list_all_projects()
    return JSONResponse({"projects": projects})


@router.delete("/projects/{project_name}")
async def admin_delete_project(
    project_name: str,
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """Delete a project (platform admin only)."""
    project = db_project.get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    success = db_project.delete_project_by_name(project_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete project")

    logger.info(f"Platform admin '{current_user.username}' deleted project '{project_name}'")
    return JSONResponse({"success": True, "message": f"Project '{project_name}' deleted successfully"})


@router.get("/workbench-access")
async def list_workbench_grants(
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """List all workbench access grants."""
    grants = db_project.list_workbench_grants()
    return JSONResponse({"grants": grants})


@router.post("/workbench-access")
async def add_workbench_grant(
    body: WorkbenchAccessGrantCreate,
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """Add a workbench access grant for a user or AD group."""
    try:
        grant = db_project.add_workbench_grant(
            grant_type=body.grant_type,
            grant_value=body.grant_value,
            display_name=body.display_name,
            granted_by=current_user.user_id,
        )
        return JSONResponse(grant, status_code=201)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/workbench-access/{grant_id}")
async def remove_workbench_grant(
    grant_id: int,
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """Remove a workbench access grant."""
    deleted = db_project.remove_workbench_grant(grant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Grant not found")
    return JSONResponse({"success": True})
