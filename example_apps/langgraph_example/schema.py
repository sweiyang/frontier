"""State schema for the Conduit elements demo graph."""
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class State(TypedDict):
    """Graph state: messages and optional step counter for demo flow."""

    messages: Annotated[list, add_messages]
    step: int
