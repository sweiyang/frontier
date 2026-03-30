from datetime import datetime
from typing import List, Optional, Any
import re
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, func, Text, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, deferred
from core.db.db import Base
from core.db.db_chat import get_db, project_members
from core.logging import get_logger

logger = get_logger(__name__)


class Project(Base):
    """
    Project model for workspace isolation.
    
    Each project provides isolated conversations, agents, and access control.
    Projects have owners (full control) and members (configured access).
    
    Attributes:
        id: Internal primary key.
        project_id: UUID for external reference.
        project_name: Human-readable project name.
        owner_id: User ID of the project owner.
        created_at: Project creation timestamp.
        updated_at: Last modification timestamp.
        disable_authentication: Skip auth for this project.
        disable_message_storage: Don't persist messages for this project.
        owner: Relationship to owner User.
        members: Users with access to this project.
        agents: AI agents configured for this project.
        ad_groups: AD groups with project access.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    project_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    project_name = Column(String(255), nullable=False, unique=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    disable_authentication = Column(Boolean, default=False, nullable=False)
    disable_message_storage = Column(Boolean, default=True, nullable=False)
    site_builder_enabled = Column(Boolean, default=True, nullable=False)
    description = Column(String(500), nullable=True)
    default_view = deferred(Column(String(10), default="site", nullable=False))
    view_locked = deferred(Column(Boolean, default=False, nullable=False))
    is_artefact = Column(Boolean, default=False, nullable=False)  # DEPRECATED: use Agent.is_artefact
    artefact_visibility = Column(String(20), default="private", nullable=False)  # DEPRECATED

    owner = relationship("User", back_populates="owned_projects")
    members = relationship("User", secondary=project_members, back_populates="projects")
    agents = relationship("Agent", back_populates="project", cascade="all, delete-orphan")
    ad_groups = relationship("ProjectADGroup", back_populates="project", cascade="all, delete-orphan")


class Agent(Base):
    """
    AI agent configuration for a project.
    
    Stores connection details, authentication, and settings for AI agents
    that can be used within a project's conversations.
    
    Attributes:
        id: Primary key.
        project_id: Foreign key to owning project.
        name: Display name for the agent.
        endpoint: API endpoint URL.
        connection_type: Connector type ('http', 'langgraph', 'openai').
        is_default: Whether this is the project's default agent.
        extras: JSON field for connector-specific configuration.
        auth: JSON field for authentication config.
        icon: Optional icon URL or base64 data.
        created_at: Creation timestamp.
        updated_at: Last modification timestamp.
        project: Relationship to parent Project.
    """
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    endpoint = Column(String(512), nullable=False)
    connection_type = Column(String(50), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    extras = Column(JSON, nullable=True)
    auth = Column(JSON, nullable=True)
    icon = Column(Text, nullable=True)
    is_artefact = Column(Boolean, default=False, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="agents")


class ProjectADGroup(Base):
    """
    Active Directory group association for project RBAC.
    
    Links AD/LDAP groups to projects, granting members of those groups
    access to the project with the specified role.
    
    Attributes:
        id: Primary key.
        project_id: Foreign key to project.
        group_dn: Full AD distinguished name of the group.
        group_name: Human-readable group name.
        role: Access role ('member', 'admin').
        added_at: When the group was linked.
        project: Relationship to parent Project.
    """
    __tablename__ = "project_ad_groups"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    group_dn = Column(String(512), nullable=False)
    group_name = Column(String(255), nullable=False)
    role = Column(String(50), default="member")
    added_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="ad_groups")


class MemberAgentPermission(Base):
    """
    Per-user agent access permissions within a project.
    
    Controls which specific agents a user can access, enabling
    fine-grained agent visibility per team member.
    
    Attributes:
        id: Primary key.
        user_id: Foreign key to user.
        project_id: Foreign key to project.
        agent_id: Foreign key to permitted agent.
        created_at: When permission was granted.
    """
    __tablename__ = "member_agent_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ADGroupAgentPermission(Base):
    """
    AD group-level agent access permissions.
    
    Controls which agents members of an AD group can access,
    enabling group-based agent visibility management.
    
    Attributes:
        id: Primary key.
        ad_group_id: Foreign key to project AD group.
        agent_id: Foreign key to permitted agent.
        created_at: When permission was granted.
    """
    __tablename__ = "ad_group_agent_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_group_id = Column(Integer, ForeignKey("project_ad_groups.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Approval Workflow Models ---

class ProjectApprover(Base):
    """
    Designated approvers for a project's change requests.
    
    Users in this list can approve or reject pending changes
    in production environments.
    
    Attributes:
        id: Primary key.
        project_id: Foreign key to project.
        user_id: Foreign key to user who can approve.
        added_by: User ID who added this approver.
        created_at: When the approver was added.
    """
    __tablename__ = "project_approvers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectApprovalSettings(Base):
    """
    Approval configuration for a project.
    
    Defines how approvals are evaluated (any single approver,
    all approvers, or majority).
    
    Attributes:
        id: Primary key.
        project_id: Foreign key to project (unique).
        approval_type: 'any', 'all', or 'majority'.
        updated_at: Last modification timestamp.
    """
    __tablename__ = "project_approval_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    approval_type = Column(String(20), default="any", nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChangeRequest(Base):
    """
    Pending change request requiring approval.
    
    Stores proposed changes to agents that must be approved
    before being applied in production environments.
    
    Attributes:
        id: Primary key.
        project_id: Foreign key to project.
        agent_id: Foreign key to agent (nullable for create requests).
        request_type: 'create', 'update', or 'delete'.
        requested_by: User ID who initiated the change.
        payload: JSON containing the proposed changes.
        status: 'pending', 'approved', or 'rejected'.
        approval_type: Snapshot of project's approval_type at creation.
        required_approvals: Number of approvals needed.
        current_approvals: Current count of approvals received.
        created_at: When the request was created.
        resolved_at: When the request was approved/rejected.
    """
    __tablename__ = "change_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    request_type = Column(String(20), nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    approval_type = Column(String(20), default="any", nullable=False)
    required_approvals = Column(Integer, default=1, nullable=False)
    current_approvals = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class ApprovalAction(Base):
    """
    Individual approval or rejection action on a change request.
    
    Records each approver's decision with optional comment.
    
    Attributes:
        id: Primary key.
        change_request_id: Foreign key to change request.
        user_id: User ID who performed the action.
        action: 'approve' or 'reject'.
        comment: Optional explanation for the decision.
        created_at: When the action was taken.
    """
    __tablename__ = "approval_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    change_request_id = Column(Integer, ForeignKey("change_requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False)
    comment = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentVersion(Base):
    """
    Version history for agent configurations.
    
    Stores snapshots of agent state for audit trail and rollback.
    
    Attributes:
        id: Primary key.
        agent_id: Foreign key to agent.
        version_number: Incrementing version number per agent.
        snapshot: JSON containing full agent configuration at this version.
        created_by: User ID who created this version.
        change_request_id: Optional link to the change request that created this version.
        created_at: When the version was created.
    """
    __tablename__ = "agent_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_request_id = Column(Integer, ForeignKey("change_requests.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UsageEvent(Base):
    """Lightweight analytics event recorded on every assistant response.

    Written regardless of disable_message_storage so analytics always work.
    One row per assistant turn: who chatted, which agent, when.
    """
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class WorkbenchAccessGrant(Base):
    """
    Controls who can access the Workbench.

    Platform admins manage these grants via the Admin panel.
    Access is granted either to individual users (by LAN ID / username)
    or to AD groups (by distinguished name).
    """
    __tablename__ = "workbench_access_grants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grant_type = Column(String(20), nullable=False)  # 'user' or 'ad_group'
    grant_value = Column(String(512), nullable=False)  # username or AD group DN
    display_name = Column(String(255), nullable=True)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("grant_type", "grant_value", name="uq_workbench_grant_type_value"),
    )


# Database operations

def validate_project_name(name: str) -> str:
    """Validate and normalize a project name for URL-safe usage.

    Rules:
    - Strips whitespace and lowercases
    - Only allows [a-z0-9_-]
    - Cannot be empty, start with hyphen/underscore, or exceed 63 chars

    Returns the normalized name or raises ValueError.
    """
    name = name.strip().lower()
    if not name:
        raise ValueError("Project name cannot be empty.")
    if len(name) > 63:
        raise ValueError("Project name cannot exceed 63 characters.")
    if name[0] in ('-', '_'):
        raise ValueError("Project name cannot start with a hyphen or underscore.")
    if not re.fullmatch(r'[a-z0-9_-]+', name):
        raise ValueError(
            "Project name can only contain lowercase letters, numbers, hyphens, and underscores."
        )
    return name


def create_project(owner_id: int, project_name: str,
                   disable_authentication: bool = False,
                   disable_message_storage: bool = True) -> dict:
    """Create a new project and add owner as a member."""
    project_name = validate_project_name(project_name)
    from core.db.db_chat import User
    db = get_db()
    session = db.get_session()
    try:
        # Enforce unique project name at the application level
        existing = session.query(Project).filter(
            Project.project_name == project_name
        ).first()
        if existing:
            raise ValueError(f"A project named '{project_name}' already exists.")

        project = Project(
            owner_id=owner_id,
            project_name=project_name,
            disable_authentication=disable_authentication,
            disable_message_storage=disable_message_storage
        )
        session.add(project)
        session.flush()  # Get project.id before adding member

        # Add owner as a member with 'owner' role
        owner = session.query(User).filter(User.id == owner_id).first()
        if owner:
            project.members.append(owner)

        session.commit()
        session.refresh(project)

        return {
            "id": project.id,
            "project_id": project.project_id,
            "project_name": project.project_name,
            "owner_id": project.owner_id,
            "disable_authentication": project.disable_authentication,
            "disable_message_storage": project.disable_message_storage,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_project_by_id(project_id: str) -> Optional[dict]:
    """Get a project by its project_id (UUID string)."""
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()

        if not project:
            return None

        return {
            "id": project.id,
            "project_id": project.project_id,
            "project_name": project.project_name,
            "owner_id": project.owner_id,
            "disable_authentication": project.disable_authentication,
            "disable_message_storage": project.disable_message_storage,
            "members": [{"id": m.id, "username": m.username} for m in project.members],
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    finally:
        session.close()


def get_project_by_id_internal(internal_id: int) -> Optional[dict]:
    """Get a project by its internal database ID."""
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.id == internal_id
        ).first()

        if not project:
            return None

        return {
            "id": project.id,
            "project_id": project.project_id,
            "project_name": project.project_name,
            "owner_id": project.owner_id,
            "disable_authentication": project.disable_authentication,
            "disable_message_storage": project.disable_message_storage,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    finally:
        session.close()


def list_all_projects() -> List[dict]:
    """List all projects with owner info and member count. For platform admin use."""
    from core.db.db_chat import User
    db = get_db()
    session = db.get_session()
    try:
        projects = session.query(Project).all()
        result = []
        for p in projects:
            owner = session.query(User).filter(User.id == p.owner_id).first()
            member_count = session.query(func.count(project_members.c.user_id)).filter(
                project_members.c.project_id == p.id
            ).scalar() or 0
            agent_count = session.query(func.count(Agent.id)).filter(
                Agent.project_id == p.id
            ).scalar() or 0
            result.append({
                "id": p.id,
                "project_id": p.project_id,
                "project_name": p.project_name,
                "owner": owner.username if owner else "unknown",
                "member_count": member_count,
                "agent_count": agent_count,
                "description": getattr(p, 'description', None),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
        return result
    finally:
        session.close()


def list_projects_for_user(user_id: int, ad_groups: Optional[List[str]] = None) -> List[dict]:
    """List all projects a user has access to via direct membership OR AD group.
    
    Access is granted through:
    1. Direct membership in project_members table
    2. AD group membership matching project_ad_groups table
    
    Args:
        user_id: The user's database ID
        ad_groups: List of AD group DNs from the user's JWT token (loaded from LDAP at login)
    """
    from core.db.db_chat import User
    from sqlalchemy import select
    db = get_db()
    session = db.get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # Track projects by ID to avoid duplicates
        projects_dict = {}

        # 1. Query projects via direct membership
        stmt = select(
            Project,
            project_members.c.role
        ).join(
            project_members, Project.id == project_members.c.project_id
        ).where(
            project_members.c.user_id == user_id
        )

        direct_results = session.execute(stmt).fetchall()

        for p, role in direct_results:
            projects_dict[p.id] = {
                "id": p.id,
                "project_id": p.project_id,
                "project_name": p.project_name,
                "owner_id": p.owner_id,
                "disable_authentication": p.disable_authentication,
                "disable_message_storage": p.disable_message_storage,
                "site_builder_enabled": getattr(p, 'site_builder_enabled', True),
                "description": getattr(p, 'description', None),
                "default_view": getattr(p, 'default_view', 'site'),
                "view_locked": getattr(p, 'view_locked', False),
                "is_owner": p.owner_id == user_id,
                "role": role or "member",
                "is_admin": role in ("admin", "owner") or p.owner_id == user_id,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
                "access_via": "direct"
            }

        # 2. Query projects via AD group membership (from JWT token)
        if ad_groups:
            # Find projects where user's AD groups match configured project AD groups
            ad_group_projects = session.query(
                Project, ProjectADGroup.role, ProjectADGroup.group_name
            ).join(
                ProjectADGroup, Project.id == ProjectADGroup.project_id
            ).filter(
                ProjectADGroup.group_dn.in_(ad_groups)
            ).all()

            for p, ad_role, group_name in ad_group_projects:
                if p.id not in projects_dict:
                    # User only has access via AD group
                    projects_dict[p.id] = {
                        "id": p.id,
                        "project_id": p.project_id,
                        "project_name": p.project_name,
                        "owner_id": p.owner_id,
                        "disable_authentication": p.disable_authentication,
                        "disable_message_storage": p.disable_message_storage,
                        "site_builder_enabled": getattr(p, 'site_builder_enabled', True),
                        "description": getattr(p, 'description', None),
                        "default_view": getattr(p, 'default_view', 'site'),
                        "view_locked": getattr(p, 'view_locked', False),
                        "is_owner": False,
                        "role": ad_role or "member",
                        "is_admin": ad_role == "admin",
                        "created_at": p.created_at.isoformat(),
                        "updated_at": p.updated_at.isoformat(),
                        "access_via": f"ad_group:{group_name}"
                    }
                else:
                    # User has both direct and AD group access
                    # Keep higher privilege role
                    existing = projects_dict[p.id]
                    if ad_role == "admin" and existing["role"] == "member":
                        existing["role"] = "admin"
                        existing["is_admin"] = True

        return list(projects_dict.values())
    finally:
        session.close()


def get_user_role_in_project(user_id: int, project_id: str) -> Optional[str]:
    """Get a user's role in a project. Returns 'owner', 'admin', 'member', or None if not a member."""
    from sqlalchemy import select
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()
        if not project:
            return None

        # Owner always gets 'owner' role regardless of what's in the association table
        if project.owner_id == user_id:
            return "owner"

        role = session.execute(
            select(project_members.c.role).where(
                project_members.c.user_id == user_id,
                project_members.c.project_id == project.id,
            )
        ).scalar_one_or_none()

        return role  # "admin", "member", or None
    finally:
        session.close()


