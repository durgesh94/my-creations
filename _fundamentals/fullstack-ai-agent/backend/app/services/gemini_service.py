
from collections.abc import Iterator

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.schemas.chat import ChatMessage
from app.services.base_llm import BaseLLMService


class GeminiService(BaseLLMService):

    def __init__(self):
        settings = get_settings()

        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured"
            )

        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model

    def _contents(
        self,
        messages: list[ChatMessage]
    ) -> list[types.Content]:
        return [
            types.Content(
                role=(
                    "model"
                    if message.role == "assistant"
                    else "user"
                ),
                parts=[
                    types.Part.from_text(
                        text=message.content
                    )
                ]
            )
            for message in messages
        ]

    def generate(
        self,
        messages: list[ChatMessage]
    ) -> str:
        with genai.Client(api_key=self.api_key) as client:
            response = client.models.generate_content(
                model=self.model,
                contents=self._contents(messages)
            )

        if not response.text:
            raise ValueError("Gemini returned no text")

        return response.text

    def stream(
        self,
        messages: list[ChatMessage]
    ) -> Iterator[str]:
        with genai.Client(api_key=self.api_key) as client:
            chunks = client.models.generate_content_stream(
                model=self.model,
                contents=self._contents(messages)
            )

            for chunk in chunks:
                if chunk.text:
                    yield chunk.text
