
from abc import ABC, abstractmethod

from app.schemas.chat import ChatMessage


class BaseLLMService(ABC):

    @abstractmethod
    def generate(
        self,
        messages: list[ChatMessage]
    ) -> str:
        """Generate response using conversation history."""
        pass
