from pydantic import BaseModel


class AgentResponse(BaseModel):
    agent_name: str
    content: str
    meta: dict = {}
