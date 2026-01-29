from langchain_core.tools import tool
from langgraph.graph import END
from .schema import State

# can be a api or a DB call
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    return f"{city} is sunny, 32°C"

def route_tools(state: State):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END