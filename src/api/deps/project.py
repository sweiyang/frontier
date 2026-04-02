"""Project-related dependencies: header extraction and project access checks."""

from dataclasses import dataclass
from typing import List, Optional

from fastapi import Depends, Header, HTTPException

from api.deps.auth import get_current_user, get_optional_current_user
from core.auth.jwt import CurrentUser
from core.db import db_project


@dataclass
class ProjectAccessContext:
    """
    Context for project access in route handlers.

    Attributes:
        project: Project dict from database.
        user: Authenticated user, or None for guest access.
        is_guest: True if accessing without authentication.
    """

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
    project_name: str, user: Optional[CurrentUser] = Depends(get_optional_current_user)
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


def verify_project_admin_or_owner(project: dict, user_id: Optional[int], ad_groups: Optional[List[str]] = None) -> None:
    """
    Verify the user is either the project owner or an admin.
    If authentication is disabled for the project, skip check.
    """
    if project.get("disable_authentication", False):
        return

    if not user_id:
        raise HTTPException(status_code=403, detail="Only project owner or admin can modify settings")

    if project["owner_id"] == user_id:
        return

    role = db_project.get_user_role_in_project(user_id, project["project_id"])
    if role in ("owner", "admin"):
        return

    raise HTTPException(status_code=403, detail="Only project owner or admin can modify settings")


async def require_project_member(project_name: str, user: CurrentUser = Depends(get_current_user)) -> ProjectAccessContext:
    """
    Verify user is a member of the project (any role).
    Raises 403 if not a member.
    """
    project = get_project_or_404(project_name)

    if project.get("disable_authentication", False):
        return ProjectAccessContext(project=project, user=user, is_guest=True)

    projects = db_project.list_projects_for_user(user.user_id, user.ad_groups)
    if not any(p["project_id"] == project["project_id"] for p in projects):
        raise HTTPException(status_code=403, detail="You do not have access to this project")

    return ProjectAccessContext(project=project, user=user, is_guest=False)


def verify_project_membership(project_name: str, user_id: int, ad_groups: Optional[List[str]] = None) -> None:
    """
    Verify the user is a member of the project.
    Raises 403 if not a member.

    Args:
        project_name: The project name to check
        user_id: The user's database ID
        ad_groups: List of AD group DNs from the user's JWT token
    """
    project = db_project.get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("disable_authentication", False):
        return

    projects = db_project.list_projects_for_user(user_id, ad_groups)
    if not any(p["project_id"] == project["project_id"] for p in projects):
        raise HTTPException(status_code=403, detail="You do not have access to this project")
