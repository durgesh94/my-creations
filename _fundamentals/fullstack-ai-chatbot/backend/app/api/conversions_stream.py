
import json
import logging
from collections.abc import Iterator

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.db.session import SessionLocal
from app.schemas.chat import ChatMessage
from app.schemas.conversation import MessageCreate
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)


def sse_event(event: str, data: dict) -> str:
    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


@router.post("/{conversation_id}/messages/stream")
def stream_conversation_message(
    conversation_id: uuid.UUID,
    request: MessageCreate,
    db: DbSession,
):
    # Load conversation and history before streaming.
    conversation = ConversationService(db).get(
        conversation_id
    )

    provider_name = conversation.provider

    # Copy history into plain Pydantic objects.
    # No database session is needed during AI generation.
    history = [
        ChatMessage(
            role=message.role,
            content=message.content
        )
        for message in conversation.messages
    ]

    history.append(
        ChatMessage(
            role="user",
            content=request.content
        )
    )

    # Validate provider configuration before sending HTTP 200.
    try:
        provider = ChatService().get_provider(provider_name)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    def event_generator() -> Iterator[str]:
        generated_text = ""

        try:
            for delta in provider.stream(history):
                generated_text += delta

                yield sse_event(
                    "delta",
                    {"content": delta}
                )

            if not generated_text.strip():
                raise ValueError(
                    "AI provider returned an empty response"
                )

            # Open a new database session after generation.
            with SessionLocal() as write_db:
                ConversationService(write_db).save_turn(
                    conversation_id=conversation_id,
                    user_content=request.content,
                    assistant_content=generated_text
                )

            # Done means generation AND persistence succeeded.
            yield sse_event(
                "done",
                {"status": "completed"}
            )

        except Exception:
            logger.exception(
                "Conversation streaming or persistence failed"
            )

            yield sse_event(
                "error",
                {"message": "Unable to complete chat request"}
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
