from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base_connector import BaseAgentConnector


def get_connector(agent: dict) -> "BaseAgentConnector":
    """Factory function to get the appropriate connector based on agent type."""
    connection_type = agent.get("connection_type", "http")
    
    if connection_type == "http":
        from .http_connector import HTTPAgentConnector
        return HTTPAgentConnector(agent)
    
    elif connection_type == "langgraph":
        from .langgraph_connector import LangGraphConnector
        return LangGraphConnector(agent)
    
    elif connection_type == "openai":
        from .openai_connector import OpenAIConnector
        return OpenAIConnector(agent)
    
    elif connection_type == "websocket":
        raise NotImplementedError("WebSocket connector not yet implemented")
    
    else:
        raise ValueError(f"Unknown connection type: {connection_type}")

