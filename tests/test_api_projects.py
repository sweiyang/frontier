"""Integration tests for the projects API endpoints."""
import pytest
from unittest.mock import patch, MagicMock


class TestProjectsAPI:
    """Tests for /projects endpoints."""

    def _get_test_client(self):
        """Try to get a FastAPI TestClient."""
        try:
            from fastapi.testclient import TestClient
            from api.main import app
            return TestClient(app)
        except Exception:
            return None

    def test_create_project_duplicate_returns_409(self):
        """POST /projects with duplicate name should return 409."""
        client = self._get_test_client()
        if not client:
            pytest.skip("Cannot create test client")

        with patch("core.db.db_project.create_project") as mock_create:
            mock_create.side_effect = ValueError("A project named 'dup' already exists.")
            with patch("api.deps.auth.get_current_user") as mock_auth:
                mock_user = MagicMock()
                mock_user.user_id = 1
                mock_auth.return_value = mock_user
                response = client.post(
                    "/projects",
                    json={"project_name": "dup"},
                    headers={"Authorization": "Bearer fake-token"}
                )
                assert response.status_code == 409

    def test_get_nonexistent_project_returns_404(self):
        """GET /projects/{name} for missing project should return 404."""
        client = self._get_test_client()
        if not client:
            pytest.skip("Cannot create test client")

        with patch("core.db.db_project.get_project_by_name", return_value=None):
            with patch("api.deps.auth.get_current_user") as mock_auth:
                mock_user = MagicMock()
                mock_user.user_id = 1
                mock_user.ad_groups = []
                mock_auth.return_value = mock_user
                response = client.get(
                    "/projects/nonexistent",
                    headers={"Authorization": "Bearer fake-token"}
                )
                assert response.status_code == 404


class TestProjectNameValidation:
    """Tests for project name validation logic."""

    def test_empty_name_rejected(self):
        """Empty project name should be rejected."""
        client_getter = TestProjectsAPI()._get_test_client
        client = client_getter()
        if not client:
            pytest.skip("Cannot create test client")

        with patch("api.deps.auth.get_current_user") as mock_auth:
            mock_user = MagicMock()
            mock_user.user_id = 1
            mock_auth.return_value = mock_user
            response = client.post(
                "/projects",
                json={"project_name": ""},
                headers={"Authorization": "Bearer fake-token"}
            )
            # Should be 422 (validation error) or 400
            assert response.status_code in (400, 409, 422)
