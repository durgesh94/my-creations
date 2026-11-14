
from abc import ABC, abstractmethod


class BaseLLMService(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate an AI response."""
        pass
