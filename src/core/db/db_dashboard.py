from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, DateTime

from core.db.db import Base
from core.db.db_chat import get_db


class ProjectDashboard(Base):
    """
    Per-project dashboard configuration.

    Each project can have at most one active dashboard definition that
    describes the layout and components rendered on the project landing
    page.

    Attributes:
        id: Primary key.
        project_id: Foreign key to the owning project (unique).
        layout: JSON structure describing the grid layout and components.
        components: Optional JSON registry of component definitions.
        is_active: Whether this dashboard is active.
        created_at: Creation timestamp.
        updated_at: Last modification timestamp.
    """

    __tablename__ = "project_dashboards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    layout = Column(JSON, nullable=False)
    components = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FormSubmission(Base):
    """Stores submissions from site builder form components."""

    __tablename__ = "form_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    component_id = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def _serialize_dashboard(model: ProjectDashboard) -> Dict[str, Any]:
    """Convert a ProjectDashboard ORM instance into a plain dict."""
    return {
        "id": model.id,
        "project_id": model.project_id,
        "layout": model.layout,
        "components": model.components,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def get_dashboard_for_project(project_internal_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch the dashboard configuration for a project by its internal ID.

    Returns None if no dashboard exists.
    """
    db = get_db()
    session = db.get_session()
    try:
        dashboard = (
            session.query(ProjectDashboard)
            .filter(ProjectDashboard.project_id == project_internal_id)
            .first()
        )
        if not dashboard:
            return None
        return _serialize_dashboard(dashboard)
    finally:
        session.close()


def upsert_dashboard_for_project(
    project_internal_id: int,
    layout: Dict[str, Any],
    components: Optional[Dict[str, Any]] = None,
    is_active: bool = True,
) -> Dict[str, Any]:
    """
    Create or update the dashboard configuration for a project.

    If a dashboard already exists for the project, it is updated in-place.
    Otherwise, a new dashboard row is created.
    """
    db = get_db()
    session = db.get_session()
    try:
        dashboard = (
            session.query(ProjectDashboard)
            .filter(ProjectDashboard.project_id == project_internal_id)
            .first()
        )

        if dashboard is None:
            dashboard = ProjectDashboard(
                project_id=project_internal_id,
                layout=layout,
                components=components,
                is_active=is_active,
            )
            session.add(dashboard)
        else:
            dashboard.layout = layout
            dashboard.components = components
            dashboard.is_active = is_active

        session.commit()
        session.refresh(dashboard)
        return _serialize_dashboard(dashboard)
    finally:
        session.close()


def delete_dashboard_for_project(project_internal_id: int) -> bool:
    """
    Delete the dashboard configuration for a project.

    Returns True if a dashboard was deleted, False if none existed.
    """
    db = get_db()
    session = db.get_session()
    try:
        dashboard = (
            session.query(ProjectDashboard)
            .filter(ProjectDashboard.project_id == project_internal_id)
            .first()
        )
        if not dashboard:
            return False

        session.delete(dashboard)
        session.commit()
        return True
    finally:
        session.close()


def save_form_submission(
    project_id: int,
    component_id: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Save a form submission from a site builder form component."""
    db = get_db()
    session = db.get_session()
    try:
        submission = FormSubmission(
            project_id=project_id,
            component_id=component_id,
            data=data,
        )
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return {
            "id": submission.id,
            "project_id": submission.project_id,
            "component_id": submission.component_id,
            "data": submission.data,
            "created_at": submission.created_at.isoformat() if submission.created_at else None,
        }
    finally:
        session.close()

