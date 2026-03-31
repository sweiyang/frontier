"""Unit tests for approval_service.py using mocked DB sessions."""

from datetime import datetime
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_db(session):
    """Return a fake DB object whose get_session() yields *session*."""
    db = MagicMock()
    db.get_session.return_value = session
    return db


def _make_approver(project_id=1, user_id=10):
    a = MagicMock()
    a.id = 1
    a.project_id = project_id
    a.user_id = user_id
    a.added_by = 99
    a.created_at = datetime(2024, 1, 1)
    return a


def _make_change_request(
    cr_id=1,
    project_id=1,
    agent_id=5,
    requested_by=2,
    status="pending",
    approval_type="any",
    required_approvals=1,
    current_approvals=0,
    payload=None,
    request_type="update",
):
    cr = MagicMock()
    cr.id = cr_id
    cr.project_id = project_id
    cr.agent_id = agent_id
    cr.requested_by = requested_by
    cr.status = status
    cr.request_type = request_type
    cr.approval_type = approval_type
    cr.required_approvals = required_approvals
    cr.current_approvals = current_approvals
    cr.payload = payload or {"name": "my-agent", "endpoint": "http://localhost"}
    cr.created_at = datetime(2024, 1, 1)
    cr.resolved_at = None
    return cr


# ---------------------------------------------------------------------------
# list_approvers
# ---------------------------------------------------------------------------


