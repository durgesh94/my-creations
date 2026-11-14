
from openai import OpenAI

from app.core.config import get_settings
from app.services.base_llm import BaseLLMService


class OpenAIService(BaseLLMService):

    def __init__(self):
        settings = get_settings()

        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured"
            )

        self.model = settings.openai_model
        self.api_key = settings.openai_api_key

    def generate(self, prompt: str) -> str:
        with OpenAI(api_key=self.api_key) as client:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                store=False
            )

        if not response.output_text:
            raise ValueError(
                "OpenAI returned an empty response"
            )

        return response.output_text
