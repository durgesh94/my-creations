
from collections.abc import Iterator

from app.schemas.chat import ChatMessage
from app.services.base_llm import BaseLLMService
from app.services.gemini_service import GeminiService
from app.services.openai_service import OpenAIService


class ChatService:

    def get_provider(
        self,
        provider: str
    ) -> BaseLLMService:
        if provider == "gemini":
            return GeminiService()

        if provider == "openai":
            return OpenAIService()

        raise ValueError(
            f"Unsupported provider: {provider}"
        )

    def generate(
        self,
        provider: str,
        messages: list[ChatMessage]
    ) -> str:
        return self.get_provider(provider).generate(messages)

    def stream(
        self,
        provider: str,
        messages: list[ChatMessage]
    ) -> Iterator[str]:
        return self.get_provider(provider).stream(messages)
