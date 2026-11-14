
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
            f"Unsupported AI provider: {provider}"
        )

    def generate(
        self,
        provider: str,
        messages: list[ChatMessage]
    ) -> str:

        llm = self.get_provider(provider)

        return llm.generate(messages)
