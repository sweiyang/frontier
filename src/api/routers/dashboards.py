"""Dashboards: /projects/{project_name}/dashboard."""

import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from api.deps.project import (
    ProjectAccessContext,
    get_project_context,
    require_project_member,
    verify_project_admin_or_owner,
)
from api.schema import FormSubmitRequest, SiteAnalyticsBatch, SiteUpdate
from core.db import db_dashboard
from core.logging import get_logger

logger = get_logger(__name__)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/projects/{project_name}/dashboard", tags=["dashboards"])


@router.get("")
async def get_dashboard(
    project_name: str,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """
    Get the site configuration for a project (one site per project).

    Any project member can view the site. Returns { "site": site_document } or { "site": null }.
    """
    dashboard = db_dashboard.get_dashboard_for_project(ctx.project["id"])
    site = dashboard["layout"] if dashboard and dashboard.get("layout") else None
    return JSONResponse({"site": site})


@router.put("")
async def upsert_dashboard(
    project_name: str,
    request: SiteUpdate,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """
    Create or update the site for a project (one site per project).

    Restricted to project owner/admins. Accepts site document (name, pages).
    """
    verify_project_admin_or_owner(
        ctx.project,
        ctx.user.user_id if ctx.user else None,
        ctx.user.ad_groups if ctx.user else None,
    )

    site_document = request.model_dump(exclude_none=True)
    dashboard = db_dashboard.upsert_dashboard_for_project(
        project_internal_id=ctx.project["id"],
        layout=site_document,
        components=None,
        is_active=True,
    )
    return JSONResponse({"site": dashboard["layout"]})


@router.delete("")
async def delete_dashboard(
    project_name: str,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """
    Delete the dashboard configuration for a project.

    Restricted to project owner/admins.
    """
    verify_project_admin_or_owner(
        ctx.project,
        ctx.user.user_id if ctx.user else None,
        ctx.user.ad_groups if ctx.user else None,
    )

    deleted = db_dashboard.delete_dashboard_for_project(ctx.project["id"])
    return JSONResponse({"success": deleted})


@router.post("/upload")
async def upload_image(
    project_name: str,
    file: UploadFile = File(...),
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Upload an image for use in the site builder."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image exceeds 5 MB limit")

    ext = (
        file.filename.rsplit(".", 1)[-1].lower()
        if file.filename and "." in file.filename
        else "png"
    )
    filename = f"site_{uuid.uuid4()}.{ext}"

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    uploads_dir = os.path.join(base_dir, "data", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    file_path = os.path.join(uploads_dir, filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    return JSONResponse({"url": f"/uploads/{filename}"})


@router.post("/forms/{component_id}/submit")
async def submit_form(
    project_name: str,
    component_id: str,
    request: FormSubmitRequest,
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Submit form data from a site builder form component."""
    submission = db_dashboard.save_form_submission(
        project_id=ctx.project["id"],
        component_id=component_id,
        data=request.fields,
    )
    return JSONResponse({"success": True, "id": submission["id"]})


@router.post("/analytics")
async def post_analytics(
    project_name: str,
    request: SiteAnalyticsBatch,
    ctx: ProjectAccessContext = Depends(get_project_context),
):
    """Record site analytics events (works for both authenticated and guest users)."""
    user_id = ctx.user.user_id if ctx.user else None
    events = [e.model_dump() for e in request.events]
    count = db_dashboard.save_analytics_events(
        project_id=ctx.project["id"],
        events=events,
        user_id=user_id,
    )
    return JSONResponse({"recorded": count})


@router.get("/analytics")
async def get_analytics(
    project_name: str,
    period: str = "7d",
    ctx: ProjectAccessContext = Depends(require_project_member),
):
    """Get aggregated site analytics for the project dashboard."""
    period_map = {"1d": 1, "7d": 7, "30d": 30, "all": None}
    period_days = period_map.get(period, 7)
    data = db_dashboard.get_site_analytics(
        project_id=ctx.project["id"],
        period_days=period_days,
    )
    return JSONResponse(data)
