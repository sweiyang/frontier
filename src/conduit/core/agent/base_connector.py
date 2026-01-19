from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List, Dict, Any
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
        messages: list,
        conversation_id: int,
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Stream response from the agent. Yields text chunks.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            conversation_id: The conversation ID
            files: Optional list of file attachments with 'filename', 'content_type', and 'data' (base64)
            metadata: Optional metadata dict containing user details and other context
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Cleanup resources."""
        pass

