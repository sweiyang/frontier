from datetime import datetime
from typing import List, Optional, Any
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, JSON, Boolean
from sqlalchemy.orm import relationship
from conduit.core.db.db import Base, Database


# Association table for many-to-many relationship between users and projects
project_members = Table(
    "project_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("role", String(50), default="member"),  # owner, admin, member
    Column("joined_at", DateTime, default=datetime.utcnow)
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    project_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    project_name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="owned_projects")
    members = relationship("User", secondary=project_members, back_populates="projects")
    agents = relationship("Agent", back_populates="project", cascade="all, delete-orphan")
    ad_groups = relationship("ProjectADGroup", back_populates="project", cascade="all, delete-orphan")


class Agent(Base):
    """Agent table for storing AI agent connection details per project."""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    endpoint = Column(String(512), nullable=False)
    connection_type = Column(String(50), nullable=False)  # e.g., "http", "websocket", "grpc"
    is_default = Column(Boolean, default=False, nullable=False)  # Whether this is the default agent
    extras = Column(JSON, nullable=True)  # Flexible field for additional config
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="agents")


class ProjectADGroup(Base):
    """AD/LDAP group memberships for project RBAC."""
    __tablename__ = "project_ad_groups"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    group_dn = Column(String(512), nullable=False)  # AD distinguished name
    group_name = Column(String(255), nullable=False)  # Display name
    role = Column(String(50), default="member")  # member, admin
    added_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="ad_groups")


# Database operations

def _get_db() -> Database:
    """Get the database instance."""
    from conduit.core.db.db_chat import get_db
    return get_db()


def create_project(owner_id: int, project_name: str) -> dict:
    """Create a new project and add owner as a member."""
    from conduit.core.db.db_chat import User
    db = _get_db()
    session = db.get_session()
    try:
        project = Project(
            owner_id=owner_id,
            project_name=project_name
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
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    finally:
        session.close()


def get_project_by_id(project_id: str) -> Optional[dict]:
    """Get a project by its project_id."""
    db = _get_db()
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
            "members": [{"id": m.id, "username": m.username} for m in project.members],
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    finally:
        session.close()


def list_projects_for_user(user_id: int) -> List[dict]:
    """List all projects a user is a member of."""
    from conduit.core.db.db_chat import User
    db = _get_db()
    session = db.get_session()
    print(User, user_id)
    try:
        user = session.query(User).filter(User.id == user_id).first()
        print(user)
        if not user:
            return []

        return [
            {
                "id": p.id,
                "project_id": p.project_id,
                "project_name": p.project_name,
                "owner_id": p.owner_id,
                "is_owner": p.owner_id == user_id,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            }
            for p in user.projects
        ]
    finally:
        session.close()


def add_member_to_project(project_id: str, user_id: int) -> bool:
    """Add a user as a member to a project."""
    from conduit.core.db.db_chat import User
    db = _get_db()
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
    from conduit.core.db.db_chat import User
    db = _get_db()
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
    db = _get_db()
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


def update_project(project_id: str, project_name: str) -> Optional[dict]:
    """Update a project's name."""
    db = _get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()

        if not project:
            return None

        project.project_name = project_name
        session.commit()
        session.refresh(project)

        return {
            "id": project.id,
            "project_id": project.project_id,
            "project_name": project.project_name,
            "owner_id": project.owner_id,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    finally:
        session.close()


def delete_project(project_id: str) -> bool:
    """Delete a project by its project_id."""
    db = _get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(
            Project.project_id == project_id
        ).first()

        if not project:
            return False

        session.delete(project)
        session.commit()
        return True
    finally:
        session.close()


def get_project_by_name(project_name: str) -> Optional[dict]:
    """Get a project by its project_name."""
    db = _get_db()
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
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    finally:
        session.close()


# Agent CRUD operations

def create_agent(project_id: int, name: str, endpoint: str, connection_type: str, 
                 is_default: bool = False, extras: Optional[dict] = None) -> dict:
    """Create a new agent for a project."""
    db = _get_db()
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
            extras=extras
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)

        return {
            "id": agent.id,
            "project_id": agent.project_id,
            "name": agent.name,
            "endpoint": agent.endpoint,
            "connection_type": agent.connection_type,
            "is_default": agent.is_default,
            "extras": agent.extras,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def list_agents_for_project(project_id: int) -> List[dict]:
    """List all agents for a project."""
    db = _get_db()
    session = db.get_session()
    try:
        agents = session.query(Agent).filter(Agent.project_id == project_id).all()
        return [
            {
                "id": a.id,
                "project_id": a.project_id,
                "name": a.name,
                "endpoint": a.endpoint,
                "connection_type": a.connection_type,
                "is_default": a.is_default,
                "extras": a.extras,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat()
            }
            for a in agents
        ]
    finally:
        session.close()


def get_agent_by_id(agent_id: int) -> Optional[dict]:
    """Get an agent by its ID."""
    db = _get_db()
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
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def get_agent_by_name(project_id: int, agent_name: str) -> Optional[dict]:
    """Get an agent by its name within a project."""
    db = _get_db()
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
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def get_default_agent_for_project(project_id: int) -> Optional[dict]:
    """Get the default agent for a project, or the first agent if no default is set."""
    db = _get_db()
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
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def update_agent(agent_id: int, name: Optional[str] = None, endpoint: Optional[str] = None, 
                 connection_type: Optional[str] = None, is_default: Optional[bool] = None,
                 extras: Optional[dict] = None) -> Optional[dict]:
    """Update an agent's details."""
    db = _get_db()
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

        session.commit()
        session.refresh(agent)

        return {
            "id": agent.id,
            "project_id": agent.project_id,
            "name": agent.name,
            "endpoint": agent.endpoint,
            "connection_type": agent.connection_type,
            "is_default": agent.is_default,
            "extras": agent.extras,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def delete_agent(agent_id: int) -> bool:
    """Delete an agent by its ID."""
    db = _get_db()
    session = db.get_session()
    try:
        agent = session.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False

        session.delete(agent)
        session.commit()
        return True
    finally:
        session.close()


# ProjectADGroup CRUD operations

def add_ad_group_to_project(project_id: int, group_dn: str, group_name: str, role: str = "member") -> dict:
    """Add an AD group to a project."""
    db = _get_db()
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
    """List all AD groups for a project."""
    db = _get_db()
    session = db.get_session()
    try:
        groups = session.query(ProjectADGroup).filter(ProjectADGroup.project_id == project_id).all()
        return [
            {
                "id": g.id,
                "project_id": g.project_id,
                "group_dn": g.group_dn,
                "group_name": g.group_name,
                "role": g.role,
                "added_at": g.added_at.isoformat()
            }
            for g in groups
        ]
    finally:
        session.close()


def update_ad_group_role(group_id: int, role: str) -> Optional[dict]:
    """Update an AD group's role."""
    db = _get_db()
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
    db = _get_db()
    session = db.get_session()
    try:
        group = session.query(ProjectADGroup).filter(ProjectADGroup.id == group_id).first()
        if not group:
            return False

        session.delete(group)
        session.commit()
        return True
    finally:
        session.close()
