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
    auth = Column(JSON, nullable=True)  # {"auth_type": "bearer|basic|api_key", "credentials": str|{username, password}}
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


class MemberAgentPermission(Base):
    """Tracks which agents a member (LAN ID) can access within a project."""
    __tablename__ = "member_agent_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ADGroupAgentPermission(Base):
    """Tracks which agents an AD group can access within a project."""
    __tablename__ = "ad_group_agent_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_group_id = Column(Integer, ForeignKey("project_ad_groups.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


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
                 is_default: bool = False, extras: Optional[dict] = None,
                 auth: Optional[dict] = None) -> dict:
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
            extras=extras,
            auth=auth
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
            "auth": agent.auth,
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
                "auth": a.auth,
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
            "auth": agent.auth,
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
            "auth": agent.auth,
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
            "auth": agent.auth,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    finally:
        session.close()


def get_agent_by_graph_id(project_id: int, graph_id: str) -> Optional[dict]:
    """Get an agent by graph_id (assistant_id in extras) within a project."""
    db = _get_db()
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
                        "created_at": agent.created_at.isoformat(),
                        "updated_at": agent.updated_at.isoformat()
                    }
        return None
    finally:
        session.close()


def update_agent(agent_id: int, name: Optional[str] = None, endpoint: Optional[str] = None, 
                 connection_type: Optional[str] = None, is_default: Optional[bool] = None,
                 extras: Optional[dict] = None, auth: Optional[dict] = None) -> Optional[dict]:
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
        if auth is not None:
            agent.auth = auth

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
            "auth": agent.auth,
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
    """List all AD groups for a project with their agent permissions."""
    db = _get_db()
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
    db = _get_db()
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
    db = _get_db()
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
    """Add a user to project by their LAN ID (username). Creates user if doesn't exist."""
    from conduit.core.db.db_chat import User
    from sqlalchemy import insert
    db = _get_db()
    session = db.get_session()
    try:
        # Get or create user
        user = session.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
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
    from conduit.core.db.db_chat import User
    db = _get_db()
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
    from conduit.core.db.db_chat import User
    db = _get_db()
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
    db = _get_db()
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
    db = _get_db()
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
    from conduit.core.db.db_chat import User
    from sqlalchemy import select
    db = _get_db()
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


def get_project_usage_by_agent(project_name: str) -> dict:
    """Get usage statistics grouped by agent/model for a project."""
    from conduit.core.db.db_chat import (
        get_conversation_table_class,
        get_message_table_class,
        ensure_project_tables_exist
    )
    from sqlalchemy import func, distinct
    from datetime import datetime, timedelta
    
    # Ensure project tables exist
    ensure_project_tables_exist(project_name)
    
    # Get project-specific table classes
    ConversationClass = get_conversation_table_class(project_name)
    MessageClass = get_message_table_class(project_name)
    
    db = _get_db()
    session = db.get_session()
    try:
        # Get all conversations for this project
        conversations = session.query(ConversationClass).all()
        
        if not conversations:
            return {
                "project_name": project_name,
                "total_messages": 0,
                "total_tokens": 0,
                "by_agent": {}
            }
        
        conversation_ids = [c.id for c in conversations]
        
        # Calculate date threshold for active users (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Aggregate messages by model/agent with user statistics
        usage_query = session.query(
            MessageClass.model,
            func.count(MessageClass.id).label("message_count"),
            func.sum(MessageClass.token_count).label("total_tokens"),
            func.count(distinct(ConversationClass.user_id)).label("total_users")
        ).join(
            ConversationClass, MessageClass.conversation_id == ConversationClass.id
        ).filter(
            MessageClass.conversation_id.in_(conversation_ids),
            MessageClass.model.isnot(None)
        ).group_by(MessageClass.model)
        
        usage_results = usage_query.all()
        
        # Build usage by agent dictionary
        by_agent = {}
        total_messages = 0
        total_tokens = 0
        
        for result in usage_results:
            agent_name = result.model or "unknown"
            message_count = result.message_count or 0
            tokens = result.total_tokens or 0
            total_users = result.total_users or 0
            
            # Get active users (last 7 days) for this agent
            active_users_query = session.query(
                func.count(distinct(ConversationClass.user_id)).label("active_users")
            ).select_from(MessageClass).join(
                ConversationClass, MessageClass.conversation_id == ConversationClass.id
            ).filter(
                MessageClass.conversation_id.in_(conversation_ids),
                MessageClass.model == agent_name,
                MessageClass.created_at >= seven_days_ago
            )
            
            active_users_result = active_users_query.first()
            active_users = active_users_result.active_users if active_users_result else 0
            
            by_agent[agent_name] = {
                "message_count": message_count,
                "total_tokens": int(tokens) if tokens else 0,
                "total_users": int(total_users),
                "active_users": int(active_users)
            }
            
            total_messages += message_count
            total_tokens += int(tokens) if tokens else 0
        
        # Also get user message stats (no model specified)
        user_messages = session.query(
            func.count(MessageClass.id).label("message_count"),
            func.sum(MessageClass.token_count).label("total_tokens")
        ).filter(
            MessageClass.conversation_id.in_(conversation_ids),
            MessageClass.role == "user"
        ).first()
        
        if user_messages and user_messages.message_count:
            total_messages += user_messages.message_count
            total_tokens += int(user_messages.total_tokens) if user_messages.total_tokens else 0
        
        return {
            "project_name": project_name,
            "total_messages": total_messages,
            "total_tokens": int(total_tokens),
            "by_agent": by_agent
        }
    finally:
        session.close()


def get_all_projects_usage() -> List[dict]:
    """Get usage statistics for all projects."""
    db = _get_db()
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
            from conduit.core.db.db_chat import (
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
            
            result.append(usage)
        
        return result
    finally:
        session.close()
