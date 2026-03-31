"""Agent data models."""

from pydantic import BaseModel


class Agent(BaseModel):
    """
    Agent configuration schema.

    Defines the basic properties needed to register and connect
    to an AI agent.

    Attributes:
        name: Unique identifier for the agent.
        description: Human-readable description.
        endpoint: API endpoint URL for the agent.
    """

    name: str
    description: str
    endpoint: str
