"""Fetch LangGraph assistants and endpoint validation."""
from typing import Optional

from conduit.core.agent.connectors.langgraph_connector import LangGraphConnector


async def fetch_assistants(
    endpoint: str, graph_id: Optional[str], auth: Optional[dict]
) -> list:
    """Fetch available assistants from a LangGraph endpoint.

    Returns:
        List of assistant dicts with assistant_id, name, graph_id, metadata.
    """
    temp_agent = {
        "name": "temp",
        "endpoint": endpoint,
        "graph_id": graph_id,
        "auth": auth,
        "extras": {},
    }

    connector = None
    try:
        connector = LangGraphConnector(temp_agent)
        await connector.initialize()

        assistants = []
        for assistant in connector.get_assistant_list():
            if isinstance(assistant, dict):
                assistants.append({
                    "assistant_id": assistant.get("assistant_id"),
                    "name": assistant.get("name"),
                    "graph_id": assistant.get("graph_id"),
                    "metadata": assistant.get("metadata", {}),
                })
            else:
                assistants.append({
                    "assistant_id": getattr(assistant, "assistant_id", None),
                    "name": getattr(assistant, "name", None),
                    "graph_id": getattr(assistant, "graph_id", None),
                    "metadata": getattr(assistant, "metadata", {}),
                })
        return assistants
    finally:
        if connector:
            await connector.close()
