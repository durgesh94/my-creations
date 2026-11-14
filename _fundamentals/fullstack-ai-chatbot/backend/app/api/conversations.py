
from __future__ import annotations

import json
import logging
import uuid
from typing import Annotated, Iterator

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.schemas.chat import ChatMessage
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationDetail,
    MessageCreate,
)
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService


# ---------------------------------------------------------
# Logger
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Router
# ---------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["Conversations"],
)

DbSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------
# SSE Helper
# ---------------------------------------------------------

def sse_event(event: str, data: dict) -> str:
    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


# ---------------------------------------------------------
# Create Conversation
# ---------------------------------------------------------

@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    request: ConversationCreate,
    db: DbSession,
):
    return ConversationService(db).create(request)


# ---------------------------------------------------------
# List Conversations
# ---------------------------------------------------------

@router.get(
    "",
    response_model=list[ConversationRead],
)
def list_conversations(db: DbSession):
    return ConversationService(db).list_all()


# ---------------------------------------------------------
# Get Conversation with Messages
# ---------------------------------------------------------

@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
)
def get_conversation(
    conversation_id: uuid.UUID,
    db: DbSession,
):
    return ConversationService(db).get(conversation_id)


# ---------------------------------------------------------
# Delete Conversation
# ---------------------------------------------------------

@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: DbSession,
):
    ConversationService(db).delete(conversation_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------
# Stream AI Message and Save to PostgreSQL
# ---------------------------------------------------------

@router.post("/{conversation_id}/messages/stream")
def stream_conversation_message(
    conversation_id: uuid.UUID,
    request: MessageCreate,
    db: DbSession,
):
    # 1. Load conversation and existing messages.
    conversation = ConversationService(db).get(
        conversation_id
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    provider_name = conversation.provider

    # 2. Convert database messages into chat history.
    history = [
        ChatMessage(
            role=message.role,
            content=message.content,
        )
        for message in conversation.messages
    ]

    # 3. Append the latest user message.
    history.append(
        ChatMessage(
            role="user",
            content=request.content,
        )
    )

    # 4. Resolve the AI provider before streaming begins.
    try:
        provider = ChatService().get_provider(
            provider_name
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    # 5. Stream AI response to the client.
    def event_generator() -> Iterator[str]:
        generated_text = ""

        try:
            for delta in provider.stream(history):
                if not delta:
                    continue

                generated_text += delta

                yield sse_event(
                    "delta",
                    {"content": delta},
                )

            # 6. Ensure AI generated a valid response.
            if not generated_text.strip():
                raise ValueError(
                    "AI provider returned an empty response"
                )

            # 7. Persist user and assistant messages.
            # Use a new database session for streaming.
            with SessionLocal() as write_db:
                ConversationService(write_db).save_turn(
                    conversation_id=conversation_id,
                    user_content=request.content,
                    assistant_content=generated_text,
                )

            # 8. Notify client after successful persistence.
            yield sse_event(
                "done",
                {"status": "completed"},
            )

        except Exception:
            logger.exception(
                "Conversation streaming or persistence failed"
            )

            yield sse_event(
                "error",
                {
                    "message": "Unable to complete chat request"
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
