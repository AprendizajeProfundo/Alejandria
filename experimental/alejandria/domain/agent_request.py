from pydantic import BaseModel


class AgentRequest(BaseModel):
    user_id: str
    message: str
    context: dict = {}
