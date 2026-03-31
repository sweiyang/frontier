"""Unit tests for the three agent connectors (HTTP, OpenAI, LangGraph)."""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Shared agent config factories
# ---------------------------------------------------------------------------


def _agent(
    endpoint="https://localhost:8000", auth=None, extras=None, name="test-agent"
):
    return {
        "id": 1,
        "name": name,
        "endpoint": endpoint,
        "auth": auth or {},
        "extras": extras or {},
    }


# ---------------------------------------------------------------------------
# BaseAgentConnector.get_auth_headers
# ---------------------------------------------------------------------------


class TestGetAuthHeaders:
    """Test auth header construction shared by all connectors."""

    def _make_connector(self, auth):
        from core.agent.connectors.http_connector import HTTPAgentConnector

        return HTTPAgentConnector(_agent(auth=auth))

    def test_no_auth_returns_empty(self):
        """Test that no auth config returns empty headers."""
        conn = self._make_connector(auth={})
        assert conn.get_auth_headers() == {}

    def test_bearer_auth(self):
        """Test that bearer auth returns correct headers."""
        conn = self._make_connector(
            auth={"auth_type": "bearer", "credentials": "mytoken"}
        )
        headers = conn.get_auth_headers()
        assert headers["Authorization"] == "Bearer mytoken"

    def test_api_key_auth(self):
        """Test that API key auth returns correct headers."""
        conn = self._make_connector(
            auth={"auth_type": "api_key", "credentials": "secret"}
        )
        headers = conn.get_auth_headers()
        assert headers["X-API-Key"] == "secret"

    def test_basic_auth(self):
        """Test that basic auth returns correct headers."""
        conn = self._make_connector(
            auth={
                "auth_type": "basic",
                "credentials": {"username": "alice", "password": "pass"},
            }
        )
        headers = conn.get_auth_headers()
        expected = base64.b64encode(b"alice:pass").decode()
        assert headers["Authorization"] == f"Basic {expected}"

    def test_unknown_auth_type_returns_empty(self):
        """Test that unknown auth type returns empty headers."""
        conn = self._make_connector(auth={"auth_type": "unknown", "credentials": "x"})
        # Unknown type — no header should be set (no crash)
        headers = conn.get_auth_headers()
        assert "Authorization" not in headers
        assert "X-API-Key" not in headers


# ---------------------------------------------------------------------------
# HTTPAgentConnector
# ---------------------------------------------------------------------------


class TestHTTPAgentConnector:
    """Tests for HTTPAgentConnector.stream()."""

    def _make_connector(self, **kwargs):
        from core.agent.connectors.http_connector import HTTPAgentConnector

        return HTTPAgentConnector(_agent(**kwargs))

    @pytest.mark.anyio
    async def test_stream_plain_text(self):
        """Plain text chunks should be yielded as-is."""
        conn = self._make_connector()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        # aiter_text is called directly (not awaited), so assign the async gen directly
        mock_response.aiter_text = lambda: _async_iter(["Hello", " World"])

        with patch("httpx.AsyncClient") as MockClient:
            _setup_httpx_mock(MockClient, mock_response)
            chunks = []
            async for chunk in conn.stream([], "hi"):
                chunks.append(chunk)

        assert "Hello" in chunks
        assert " World" in chunks

    @pytest.mark.anyio
    async def test_stream_sse_data(self):
        """SSE-formatted lines should be stripped of 'data: ' prefix."""
        conn = self._make_connector()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/event-stream"}
        mock_response.aiter_text = lambda: _async_iter(
            ["data: chunk1", "data: chunk2", "data: [DONE]"]
        )

        with patch("httpx.AsyncClient") as MockClient:
            _setup_httpx_mock(MockClient, mock_response)
            chunks = []
            async for chunk in conn.stream([], "hi"):
                chunks.append(chunk)

        assert "chunk1" in chunks
        assert "chunk2" in chunks
        assert "[DONE]" not in chunks

    @pytest.mark.anyio
    async def test_stream_json_response(self):
        """A JSON application/json response should be yielded as a dict."""
        conn = self._make_connector()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.aread = AsyncMock(return_value=b'{"content": "hello"}')
        mock_response.json.return_value = {"content": "hello"}

        with patch("httpx.AsyncClient") as MockClient:
            _setup_httpx_mock(MockClient, mock_response)
            chunks = []
            async for chunk in conn.stream([], "hi"):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0] == {"content": "hello"}

    @pytest.mark.anyio
    async def test_stream_error_response_yields_error_message(self):
        """Non-200 status should yield an error string."""
        conn = self._make_connector()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.aread = AsyncMock(return_value=b"Internal Error")
        mock_response.headers = {"content-type": "text/plain"}

        with patch("httpx.AsyncClient") as MockClient:
            _setup_httpx_mock(MockClient, mock_response)
            chunks = []
            async for chunk in conn.stream([], "hi"):
                chunks.append(chunk)

        assert any("500" in str(c) for c in chunks)

    @pytest.mark.anyio
    async def test_close_is_noop(self):
        """HTTPAgentConnector.close() should not raise."""
        conn = self._make_connector()
        await conn.close()  # Should not raise


# ---------------------------------------------------------------------------
# OpenAIConnector
# ---------------------------------------------------------------------------


