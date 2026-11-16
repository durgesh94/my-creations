
from collections.abc import Iterator

from openai import OpenAI

from app.core.config import get_settings
from app.schemas.chat import ChatMessage
from app.services.base_llm import BaseLLMService


class OpenAIService(BaseLLMService):

    def __init__(self):
        settings = get_settings()

        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured"
            )

        self.api_key = settings.openai_api_key
        self.model = settings.openai_model

    def _history(
        self,
        messages: list[ChatMessage]
    ) -> list[dict[str, str]]:
        return [
            {
                "role": message.role,
                "content": message.content
            }
            for message in messages
        ]

    def generate(
        self,
        messages: list[ChatMessage]
    ) -> str:
        with OpenAI(api_key=self.api_key) as client:
            response = client.responses.create(
                model=self.model,
                input=self._history(messages),
                store=False
            )

        if not response.output_text:
            raise ValueError("OpenAI returned no text")

        return response.output_text

    def stream(
        self,
        messages: list[ChatMessage]
    ) -> Iterator[str]:
        with OpenAI(api_key=self.api_key) as client:
            events = client.responses.create(
                model=self.model,
                input=self._history(messages),
                store=False,
                stream=True
            )

            for event in events:
                if event.type == "response.output_text.delta":
                    if event.delta:
                        yield event.delta

                elif event.type == "response.failed":
                    raise RuntimeError(
                        "OpenAI response generation failed"
                    )

                elif event.type == "response.incomplete":
                    raise RuntimeError(
                        "OpenAI response was incomplete"
                    )
