"""Project-related dependencies: header extraction and project access checks."""
from typing import Optional
from dataclasses import dataclass

from fastapi import Header, HTTPException, Depends

from conduit.core.db import db_project
from conduit.api.deps.auth import get_optional_current_user
from conduit.core.auth.jwt import CurrentUser


@dataclass
class ProjectAccessContext:
    project: dict
    user: Optional[CurrentUser]
    is_guest: bool


def get_project_from_header(x_project: Optional[str] = Header(None)) -> Optional[str]:
    """Extract project name from X-Project header."""
    return x_project


def get_project_or_404(project_name: str) -> dict:
    """Helper to get project by name or raise 404."""
    project = db_project.get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def get_project_context(
    project_name: str,
    user: Optional[CurrentUser] = Depends(get_optional_current_user)
) -> ProjectAccessContext:
    """
    Get project context, handling optional authentication if project allows it.
    """
    project = get_project_or_404(project_name)
    
    if project.get("disable_authentication", False):
        return ProjectAccessContext(project=project, user=user, is_guest=True)
        
    if not user:
         raise HTTPException(status_code=401, detail="Not authenticated")
         
    return ProjectAccessContext(project=project, user=user, is_guest=False)


def verify_project_owner(project: dict, user_id: Optional[int]) -> None:
    """
    Verify the user is the project owner.
    If authentication is disabled for the project, skip check.
    """
    # If auth is disabled, allow access (implicitly admin/owner access for everyone)
    if project.get("disable_authentication", False):
        return

    if not user_id or project["owner_id"] != user_id:
        raise HTTPException(status_code=403, detail="Only project owner can modify settings")
