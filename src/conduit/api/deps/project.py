"""Project-related dependencies: header extraction and project access checks."""
from typing import Optional

from fastapi import Header, HTTPException

from conduit.core.db import db_project


def get_project_from_header(x_project: Optional[str] = Header(None)) -> Optional[str]:
    """Extract project name from X-Project header."""
    return x_project


def get_project_or_404(project_name: str) -> dict:
    """Helper to get project by name or raise 404."""
    project = db_project.get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def verify_project_owner(project: dict, user_id: int) -> None:
    """Verify the user is the project owner."""
    if project["owner_id"] != user_id:
        raise HTTPException(status_code=403, detail="Only project owner can modify settings")
