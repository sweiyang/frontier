"""Tests for Pydantic schema models."""
import pytest


class TestChatRequestSchema:
    def test_chat_request_requires_message(self):
        from api.schema import ChatRequest
        with pytest.raises(Exception):
            ChatRequest(conversation_id=1)  # Missing message

    def test_chat_request_valid(self):
        from api.schema import ChatRequest
        req = ChatRequest(message="hello", conversation_id=1)
        assert req.message == "hello"
        assert req.conversation_id == 1
        assert req.model == "default"

    def test_project_create_schema(self):
        from api.schema import ProjectCreate
        p = ProjectCreate(project_name="my-project")
        assert p.project_name == "my-project"
        assert p.disable_authentication is False

    def test_project_update_all_optional(self):
        from api.schema import ProjectUpdate
        u = ProjectUpdate()  # All fields optional
        assert u.project_name is None

    def test_agent_create_schema(self):
        from api.schema import AgentCreate
        a = AgentCreate(name="my-agent", endpoint="http://localhost:8000", connection_type="http")
        assert a.name == "my-agent"
        assert a.is_default is False

    def test_site_component_defaults(self):
        from api.schema import SiteComponent
        c = SiteComponent(id="c1", type="button")
        assert c.x == 0
        assert c.y == 0
        assert c.w == 160
        assert c.h == 44
        assert c.props == {}


class TestArtefactSchema:
    def test_artefact_settings_schema(self):
        try:
            from api.schema import ArtefactSettings
            s = ArtefactSettings(is_artefact=True, artefact_visibility="org")
            assert s.is_artefact is True
            assert s.artefact_visibility == "org"
        except ImportError:
            pytest.skip("ArtefactSettings not yet available")

    def test_artefact_settings_default_visibility(self):
        try:
            from api.schema import ArtefactSettings
            s = ArtefactSettings(is_artefact=True)
            assert s.artefact_visibility == "org"
        except ImportError:
            pytest.skip("ArtefactSettings not yet available")
