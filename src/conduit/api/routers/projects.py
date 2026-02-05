"""Projects: /projects, /projects/owned."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from conduit.api.deps.auth import get_current_user
from conduit.api.schema import ProjectCreate, ProjectUpdate
from conduit.core.auth.jwt import CurrentUser
from conduit.core.db import db_project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/owned")
async def list_owned_projects(current_user: CurrentUser = Depends(get_current_user)):
    """List all projects owned by the authenticated user."""
    projects = db_project.list_projects_for_user(current_user.user_id)
    owned_projects = [p for p in projects if p.get("is_owner", False)]
    return JSONResponse({"projects": owned_projects})


@router.post("")
async def create_project(
    request: ProjectCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new project for the authenticated user."""
    project = db_project.create_project(
        owner_id=current_user.user_id, 
        project_name=request.project_name,
        disable_authentication=request.disable_authentication,
        disable_message_storage=request.disable_message_storage
    )
    return JSONResponse(project)


@router.get("/{project_name}")
async def get_project(
    project_name: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get project details."""
    project = db_project.get_project_by_name(project_name)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    return JSONResponse(project)


@router.put("/{project_name}")
async def update_project(
    project_name: str,
    request: ProjectUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update project settings."""
    project = db_project.get_project_by_name(project_name)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    
    # Verify ownership
    if project["owner_id"] != current_user.user_id:
        return JSONResponse({"error": "Only owner can modify settings"}, status_code=403)

    updated = db_project.update_project(
        project_id=project["project_id"],
        project_name=request.project_name,
        disable_authentication=request.disable_authentication,
        disable_message_storage=request.disable_message_storage
    )
    return JSONResponse(updated)
