"""Version management service for agent configurations."""

import logging
from datetime import datetime
from typing import Optional, List

from core.db.db_chat import get_db, User
from core.db.db_project import AgentVersion, Agent

logger = logging.getLogger(__name__)


def create_agent_version(
    agent_id: int,
    user_id: int,
    change_request_id: Optional[int] = None
) -> Optional[dict]:
    """Create a new version snapshot of an agent's configuration."""
    db = get_db()
    session = db.get_session()
    try:
        agent = session.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        last_version = session.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.version_number.desc()).first()

        new_version_number = (last_version.version_number + 1) if last_version else 1

        snapshot = {
            "name": agent.name,
            "endpoint": agent.endpoint,
            "connection_type": agent.connection_type,
            "extras": agent.extras,
            "is_default": agent.is_default,
            "auth": agent.auth,
            "icon": agent.icon,
            "approval_required": agent.approval_required,
        }

        version = AgentVersion(
            agent_id=agent_id,
            version_number=new_version_number,
            snapshot=snapshot,
            created_by=user_id,
            change_request_id=change_request_id,
            created_at=datetime.utcnow(),
        )
        session.add(version)
        session.commit()

        user = session.query(User).filter(User.id == user_id).first()

        return {
            "id": version.id,
            "agent_id": version.agent_id,
            "version_number": version.version_number,
            "snapshot": version.snapshot,
            "created_by": version.created_by,
            "created_by_username": user.username if user else None,
            "change_request_id": version.change_request_id,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create agent version: {e}")
        return None
    finally:
        session.close()


def get_agent_versions(agent_id: int) -> List[dict]:
    """Get all versions for an agent."""
    db = get_db()
    session = db.get_session()
    try:
        versions = session.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.version_number.desc()).all()

        result = []
        for v in versions:
            user = session.query(User).filter(User.id == v.created_by).first()
            snapshot_display = dict(v.snapshot) if v.snapshot else {}
            if "auth" in snapshot_display:
                snapshot_display["auth"] = "[REDACTED]"

            result.append({
                "id": v.id,
                "agent_id": v.agent_id,
                "version_number": v.version_number,
                "snapshot": snapshot_display,
                "created_by": v.created_by,
                "created_by_username": user.username if user else None,
                "change_request_id": v.change_request_id,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            })
        return result
    finally:
        session.close()


def get_agent_version(agent_id: int, version_number: int) -> Optional[dict]:
    """Get a specific version of an agent."""
    db = get_db()
    session = db.get_session()
    try:
        version = session.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id,
            AgentVersion.version_number == version_number
        ).first()

        if not version:
            return None

        user = session.query(User).filter(User.id == version.created_by).first()
        snapshot_display = dict(version.snapshot) if version.snapshot else {}
        if "auth" in snapshot_display:
            snapshot_display["auth"] = "[REDACTED]"

        return {
            "id": version.id,
            "agent_id": version.agent_id,
            "version_number": version.version_number,
            "snapshot": snapshot_display,
            "created_by": version.created_by,
            "created_by_username": user.username if user else None,
            "change_request_id": version.change_request_id,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }
    finally:
        session.close()


def rollback_agent_to_version(
    agent_id: int,
    version_number: int,
    user_id: int
) -> Optional[dict]:
    """Rollback an agent to a previous version."""
    db = get_db()
    session = db.get_session()
    try:
        version = session.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id,
            AgentVersion.version_number == version_number
        ).first()

        if not version or not version.snapshot:
            return None

        agent = session.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        snapshot = version.snapshot
        agent.name = snapshot.get("name", agent.name)
        agent.endpoint = snapshot.get("endpoint", agent.endpoint)
        agent.connection_type = snapshot.get("connection_type", agent.connection_type)
        agent.extras = snapshot.get("extras", agent.extras)
        agent.is_default = snapshot.get("is_default", agent.is_default)
        if "auth" in snapshot and snapshot["auth"]:
            agent.auth = snapshot["auth"]
        if "icon" in snapshot:
            agent.icon = snapshot.get("icon")
        if "approval_required" in snapshot:
            agent.approval_required = snapshot.get("approval_required", False)

        session.commit()

        new_version = create_agent_version(agent_id, user_id)

        return {
            "agent_id": agent_id,
            "rolled_back_to_version": version_number,
            "new_version": new_version,
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to rollback agent to version: {e}")
        return None
    finally:
        session.close()
