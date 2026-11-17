
import uuid
from typing import Any, Literal, TypedDict

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session

from app.services.conversation_service import (
    ConversationService,
)

from langgraph.types import Command
from fastapi import HTTPException


class AgentChatResult(TypedDict):
    conversation_id: str
    status: Literal["completed", "approval_required"]
    response: str
    approval: dict[str, Any] | None


class AgentService:

    def __init__(
        self,
        db: Session,
        agent: CompiledStateGraph,
    ):
        self.conversation_service = ConversationService(db)
        self.agent = agent

    async def chat(
        self,
        conversation_id: uuid.UUID,
        message: str,
    ) -> AgentChatResult:

        # 1. Validate conversation exists.
        self.conversation_service.get(conversation_id)

        # 2. Reuse the conversation UUID as LangGraph thread ID.
        config = {
            "configurable": {
                "thread_id": str(conversation_id),
            },
            "recursion_limit": 20,
        }

        # 3. Don't start another turn while approval is pending.
        previous_state = await self.agent.aget_state(config)

        if previous_state.interrupts:
            pending = previous_state.interrupts[0].value

            return {
                "conversation_id": str(conversation_id),
                "status": "approval_required",
                "response": pending.get(
                    "message",
                    "Appointment approval is pending.",
                ),
                "approval": pending,
            }

        # 4. Invoke LangGraph with only the new message.
        # Previous messages come from PostgreSQL checkpoints.
        result = await self.agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content=message)
                ]
            },
            config=config,
        )

        # 5. Check whether LangGraph paused execution.
        interrupts = result.get("__interrupt__", ())

        if interrupts:
            approval_request = interrupts[0].value

            # Persist the visible user turn for React.
            # This is not a final AI response.
            self.conversation_service.save_turn(
                conversation_id=conversation_id,
                user_content=message,
                assistant_content=approval_request.get(
                    "message",
                    "Appointment approval is pending.",
                ),
            )

            return {
                "conversation_id": str(conversation_id),
                "status": "approval_required",
                "response": approval_request.get(
                    "message",
                    "Appointment approval is pending.",
                ),
                "approval": approval_request,
            }

        # 6. Extract the completed AI response.
        final_message = result["messages"][-1]

        if not isinstance(final_message, AIMessage):
            raise RuntimeError(
                "Agent did not return a final AI response"
            )

        answer = "\n".join(
            block["text"]
            for block in final_message.content_blocks
            if block.get("type") == "text"
        ).strip()

        if not answer:
            raise RuntimeError("Empty agent response")

        # 7. Save the completed turn for React history.
        self.conversation_service.save_turn(
            conversation_id=conversation_id,
            user_content=message,
            assistant_content=answer,
        )
        
        self.conversation_service.touch(
            conversation_id=conversation_id,
            user_message=message,
        )

        return {
            "conversation_id": str(conversation_id),
            "status": "completed",
            "response": answer,
            "approval": None,
        }
    
    # Return the pending approval for a conversation, if any.
    async def get_pending_approval(
        self,
        conversation_id: uuid.UUID,
    ) -> dict:
        self.conversation_service.get(conversation_id)

        state = await self.agent.aget_state(
            {
                "configurable": {
                    "thread_id": str(conversation_id),
                },
            }
        )

        if state.interrupts:
            return {
                "status": "approval_required",
                "approval": state.interrupts[0].value,
            }

        return {"status": "completed", "approval": None}

    # Resume a pending approval for a conversation.
    async def resume_approval(
        self,
        conversation_id: uuid.UUID,
        decision: str,
    ) -> dict:

        # Validate conversation.
        self.conversation_service.get(conversation_id)

        config = {
            "configurable": {
                "thread_id": str(conversation_id),
            },
            "recursion_limit": 20,
        }

        # Verify the graph is actually paused.
        state = await self.agent.aget_state(config)

        if not state.interrupts:
            raise HTTPException(
                status_code=409,
                detail="No pending approval found.",
            )

        # Resume the same LangGraph thread.
        result = await self.agent.ainvoke(
            Command(resume=decision),
            config=config,
        )

        # Handle any additional interrupts.
        interrupts = result.get("__interrupt__", ())

        if interrupts:
            approval_request = interrupts[0].value

            return {
                "conversation_id": str(conversation_id),
                "status": "approval_required",
                "response": approval_request.get(
                    "message",
                    "Another approval is required.",
                ),
                "approval": approval_request,
            }

        final_message = result["messages"][-1]

        if not isinstance(final_message, AIMessage):
            raise RuntimeError(
                "Agent did not return a final AI response"
            )

        answer = "\n".join(
            block["text"]
            for block in final_message.content_blocks
            if block.get("type") == "text"
        ).strip()

        if not answer:
            raise RuntimeError("Empty agent response")

        return {
            "conversation_id": str(conversation_id),
            "status": "completed",
            "response": answer,
            "approval": None,
        }
