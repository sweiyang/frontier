"""Agent lifecycle management and message routing."""

from core.logging import get_logger

from .agent_connector import AgentConnector
from .schema import Agent

logger = get_logger(__name__)


class AgentManager:
    """
    Manages agent registration and message routing.

    Provides a registry for agents and routes messages to the appropriate
    agent connector for streaming responses.

    Attributes:
        agents: Dict mapping agent names to Agent instances.
        connector: AgentConnector for HTTP communication.
    """

    agents = {}

    def __init__(self):
        """Initialize the agent manager with an HTTP connector."""
        self.connector = AgentConnector()

    def create_agent(self, agent: Agent):
        """
        Register an agent in the manager.

        Args:
            agent: Agent instance to register.
        """
        logger.debug("Creating agent: {}", agent.name)
        self.agents[agent.name] = agent

    def get_agent(self, name: str):
        """
        Retrieve a registered agent by name.

        Args:
            name: Name of the agent to retrieve.

        Returns:
            Agent instance if found, None otherwise.
        """
        return self.agents.get(name)

    def stream_message(self, name: str, messages: list):
        """
        Stream a message to a named agent.

        Args:
            name: Name of the target agent.
            messages: List of message dicts to send.

        Yields:
            Response chunks from the agent.

        Raises:
            ValueError: If the agent is not found.
        """
        agent = self.get_agent(name)
        if agent:
            logger.debug("Streaming message to agent: {}", name)
            yield from self.connector.stream_chat(agent.endpoint, messages)
        else:
            logger.error("Agent not found: {}", name)
            raise ValueError(f"Agent {name} not found")
