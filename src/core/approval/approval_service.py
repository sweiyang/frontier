"""Approval workflow service for managing approvers and change requests."""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from core.config import get_config
from core.db.db_chat import get_db
from core.db.db_project import (
    ProjectApprover,
    ProjectApprovalSettings,
    ChangeRequest,
    ApprovalAction,
    Project,
    Agent,
)
from core.db.db_chat import User, get_or_create_user

logger = logging.getLogger(__name__)


def _auto_add_owner_as_approver(project_id: int) -> None:
    """Automatically add project owner as an approver if no approvers exist."""
    db = get_db()
    session = db.get_session()
    try:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project or not project.owner_id:
            return

        existing = session.query(ProjectApprover).filter(
            ProjectApprover.project_id == project_id,
            ProjectApprover.user_id == project.owner_id
        ).first()

        if not existing:
            approver = ProjectApprover(
                project_id=project_id,
                user_id=project.owner_id,
                added_by=project.owner_id,
                created_at=datetime.utcnow()
            )
            session.add(approver)
            session.commit()
            logger.info(f"Auto-added owner {project.owner_id} as approver for project {project_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to auto-add owner as approver: {e}")
    finally:
        session.close()


def is_approval_required(project_id: int, agent_data: Optional[Dict] = None) -> bool:
    """Check if approval is required for changes to this agent.

    Approval is per-agent: each agent's `approval_required` field controls
    whether changes need approval. The global `approval_enabled` config
    acts as a kill switch to disable all approval workflows.
    """
    cfg = get_config()

    if not cfg.approval_enabled:
        logger.info(f"Approval globally disabled, skipping for project {project_id}")
        return False

    if not agent_data or not agent_data.get("approval_required", False):
        logger.info(f"Agent does not require approval (project {project_id})")
        return False

    approvers = list_approvers(project_id, auto_add_owner=False)
    if not approvers:
        _auto_add_owner_as_approver(project_id)
        approvers = list_approvers(project_id, auto_add_owner=False)
        if not approvers:
            logger.warning(f"Project {project_id} has no approvers and owner could not be added")
            return False

    logger.info(f"Approval IS required for agent in project {project_id}")
    return True


