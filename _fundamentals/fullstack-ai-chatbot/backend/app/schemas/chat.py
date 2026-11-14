
from enum import Enum

from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"


class ChatRequest(BaseModel):
    provider: AIProvider
    prompt: str = Field(
        min_length=1,
        max_length=10000
    )


class ChatResponse(BaseModel):
    provider: AIProvider
    response: str
