"""API tests for the chat router.

The connector and DB are fully mocked. No running database or agent required.
"""

import json
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
    return {"Authorization": "Bearer test-token", "X-Project": "my-project"}


def _mock_user(user_id=1, username="testuser"):
    from core.auth.jwt import CurrentUser

    return CurrentUser(username=username, user_id=user_id)


def _mock_project(project_id=1, name="my-project"):
    return {
        "id": project_id,
        "project_name": name,
        "owner_id": 1,
        "disable_authentication": False,
        "disable_message_storage": False,
    }


def _mock_agent(project_id=1):
    return {
        "id": 1,
        "project_id": project_id,
        "name": "test-agent",
        "endpoint": "https://localhost:9000",
        "connection_type": "http",
        "is_default": True,
        "extras": {},
        "auth": {},
    }


async def _ndjson_stream():
    yield json.dumps({"type": "text", "content": "Hello"}) + "\n"
    yield json.dumps({"type": "text", "content": " world"}) + "\n"


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------


class TestStreamChat:
    """Tests for the streaming chat endpoint."""

    def test_project_not_found_returns_404(self, client):
        """Test that a missing project returns 404."""
        with patch("api.deps.auth.get_current_user", return_value=_mock_user()):
            with patch("core.db.db_project.get_project_by_name", return_value=None):
                response = client.post(
                    "/chat",
                    json={"message": "hello", "conversation_id": 1},
                    headers={"Authorization": "Bearer tok", "X-Project": "nonexistent"},
                )
        assert response.status_code == 404

    def test_no_project_header_returns_400(self, client):
        """Test that a missing project header returns 400."""
        with patch("api.deps.auth.get_current_user", return_value=_mock_user()):
            response = client.post(
                "/chat",
                json={"message": "hello", "conversation_id": 1},
                headers={"Authorization": "Bearer tok"},
                # No X-Project header
            )
        assert response.status_code == 400

    def test_no_agent_configured_returns_404(self, client, auth_headers):
        """Test that no configured agent returns 404."""
        with patch("api.deps.auth.get_current_user", return_value=_mock_user()):
            with patch(
                "core.db.db_project.get_project_by_name", return_value=_mock_project()
            ):
                with patch("api.deps.project.verify_project_membership"):
                    with patch("core.db.db_chat.save_message"):
                        with patch(
                            "core.db.db_project.get_agent_by_id", return_value=None
                        ):
                            with patch(
                                "core.db.db_project.get_default_agent_for_project",
                                return_value=None,
                            ):
                                with patch(
                                    "core.db.db_project.get_agent_by_name",
                                    return_value=None,
                                ):
                                    response = client.post(
                                        "/chat",
                                        json={"message": "hello", "conversation_id": 1},
                                        headers=auth_headers,
                                    )
        assert response.status_code == 404

    def test_successful_stream_returns_200(self, client, auth_headers):
        """Test that a successful stream returns 200."""
        with patch("api.deps.auth.get_current_user", return_value=_mock_user()):
            with patch(
                "core.db.db_project.get_project_by_name", return_value=_mock_project()
            ):
                with patch("api.deps.project.verify_project_membership"):
                    with patch("core.db.db_chat.save_message"):
                        with patch(
                            "core.db.db_chat.get_messages",
                            return_value=[{"role": "user", "content": "hello"}],
                        ):
                            with patch(
                                "core.db.db_project.get_default_agent_for_project",
                                return_value=_mock_agent(),
                            ):
                                with patch(
                                    "api.services.chat_service.agent_stream_processor",
                                    return_value=_ndjson_stream(),
                                ):
                                    response = client.post(
                                        "/chat",
                                        json={"message": "hello", "conversation_id": 1},
                                        headers=auth_headers,
                                    )
        assert response.status_code == 200
        # Response is streaming NDJSON
        assert "application/x-ndjson" in response.headers.get("content-type", "")

    def test_unauthenticated_request_returns_401(self, client, auth_headers):
        """No valid JWT should produce 401."""
        from fastapi import HTTPException

        with patch("api.deps.auth.get_current_user") as mock_auth:
            mock_auth.side_effect = HTTPException(
                status_code=401, detail="Not authenticated"
            )
            response = client.post(
                "/chat",
                json={"message": "hello", "conversation_id": 1},
                headers={
                    "Authorization": "Bearer bad-token",
                    "X-Project": "my-project",
                },
            )
        assert response.status_code == 401

    def test_agent_from_different_project_is_ignored(self, client, auth_headers):
        """Agent belonging to a different project should be excluded."""
        wrong_project_agent = {**_mock_agent(), "project_id": 999}
        with patch("api.deps.auth.get_current_user", return_value=_mock_user()):
            with patch(
                "core.db.db_project.get_project_by_name",
                return_value=_mock_project(project_id=1),
            ):
                with patch("api.deps.project.verify_project_membership"):
                    with patch("core.db.db_chat.save_message"):
                        with patch("core.db.db_chat.get_messages", return_value=[]):
                            with patch(
                                "core.db.db_project.get_agent_by_id",
                                return_value=wrong_project_agent,
                            ):
                                with patch(
                                    "core.db.db_project.get_default_agent_for_project",
                                    return_value=None,
                                ):
                                    with patch(
                                        "core.db.db_project.get_agent_by_name",
                                        return_value=None,
                                    ):
                                        response = client.post(
                                            "/chat",
                                            json={
                                                "message": "hello",
                                                "conversation_id": 1,
                                                "agent_id": 99,
                                            },
                                            headers=auth_headers,
                                        )
        # Should 404 — the wrong-project agent was ignored and no fallback exists
        assert response.status_code == 404
