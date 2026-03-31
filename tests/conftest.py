"""Shared test fixtures for the Frontier test suite."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_db_session():
    """Provide a mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def sample_project_dict():
    """A sample project dictionary as returned by db functions."""
    return {
        "id": 1,
        "project_id": "test-uuid-1234",
        "project_name": "test-project",
        "owner_id": 1,
        "disable_authentication": False,
        "disable_message_storage": False,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_user_dict():
    """A sample user dictionary."""
    return {
        "id": 1,
        "username": "testuser",
        "display_name": "Test User",
    }
