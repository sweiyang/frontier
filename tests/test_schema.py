"""Tests for Pydantic schema models."""

import pytest

from api.schema import (
    AgentCreate,
    ChatRequest,
    ProjectCreate,
    ProjectUpdate,
    SiteComponent,
)


class TestChatRequestSchema:
    """Tests for chat request schema validation."""

    def test_chat_request_requires_message(self):
        """ChatRequest without a message should raise a validation error."""
        with pytest.raises(Exception):
            ChatRequest(conversation_id=1)  # Missing message

    def test_chat_request_valid(self):
        """Valid ChatRequest should have defaults populated."""
        req = ChatRequest(message="hello", conversation_id=1)
        assert req.message == "hello"
        assert req.conversation_id == 1
        assert req.model == "default"

    def test_project_create_schema(self):
        """ProjectCreate should accept a project_name."""
        p = ProjectCreate(project_name="my-project")
        assert p.project_name == "my-project"
        assert p.disable_authentication is False

    def test_project_update_all_optional(self):
        """ProjectUpdate should allow construction with no arguments."""
        u = ProjectUpdate()
        assert u.project_name is None

    def test_agent_create_schema(self):
        """AgentCreate should populate is_default as False by default."""
        a = AgentCreate(name="my-agent", endpoint="http://localhost:8000", connection_type="http")
        assert a.name == "my-agent"
        assert a.is_default is False

    def test_site_component_defaults(self):
        """SiteComponent should have sensible default geometry."""
        c = SiteComponent(id="c1", type="button")
        assert c.x == 0
        assert c.y == 0
        assert c.w == 160
        assert c.h == 44
        assert c.props == {}


class TestArtefactSchema:
    """Tests for artefact schema validation."""

    def test_artefact_settings_schema(self):
        """ArtefactSettings should accept is_artefact and artefact_visibility."""
        from api.schema import ArtefactSettings

        s = ArtefactSettings(is_artefact=True, artefact_visibility="org")
        assert s.is_artefact is True
        assert s.artefact_visibility == "org"

    def test_artefact_settings_default_visibility(self):
        """ArtefactSettings should default visibility to 'org'."""
        from api.schema import ArtefactSettings

        s = ArtefactSettings(is_artefact=True)
        assert s.artefact_visibility == "org"
