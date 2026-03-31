"""API tests for the agents router.

These tests use FastAPI's TestClient with fully mocked DB and dependency injection.
A running database is not required.
"""

from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app with DB mocked out."""
    try:
        import multipart  # noqa: F401
    except ImportError:
        pytest.skip("python-multipart not installed; run: pip install python-multipart")
    from fastapi.testclient import TestClient

    from api.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return valid-looking auth headers (actual JWT verification is mocked)."""
    return {"Authorization": "Bearer test-token"}


def _mock_user(user_id=1, username="testuser", ad_groups=None):
    from core.auth.jwt import CurrentUser

    return CurrentUser(username=username, user_id=user_id, ad_groups=ad_groups or [])


def _mock_project(project_id=1, owner_id=1, name="my-project"):
    return {
        "id": project_id,
        "project_id": "uuid-1",
        "project_name": name,
        "owner_id": owner_id,
        "disable_authentication": False,
        "disable_message_storage": False,
    }


def _mock_agent(agent_id=1, project_id=1):
    return {
        "id": agent_id,
        "project_id": project_id,
        "name": "test-agent",
        "endpoint": "https://localhost:9000",
        "connection_type": "http",
        "is_default": False,
        "extras": {},
        "auth": {},
        "icon": None,
        "is_artefact": False,
        "description": None,
    }


def _ctx(user=None, project=None):
    from api.deps.project import ProjectAccessContext

    return ProjectAccessContext(
        project=project or _mock_project(),
        user=user or _mock_user(),
        is_guest=False,
    )


# ---------------------------------------------------------------------------
# GET /projects/{project_name}/agents
# ---------------------------------------------------------------------------


class TestListAgents:

    def test_list_agents_returns_200(self, client, auth_headers):
        agents = [_mock_agent()]
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch(
                "core.db.db_project.list_agents_for_project", return_value=agents
            ):
                response = client.get(
                    "/projects/my-project/agents",
                    headers=auth_headers,
                )
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 1

    def test_list_agents_requires_auth(self, client):
        """No Authorization header should return 401 or 403."""
        with patch("api.deps.project.require_project_member") as mock_dep:
            from fastapi import HTTPException

            mock_dep.side_effect = HTTPException(
                status_code=401, detail="Not authenticated"
            )
            response = client.get("/projects/my-project/agents")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# POST /projects/{project_name}/agents
# ---------------------------------------------------------------------------


class TestCreateAgent:

    def test_create_agent_success(self, client, auth_headers):
        agent = _mock_agent()
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("api.routers.agents.is_approval_required", return_value=False):
                with patch("core.db.db_project.create_agent", return_value=agent):
                    with patch("api.routers.agents.create_agent_version"):
                        response = client.post(
                            "/projects/my-project/agents",
                            json={
                                "name": "test-agent",
                                "endpoint": "https://localhost:9000",
                                "connection_type": "http",
                            },
                            headers=auth_headers,
                        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-agent"

    def test_create_agent_without_auth_returns_401(self, client):
        """Request without JWT should fail at auth dependency."""
        with patch("api.deps.project.require_project_member") as mock_dep:
            from fastapi import HTTPException

            mock_dep.side_effect = HTTPException(
                status_code=401, detail="Not authenticated"
            )
            response = client.post(
                "/projects/my-project/agents",
                json={
                    "name": "x",
                    "endpoint": "https://x.com",
                    "connection_type": "http",
                },
            )
        assert response.status_code == 401

    def test_create_agent_pending_approval_in_production(self, client, auth_headers):
        """In production, agent creation should be queued for approval."""
        mock_cr = {"id": 99, "status": "pending"}
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("api.routers.agents.is_approval_required", return_value=True):
                with patch(
                    "api.routers.agents.create_change_request", return_value=mock_cr
                ):
                    response = client.post(
                        "/projects/my-project/agents",
                        json={
                            "name": "test-agent",
                            "endpoint": "https://localhost:9000",
                            "connection_type": "http",
                        },
                        headers=auth_headers,
                    )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_approval"


# ---------------------------------------------------------------------------
# PUT /projects/{project_name}/agents/{agent_id}
# ---------------------------------------------------------------------------


class TestUpdateAgent:

    def test_update_agent_success(self, client, auth_headers):
        agent = _mock_agent()
        updated = {**agent, "name": "updated-agent"}
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.db.db_project.get_agent_by_id", return_value=agent):
                with patch(
                    "api.routers.agents.is_approval_required", return_value=False
                ):
                    with patch("core.db.db_project.update_agent", return_value=updated):
                        with patch("api.routers.agents.create_agent_version"):
                            response = client.put(
                                "/projects/my-project/agents/1",
                                json={
                                    "name": "updated-agent",
                                    "endpoint": "https://localhost:9000",
                                    "connection_type": "http",
                                },
                                headers=auth_headers,
                            )
        assert response.status_code == 200
        assert response.json()["name"] == "updated-agent"

    def test_update_agent_not_found_returns_404(self, client, auth_headers):
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.db.db_project.get_agent_by_id", return_value=None):
                response = client.put(
                    "/projects/my-project/agents/999",
                    json={
                        "name": "x",
                        "endpoint": "https://x.com",
                        "connection_type": "http",
                    },
                    headers=auth_headers,
                )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /projects/{project_name}/agents/{agent_id}
# ---------------------------------------------------------------------------


class TestDeleteAgent:

    def test_delete_agent_success(self, client, auth_headers):
        agent = _mock_agent()
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.db.db_project.get_agent_by_id", return_value=agent):
                with patch(
                    "api.routers.agents.is_approval_required", return_value=False
                ):
                    with patch("api.routers.agents.create_agent_version"):
                        with patch("core.db.db_project.delete_agent"):
                            response = client.delete(
                                "/projects/my-project/agents/1",
                                headers=auth_headers,
                            )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_agent_not_found_returns_404(self, client, auth_headers):
        with patch("api.deps.project.require_project_member", return_value=_ctx()):
            with patch("core.db.db_project.get_agent_by_id", return_value=None):
                response = client.delete(
                    "/projects/my-project/agents/999",
                    headers=auth_headers,
                )
        assert response.status_code == 404
