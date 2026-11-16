
from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, Field, model_validator


class AIProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(
        min_length=1,
        max_length=10000
    )


class ChatRequest(BaseModel):
    provider: AIProvider
    messages: List[ChatMessage] = Field(
        min_length=1,
        max_length=50
    )

    @model_validator(mode="after")
    def validate_last_message(self):
        if self.messages[-1].role != "user":
            raise ValueError(
                "Last message must have role 'user'"
            )
        return self


class ChatResponse(BaseModel):
    provider: AIProvider
    response: str