class TestListApprovers:
    """Tests for list_approvers()."""

    def test_returns_list_when_approvers_exist(self):
        """Test that approvers are returned when they exist."""
        session = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "alice"

        approver = _make_approver(project_id=1, user_id=10)
        session.query.return_value.filter.return_value.all.return_value = [approver]
        session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch(
            "core.approval.approval_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.approval_service import list_approvers

            result = list_approvers(project_id=1, auto_add_owner=False)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["user_id"] == 10

    def test_returns_empty_list_when_no_approvers(self):
        """Test that empty list is returned when no approvers."""
        session = MagicMock()
        session.query.return_value.filter.return_value.all.return_value = []

        with patch(
            "core.approval.approval_service.get_db", return_value=_mock_db(session)
        ):
            with patch("core.approval.approval_service._auto_add_owner_as_approver"):
                from core.approval.approval_service import list_approvers

                result = list_approvers(project_id=1, auto_add_owner=False)

        assert result == []


# ---------------------------------------------------------------------------
# add_approver
# ---------------------------------------------------------------------------


class TestAddApprover:
    """Tests for add_approver()."""

    def test_adds_approver_successfully(self):
        """Test that adding an approver succeeds."""
        session = MagicMock()
        # No existing approver
        session.query.return_value.filter.return_value.first.side_effect = [None, None]

        mock_user = MagicMock()
        mock_user.username = "bob"

        with patch(
            "core.approval.approval_service.get_db", return_value=_mock_db(session)
        ):
            with patch(
                "core.approval.approval_service.ProjectApprover"
            ) as MockApprover:
                approver_instance = MagicMock()
                approver_instance.id = 1
                approver_instance.project_id = 1
                approver_instance.user_id = 10
                approver_instance.added_by = 99
                approver_instance.created_at = datetime(2024, 1, 1)
                MockApprover.return_value = approver_instance

                session.query.return_value.filter.return_value.first.side_effect = [
                    None,  # No existing approver
                    mock_user,  # User lookup
                ]

                from core.approval.approval_service import add_approver

                result = add_approver(project_id=1, user_id=10, added_by=99)

        assert result is not None
        assert result["user_id"] == 10

    def test_rejects_duplicate_approver(self):
        """Test that duplicate approver is rejected."""
        session = MagicMock()
        existing = _make_approver(project_id=1, user_id=10)
        session.query.return_value.filter.return_value.first.return_value = existing

        with patch(
            "core.approval.approval_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.approval_service import add_approver

            result = add_approver(project_id=1, user_id=10, added_by=99)

        assert result is None


# ---------------------------------------------------------------------------
# approve_change_request — threshold logic
# ---------------------------------------------------------------------------


class TestApproveChangeRequest:
    """Tests for approve_change_request()."""

    def test_self_approval_returns_error(self):
        """Requester should not be able to approve their own request."""
        session = MagicMock()
        cr = _make_change_request(requested_by=5, status="pending")
        session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = (
            cr
        )

        with patch(
            "core.approval.approval_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.approval_service import approve_change_request

            result = approve_change_request(request_id=1, user_id=5)

        assert result is not None
        assert result.get("error") == "self_approval"

    def test_already_resolved_returns_none(self):
        """Approving a non-pending request should return None."""
        session = MagicMock()
        cr = _make_change_request(status="approved")
        session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = (
            cr
        )

        with patch(
            "core.approval.approval_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.approval_service import approve_change_request

            result = approve_change_request(request_id=1, user_id=99)

        assert result is None

    def test_already_voted_returns_none(self):
        """A user who already voted should get None."""
        session = MagicMock()
        cr = _make_change_request(status="pending", requested_by=2)
        existing_action = MagicMock()

        def query_side_effect(model):
            """Mock query side effect."""
            q = MagicMock()
            if model.__name__ == "ChangeRequest":
                q.filter.return_value.with_for_update.return_value.first.return_value = (
                    cr
                )
            else:
                # ApprovalAction query — simulate already voted
                q.filter.return_value.first.return_value = existing_action
            return q

        session.query.side_effect = query_side_effect

        with patch(
            "core.approval.approval_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.approval_service import approve_change_request

            result = approve_change_request(request_id=1, user_id=99)

        assert result is None

    def test_approval_threshold_met_marks_approved(self):
        """When required approvals are met, status should become 'approved'."""
        session = MagicMock()
        cr = _make_change_request(
            status="pending",
            requested_by=2,
            required_approvals=1,
            current_approvals=0,
        )

        def query_side_effect(model):
            """Mock query side effect."""
            q = MagicMock()
            name = getattr(model, "__name__", "")
            if name == "ChangeRequest":
                q.filter.return_value.with_for_update.return_value.first.return_value = (
                    cr
                )
            else:
                # ApprovalAction / any other — no existing vote
                q.filter.return_value.first.return_value = None
            return q

        session.query.side_effect = query_side_effect

        with patch(
            "core.approval.approval_service.get_db", return_value=_mock_db(session)
        ):
            with patch(
                "core.approval.approval_service._apply_change_request",
                return_value=True,
            ):
                with patch(
                    "core.approval.approval_service.get_change_request"
                ) as mock_get:
                    mock_get.return_value = {"id": 1, "status": "approved"}
                    from core.approval.approval_service import approve_change_request

                    result = approve_change_request(request_id=1, user_id=99)

        # After commit, status should be set to approved
        assert cr.status == "approved"


# ---------------------------------------------------------------------------
# _apply_change_request
# ---------------------------------------------------------------------------


class TestApplyChangeRequest:
    """Tests for _apply_change_request()."""

    def test_apply_update_request(self):
        """'update' type should call db_project.update_agent."""
        session = MagicMock()
        cr = _make_change_request(
            request_type="update",
            agent_id=5,
            requested_by=2,
            payload={"name": "agent-v2", "endpoint": "http://localhost:9000"},
        )
        cr.request_type = "update"

        with patch("core.db.db_project.update_agent") as mock_update:
            mock_update.return_value = {"id": 5, "name": "agent-v2"}
            with patch("core.approval.version_service.create_agent_version"):
                from core.approval.approval_service import _apply_change_request

                result = _apply_change_request(cr, session)

        assert result is True
        mock_update.assert_called_once()

    def test_apply_unknown_type_returns_false(self):
        """An unknown request_type should return False without raising."""
        session = MagicMock()
        cr = _make_change_request(payload={"name": "x"})
        cr.request_type = "unknown_op"

        from core.approval.approval_service import _apply_change_request

        result = _apply_change_request(cr, session)
        assert result is False

    def test_apply_delete_request(self):
        """'delete' type should call db_project.delete_agent."""
        session = MagicMock()
        cr = _make_change_request(
            request_type="delete",
            agent_id=7,
            payload={"agent_id": 7},
        )
        cr.request_type = "delete"

        with patch("core.db.db_project.delete_agent", return_value=True) as mock_delete:
            with patch("core.approval.version_service.create_agent_version"):
                from core.approval.approval_service import _apply_change_request

                result = _apply_change_request(cr, session)

        assert result is True
        mock_delete.assert_called_once_with(7)
