from pydantic import BaseModel

class Agent(BaseModel):
    name: str
    description: str
    endpoint: str
