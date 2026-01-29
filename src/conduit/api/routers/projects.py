"""Projects: /projects, /projects/owned."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from conduit.api.deps.auth import get_current_user
from conduit.api.schema import ProjectCreate
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
    project = db_project.create_project(current_user.user_id, request.project_name)
    return JSONResponse(project)
