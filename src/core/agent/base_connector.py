from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List, Dict, Any, Union
import base64


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

