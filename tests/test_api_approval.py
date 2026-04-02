"""API tests for the approval router.

All DB and approval service calls are mocked — no running database required.
"""

from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Provide a test client."""
    try:
        import multipart  # noqa: F401
    except ImportError:
        pytest.skip("python-multipart not installed")
    from fastapi.testclient import TestClient

    from api.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Provide authentication headers."""
    return {"Authorization": "Bearer test-token"}


def _mock_user(user_id=1, username="testuser"):
    from core.auth.jwt import CurrentUser

    return CurrentUser(username=username, user_id=user_id)


def _mock_project(project_id=1, owner_id=1):
    return {
        "id": project_id,
        "project_id": "uuid-1",
        "project_name": "my-project",
        "owner_id": owner_id,
        "disable_authentication": False,
        "disable_message_storage": False,
    }


def _ctx(user_id=1, project_id=1):
    from api.deps.project import ProjectAccessContext

    return ProjectAccessContext(
        project=_mock_project(project_id=project_id),
        user=_mock_user(user_id=user_id),
        is_guest=False,
    )


def _pending_cr(cr_id=1, project_id=1, requested_by=2):
    return {
        "id": cr_id,
        "project_id": project_id,
        "agent_id": 5,
        "request_type": "update",
        "requested_by": requested_by,
        "status": "pending",
        "approval_type": "any",
        "required_approvals": 1,
        "current_approvals": 0,
        "payload": {},
        "created_at": "2024-01-01T00:00:00",
        "resolved_at": None,
    }


# ---------------------------------------------------------------------------
# GET change-requests
# ---------------------------------------------------------------------------


class TestGetChangeRequests:
    """Tests for listing change requests."""

    def test_list_change_requests_returns_200(self, client, auth_headers):
        """Test that listing change requests returns 200."""
        crs = [_pending_cr()]
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.approval.approval_service.list_change_requests", return_value=crs):
                response = client.get(
                    "/projects/my-project/change-requests",
                    headers=auth_headers,
                )
        assert response.status_code == 200
        data = response.json()
        assert "change_requests" in data
        assert len(data["change_requests"]) == 1


# ---------------------------------------------------------------------------
# POST approve
# ---------------------------------------------------------------------------


class TestApproveChangeRequest:
    """Tests for approving change requests."""

    def test_approve_happy_path(self, client, auth_headers):
        """Test that approving a change request succeeds."""
        cr = _pending_cr()
        approved_cr = {**cr, "status": "approved"}

        with patch("api.deps.project.require_project_member", return_value=_ctx(user_id=99)):
            with patch("core.approval.approval_service.get_change_request", return_value=cr):
                with patch(
                    "core.approval.approval_service.approve_change_request",
                    return_value=approved_cr,
                ):
                    response = client.post(
                        "/projects/my-project/change-requests/1/approve",
                        json={"comment": "LGTM"},
                        headers=auth_headers,
                    )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    def test_approve_already_resolved_returns_400(self, client, auth_headers):
        """Test that approving a resolved request returns 400."""
        cr = _pending_cr()
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.approval.approval_service.get_change_request", return_value=cr):
                # Service returns None for already-resolved
                with patch(
                    "core.approval.approval_service.approve_change_request",
                    return_value=None,
                ):
                    response = client.post(
                        "/projects/my-project/change-requests/1/approve",
                        json={"comment": ""},
                        headers=auth_headers,
                    )
        assert response.status_code == 400

    def test_self_approval_returns_403(self, client, auth_headers):
        """Test that self-approval returns 403."""
        cr = _pending_cr(requested_by=1)  # Same user_id as _ctx default
        self_approval_result = {
            "error": "self_approval",
            "message": "You cannot approve your own change request",
        }
        with patch("api.deps.project.require_project_member", return_value=_ctx(user_id=1)):
            with patch("core.approval.approval_service.get_change_request", return_value=cr):
                with patch(
                    "core.approval.approval_service.approve_change_request",
                    return_value=self_approval_result,
                ):
                    response = client.post(
                        "/projects/my-project/change-requests/1/approve",
                        json={"comment": "trying to self-approve"},
                        headers=auth_headers,
                    )
        assert response.status_code == 403

    def test_approve_cr_not_in_project_returns_404(self, client, auth_headers):
        """Test that approving a non-existent request returns 404."""
        # CR belongs to a different project
        cr = {**_pending_cr(), "project_id": 999}
        with patch("api.deps.project.require_project_member", return_value=_ctx(project_id=1)):
            with patch("core.approval.approval_service.get_change_request", return_value=cr):
                response = client.post(
                    "/projects/my-project/change-requests/1/approve",
                    json={"comment": ""},
                    headers=auth_headers,
                )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST reject
# ---------------------------------------------------------------------------


class TestRejectChangeRequest:
    """Tests for rejecting change requests."""

    def test_reject_happy_path(self, client, auth_headers):
        """Test that rejecting a change request succeeds."""
        cr = _pending_cr()
        rejected_cr = {**cr, "status": "rejected"}
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.approval.approval_service.get_change_request", return_value=cr):
                with patch(
                    "core.approval.approval_service.reject_change_request",
                    return_value=rejected_cr,
                ):
                    response = client.post(
                        "/projects/my-project/change-requests/1/reject",
                        json={"comment": "Not ready"},
                        headers=auth_headers,
                    )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

    def test_reject_without_comment_returns_400(self, client, auth_headers):
        """Test that rejecting without comment returns 400."""
        cr = _pending_cr()
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.approval.approval_service.get_change_request", return_value=cr):
                response = client.post(
                    "/projects/my-project/change-requests/1/reject",
                    json={"comment": ""},
                    headers=auth_headers,
                )
        assert response.status_code == 400

    def test_reject_already_resolved_returns_400(self, client, auth_headers):
        """Test that rejecting a resolved request returns 400."""
        cr = _pending_cr()
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.approval.approval_service.get_change_request", return_value=cr):
                with patch(
                    "core.approval.approval_service.reject_change_request",
                    return_value=None,
                ):
                    response = client.post(
                        "/projects/my-project/change-requests/1/reject",
                        json={"comment": "rejected"},
                        headers=auth_headers,
                    )
        assert response.status_code == 400
