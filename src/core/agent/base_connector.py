from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List, Dict, Any, Union
import base64
import logging

_connector_logger = logging.getLogger(__name__)


def _check_endpoint_security(endpoint: str, auth_type: str) -> None:
    """Warn if credentials are being sent over an insecure HTTP connection.

    Raises ValueError for non-localhost HTTP endpoints that carry credentials.
    Localhost/127.0.0.1 connections are allowed for local development.
    """
    if not endpoint:
        return
    url_lower = endpoint.lower()
    if url_lower.startswith("https://"):
        return  # Secure — no warning needed
    if not url_lower.startswith("http://"):
        return  # Non-HTTP scheme (e.g. unix socket) — skip check

    # Allow localhost for development
    is_local = (
        "localhost" in url_lower
        or "127.0.0.1" in url_lower
        or "::1" in url_lower
    )
    if is_local:
        _connector_logger.debug(
            "Using HTTP (not HTTPS) with %s auth on localhost endpoint %s — allowed for development",
            auth_type,
            endpoint,
        )
        return

    raise ValueError(
        f"Security error: credentials ({auth_type}) must not be sent over plain HTTP to "
        f"a non-localhost endpoint ({endpoint}). Use HTTPS instead."
    )


class BaseAgentConnector(ABC):
    """Abstract base class for agent connectors."""

    def __init__(self, agent: dict):
        self.agent = agent
        self.endpoint = agent["endpoint"]
        self.name = agent["name"]
        self.extras = agent.get("extras") or {}
        self.auth = agent.get("auth") or {}

    def get_auth_headers(self) -> dict:
        """Build authentication headers based on auth config.

        Auth format: {"auth_type": "bearer|basic|api_key", "credentials": str|{username, password}}
        """
        headers = {}
        auth_type = self.auth.get("auth_type")
        credentials = self.auth.get("credentials")

        if not auth_type or not credentials:
            return headers

        # Enforce HTTPS when credentials are present (localhost exempted for dev)
        _check_endpoint_security(self.endpoint, auth_type)

        if auth_type == "api_key":
            headers["X-API-Key"] = credentials
        elif auth_type == "bearer":
            headers["Authorization"] = f"Bearer {credentials}"
        elif auth_type == "basic":
            if isinstance(credentials, dict):
                username = credentials.get("username", "")
                password = credentials.get("password", "")
                encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"

        return headers
    
    @abstractmethod
    async def stream(
        self, 
        messages_history: list,
        message: str,
        conversation_id: Optional[int] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncIterator[Union[str, dict]]:
        """Stream response from the agent. Yields raw chunks for the chat service to convert to NDJSON.
        
        Agent response contract:
        - str: plain text (e.g. streaming LLM tokens).
        - dict: structured response with optional keys: content (str), elements (list), file (dict).
          The chat service converts these to typed NDJSON events for the frontend.
        
        Args:
            messages_history: List of previous conversation messages (dicts with 'role' and 'content')
            message: The new user message string
            conversation_id: Optional conversation ID (used by HTTP connector)
            files: Optional list of file attachments with 'filename', 'content_type', and 'data' (base64)
            metadata: Optional metadata dict containing user details and other context
            **kwargs: Additional connector-specific parameters (e.g., thread_id for LangGraph)
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Cleanup resources."""
        pass