def add_member_to_project(project_id: str, user_id: int) -> bool:
    """Add a user as a member to a project."""
    from core.db.db_chat import User
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()
        user = session.query(User).filter(User.id == user_id).first()

        if not project or not user:
            return False

        if user not in project.members:
            project.members.append(user)
            session.commit()

        return True
    finally:
        session.close()


def remove_member_from_project(project_id: str, user_id: int) -> bool:
    """Remove a user from a project (cannot remove owner)."""
    from core.db.db_chat import User
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()
        user = session.query(User).filter(User.id == user_id).first()

        if not project or not user:
            return False

        # Cannot remove the owner
        if project.owner_id == user_id:
            return False

        if user in project.members:
            project.members.remove(user)
            session.commit()

        return True
    finally:
        session.close()


def get_project_members(project_id: str) -> List[dict]:
    """Get all members of a project."""
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()

        if not project:
            return []

        return [
            {
                "id": m.id,
                "username": m.username,
                "is_owner": m.id == project.owner_id,
                "joined_at": m.created_at.isoformat()
            }
            for m in project.members
        ]
    finally:
        session.close()


def update_project(project_id: str, project_name: Optional[str] = None,
                   disable_authentication: Optional[bool] = None,
                   disable_message_storage: Optional[bool] = None,
                   site_builder_enabled: Optional[bool] = None,
                   description: Optional[str] = None,
                   default_view: Optional[str] = None,
                   view_locked: Optional[bool] = None) -> Optional[dict]:
    """Update a project's settings."""
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()

        if not project:
            return None

        if project_name is not None:
            project_name = validate_project_name(project_name)
            project.project_name = project_name

        if disable_authentication is not None:
            project.disable_authentication = disable_authentication

        if disable_message_storage is not None:
            project.disable_message_storage = disable_message_storage

        if site_builder_enabled is not None:
            project.site_builder_enabled = site_builder_enabled

        if description is not None:
            project.description = description

        if default_view is not None:
            project.default_view = default_view

        if view_locked is not None:
            project.view_locked = view_locked

        session.commit()
        session.refresh(project)

        return {
            "id": project.id,
            "project_id": project.project_id,
            "project_name": project.project_name,
            "owner_id": project.owner_id,
            "disable_authentication": project.disable_authentication,
            "disable_message_storage": project.disable_message_storage,
            "site_builder_enabled": getattr(project, 'site_builder_enabled', True),
            "description": getattr(project, 'description', None),
            "default_view": getattr(project, 'default_view', 'site'),
            "view_locked": getattr(project, 'view_locked', False),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_project(project_id: str) -> bool:
    """Delete a project by its project_id with comprehensive cleanup.
    
    Cleans up:
    - member_agent_permissions (not cascaded)
    - ad_group_agent_permissions (not cascaded)
    - approval_actions (via change_requests)
    - agent_versions (via agents)
    - change_requests
    - project_approvers
    - project_approval_settings
    - project_dashboards, form_submissions, site_analytics_events
    - usage_events
    - Dynamic {project_name}_conversation and {project_name}_messages tables
    - Project record (cascades to agents, project_ad_groups, project_members)
    """
    from core.db.db_chat import delete_project_tables
    from core.db.db_dashboard import ProjectDashboard, FormSubmission, SiteAnalyticsEvent

    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()

        if not project:
            return False

        project_internal_id = project.id
        project_name = project.project_name

        # 1. Delete member_agent_permissions for this project
        session.query(MemberAgentPermission).filter(
            MemberAgentPermission.project_id == project_internal_id
        ).delete()

        # 2. Delete ad_group_agent_permissions for this project's AD groups
        ad_group_ids = [g.id for g in project.ad_groups]
        if ad_group_ids:
            session.query(ADGroupAgentPermission).filter(
                ADGroupAgentPermission.ad_group_id.in_(ad_group_ids)
            ).delete(synchronize_session='fetch')

        # 3. Delete approval-related records (order matters due to FKs)
        agent_ids = [a.id for a in project.agents]
        change_request_ids = [
            cr.id for cr in session.query(ChangeRequest.id).filter(
                ChangeRequest.project_id == project_internal_id
            ).all()
        ]
        if change_request_ids:
            session.query(ApprovalAction).filter(
                ApprovalAction.change_request_id.in_(change_request_ids)
            ).delete(synchronize_session='fetch')
        if agent_ids:
            session.query(AgentVersion).filter(
                AgentVersion.agent_id.in_(agent_ids)
            ).delete(synchronize_session='fetch')
        session.query(ChangeRequest).filter(
            ChangeRequest.project_id == project_internal_id
        ).delete()
        session.query(ProjectApprover).filter(
            ProjectApprover.project_id == project_internal_id
        ).delete()
        session.query(ProjectApprovalSettings).filter(
            ProjectApprovalSettings.project_id == project_internal_id
        ).delete()

        # 4. Delete dashboard-related records
        session.query(SiteAnalyticsEvent).filter(
            SiteAnalyticsEvent.project_id == project_internal_id
        ).delete()
        session.query(FormSubmission).filter(
            FormSubmission.project_id == project_internal_id
        ).delete()
        session.query(ProjectDashboard).filter(
            ProjectDashboard.project_id == project_internal_id
        ).delete()

        # 5. Delete usage events
        session.query(UsageEvent).filter(
            UsageEvent.project_id == project_internal_id
        ).delete()

        # 6. Delete the project record (cascades to agents, ad_groups, project_members)
        session.delete(project)
        session.commit()
        
        # 4. Drop dynamic conversation/messages tables (after commit to avoid FK issues)
        try:
            delete_project_tables(project_name)
        except Exception:
            logger.opt(exception=True).error("Failed to delete project tables for {}", project_name)
        
        return True
    finally:
        session.close()


def delete_project_by_name(project_name: str) -> bool:
    """Delete a project by its project_name with comprehensive cleanup."""
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_name == project_name
        ).first()
        
        if not project:
            return False
        
        return delete_project(project.project_id)
    finally:
        session.close()


