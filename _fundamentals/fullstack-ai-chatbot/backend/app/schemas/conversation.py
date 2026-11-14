
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chat import AIProvider


class ConversationCreate(BaseModel):
    provider: AIProvider
    title: str = Field(
        default="New conversation",
        min_length=1,
        max_length=200,
    )


class MessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    provider: AIProvider
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationRead):
    messages: list[MessageRead]
