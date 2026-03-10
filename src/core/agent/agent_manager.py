from .schema import Agent
from .agent_connector import AgentConnector

class AgentManager:
    agents = {}
    def __init__(self):
        self.connector = AgentConnector()

    def create_agent(self, agent: Agent):
        self.agents[agent.name] = agent         

    def get_agent(self, name: str):
        return self.agents.get(name)
    
    def stream_message(self, name: str, messages: list):
        agent = self.get_agent(name)
        if agent:
            yield from self.connector.stream_chat(agent.endpoint, messages)
        else:
            raise ValueError(f"Agent {name} not found")