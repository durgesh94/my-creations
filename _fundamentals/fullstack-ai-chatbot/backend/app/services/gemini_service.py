
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

        self.model = settings.gemini_model
        self.api_key = settings.gemini_api_key

    def generate(
        self,
        messages: list[ChatMessage]
    ) -> str:

        # Convert messages into Gemini format
        contents = []

        for message in messages:

            role = (
                "model"
                if message.role == "assistant"
                else "user"
            )

            contents.append(
                types.Content(
                    role=role,
                    parts=[
                        types.Part.from_text(
                            text=message.content
                        )
                    ]
                )
            )

        with genai.Client(api_key=self.api_key) as client:
            response = client.models.generate_content(
                model=self.model,
                contents=contents
            )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response"
            )

        return response.text