class TestOpenAIConnector:
    """Tests for OpenAIConnector.stream()."""

    def _make_connector(self, **kwargs):
        from core.agent.connectors.openai_connector import OpenAIConnector

        return OpenAIConnector(_agent(extras={"model": "gpt-4o"}, **kwargs))

    @pytest.mark.anyio
    async def test_stream_yields_text_delta(self):
        """Stream should yield content deltas from SSE chunks."""
        conn = self._make_connector()

        sse_lines = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " there"}}]}',
            "data: [DONE]",
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = lambda: _async_iter(sse_lines)

        with patch("httpx.AsyncClient") as MockClient:
            _setup_httpx_mock(MockClient, mock_response)
            chunks = []
            async for chunk in conn.stream([], "hi"):
                chunks.append(chunk)

        assert chunks == ["Hello", " there"]

    @pytest.mark.anyio
    async def test_stream_skips_non_data_lines(self):
        """Non-data: lines should be ignored."""
        conn = self._make_connector()

        sse_lines = [
            "",
            "event: ping",
            'data: {"choices": [{"delta": {"content": "word"}}]}',
            "data: [DONE]",
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = lambda: _async_iter(sse_lines)

        with patch("httpx.AsyncClient") as MockClient:
            _setup_httpx_mock(MockClient, mock_response)
            chunks = []
            async for chunk in conn.stream([], "hi"):
                chunks.append(chunk)

        assert chunks == ["word"]

    @pytest.mark.anyio
    async def test_stream_error_response(self):
        """Non-200 response should yield an error string."""
        conn = self._make_connector()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.aread = AsyncMock(
            return_value=b'{"error": {"message": "Unauthorized"}}'
        )

        with patch("httpx.AsyncClient") as MockClient:
            _setup_httpx_mock(MockClient, mock_response)
            chunks = []
            async for chunk in conn.stream([], "hi"):
                chunks.append(chunk)

        assert any("401" in str(c) or "Unauthorized" in str(c) for c in chunks)

    @pytest.mark.anyio
    async def test_close_is_noop(self):
        """OpenAIConnector.close() should not raise."""
        conn = self._make_connector()
        await conn.close()

    def test_build_endpoint_url_appends_path(self):
        """Endpoint without /chat/completions should have path appended."""
        from core.agent.connectors.openai_connector import OpenAIConnector

        conn = OpenAIConnector(
            _agent(endpoint="https://api.openai.com", extras={"model": "gpt-4o"})
        )
        url = conn._build_endpoint_url()
        assert url.endswith("/chat/completions")

    def test_build_endpoint_url_keeps_existing_path(self):
        """Endpoint already ending with /chat/completions should be kept as-is."""
        from core.agent.connectors.openai_connector import OpenAIConnector

        conn = OpenAIConnector(
            _agent(
                endpoint="https://api.openai.com/v1/chat/completions",
                extras={"model": "gpt-4o"},
            )
        )
        url = conn._build_endpoint_url()
        # Should not double-append
        assert url.count("/chat/completions") == 1

    def test_system_prompt_prepended(self):
        """A system_prompt extra should appear at the start of messages."""
        from core.agent.connectors.openai_connector import OpenAIConnector

        conn = OpenAIConnector(
            _agent(extras={"model": "gpt-4o", "system_prompt": "You are helpful."})
        )
        messages = conn._build_messages([], "hello")
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are helpful."


# ---------------------------------------------------------------------------
# LangGraphConnector
# ---------------------------------------------------------------------------


class TestLangGraphConnector:
    """Tests for LangGraphConnector."""

    def _make_connector(self, **kwargs):
        # LangGraph SDK may not be installed; skip if so.
        try:
            from core.agent.connectors.langgraph_connector import LangGraphConnector
        except ImportError:
            pytest.skip("langgraph-sdk not installed")
        return LangGraphConnector(_agent(extras={"graph_id": "g1"}, **kwargs))

    def test_get_auth_headers_bearer(self):
        """Test LangGraph connector bearer auth headers."""
        conn = self._make_connector()
        conn.auth = {"auth_type": "bearer", "credentials": "lg-token"}
        headers = conn.get_auth_headers()
        assert headers["Authorization"] == "Bearer lg-token"

    def test_get_auth_headers_no_auth(self):
        """Test LangGraph connector with no auth config."""
        conn = self._make_connector()
        conn.auth = {}
        assert conn.get_auth_headers() == {}

    @pytest.mark.anyio
    async def test_close_releases_client(self):
        """close() should set _client to None."""
        conn = self._make_connector()
        conn._client = MagicMock()
        await conn.close()
        assert conn._client is None

    @pytest.mark.anyio
    async def test_stream_yields_error_on_exception(self):
        """If streaming raises, a human-readable error string should be yielded."""
        conn = self._make_connector()
        conn._initialized = True

        mock_client = MagicMock()
        mock_client.runs.stream = MagicMock(side_effect=RuntimeError("boom"))
        conn._client = mock_client

        with patch.object(
            conn, "create_thread", new=AsyncMock(return_value="thread-1")
        ):
            chunks = []
            async for chunk in conn.stream([], "hello"):
                chunks.append(chunk)

        assert any("LangGraph error" in str(c) or "boom" in str(c) for c in chunks)


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------


async def _async_iter_impl(items):
    for item in items:
        yield item


def _async_iter(items):
    """Return an async iterator over *items*."""
    return _async_iter_impl(items)


def _setup_httpx_mock(MockClient, mock_response):
    """Wire up MockClient context manager to return mock_response."""
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_client_instance = MagicMock()
    mock_client_instance.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_ctx = MagicMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=None)

    MockClient.return_value = mock_client_ctx
