"""Artefacts: shared chatbots accessible via permission settings."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.deps.auth import get_current_user
from api.schema import ArtefactSettings
from core.auth.jwt import CurrentUser
from core.db import db_project

router = APIRouter(prefix="/artefacts", tags=["artefacts"])


@router.get("")
async def list_artefacts(current_user: CurrentUser = Depends(get_current_user)):
    """List all artefacts accessible to the authenticated user."""
    artefacts = db_project.list_artefacts(
        user_id=current_user.user_id,
        ad_groups=getattr(current_user, "ad_groups", [])
    )
    return JSONResponse({"artefacts": artefacts})


@router.put("/{project_name}/settings")
async def update_artefact_settings(
    project_name: str,
    request: ArtefactSettings,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Enable/disable artefact mode and set visibility for a project."""
    project = db_project.get_project_by_name(project_name)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)

    role = db_project.get_user_role_in_project(current_user.user_id, project["project_id"])
    if role not in ("owner", "admin"):
        return JSONResponse({"error": "Only owners and admins can manage artefact settings"}, status_code=403)

    if request.artefact_visibility not in ("private", "org", "public"):
        return JSONResponse({"error": "visibility must be 'private', 'org', or 'public'"}, status_code=400)

    updated = db_project.set_artefact(
        project_id=project["project_id"],
        is_artefact=request.is_artefact,
        visibility=request.artefact_visibility
    )
    if not updated:
        return JSONResponse({"error": "Failed to update artefact settings"}, status_code=500)

    return JSONResponse(updated)
