
import json
import logging
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        answer = ChatService().generate(
            provider=request.provider.value,
            messages=request.messages
        )

        return ChatResponse(
            provider=request.provider,
            response=answer
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error
    except Exception as error:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=502,
            detail="AI provider request failed"
        ) from error


def sse_event(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/chat/stream")
def stream_chat(request: ChatRequest):
    # Create the provider before starting the response.
    # Configuration errors can still return HTTP 400.
    try:
        provider = ChatService().get_provider(
            request.provider.value
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    def event_generator() -> Iterator[str]:
        generated_text = ""

        try:
            for delta in provider.stream(request.messages):
                generated_text += delta

                yield sse_event(
                    "delta",
                    {"content": delta}
                )

            if not generated_text:
                raise ValueError(
                    "AI provider returned no text"
                )

            yield sse_event(
                "done",
                {"status": "completed"}
            )

        except Exception:
            logger.exception("AI streaming failed")

            yield sse_event(
                "error",
                {"message": "AI streaming failed"}
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
