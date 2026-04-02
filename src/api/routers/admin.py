"""API endpoints for platform administration."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.auth import CurrentUser, get_current_user
from api.schema import (
    BannerCreate,
    BannerReorder,
    BannerUpdate,
    WorkbenchAccessGrantCreate,
)
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


@router.get("/usage")
async def get_platform_usage(
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """Get platform-wide monthly usage statistics (platform admin only)."""
    usage = db_project.get_platform_monthly_usage()
    return JSONResponse(usage)


# --- Platform Banners ---


@router.get("/banners/active")
async def get_active_banners(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get currently active, non-expired banners for all authenticated users."""
    banners = db_project.list_banners(active_only=True)
    return JSONResponse({"banners": banners})


@router.get("/banners")
async def list_all_banners(
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """List all banners including inactive (platform admin only)."""
    banners = db_project.list_banners(active_only=False)
    return JSONResponse({"banners": banners})


@router.post("/banners")
async def create_banner(
    body: BannerCreate,
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """Create a new platform notification banner."""
    expires_at = None
    if body.expires_at:
        try:
            expires_at = datetime.fromisoformat(body.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format. Use ISO 8601.")

    banner = db_project.create_banner(
        message=body.message,
        tag=body.tag,
        tag_color=body.tag_color,
        link_url=body.link_url,
        is_active=body.is_active,
        expires_at=expires_at,
        created_by=current_user.user_id,
    )
    return JSONResponse(banner, status_code=201)


@router.put("/banners/reorder")
async def reorder_banners(
    body: BannerReorder,
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """Reorder banners by providing an ordered list of banner IDs."""
    db_project.reorder_banners(body.banner_ids)
    return JSONResponse({"success": True})


@router.put("/banners/{banner_id}")
async def update_banner(
    banner_id: int,
    body: BannerUpdate,
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """Update an existing platform banner."""
    updates = body.model_dump(exclude_unset=True)
    if "expires_at" in updates and updates["expires_at"] is not None:
        try:
            updates["expires_at"] = datetime.fromisoformat(updates["expires_at"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format. Use ISO 8601.")

    banner = db_project.update_banner(banner_id, **updates)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return JSONResponse(banner)


@router.delete("/banners/{banner_id}")
async def delete_banner(
    banner_id: int,
    current_user: CurrentUser = Depends(require_platform_admin),
):
    """Delete a platform banner."""
    deleted = db_project.delete_banner(banner_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Banner not found")
    logger.info(f"Platform admin '{current_user.username}' deleted banner {banner_id}")
    return JSONResponse({"success": True})