def add_approver(project_id: int, user_id: int, added_by: int) -> Optional[dict]:
    """Add a user as an approver for a project."""
    db = get_db()
    session = db.get_session()
    try:
        existing = session.query(ProjectApprover).filter(
            ProjectApprover.project_id == project_id,
            ProjectApprover.user_id == user_id
        ).first()

        if existing:
            return None

        approver = ProjectApprover(
            project_id=project_id,
            user_id=user_id,
            added_by=added_by,
            created_at=datetime.utcnow()
        )
        session.add(approver)
        session.commit()

        user = session.query(User).filter(User.id == user_id).first()
        return {
            "id": approver.id,
            "project_id": approver.project_id,
            "user_id": approver.user_id,
            "username": user.username if user else None,
            "added_by": approver.added_by,
            "created_at": approver.created_at.isoformat() if approver.created_at else None,
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to add approver: {e}")
        return None
    finally:
        session.close()


def add_approver_by_username(project_id: int, username: str, added_by: int) -> Optional[dict]:
    """Add an approver by username."""
    user = get_or_create_user(username)
    if not user:
        return None
    return add_approver(project_id, user.id, added_by)


def remove_approver(project_id: int, user_id: int) -> bool:
    """Remove an approver from a project."""
    db = get_db()
    session = db.get_session()
    try:
        approver = session.query(ProjectApprover).filter(
            ProjectApprover.project_id == project_id,
            ProjectApprover.user_id == user_id
        ).first()

        if not approver:
            return False

        session.delete(approver)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to remove approver: {e}")
        return False
    finally:
        session.close()


def list_approvers(project_id: int, auto_add_owner: bool = True) -> List[dict]:
    """List all approvers for a project.
    
    Args:
        project_id: The project ID
        auto_add_owner: If True and no approvers exist, auto-add the owner
    """
    db = get_db()
    session = db.get_session()
    try:
        approvers = session.query(ProjectApprover).filter(
            ProjectApprover.project_id == project_id
        ).all()

        # Auto-add owner if no approvers exist
        if not approvers and auto_add_owner:
            session.close()
            _auto_add_owner_as_approver(project_id)
            session = db.get_session()
            approvers = session.query(ProjectApprover).filter(
                ProjectApprover.project_id == project_id
            ).all()

        result = []
        for a in approvers:
            user = session.query(User).filter(User.id == a.user_id).first()
            result.append({
                "id": a.id,
                "project_id": a.project_id,
                "user_id": a.user_id,
                "username": user.username if user else None,
                "added_by": a.added_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })
        return result
    finally:
        session.close()


def get_approval_settings(project_id: int) -> dict:
    """Get approval settings for a project."""
    db = get_db()
    session = db.get_session()
    try:
        settings = session.query(ProjectApprovalSettings).filter(
            ProjectApprovalSettings.project_id == project_id
        ).first()

        cfg = get_config()
        if not settings:
            return {
                "project_id": project_id,
                "approval_type": "any",
                "approval_enabled": cfg.approval_enabled,
            }

        return {
            "project_id": settings.project_id,
            "approval_type": settings.approval_type,
            "approval_enabled": cfg.approval_enabled,
        }
    finally:
        session.close()


def update_approval_settings(project_id: int, approval_type: str) -> dict:
    """Update approval settings for a project."""
    if approval_type not in ("any", "all", "majority"):
        raise ValueError("approval_type must be 'any', 'all', or 'majority'")

    db = get_db()
    session = db.get_session()
    try:
        settings = session.query(ProjectApprovalSettings).filter(
            ProjectApprovalSettings.project_id == project_id
        ).first()

        if settings:
            settings.approval_type = approval_type
        else:
            settings = ProjectApprovalSettings(
                project_id=project_id,
                approval_type=approval_type
            )
            session.add(settings)

        session.commit()

        return {
            "project_id": settings.project_id,
            "approval_type": settings.approval_type,
            "approval_required": is_approval_required(project_id),
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update approval settings: {e}")
        raise
    finally:
        session.close()


def create_change_request(
    project_id: int,
    request_type: str,
    requested_by: int,
    payload: Dict[str, Any],
    agent_id: Optional[int] = None,
) -> dict:
    """Create a new change request."""
    db = get_db()
    session = db.get_session()
    try:
        settings = get_approval_settings(project_id)
        approval_type = settings.get("approval_type", "any")
        approvers = list_approvers(project_id)

        if approval_type == "any":
            required_approvals = 1
        elif approval_type == "majority":
            required_approvals = (len(approvers) // 2) + 1
        else:
            required_approvals = len(approvers)

        # For update requests, capture the original agent state for diff comparison
        original_agent = None
        if request_type == "update" and agent_id:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                original_agent = {
                    "name": agent.name,
                    "endpoint": agent.endpoint,
                    "connection_type": agent.connection_type,
                    "is_default": agent.is_default,
                    "extras": agent.extras,
                    "auth": agent.auth,
                    "icon": agent.icon,
                    "approval_required": agent.approval_required,
                }

        # Store both the proposed changes (payload) and original state
        full_payload = {
            "proposed": payload,
            "original": original_agent,
        } if original_agent else payload

        cr = ChangeRequest(
            project_id=project_id,
            agent_id=agent_id,
            request_type=request_type,
            requested_by=requested_by,
            payload=full_payload,
            status="pending",
            approval_type=approval_type,
            required_approvals=required_approvals,
            current_approvals=0,
            created_at=datetime.utcnow(),
        )
        session.add(cr)
        session.commit()

        return {
            "id": cr.id,
            "project_id": cr.project_id,
            "agent_id": cr.agent_id,
            "request_type": cr.request_type,
            "requested_by": cr.requested_by,
            "payload": cr.payload,
            "status": cr.status,
            "approval_type": cr.approval_type,
            "required_approvals": cr.required_approvals,
            "current_approvals": cr.current_approvals,
            "created_at": cr.created_at.isoformat() if cr.created_at else None,
            "resolved_at": None,
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create change request: {e}")
        raise
    finally:
        session.close()


def get_change_request(request_id: int) -> Optional[dict]:
    """Get a change request by ID with approval actions."""
    db = get_db()
    session = db.get_session()
    try:
        cr = session.query(ChangeRequest).filter(ChangeRequest.id == request_id).first()
        if not cr:
            return None

        actions = session.query(ApprovalAction).filter(
            ApprovalAction.change_request_id == request_id
        ).all()

        approvals = []
        for a in actions:
            user = session.query(User).filter(User.id == a.user_id).first()
            approvals.append({
                "id": a.id,
                "user_id": a.user_id,
                "username": user.username if user else None,
                "action": a.action,
                "comment": a.comment,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })

        # Get requester username
        requester = session.query(User).filter(User.id == cr.requested_by).first()
        requester_username = requester.username if requester else None

        # Extract original and proposed from payload (new format)
        # Support both old format (just payload) and new format (proposed + original)
        payload_data = cr.payload
        if isinstance(payload_data, dict) and "proposed" in payload_data:
            proposed = payload_data.get("proposed")
            original_agent = payload_data.get("original")
        else:
            # Old format - payload is the proposed changes directly
            proposed = payload_data
            original_agent = None

        return {
            "id": cr.id,
            "project_id": cr.project_id,
            "agent_id": cr.agent_id,
            "request_type": cr.request_type,
            "requested_by": cr.requested_by,
            "requested_by_username": requester_username,
            "payload": proposed,
            "original_agent": original_agent,
            "status": cr.status,
            "approval_type": cr.approval_type,
            "required_approvals": cr.required_approvals,
            "current_approvals": cr.current_approvals,
            "approvals": approvals,
            "created_at": cr.created_at.isoformat() if cr.created_at else None,
            "resolved_at": cr.resolved_at.isoformat() if cr.resolved_at else None,
        }
    finally:
        session.close()


def list_change_requests(project_id: int, status: Optional[str] = None) -> List[dict]:
    """List change requests for a project."""
    db = get_db()
    session = db.get_session()
    try:
        query = session.query(ChangeRequest).filter(ChangeRequest.project_id == project_id)
        if status:
            query = query.filter(ChangeRequest.status == status)
        
        requests = query.order_by(ChangeRequest.created_at.desc()).all()

        result = []
        for cr in requests:
            # Get requester username
            requester = session.query(User).filter(User.id == cr.requested_by).first()
            requester_username = requester.username if requester else None

            result.append({
                "id": cr.id,
                "project_id": cr.project_id,
                "agent_id": cr.agent_id,
                "request_type": cr.request_type,
                "requested_by": cr.requested_by,
                "requested_by_username": requester_username,
                "payload": cr.payload,
                "status": cr.status,
                "approval_type": cr.approval_type,
                "required_approvals": cr.required_approvals,
                "current_approvals": cr.current_approvals,
                "created_at": cr.created_at.isoformat() if cr.created_at else None,
                "resolved_at": cr.resolved_at.isoformat() if cr.resolved_at else None,
            })
        return result
    finally:
        session.close()


def _apply_change_request(cr: ChangeRequest, session) -> bool:
    """Apply an approved change request."""
    from core.db import db_project
    from core.approval.version_service import create_agent_version

    try:
        # Handle both old format (just payload) and new format (proposed + original)
        raw_payload = cr.payload
        if isinstance(raw_payload, dict) and "proposed" in raw_payload:
            payload = raw_payload.get("proposed")
        else:
            payload = raw_payload

        logger.info(f"Applying change request {cr.id}, type: {cr.request_type}, agent_id: {cr.agent_id}")
        logger.info(f"Payload: {payload}")

        if cr.request_type == "create":
            agent = db_project.create_agent(
                project_id=cr.project_id,
                name=payload.get("name"),
                endpoint=payload.get("endpoint"),
                connection_type=payload.get("connection_type", "openai"),
                extras=payload.get("extras"),
                auth=payload.get("auth"),
                is_default=payload.get("is_default", False),
                icon=payload.get("icon"),
                is_artefact=payload.get("is_artefact", False),
                approval_required=payload.get("approval_required", False),
            )
            if agent:
                create_agent_version(agent["id"], cr.requested_by, cr.id)
            return bool(agent)

        elif cr.request_type == "update":
            logger.info(f"Updating agent {cr.agent_id} with: name={payload.get('name')}, endpoint={payload.get('endpoint')}, connection_type={payload.get('connection_type')}")
            agent = db_project.update_agent(
                agent_id=cr.agent_id,
                name=payload.get("name"),
                endpoint=payload.get("endpoint"),
                connection_type=payload.get("connection_type"),
                extras=payload.get("extras"),
                auth=payload.get("auth"),
                is_default=payload.get("is_default"),
                icon=payload.get("icon"),
                is_artefact=payload.get("is_artefact"),
                approval_required=payload.get("approval_required"),
            )
            logger.info(f"Update agent result: {agent}")
            if agent:
                create_agent_version(cr.agent_id, cr.requested_by, cr.id)
            else:
                logger.error(f"Failed to update agent {cr.agent_id}")
            return bool(agent)

        elif cr.request_type == "delete":
            create_agent_version(cr.agent_id, cr.requested_by, cr.id)
            return db_project.delete_agent(cr.agent_id)

        logger.warning(f"Unknown change request type '{cr.request_type}' for request {cr.id}")
        return False
    except (ValueError, TypeError, KeyError) as e:
        logger.exception(f"Invalid payload in change request {cr.id}: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error applying change request {cr.id}: {e}")
        return False


def approve_change_request(request_id: int, user_id: int, comment: Optional[str] = None) -> Optional[dict]:
    """Approve a change request.

    Uses SELECT FOR UPDATE to prevent race conditions when two approvers submit
    simultaneously. Only one transaction will increment the approval count and
    apply the change if the threshold is met.
    """
    db = get_db()
    session = db.get_session()
    try:
        # Lock the row for update to prevent concurrent approval races
        cr = (
            session.query(ChangeRequest)
            .filter(ChangeRequest.id == request_id)
            .with_for_update()
            .first()
        )
        if not cr or cr.status != "pending":
            return None

        # Prevent self-approval - requester cannot approve their own request
        if cr.requested_by == user_id:
            logger.warning(f"User {user_id} attempted to approve their own change request {request_id}")
            return {"error": "self_approval", "message": "You cannot approve your own change request"}

        existing = session.query(ApprovalAction).filter(
            ApprovalAction.change_request_id == request_id,
            ApprovalAction.user_id == user_id
        ).first()
        if existing:
            return None

        action = ApprovalAction(
            change_request_id=request_id,
            user_id=user_id,
            action="approve",
            comment=comment,
            created_at=datetime.utcnow(),
        )
        session.add(action)

        cr.current_approvals += 1

        if cr.current_approvals >= cr.required_approvals:
            cr.status = "approved"
            cr.resolved_at = datetime.utcnow()
            session.commit()
            logger.info(f"Change request {request_id} approved, applying changes...")
            result = _apply_change_request(cr, session)
            logger.info(f"Apply change request result: {result}")
        else:
            session.commit()
            logger.info(f"Change request {request_id} has {cr.current_approvals}/{cr.required_approvals} approvals, waiting for more")

        return get_change_request(request_id)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to approve change request: {e}")
        return None
    finally:
        session.close()


def reject_change_request(request_id: int, user_id: int, comment: str) -> Optional[dict]:
    """Reject a change request."""
    db = get_db()
    session = db.get_session()
    try:
        cr = session.query(ChangeRequest).filter(ChangeRequest.id == request_id).first()
        if not cr or cr.status != "pending":
            return None

        action = ApprovalAction(
            change_request_id=request_id,
            user_id=user_id,
            action="reject",
            comment=comment,
            created_at=datetime.utcnow(),
        )
        session.add(action)

        cr.status = "rejected"
        cr.resolved_at = datetime.utcnow()
        session.commit()

        return get_change_request(request_id)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to reject change request: {e}")
        return None
    finally:
        session.close()
