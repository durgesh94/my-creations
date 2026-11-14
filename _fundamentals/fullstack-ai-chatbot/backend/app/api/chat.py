
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1", tags=["Chat"])

logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        service = ChatService()

        answer = service.generate(
            provider=request.provider.value,
            messages=request.messages
        )

        return ChatResponse(
            provider=request.provider,
            response=answer
        )

    except ValueError as error:
        logger.warning("Chat request failed: %s", error)
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception:
        logger.exception("AI provider request failed")
        raise HTTPException(
            status_code=502,
            detail="AI provider request failed"
        )
