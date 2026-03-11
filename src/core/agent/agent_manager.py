from .schema import Agent
from .agent_connector import AgentConnector
from core.logging import get_logger

logger = get_logger(__name__)


class AgentManager:
    agents = {}
    def __init__(self):
        self.connector = AgentConnector()

    def create_agent(self, agent: Agent):
        logger.debug("Creating agent: %s", agent.name)
        self.agents[agent.name] = agent         

    def get_agent(self, name: str):
        return self.agents.get(name)
    
    def stream_message(self, name: str, messages: list):
        agent = self.get_agent(name)
        if agent:
            logger.debug("Streaming message to agent: %s", name)
            yield from self.connector.stream_chat(agent.endpoint, messages)
        else:
            logger.error("Agent not found: %s", name)
            raise ValueError(f"Agent {name} not found")