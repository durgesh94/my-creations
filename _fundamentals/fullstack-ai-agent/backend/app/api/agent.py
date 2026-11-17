
import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Literal

from app.services.agent_service import AgentService
from app.db.session import get_db


router = APIRouter(
    prefix="/api/v1/agent",
    tags=["Agent"],
)


class AgentChatRequest(BaseModel):
    conversation_id: uuid.UUID
    message: str = Field(min_length=1)


class AgentChatResponse(BaseModel):
    conversation_id: uuid.UUID
    status: Literal["completed", "approval_required"]
    response: str
    approval: dict[str, Any] | None = None

class AgentApprovalRequest(BaseModel):
    conversation_id: uuid.UUID
    decision: Literal["approve", "reject"]


class PendingApprovalResponse(BaseModel):
    status: Literal["completed", "approval_required"]
    approval: dict[str, Any] | None = None


@router.get(
    "/pending/{conversation_id}",
    response_model=PendingApprovalResponse,
)
async def agent_pending(
    conversation_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    service = AgentService(
        db=db,
        agent=request.app.state.hospital_agent,
    )

    return await service.get_pending_approval(conversation_id)


@router.post(
    "/chat",
    response_model=AgentChatResponse,
)
async def agent_chat(
    body: AgentChatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Get the LangGraph agent initialized
    # during FastAPI startup.
    hospital_agent = request.app.state.hospital_agent

    # Inject database session and LangGraph agent.
    service = AgentService(
        db=db,
        agent=hospital_agent,
    )

    result = await service.chat(
        conversation_id=body.conversation_id,
        message=body.message,
    )

    return AgentChatResponse(**result)



@router.post(
    "/approval",
    response_model=AgentChatResponse,
)
async def agent_approval(
    body: AgentApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    service = AgentService(
        db=db,
        agent=request.app.state.hospital_agent,
    )

    result = await service.resume_approval(
        conversation_id=body.conversation_id,
        decision=body.decision,
    )

    return AgentChatResponse(**result)
