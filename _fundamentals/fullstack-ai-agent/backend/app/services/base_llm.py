
from abc import ABC, abstractmethod
from collections.abc import Iterator

from app.schemas.chat import ChatMessage


class BaseLLMService(ABC):

    @abstractmethod
    def generate(
        self,
        messages: list[ChatMessage]
    ) -> str:
        pass

    @abstractmethod
    def stream(
        self,
        messages: list[ChatMessage]
    ) -> Iterator[str]:
        pass
