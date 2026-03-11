"""Projects: /projects, /projects/owned."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from api.deps.auth import get_current_user
from api.deps.project import verify_project_membership
from api.schema import ProjectCreate, ProjectUpdate
from core.auth.jwt import CurrentUser
from core.config import get_config
from core.db import db_project

router = APIRouter(prefix="/projects", tags=["projects"])
security = HTTPBasic()


@router.get("/owned")
async def list_admin_projects(current_user: CurrentUser = Depends(get_current_user)):
    """List all projects the user can administer (owner or admin role)."""
    projects = db_project.list_projects_for_user(current_user.user_id, current_user.ad_groups)
    admin_projects = [p for p in projects if p.get("is_admin", False)]
    return JSONResponse({"projects": admin_projects})


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
    
    verify_project_membership(project_name, current_user.user_id, current_user.ad_groups)
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
    
    # Verify user is owner or admin
    role = db_project.get_user_role_in_project(current_user.user_id, project["project_id"])
    if role not in ("owner", "admin"):
        return JSONResponse({"error": "Only owners and admins can modify settings"}, status_code=403)

    updated = db_project.update_project(
        project_id=project["project_id"],
        project_name=request.project_name,
        disable_authentication=request.disable_authentication,
        disable_message_storage=request.disable_message_storage
    )
    return JSONResponse(updated)


@router.delete("/admin/{project_name}")
async def admin_delete_project(
    project_name: str,
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Delete a project (admin only). Requires HTTP Basic Auth with admin credentials from config.yaml."""
    cfg = get_config()
    
    if not cfg.admin_username or not cfg.admin_password:
        raise HTTPException(
            status_code=503,
            detail="Admin credentials not configured"
        )
    
    if credentials.username != cfg.admin_username or credentials.password != cfg.admin_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    project = db_project.get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    success = db_project.delete_project_by_name(project_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete project")
    
    return JSONResponse({
        "success": True,
        "message": f"Project '{project_name}' deleted successfully"
    })