def get_project_by_name(project_name: str) -> Optional[dict]:
    """Get a project by its project_name."""
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_name == project_name
        ).first()

        if not project:
            return None

        return {
            "id": project.id,
            "project_id": project.project_id,
            "project_name": project.project_name,
            "owner_id": project.owner_id,
            "disable_authentication": project.disable_authentication,
            "disable_message_storage": project.disable_message_storage,
            "site_builder_enabled": getattr(project, 'site_builder_enabled', True),
            "description": getattr(project, 'description', None),
            "default_view": getattr(project, 'default_view', 'site'),
            "view_locked": getattr(project, 'view_locked', False),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    finally:
        session.close()


# Agent CRUD operations

def create_agent(project_id: int, name: str, endpoint: str, connection_type: str,
                 is_default: bool = False, extras: Optional[dict] = None,
                 auth: Optional[dict] = None, icon: Optional[str] = None,
                 is_artefact: bool = False, description: Optional[str] = None) -> dict:
    """Create a new agent for a project."""
    db = get_db()
    session = db.get_session()
    try:
        # If this agent is set as default, unset any existing default
        if is_default:
            session.query(Agent).filter(
                Agent.project_id == project_id,
                Agent.is_default == True
            ).update({"is_default": False})

        agent = Agent(
            project_id=project_id,
            name=name,
            endpoint=endpoint,
            connection_type=connection_type,
            is_default=is_default,
            extras=extras,
            auth=auth,
            icon=icon,
            is_artefact=is_artefact,
            description=description,
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)

        return {
            "id": agent.id,
            "project_id": agent.project_id,
            "name": agent.name,
            "description": getattr(agent, 'description', None),
            "endpoint": agent.endpoint,
            "connection_type": agent.connection_type,
            "is_default": agent.is_default,
            "extras": agent.extras,
            "auth": agent.auth,
            "icon": agent.icon,
            "is_artefact": agent.is_artefact,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def list_agents_for_project(project_id: int) -> List[dict]:
    """List all agents for a project."""
    db = get_db()
    session = db.get_session()
    try:
        agents = session.query(Agent).filter(Agent.project_id == project_id).all()
        result = []
        for a in agents:
            # Get current version number
            latest_version = session.query(AgentVersion).filter(
                AgentVersion.agent_id == a.id
            ).order_by(AgentVersion.version_number.desc()).first()
            
            result.append({
                "id": a.id,
                "project_id": a.project_id,
                "name": a.name,
                "description": getattr(a, 'description', None),
                "endpoint": a.endpoint,
                "connection_type": a.connection_type,
                "is_default": a.is_default,
                "extras": a.extras,
                "auth": a.auth,
                "icon": a.icon,
                "is_artefact": a.is_artefact,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat(),
                "current_version": latest_version.version_number if latest_version else 0,
            })
        return result
    finally:
        session.close()


def get_agent_by_id(agent_id: int) -> Optional[dict]:
    """Get an agent by its ID."""
    db = get_db()
    session = db.get_session()
    try:
        agent = session.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        return {
            "id": agent.id,
            "project_id": agent.project_id,
            "name": agent.name,
            "endpoint": agent.endpoint,
            "connection_type": agent.connection_type,
            "is_default": agent.is_default,
            "extras": agent.extras,
            "auth": agent.auth,
            "icon": agent.icon,
            "is_artefact": agent.is_artefact,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def get_agent_by_name(project_id: int, agent_name: str) -> Optional[dict]:
    """Get an agent by its name within a project."""
    db = get_db()
    session = db.get_session()
    try:
        agent = session.query(Agent).filter(
            Agent.project_id == project_id,
            Agent.name == agent_name
        ).first()
        if not agent:
            return None

        return {
            "id": agent.id,
            "project_id": agent.project_id,
            "name": agent.name,
            "endpoint": agent.endpoint,
            "connection_type": agent.connection_type,
            "is_default": agent.is_default,
            "extras": agent.extras,
            "auth": agent.auth,
            "icon": agent.icon,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def get_default_agent_for_project(project_id: int) -> Optional[dict]:
    """Get the default agent for a project, or the first agent if no default is set."""
    db = get_db()
    session = db.get_session()
    try:
        # Try to find the default agent
        agent = session.query(Agent).filter(
            Agent.project_id == project_id,
            Agent.is_default == True
        ).first()
        
        # If no default, get the first agent
        if not agent:
            agent = session.query(Agent).filter(
                Agent.project_id == project_id
            ).first()
        
        if not agent:
            return None

        return {
            "id": agent.id,
            "project_id": agent.project_id,
            "name": agent.name,
            "endpoint": agent.endpoint,
            "connection_type": agent.connection_type,
            "is_default": agent.is_default,
            "extras": agent.extras,
            "auth": agent.auth,
            "icon": agent.icon,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def get_agent_by_graph_id(project_id: int, graph_id: str) -> Optional[dict]:
    """Get an agent by graph_id (assistant_id in extras) within a project."""
    db = get_db()
    session = db.get_session()
    try:
        agents = session.query(Agent).filter(
            Agent.project_id == project_id
        ).all()
        
        # Search for agent with matching assistant_id in extras
        for agent in agents:
            if agent.extras and isinstance(agent.extras, dict):
                assistant_id = agent.extras.get("assistant_id")
                if assistant_id == graph_id:
                    return {
                        "id": agent.id,
                        "project_id": agent.project_id,
                        "name": agent.name,
                        "endpoint": agent.endpoint,
                        "connection_type": agent.connection_type,
                        "is_default": agent.is_default,
                        "extras": agent.extras,
                        "auth": agent.auth,
                        "icon": agent.icon,
                        "created_at": agent.created_at.isoformat(),
                        "updated_at": agent.updated_at.isoformat()
                    }
        return None
    finally:
        session.close()


def update_agent(agent_id: int, name: Optional[str] = None, endpoint: Optional[str] = None,
                 connection_type: Optional[str] = None, is_default: Optional[bool] = None,
                 extras: Optional[dict] = None, auth: Optional[dict] = None, icon: Optional[str] = None,
                 is_artefact: Optional[bool] = None, description: Optional[str] = None) -> Optional[dict]:
    """Update an agent's details."""
    db = get_db()
    session = db.get_session()
    try:
        agent = session.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        if name is not None:
            agent.name = name
        if endpoint is not None:
            agent.endpoint = endpoint
        if connection_type is not None:
            agent.connection_type = connection_type
        if is_default is not None:
            # If setting as default, unset any existing default for this project
            if is_default:
                session.query(Agent).filter(
                    Agent.project_id == agent.project_id,
                    Agent.id != agent_id,
                    Agent.is_default == True
                ).update({"is_default": False})
            agent.is_default = is_default
        if extras is not None:
            agent.extras = extras
        if auth is not None:
            agent.auth = auth
        if icon is not None:
            agent.icon = icon
        if is_artefact is not None:
            agent.is_artefact = is_artefact
        if description is not None:
            agent.description = description

        session.commit()
        session.refresh(agent)

        return {
            "id": agent.id,
            "project_id": agent.project_id,
            "name": agent.name,
            "description": getattr(agent, 'description', None),
            "endpoint": agent.endpoint,
            "connection_type": agent.connection_type,
            "is_default": agent.is_default,
            "extras": agent.extras,
            "auth": agent.auth,
            "icon": agent.icon,
            "is_artefact": agent.is_artefact,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_agent(agent_id: int) -> bool:
    """Delete an agent by its ID, cleaning up all FK references first."""
    db = get_db()
    session = db.get_session()
    try:
        agent = session.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False

        # Clean up all FK references to this agent
        session.query(AgentVersion).filter(AgentVersion.agent_id == agent_id).delete()
        session.query(MemberAgentPermission).filter(MemberAgentPermission.agent_id == agent_id).delete()
        session.query(ADGroupAgentPermission).filter(ADGroupAgentPermission.agent_id == agent_id).delete()
        session.query(ChangeRequest).filter(ChangeRequest.agent_id == agent_id).update({"agent_id": None})
        session.query(UsageEvent).filter(UsageEvent.agent_id == agent_id).update({"agent_id": None})

        session.delete(agent)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.opt(exception=True).error("Failed to delete agent {}: {}", agent_id, e)
        return False
    finally:
        session.close()


# ProjectADGroup CRUD operations

def add_ad_group_to_project(project_id: int, group_dn: str, group_name: str, role: str = "member") -> dict:
    """Add an AD group to a project."""
    db = get_db()
    session = db.get_session()
    try:
        ad_group = ProjectADGroup(
            project_id=project_id,
            group_dn=group_dn,
            group_name=group_name,
            role=role
        )
        session.add(ad_group)
        session.commit()
        session.refresh(ad_group)

        return {
            "id": ad_group.id,
            "project_id": ad_group.project_id,
            "group_dn": ad_group.group_dn,
            "group_name": ad_group.group_name,
            "role": ad_group.role,
            "added_at": ad_group.added_at.isoformat()
        }
    finally:
        session.close()


def list_ad_groups_for_project(project_id: int) -> List[dict]:
    """List all AD groups for a project with their agent permissions."""
    db = get_db()
    session = db.get_session()
    try:
        groups = session.query(ProjectADGroup).filter(ProjectADGroup.project_id == project_id).all()
        result = []
        for g in groups:
            # Get agent permissions for this group
            agent_permissions = session.query(ADGroupAgentPermission).filter(
                ADGroupAgentPermission.ad_group_id == g.id
            ).all()
            agent_ids = [p.agent_id for p in agent_permissions]
            
            result.append({
                "id": g.id,
                "project_id": g.project_id,
                "group_dn": g.group_dn,
                "group_name": g.group_name,
                "role": g.role,
                "added_at": g.added_at.isoformat(),
                "agent_ids": agent_ids
            })
        return result
    finally:
        session.close()


def update_ad_group_role(group_id: int, role: str) -> Optional[dict]:
    """Update an AD group's role."""
    db = get_db()
    session = db.get_session()
    try:
        group = session.query(ProjectADGroup).filter(ProjectADGroup.id == group_id).first()
        if not group:
            return None

        group.role = role
        session.commit()
        session.refresh(group)

        return {
            "id": group.id,
            "project_id": group.project_id,
            "group_dn": group.group_dn,
            "group_name": group.group_name,
            "role": group.role,
            "added_at": group.added_at.isoformat()
        }
    finally:
        session.close()


def remove_ad_group_from_project(group_id: int) -> bool:
    """Remove an AD group from a project."""
    db = get_db()
    session = db.get_session()
    try:
        group = session.query(ProjectADGroup).filter(ProjectADGroup.id == group_id).first()
        if not group:
            return False

        # Also remove agent permissions for this group
        session.query(ADGroupAgentPermission).filter(
            ADGroupAgentPermission.ad_group_id == group_id
        ).delete()

        session.delete(group)
        session.commit()
        return True
    finally:
        session.close()


# AD Group Agent Permission operations

def get_ad_group_agent_permissions(ad_group_id: int) -> List[int]:
    """Get list of agent IDs that an AD group has access to."""
    db = get_db()
    session = db.get_session()
    try:
        permissions = session.query(ADGroupAgentPermission).filter(
            ADGroupAgentPermission.ad_group_id == ad_group_id
        ).all()
        return [p.agent_id for p in permissions]
    finally:
        session.close()


def set_ad_group_agent_permissions(ad_group_id: int, project_id: int, agent_ids: List[int]) -> List[int]:
    """Set the agent permissions for an AD group. Replaces existing permissions."""
    db = get_db()
    session = db.get_session()
    try:
        # Delete existing permissions
        session.query(ADGroupAgentPermission).filter(
            ADGroupAgentPermission.ad_group_id == ad_group_id
        ).delete()
        
        # Add new permissions
        for agent_id in agent_ids:
            # Verify agent belongs to this project
            agent = session.query(Agent).filter(
                Agent.id == agent_id,
                Agent.project_id == project_id
            ).first()
            if agent:
                permission = ADGroupAgentPermission(
                    ad_group_id=ad_group_id,
                    agent_id=agent_id
                )
                session.add(permission)
        
        session.commit()
        return agent_ids
    finally:
        session.close()


# LAN ID (Username) operations - uses project_members table

def add_member_by_username(project_id: int, username: str, role: str = "member") -> Optional[dict]:
    """Add a user to project by their LAN ID (username). Creates user if doesn't exist. Username comparison is case-insensitive."""
    from core.db.db_chat import User
    from sqlalchemy import insert
    # Normalize username to lowercase for case-insensitive handling
    normalized_username = username.lower()
    db = get_db()
    session = db.get_session()
    try:
        # Case-insensitive lookup: find user by lowercase username
        user = session.query(User).filter(func.lower(User.username) == normalized_username).first()
        if not user:
            user = User(username=normalized_username)
            session.add(user)
            session.flush()
        
        # Check if already a member
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
            
        if user in project.members:
            # Update role if already a member
            session.execute(
                project_members.update()
                .where(project_members.c.user_id == user.id)
                .where(project_members.c.project_id == project_id)
                .values(role=role)
            )
        else:
            # Add as new member
            session.execute(
                insert(project_members).values(
                    user_id=user.id,
                    project_id=project_id,
                    role=role,
                    joined_at=datetime.utcnow()
                )
            )
        
        session.commit()
        
        return {
            "user_id": user.id,
            "username": user.username,
            "role": role,
            "project_id": project_id
        }
    finally:
        session.close()


def update_member_role(project_id: int, user_id: int, role: str) -> Optional[dict]:
    """Update a member's role in the project."""
    from core.db.db_chat import User
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        # Can't change owner's role
        if project.owner_id == user_id:
            return None
        
        user = session.query(User).filter(User.id == user_id).first()
        if not user or user not in project.members:
            return None
        
        session.execute(
            project_members.update()
            .where(project_members.c.user_id == user_id)
            .where(project_members.c.project_id == project_id)
            .values(role=role)
        )
        session.commit()
        
        return {
            "user_id": user.id,
            "username": user.username,
            "role": role,
            "project_id": project_id
        }
    finally:
        session.close()


def remove_member_by_id(project_id: int, user_id: int) -> bool:
    """Remove a member from project by user_id. Cannot remove owner."""
    from core.db.db_chat import User
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # Cannot remove owner
        if project.owner_id == user_id:
            return False
        
        user = session.query(User).filter(User.id == user_id).first()
        if not user or user not in project.members:
            return False
        
        # Also remove agent permissions for this member
        session.query(MemberAgentPermission).filter(
            MemberAgentPermission.user_id == user_id,
            MemberAgentPermission.project_id == project_id
        ).delete()
        
        project.members.remove(user)
        session.commit()
        return True
    finally:
        session.close()


# Member Agent Permission operations

def get_member_agent_permissions(project_id: int, user_id: int) -> List[int]:
    """Get list of agent IDs that a member has access to."""
    db = get_db()
    session = db.get_session()
    try:
        permissions = session.query(MemberAgentPermission).filter(
            MemberAgentPermission.project_id == project_id,
            MemberAgentPermission.user_id == user_id
        ).all()
        return [p.agent_id for p in permissions]
    finally:
        session.close()


def set_member_agent_permissions(project_id: int, user_id: int, agent_ids: List[int]) -> List[int]:
    """Set the agent permissions for a member. Replaces existing permissions."""
    db = get_db()
    session = db.get_session()
    try:
        # Delete existing permissions
        session.query(MemberAgentPermission).filter(
            MemberAgentPermission.project_id == project_id,
            MemberAgentPermission.user_id == user_id
        ).delete()
        
        # Add new permissions
        for agent_id in agent_ids:
            # Verify agent belongs to this project
            agent = session.query(Agent).filter(
                Agent.id == agent_id,
                Agent.project_id == project_id
            ).first()
            if agent:
                permission = MemberAgentPermission(
                    user_id=user_id,
                    project_id=project_id,
                    agent_id=agent_id
                )
                session.add(permission)
        
        session.commit()
        return agent_ids
    finally:
        session.close()


def list_project_members_with_roles(project_id: int) -> List[dict]:
    """List all members of a project with their roles and agent permissions."""
    from core.db.db_chat import User
    from sqlalchemy import select
    db = get_db()
    session = db.get_session()
    try:
        # Query members with roles from association table
        stmt = select(
            User.id,
            User.username,
            User.created_at,
            project_members.c.role,
            project_members.c.joined_at
        ).join(
            project_members, User.id == project_members.c.user_id
        ).where(
            project_members.c.project_id == project_id
        )
        
        results = session.execute(stmt).fetchall()
        
        project = session.query(Project).filter(Project.id == project_id).first()
        owner_id = project.owner_id if project else None
        
        members = []
        for row in results:
            # Get agent permissions for this member
            agent_permissions = session.query(MemberAgentPermission).filter(
                MemberAgentPermission.user_id == row.id,
                MemberAgentPermission.project_id == project_id
            ).all()
            agent_ids = [p.agent_id for p in agent_permissions]
            
            members.append({
                "user_id": row.id,
                "username": row.username,
                "role": row.role or "member",
                "is_owner": row.id == owner_id,
                "joined_at": row.joined_at.isoformat() if row.joined_at else None,
                "agent_ids": agent_ids
            })
        
        return members
    finally:
        session.close()


def record_chat_interaction(project_id: int, agent_id: int, user_id: int) -> None:
    """Record one analytics event per assistant response.

    Always called regardless of disable_message_storage so that usage stats
    (interactions, active users, monthly breakdown) are always populated.
    """
    db = get_db()
    session = db.get_session()
    try:
        event = UsageEvent(
            project_id=project_id,
            agent_id=agent_id,
            user_id=user_id,
        )
        session.add(event)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_project_usage_by_agent(project_name: str) -> dict:
    """Get usage statistics grouped by agent and month for a project.

    Queries the usage_events table which is written on every assistant response
    regardless of the disable_message_storage setting.
    """
    from sqlalchemy import func, distinct
    from datetime import datetime, timedelta

    project = get_project_by_name(project_name)
    if not project:
        return {
            "project_name": project_name,
            "total_messages": 0,
            "total_tokens": 0,
            "total_interactions": 0,
            "by_agent": {},
            "by_month": {}
        }

    project_id = project["id"]
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    db = get_db()
    session = db.get_session()
    try:
        # Per-agent: total interactions and distinct users all-time
        usage_rows = (
            session.query(
                Agent.id.label("agent_db_id"),
                Agent.name.label("agent_name"),
                func.count(UsageEvent.id).label("interactions"),
                func.count(distinct(UsageEvent.user_id)).label("total_users"),
            )
            .join(UsageEvent, UsageEvent.agent_id == Agent.id)
            .filter(UsageEvent.project_id == project_id)
            .group_by(Agent.id, Agent.name)
            .all()
        )

        # Active users per agent in the last 7 days
        active_rows = (
            session.query(
                UsageEvent.agent_id,
                func.count(distinct(UsageEvent.user_id)).label("active_users"),
            )
            .filter(
                UsageEvent.project_id == project_id,
                UsageEvent.created_at >= seven_days_ago,
            )
            .group_by(UsageEvent.agent_id)
            .all()
        )
        active_by_agent_id = {r.agent_id: r.active_users for r in active_rows}

        # Build by_agent dict keyed by agent name
        by_agent = {}
        total_interactions = 0
        for row in usage_rows:
            active_users = active_by_agent_id.get(row.agent_db_id, 0)
            by_agent[row.agent_name] = {
                "message_count": 0,
                "total_tokens": 0,
                "total_users": int(row.total_users or 0),
                "active_users": int(active_users),
                "interactions": int(row.interactions or 0),
            }
            total_interactions += int(row.interactions or 0)

        # Monthly breakdown: interactions and distinct users per agent per month
        monthly_rows = (
            session.query(
                func.date_trunc("month", UsageEvent.created_at).label("month"),
                Agent.name.label("agent_name"),
                func.count(UsageEvent.id).label("interactions"),
                func.count(distinct(UsageEvent.user_id)).label("user_count"),
            )
            .join(Agent, UsageEvent.agent_id == Agent.id)
            .filter(UsageEvent.project_id == project_id)
            .group_by(func.date_trunc("month", UsageEvent.created_at), Agent.name)
            .order_by(func.date_trunc("month", UsageEvent.created_at).desc())
            .all()
        )

        by_month = {}
        for row in monthly_rows:
            month_key = row.month.strftime("%Y-%m") if hasattr(row.month, "strftime") else str(row.month)[:7]
            if month_key not in by_month:
                by_month[month_key] = {}
            by_month[month_key][row.agent_name] = {
                "message_count": 0,
                "total_tokens": 0,
                "interactions": int(row.interactions or 0),
                "user_count": int(row.user_count or 0),
            }

        return {
            "project_name": project_name,
            "total_messages": 0,
            "total_tokens": 0,
            "total_interactions": total_interactions,
            "by_agent": by_agent,
            "by_month": by_month,
        }
    finally:
        session.close()


def get_all_projects_usage() -> List[dict]:
    """Get usage statistics for all projects."""
    db = get_db()
    session = db.get_session()
    try:
        # Get all projects
        projects = session.query(Project).all()

        if not projects:
            return []

        result = []
        for project in projects:
            # Get usage for this project
            usage = get_project_usage_by_agent(project.project_name)

            # Get conversation count
            from core.db.db_chat import (
                get_conversation_table_class,
                ensure_project_tables_exist
            )
            ensure_project_tables_exist(project.project_name)
            ConversationClass = get_conversation_table_class(project.project_name)
            conversation_count = session.query(ConversationClass).count()

            # Get agent count
            agent_count = session.query(Agent).filter(
                Agent.project_id == project.id
            ).count()

            # Add additional metadata
            usage["total_conversations"] = conversation_count
            usage["total_agents"] = agent_count

            # Site analytics (if dashboard exists)
            try:
                from core.db.db_dashboard import get_site_analytics, get_dashboard_for_project
                if get_dashboard_for_project(project.id):
                    usage["site_analytics"] = get_site_analytics(project.id, period_days=7)
            except Exception:
                pass

            result.append(usage)

        return result
    finally:
        session.close()


def list_all_user_agents(user_id: int, ad_groups: Optional[List[str]] = None) -> List[dict]:
    """Return all agents across every project the user has access to,
    plus agents from global projects (disable_authentication=True).

    Calls list_projects_for_user to resolve accessible projects, then queries
    agents for each project. Also includes agents from projects with
    disable_authentication enabled, making them visible to all users.
    Returns a flat list with project_name injected.
    """
    db = get_db()
    session = db.get_session()
    try:
        projects = list_projects_for_user(user_id, ad_groups)
        project_ids = [p["id"] for p in projects] if projects else []
        project_name_by_id = {p["id"]: p["project_name"] for p in projects} if projects else {}

        agents = list(session.query(Agent).filter(Agent.project_id.in_(project_ids)).all()) if project_ids else []

        # Also include agents from global projects (disable_authentication=True)
        global_filter = [Project.disable_authentication == True]
        if project_ids:
            global_filter.append(~Project.id.in_(project_ids))
        global_projects = session.query(Project).filter(*global_filter).all()
        if global_projects:
            global_ids = [gp.id for gp in global_projects]
            for gp in global_projects:
                project_name_by_id[gp.id] = gp.project_name
            global_agents = session.query(Agent).filter(Agent.project_id.in_(global_ids)).all()
            agents.extend(global_agents)

        # Fetch usage stats per project (keyed by project_name then agent_name)
        project_usage_cache = {}

        result = []
        projects_with_agents = set()
        for a in agents:
            proj_name = project_name_by_id.get(a.project_id)
            if a.project_id:
                projects_with_agents.add(a.project_id)
            # Lazy-load usage for this project once
            if proj_name and proj_name not in project_usage_cache:
                try:
                    usage = get_project_usage_by_agent(proj_name)
                    project_usage_cache[proj_name] = usage.get("by_agent", {})
                except Exception:
                    project_usage_cache[proj_name] = {}
            by_agent = project_usage_cache.get(proj_name, {})
            agent_stats = by_agent.get(a.name, {})
            result.append({
                "id": a.id,
                "name": a.name,
                "description": getattr(a, "description", None),
                "endpoint": a.endpoint,
                "connection_type": a.connection_type,
                "is_default": a.is_default,
                "is_artefact": a.is_artefact,
                "icon": a.icon,
                "project_name": proj_name,
                "project_id": a.project_id,
                "active_users": agent_stats.get("active_users", 0),
                "interactions": agent_stats.get("interactions", 0),
            })

        # Enrich agent entries with site interaction counts
        from core.db.db_dashboard import get_projects_with_dashboards, get_site_analytics, get_project_site_interaction_count
        all_agent_project_ids = list(projects_with_agents)
        agent_proj_with_dash = get_projects_with_dashboards(all_agent_project_ids) if all_agent_project_ids else []
        site_counts_by_pid = {}
        for pid in agent_proj_with_dash:
            try:
                site_counts_by_pid[pid] = get_project_site_interaction_count(pid)
            except Exception:
                pass
        for entry in result:
            entry["site_interactions"] = site_counts_by_pid.get(entry.get("project_id"), 0)

        # Include virtual entries for projects with dashboards but no agents
        all_project_ids = list(project_name_by_id.keys())
        agentless_ids = [pid for pid in all_project_ids if pid not in projects_with_agents]
        if agentless_ids:
            ids_with_dash = get_projects_with_dashboards(agentless_ids)
            for pid in ids_with_dash:
                proj_name = project_name_by_id.get(pid)
                # Fetch site analytics for active users and interactions
                try:
                    analytics = get_site_analytics(pid, period_days=7)
                except Exception:
                    analytics = {}
                summary = analytics.get("summary", {})
                result.append({
                    "id": None,
                    "name": proj_name,
                    "description": "Project site",
                    "endpoint": None,
                    "connection_type": "site",
                    "is_default": False,
                    "is_artefact": False,
                    "icon": None,
                    "project_name": proj_name,
                    "project_id": pid,
                    "active_users": summary.get("unique_users", 0),
                    "interactions": summary.get("interactions", 0),
                    "page_views": summary.get("page_views", 0),
                    "is_site": True,
                })

        return result
    finally:
        session.close()


def get_user_total_interactions(user_id: int, ad_groups: Optional[List[str]] = None) -> int:
    """Return total interactions (chat + site) across all projects the user can access."""
    from core.db.db_dashboard import get_project_site_interaction_count
    projects = list_projects_for_user(user_id, ad_groups)
    total = 0
    for p in projects:
        try:
            usage = get_project_usage_by_agent(p["project_name"])
            total += usage.get("total_interactions", 0)
        except Exception:
            pass
        try:
            total += get_project_site_interaction_count(p["id"])
        except Exception:
            pass
    return total


def list_artefact_agents() -> list:
    """List all agents from projects that have at least one agent or site builder enabled.

    Projects with no agents AND site_builder_enabled=False are excluded
    from the hub since they have no content to show.
    """
    db = get_db()
    session = db.get_session()
    try:
        agents = (
            session.query(Agent)
            .join(Project, Project.id == Agent.project_id)
            .all()
        )

        # Collect projects that have agents
        projects_with_agents = set()
        result = []
        for a in agents:
            projects_with_agents.add(a.project_id)
            project = session.query(Project).filter(Project.id == a.project_id).first()
            result.append({
                "agent_id": a.id,
                "agent_name": a.name,
                "icon": a.icon,
                "project_name": project.project_name if project else None,
                "project_id": project.project_id if project else None,
                "connection_type": a.connection_type,
                "site_builder_enabled": project.site_builder_enabled if project else False,
            })

        # Also include site-builder-enabled projects that have no agents
        site_only_projects = (
            session.query(Project)
            .filter(
                Project.site_builder_enabled == True,
                ~Project.id.in_(projects_with_agents) if projects_with_agents else True,
            )
            .all()
        )
        for p in site_only_projects:
            result.append({
                "agent_id": None,
                "agent_name": p.project_name,
                "icon": None,
                "project_name": p.project_name,
                "project_id": p.project_id,
                "connection_type": None,
                "site_builder_enabled": True,
            })

        return result
    finally:
        session.close()


# DEPRECATED: Use agent-level is_artefact instead
def set_artefact(project_id: str, is_artefact: bool, visibility: str = "org") -> Optional[dict]:
    """Enable or disable artefact mode for a project. DEPRECATED: use agent-level is_artefact."""
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()
        if not project:
            return None
        project.is_artefact = is_artefact
        project.artefact_visibility = visibility if is_artefact else "private"
        project.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(project)
        return _project_to_dict(project)
    finally:
        session.close()


# DEPRECATED: Use list_artefact_agents() instead
def list_artefacts(user_id: int, ad_groups: list = None) -> list:
    """List all artefacts accessible to the given user. DEPRECATED: use list_artefact_agents().

    Returns projects marked as artefacts that the user can access:
    - public artefacts: visible to all authenticated users
    - org artefacts: visible to members/users with any project membership
    - private artefacts: only visible to project members
    """
    db = get_db()
    session = db.get_session()
    try:
        artefacts = session.query(Project).filter(
            Project.is_artefact == True
        ).all()

        result = []
        for project in artefacts:
            if project.artefact_visibility == "public":
                result.append(_artefact_to_dict(project))
            elif project.artefact_visibility == "org":
                result.append(_artefact_to_dict(project))
            elif project.artefact_visibility == "private":
                # Only show to members
                member_ids = [m.id for m in project.members]
                if user_id in member_ids:
                    result.append(_artefact_to_dict(project))
        return result
    finally:
        session.close()


def _project_to_dict(project: Project) -> dict:
    """Convert a Project ORM object to a dictionary."""
    return {
        "id": project.id,
        "project_id": project.project_id,
        "project_name": project.project_name,
        "owner_id": project.owner_id,
        "disable_authentication": project.disable_authentication,
        "disable_message_storage": project.disable_message_storage,
        "is_artefact": project.is_artefact,
        "artefact_visibility": project.artefact_visibility,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat()
    }


def _artefact_to_dict(project: Project) -> dict:
    """Convert a Project to an artefact-focused dictionary."""
    return {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "artefact_visibility": project.artefact_visibility,
        "created_at": project.created_at.isoformat(),
    }


# --- Workbench Access Grant operations ---

def list_workbench_grants() -> list:
    """Return all workbench access grants."""
    from core.db.db_chat import User
    db = get_db()
    session = db.get_session()
    try:
        grants = session.query(WorkbenchAccessGrant).order_by(
            WorkbenchAccessGrant.created_at.desc()
        ).all()
        result = []
        for g in grants:
            grantor = session.query(User).filter(User.id == g.granted_by).first()
            result.append({
                "id": g.id,
                "grant_type": g.grant_type,
                "grant_value": g.grant_value,
                "display_name": g.display_name,
                "granted_by": grantor.username if grantor else str(g.granted_by),
                "created_at": g.created_at.isoformat(),
            })
        return result
    finally:
        session.close()


def add_workbench_grant(grant_type: str, grant_value: str,
                        display_name: str | None, granted_by: int) -> dict:
    """Add a workbench access grant. Raises ValueError on duplicate."""
    db = get_db()
    session = db.get_session()
    try:
        grant = WorkbenchAccessGrant(
            grant_type=grant_type,
            grant_value=grant_value.strip().lower() if grant_type == "user" else grant_value.strip(),
            display_name=display_name,
            granted_by=granted_by,
        )
        session.add(grant)
        session.commit()
        session.refresh(grant)
        return {
            "id": grant.id,
            "grant_type": grant.grant_type,
            "grant_value": grant.grant_value,
            "display_name": grant.display_name,
            "granted_by": granted_by,
            "created_at": grant.created_at.isoformat(),
        }
    except IntegrityError:
        session.rollback()
        raise ValueError(f"A grant for '{grant_value}' already exists.")
    finally:
        session.close()


def remove_workbench_grant(grant_id: int) -> bool:
    """Remove a workbench access grant by ID. Returns True if deleted."""
    db = get_db()
    session = db.get_session()
    try:
        grant = session.query(WorkbenchAccessGrant).filter(
            WorkbenchAccessGrant.id == grant_id
        ).first()
        if not grant:
            return False
        session.delete(grant)
        session.commit()
        return True
    finally:
        session.close()


def has_workbench_access(username: str, ad_groups: list | None = None) -> bool:
    """Check if a user has workbench access via a direct grant or AD group grant."""
    db = get_db()
    session = db.get_session()
    try:
        # Check direct user grant (case-insensitive)
        user_grant = session.query(WorkbenchAccessGrant).filter(
            WorkbenchAccessGrant.grant_type == "user",
            func.lower(WorkbenchAccessGrant.grant_value) == username.lower(),
        ).first()
        if user_grant:
            return True

        # Check AD group grants
        if ad_groups:
            ad_lower = [g.lower() for g in ad_groups]
            group_grant = session.query(WorkbenchAccessGrant).filter(
                WorkbenchAccessGrant.grant_type == "ad_group",
                func.lower(WorkbenchAccessGrant.grant_value).in_(ad_lower),
            ).first()
            if group_grant:
                return True

        return False
    finally:
        session.close()
