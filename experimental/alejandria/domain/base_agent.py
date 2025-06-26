from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str
    instructions: str

    @abstractmethod
    async def act(self, req: Any) -> Any:
        pass
