"""Unit tests for core/approval/version_service.py."""

from datetime import datetime
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_db(session):
    db = MagicMock()
    db.get_session.return_value = session
    return db


def _make_agent(agent_id=1):
    a = MagicMock()
    a.id = agent_id
    a.name = "test-agent"
    a.endpoint = "https://localhost:9000"
    a.connection_type = "http"
    a.extras = {"model": "gpt-4o"}
    a.is_default = False
    a.auth = {"auth_type": "bearer", "credentials": "tok"}
    a.icon = None
    return a


def _make_version(agent_id=1, version_number=1, snapshot=None):
    v = MagicMock()
    v.id = 10
    v.agent_id = agent_id
    v.version_number = version_number
    v.snapshot = snapshot or {
        "name": "test-agent",
        "endpoint": "https://localhost:9000",
        "connection_type": "http",
        "extras": {},
        "is_default": False,
        "auth": {"auth_type": "bearer", "credentials": "tok"},
        "icon": None,
    }
    v.created_by = 99
    v.change_request_id = None
    v.created_at = datetime(2024, 1, 1)
    return v


# ---------------------------------------------------------------------------
# create_agent_version
# ---------------------------------------------------------------------------


class TestCreateAgentVersion:
    """Tests for create_agent_version()."""

    def test_creates_first_version(self):
        """Test that the first version is created correctly."""
        session = MagicMock()
        agent = _make_agent()
        session.query.return_value.filter.return_value.first.return_value = agent
        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        mock_user = MagicMock()
        mock_user.username = "creator"

        def query_side(model):
            """Mock query side effect."""
            q = MagicMock()
            name = getattr(model, "__name__", "")
            if name == "Agent":
                q.filter.return_value.first.return_value = agent
            elif name == "AgentVersion":
                q.filter.return_value.order_by.return_value.first.return_value = None
            else:
                q.filter.return_value.first.return_value = mock_user
            return q

        session.query.side_effect = query_side

        with patch(
            "core.approval.version_service.get_db", return_value=_mock_db(session)
        ):
            with patch("core.approval.version_service.AgentVersion") as MockVersion:
                version_instance = MagicMock()
                version_instance.id = 10
                version_instance.agent_id = 1
                version_instance.version_number = 1
                version_instance.snapshot = {}
                version_instance.created_by = 99
                version_instance.change_request_id = None
                version_instance.created_at = datetime(2024, 1, 1)
                MockVersion.return_value = version_instance

                from core.approval.version_service import create_agent_version

                result = create_agent_version(agent_id=1, user_id=99)

        assert result is not None
        assert result["version_number"] == 1

    def test_returns_none_for_missing_agent(self):
        """Test that missing agent returns None."""
        session = MagicMock()

        def query_side(model):
            """Mock query side effect."""
            q = MagicMock()
            q.filter.return_value.first.return_value = None
            q.filter.return_value.order_by.return_value.first.return_value = None
            return q

        session.query.side_effect = query_side

        with patch(
            "core.approval.version_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.version_service import create_agent_version

            result = create_agent_version(agent_id=999, user_id=1)

        assert result is None

    def test_increments_version_number(self):
        """Test that version number is incremented."""
        session = MagicMock()
        agent = _make_agent()
        existing_version = _make_version(version_number=3)

        def query_side(model):
            """Mock query side effect."""
            q = MagicMock()
            name = getattr(model, "__name__", "")
            if name == "Agent":
                q.filter.return_value.first.return_value = agent
            elif name == "AgentVersion":
                q.filter.return_value.order_by.return_value.first.return_value = (
                    existing_version
                )
            else:
                mock_user = MagicMock()
                mock_user.username = "u"
                q.filter.return_value.first.return_value = mock_user
            return q

        session.query.side_effect = query_side

        with patch(
            "core.approval.version_service.get_db", return_value=_mock_db(session)
        ):
            with patch("core.approval.version_service.AgentVersion") as MockVersion:
                created = MagicMock()
                created.id = 20
                created.agent_id = 1
                created.version_number = 4  # 3 + 1
                created.snapshot = {}
                created.created_by = 1
                created.change_request_id = None
                created.created_at = datetime(2024, 1, 2)
                MockVersion.return_value = created

                from core.approval.version_service import create_agent_version

                result = create_agent_version(agent_id=1, user_id=1)

        assert result["version_number"] == 4


# ---------------------------------------------------------------------------
# get_agent_versions
# ---------------------------------------------------------------------------


class TestGetAgentVersions:
    """Tests for get_agent_versions()."""

    def test_returns_list_of_versions(self):
        """Test that versions are returned as a list."""
        session = MagicMock()
        v1 = _make_version(version_number=2)
        v2 = _make_version(version_number=1)
        mock_user = MagicMock()
        mock_user.username = "u"

        def query_side(model):
            """Mock query side effect."""
            q = MagicMock()
            name = getattr(model, "__name__", "")
            if name == "AgentVersion":
                q.filter.return_value.order_by.return_value.all.return_value = [v1, v2]
            else:
                q.filter.return_value.first.return_value = mock_user
            return q

        session.query.side_effect = query_side

        with patch(
            "core.approval.version_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.version_service import get_agent_versions

            result = get_agent_versions(agent_id=1)

        assert len(result) == 2
        assert result[0]["version_number"] == 2

    def test_returns_empty_list_when_none(self):
        """Test that empty list is returned when no versions."""
        session = MagicMock()

        def query_side(model):
            """Mock query side effect."""
            q = MagicMock()
            q.filter.return_value.order_by.return_value.all.return_value = []
            return q

        session.query.side_effect = query_side

        with patch(
            "core.approval.version_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.version_service import get_agent_versions

            result = get_agent_versions(agent_id=999)

        assert result == []

    def test_auth_field_is_redacted(self):
        """Test that auth field is redacted in version snapshot."""
        session = MagicMock()
        v = _make_version(snapshot={"auth": "supersecret", "name": "a"})
        mock_user = MagicMock()
        mock_user.username = "u"

        def query_side(model):
            """Mock query side effect."""
            q = MagicMock()
            name = getattr(model, "__name__", "")
            if name == "AgentVersion":
                q.filter.return_value.order_by.return_value.all.return_value = [v]
            else:
                q.filter.return_value.first.return_value = mock_user
            return q

        session.query.side_effect = query_side

        with patch(
            "core.approval.version_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.version_service import get_agent_versions

            result = get_agent_versions(agent_id=1)

        assert result[0]["snapshot"]["auth"] == "[REDACTED]"


# ---------------------------------------------------------------------------
# rollback_agent_to_version
# ---------------------------------------------------------------------------


class TestRollbackAgentToVersion:
    """Tests for rollback_agent_to_version()."""

    def test_rollback_nonexistent_version_returns_none(self):
        """Test that rollback of missing version returns None."""
        session = MagicMock()

        def query_side(model):
            """Mock query side effect."""
            q = MagicMock()
            q.filter.return_value.first.return_value = None
            return q

        session.query.side_effect = query_side

        with patch(
            "core.approval.version_service.get_db", return_value=_mock_db(session)
        ):
            from core.approval.version_service import rollback_agent_to_version

            result = rollback_agent_to_version(agent_id=1, version_number=99, user_id=1)

        assert result is None

    def test_rollback_applies_snapshot_to_agent(self):
        """Test that rollback applies the version snapshot."""
        session = MagicMock()
        snapshot = {
            "name": "old-name",
            "endpoint": "https://old.endpoint",
            "connection_type": "openai",
            "extras": {},
            "is_default": False,
            "auth": None,
            "icon": None,
        }
        version = _make_version(version_number=1, snapshot=snapshot)
        agent = _make_agent()

        call_tracker = {"count": 0}

        def query_side(model):
            """Mock query side effect."""
            q = MagicMock()
            name = getattr(model, "__name__", "")
            if name == "AgentVersion":
                q.filter.return_value.first.return_value = version
            elif name == "Agent":
                q.filter.return_value.first.return_value = agent
            return q

        session.query.side_effect = query_side

        with patch(
            "core.approval.version_service.get_db", return_value=_mock_db(session)
        ):
            with patch(
                "core.approval.version_service.create_agent_version",
                return_value={"version_number": 2},
            ):
                from core.approval.version_service import rollback_agent_to_version

                result = rollback_agent_to_version(
                    agent_id=1, version_number=1, user_id=1
                )

        assert result is not None
        assert result["rolled_back_to_version"] == 1
        assert agent.name == "old-name"
        assert agent.endpoint == "https://old.endpoint"
