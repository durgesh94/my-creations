
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.agent_service import AgentService
from app.db.session import get_db  # Adjust to your existing dependency

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["Agent"],
)


class AgentChatRequest(BaseModel):
    conversation_id: uuid.UUID
    message: str = Field(min_length=1)


class AgentChatResponse(BaseModel):
    conversation_id: uuid.UUID
    response: str


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
):
    service = AgentService(db)

    answer = await service.chat(
        conversation_id=request.conversation_id,
        message=request.message,
    )

    return AgentChatResponse(
        conversation_id=request.conversation_id,
        response=answer,
    )
