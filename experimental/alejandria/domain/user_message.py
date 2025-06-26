from pydantic import BaseModel


class UserMessage(BaseModel):
    user_id: str
    message: str
