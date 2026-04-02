from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)

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


class SiteAnalyticsEvent(Base):
    """Tracks usage events for published dashboard sites."""

    __tablename__ = "site_analytics_events"
    __table_args__ = (Index("ix_site_analytics_project_created", "project_id", "created_at"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # page_view, button_click, form_submit, table_action
    page_id = Column(String, nullable=True)
    page_path = Column(String, nullable=True)
    component_id = Column(String, nullable=True)
    component_type = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(64), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


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
        dashboard = session.query(ProjectDashboard).filter(ProjectDashboard.project_id == project_internal_id).first()
        if not dashboard:
            return None
        return _serialize_dashboard(dashboard)
    finally:
        session.close()


def get_projects_with_dashboards(project_ids: List[int]) -> Set[int]:
    """Return the subset of project internal IDs that have a dashboard."""
    if not project_ids:
        return set()
    db = get_db()
    session = db.get_session()
    try:
        rows = session.query(ProjectDashboard.project_id).filter(ProjectDashboard.project_id.in_(project_ids)).all()
        return {r[0] for r in rows}
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
        dashboard = session.query(ProjectDashboard).filter(ProjectDashboard.project_id == project_internal_id).first()

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
        dashboard = session.query(ProjectDashboard).filter(ProjectDashboard.project_id == project_internal_id).first()
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
            "created_at": (submission.created_at.isoformat() if submission.created_at else None),
        }
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Site Analytics
# ---------------------------------------------------------------------------


def save_analytics_events(
    project_id: int,
    events: List[Dict[str, Any]],
    user_id: Optional[int] = None,
) -> int:
    """Bulk-insert site analytics events. Returns the number of rows inserted."""
    if not events:
        return 0
    db = get_db()
    session = db.get_session()
    try:
        rows = []
        for evt in events:
            rows.append(
                SiteAnalyticsEvent(
                    project_id=project_id,
                    event_type=evt.get("event_type", "page_view"),
                    page_id=evt.get("page_id"),
                    page_path=evt.get("page_path"),
                    component_id=evt.get("component_id"),
                    component_type=evt.get("component_type"),
                    user_id=user_id,
                    session_id=evt.get("session_id"),
                    metadata_=evt.get("metadata"),
                )
            )
        session.add_all(rows)
        session.commit()
        return len(rows)
    finally:
        session.close()


def get_site_analytics(project_id: int, period_days: Optional[int] = 7) -> Dict[str, Any]:
    """Aggregate site analytics for a project over a given period."""
    db = get_db()
    session = db.get_session()
    try:
        q = session.query(SiteAnalyticsEvent).filter(SiteAnalyticsEvent.project_id == project_id)
        if period_days is not None:
            cutoff = datetime.utcnow() - timedelta(days=period_days)
            q = q.filter(SiteAnalyticsEvent.created_at >= cutoff)

        # Summary counts
        total_page_views = q.filter(SiteAnalyticsEvent.event_type == "page_view").count()

        unique_users = (
            session.query(func.count(func.distinct(SiteAnalyticsEvent.session_id)))
            .filter(
                SiteAnalyticsEvent.project_id == project_id,
                SiteAnalyticsEvent.event_type == "page_view",
                *([SiteAnalyticsEvent.created_at >= cutoff] if period_days is not None else []),
            )
            .scalar()
            or 0
        )

        interaction_types = ["button_click", "form_submit", "table_action"]
        total_interactions = q.filter(SiteAnalyticsEvent.event_type.in_(interaction_types)).count()
        total_form_submissions = q.filter(SiteAnalyticsEvent.event_type == "form_submit").count()

        # Breakdown by page
        page_rows = (
            session.query(
                SiteAnalyticsEvent.page_path,
                func.count().label("views"),
                func.count(func.distinct(SiteAnalyticsEvent.session_id)).label("unique_users"),
            )
            .filter(
                SiteAnalyticsEvent.project_id == project_id,
                SiteAnalyticsEvent.event_type == "page_view",
                *([SiteAnalyticsEvent.created_at >= cutoff] if period_days is not None else []),
            )
            .group_by(SiteAnalyticsEvent.page_path)
            .order_by(func.count().desc())
            .all()
        )
        by_page = [
            {
                "page_path": r.page_path or "/",
                "views": r.views,
                "unique_users": r.unique_users,
            }
            for r in page_rows
        ]

        # Top components (interactions only)
        comp_rows = (
            session.query(
                SiteAnalyticsEvent.component_id,
                SiteAnalyticsEvent.component_type,
                func.count().label("interactions"),
            )
            .filter(
                SiteAnalyticsEvent.project_id == project_id,
                SiteAnalyticsEvent.event_type.in_(interaction_types),
                SiteAnalyticsEvent.component_id.isnot(None),
                *([SiteAnalyticsEvent.created_at >= cutoff] if period_days is not None else []),
            )
            .group_by(SiteAnalyticsEvent.component_id, SiteAnalyticsEvent.component_type)
            .order_by(func.count().desc())
            .limit(10)
            .all()
        )
        top_components = [
            {
                "component_id": r.component_id,
                "component_type": r.component_type,
                "interactions": r.interactions,
            }
            for r in comp_rows
        ]

        # Breakdown by interaction type
        type_rows = (
            session.query(
                SiteAnalyticsEvent.event_type,
                func.count().label("count"),
            )
            .filter(
                SiteAnalyticsEvent.project_id == project_id,
                SiteAnalyticsEvent.event_type.in_(interaction_types),
                *([SiteAnalyticsEvent.created_at >= cutoff] if period_days is not None else []),
            )
            .group_by(SiteAnalyticsEvent.event_type)
            .all()
        )
        by_type = {r.event_type: r.count for r in type_rows}

        return {
            "summary": {
                "page_views": total_page_views,
                "unique_users": unique_users,
                "interactions": total_interactions,
                "form_submissions": total_form_submissions,
            },
            "by_page": by_page,
            "by_type": by_type,
            "top_components": top_components,
        }
    finally:
        session.close()


def get_project_site_interaction_count(project_id: int) -> int:
    """Count site interaction events (clicks, submits, table actions) for a project."""
    db = get_db()
    session = db.get_session()
    try:
        interaction_types = ["button_click", "form_submit", "table_action"]
        return (
            session.query(SiteAnalyticsEvent)
            .filter(
                SiteAnalyticsEvent.project_id == project_id,
                SiteAnalyticsEvent.event_type.in_(interaction_types),
            )
            .count()
        )
    finally:
        session.close()
