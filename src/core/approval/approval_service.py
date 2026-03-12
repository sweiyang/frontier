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


def is_approval_required(project_id: int) -> bool:
    """Check if approval is required for changes to this project."""
    cfg = get_config()
    if not cfg.is_production:
        return False

    if not cfg.approval_enabled:
        return False

    if not cfg.approval_require_for_agent_config:
        return False

    approvers = list_approvers(project_id)
    if not approvers:
        _auto_add_owner_as_approver(project_id)
        approvers = list_approvers(project_id)
        if not approvers:
            logger.warning(f"Project {project_id} has no approvers and owner could not be added")
            return False

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


def list_approvers(project_id: int) -> List[dict]:
    """List all approvers for a project."""
    db = get_db()
    session = db.get_session()
    try:
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

        if not settings:
            return {
                "project_id": project_id,
                "approval_type": "any",
                "approval_required": is_approval_required(project_id),
            }

        return {
            "project_id": settings.project_id,
            "approval_type": settings.approval_type,
            "approval_required": is_approval_required(project_id),
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

        cr = ChangeRequest(
            project_id=project_id,
            agent_id=agent_id,
            request_type=request_type,
            requested_by=requested_by,
            payload=payload,
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
            result.append({
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
        payload = cr.payload
        if cr.request_type == "create":
            agent = db_project.create_agent(
                project_id=cr.project_id,
                name=payload.get("name"),
                endpoint=payload.get("endpoint"),
                connector_type=payload.get("connector_type", "openai"),
                extras=payload.get("extras"),
                auth=payload.get("auth"),
                is_default=payload.get("is_default", False),
            )
            if agent:
                create_agent_version(agent["id"], cr.requested_by, cr.id)
            return bool(agent)

        elif cr.request_type == "update":
            agent = db_project.update_agent(
                agent_id=cr.agent_id,
                name=payload.get("name"),
                endpoint=payload.get("endpoint"),
                connector_type=payload.get("connector_type"),
                extras=payload.get("extras"),
                auth=payload.get("auth"),
                is_default=payload.get("is_default"),
            )
            if agent:
                create_agent_version(cr.agent_id, cr.requested_by, cr.id)
            return bool(agent)

        elif cr.request_type == "delete":
            create_agent_version(cr.agent_id, cr.requested_by, cr.id)
            return db_project.delete_agent(cr.agent_id)

        return False
    except Exception as e:
        logger.error(f"Failed to apply change request {cr.id}: {e}")
        return False


def approve_change_request(request_id: int, user_id: int, comment: Optional[str] = None) -> Optional[dict]:
    """Approve a change request."""
    db = get_db()
    session = db.get_session()
    try:
        cr = session.query(ChangeRequest).filter(ChangeRequest.id == request_id).first()
        if not cr or cr.status != "pending":
            return None

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
            _apply_change_request(cr, session)
        else:
            session.commit()

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
