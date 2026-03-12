"""Simple HTTP streaming agent connector."""

from core.http_client.http_client import http_client


class AgentConnector:
    """
    HTTP streaming connector for AI agent communication.
    
    Provides a simple interface for streaming chat messages to an agent
    endpoint and yielding response chunks.
    
    Attributes:
        client: HTTP client instance for making requests.
    """
    
    def __init__(self):
        """Initialize the connector with the shared HTTP client."""
        self.client = http_client

    def stream_chat(self, endpoint: str, messages: list):
        """
        Stream a chat request to an agent endpoint.
        
        Args:
            endpoint: Agent API endpoint URL.
            messages: List of message dicts with 'role' and 'content'.
            
        Yields:
            Response data chunks from the agent (SSE data lines).
        """
        with self.client.stream(
            "POST",
            endpoint,
            json={"messages": messages}
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    yield line[6:]

    def close(self):
        """Close the HTTP client connection."""
        self.client.close()