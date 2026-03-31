"""Unit tests for api/services/chat_service.py."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(connection_type="http"):
    return {
        "id": 1,
        "name": "test-agent",
        "endpoint": "https://localhost:9000",
        "connection_type": connection_type,
        "extras": {},
        "auth": {},
    }


def _make_user_metadata():
    from core.agent.connectors.schema import MetadataUser

    return MetadataUser(
        user_id="1",
        username="alice",
        display_name="Alice",
        email="alice@example.com",
        ad_group=[],
    )


async def _collect(gen):
    """Collect all yielded items from an async generator into a list."""
    items = []
    async for item in gen:
        items.append(item)
    return items


# ---------------------------------------------------------------------------
# to_stream_events
# ---------------------------------------------------------------------------


class TestToStreamEvents:
    """Tests for the to_stream_events() helper."""

    def test_str_input_becomes_text_event(self):
        """Test that string input becomes a text event."""
        from api.services.chat_service import to_stream_events

        output = to_stream_events("hello")
        data = json.loads(output.strip())
        assert data["type"] == "text"
        assert data["content"] == "hello"

    def test_dict_with_content(self):
        """Test that a dict with content key is handled."""
        from api.services.chat_service import to_stream_events

        output = to_stream_events({"content": "world"})
        data = json.loads(output.strip())
        assert data["type"] == "text"
        assert data["content"] == "world"

    def test_dict_with_elements(self):
        """Test that a dict with elements key is handled."""
        from api.services.chat_service import to_stream_events

        output = to_stream_events({"elements": [{"type": "button"}]})
        data = json.loads(output.strip())
        assert data["type"] == "elements"

    def test_empty_dict_returns_empty_string(self):
        """Test that an empty dict returns empty string."""
        from api.services.chat_service import to_stream_events

        output = to_stream_events({})
        assert output == ""


# ---------------------------------------------------------------------------
# agent_stream_processor
# ---------------------------------------------------------------------------


class TestAgentStreamProcessor:
    """Tests for agent_stream_processor()."""

    @pytest.mark.anyio
    async def test_successful_stream_yields_ndjson(self):
        """Chunks from connector should be forwarded as NDJSON text events."""
        agent = _make_agent()
        user_metadata = _make_user_metadata()

        mock_connector = MagicMock()
        mock_connector.stream = MagicMock(return_value=_async_iter(["Hello", " World"]))
        mock_connector.close = AsyncMock()

        with patch(
            "api.services.chat_service.get_connector", return_value=mock_connector
        ):
            with patch("api.services.chat_service.db_chat") as mock_db_chat:
                mock_db_chat.save_message.return_value = None
                with patch("api.services.chat_service.estimate_tokens", return_value=5):
                    with patch(
                        "api.services.chat_service.estimate_tokens_for_messages",
                        return_value=10,
                    ):
                        with patch(
                            "core.db.db_project.get_project_by_name",
                            return_value={"id": 1},
                        ):
                            with patch("core.db.db_project.record_chat_interaction"):
                                from api.services.chat_service import (
                                    agent_stream_processor,
                                )

                                results = await _collect(
                                    agent_stream_processor(
                                        "hi", 1, agent, [], "proj", user_metadata
                                    )
                                )

        assert len(results) > 0
        first = json.loads(results[0].strip())
        assert first["type"] == "text"
        assert first["content"] == "Hello"

    @pytest.mark.anyio
    async def test_connector_close_called_on_success(self):
        """connector.close() must be called even on success."""
        agent = _make_agent()
        user_metadata = _make_user_metadata()

        mock_connector = MagicMock()
        mock_connector.stream = MagicMock(return_value=_async_iter(["ok"]))
        mock_connector.close = AsyncMock()

        with patch(
            "api.services.chat_service.get_connector", return_value=mock_connector
        ):
            with patch("api.services.chat_service.db_chat"):
                with patch("api.services.chat_service.estimate_tokens", return_value=1):
                    with patch(
                        "api.services.chat_service.estimate_tokens_for_messages",
                        return_value=1,
                    ):
                        with patch(
                            "core.db.db_project.get_project_by_name",
                            return_value={"id": 1},
                        ):
                            with patch("core.db.db_project.record_chat_interaction"):
                                from api.services.chat_service import (
                                    agent_stream_processor,
                                )

                                await _collect(
                                    agent_stream_processor(
                                        "hi", 1, agent, [], "proj", user_metadata
                                    )
                                )

        mock_connector.close.assert_awaited_once()

    @pytest.mark.anyio
    async def test_connector_close_called_on_error(self):
        """connector.close() must be called even when connector raises mid-stream."""
        agent = _make_agent()
        user_metadata = _make_user_metadata()

        mock_connector = MagicMock()
        mock_connector.stream = MagicMock(
            return_value=_async_iter_raise(RuntimeError("boom"))
        )
        mock_connector.close = AsyncMock()

        with patch(
            "api.services.chat_service.get_connector", return_value=mock_connector
        ):
            with patch("api.services.chat_service.db_chat") as mock_db:
                mock_db.save_message.return_value = None
                with patch("api.services.chat_service.estimate_tokens", return_value=1):
                    with patch(
                        "api.services.chat_service.estimate_tokens_for_messages",
                        return_value=1,
                    ):
                        from api.services.chat_service import agent_stream_processor

                        results = await _collect(
                            agent_stream_processor(
                                "hi", 1, agent, [], "proj", user_metadata
                            )
                        )

        mock_connector.close.assert_awaited_once()
        # Error event should have been yielded
        assert len(results) > 0
        data = json.loads(results[0].strip())
        assert data["type"] == "text"

    @pytest.mark.anyio
    async def test_error_event_yielded_on_exception(self):
        """An exception mid-stream should produce an error NDJSON event."""
        agent = _make_agent()
        user_metadata = _make_user_metadata()

        mock_connector = MagicMock()
        mock_connector.stream = MagicMock(
            return_value=_async_iter_raise(ConnectionError("refused"))
        )
        mock_connector.close = AsyncMock()

        with patch(
            "api.services.chat_service.get_connector", return_value=mock_connector
        ):
            with patch("api.services.chat_service.db_chat") as mock_db:
                mock_db.save_message.return_value = None
                with patch("api.services.chat_service.estimate_tokens", return_value=1):
                    with patch(
                        "api.services.chat_service.estimate_tokens_for_messages",
                        return_value=1,
                    ):
                        from api.services.chat_service import agent_stream_processor

                        results = await _collect(
                            agent_stream_processor(
                                "hi", 1, agent, [], "proj", user_metadata
                            )
                        )

        assert len(results) == 1
        payload = json.loads(results[0].strip())
        assert "Error" in payload["content"] or "refused" in payload["content"]

    @pytest.mark.anyio
    async def test_usage_recorded_after_stream(self):
        """Usage interaction should be recorded after a successful stream."""
        agent = _make_agent()
        user_metadata = _make_user_metadata()

        mock_connector = MagicMock()
        mock_connector.stream = MagicMock(return_value=_async_iter(["result"]))
        mock_connector.close = AsyncMock()

        with patch(
            "api.services.chat_service.get_connector", return_value=mock_connector
        ):
            with patch("api.services.chat_service.db_chat"):
                with patch("api.services.chat_service.estimate_tokens", return_value=5):
                    with patch(
                        "api.services.chat_service.estimate_tokens_for_messages",
                        return_value=5,
                    ):
                        with patch(
                            "core.db.db_project.get_project_by_name",
                            return_value={"id": 1},
                        ):
                            with patch(
                                "core.db.db_project.record_chat_interaction"
                            ) as mock_record:
                                from api.services.chat_service import (
                                    agent_stream_processor,
                                )

                                await _collect(
                                    agent_stream_processor(
                                        "hi", 1, agent, [], "proj", user_metadata
                                    )
                                )

        mock_record.assert_called_once()


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------


async def _async_iter_impl(items):
    for item in items:
        yield item


def _async_iter(items):
    return _async_iter_impl(items)


async def _async_iter_raise_impl(exc):
    raise exc
    yield  # make it an async generator


def _async_iter_raise(exc):
    return _async_iter_raise_impl(exc)
