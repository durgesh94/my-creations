
import uuid

from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.hospital_agent import hospital_agent
from app.services.conversation_service import (
    ConversationService,
)


class AgentService:

    def __init__(self, db: Session):
        self.conversation_service = ConversationService(db)

    async def chat(
        self,
        conversation_id: uuid.UUID,
        message: str,
    ) -> str:

        # 1. Load previous conversation messages
        history = (
            self.conversation_service.get_langgraph_messages(
                conversation_id
            )
        )

        # 2. Add the current user question
        messages = [
            *history,
            HumanMessage(content=message),
        ]

        # 3. Execute LangGraph
        result = await hospital_agent.ainvoke(
            {"messages": messages},
            config={"recursion_limit": 20},
        )

        # 4. Get the final AI response
        final_message = result["messages"][-1]

        if not isinstance(final_message, AIMessage):
            raise RuntimeError(
                "Agent did not return a final AI response"
            )

        text_blocks = [
            block["text"]
            for block in final_message.content_blocks
            if block.get("type") == "text"
        ]

        answer = "\n".join(text_blocks).strip()

        if not answer:
            raise RuntimeError(
                "Agent returned an empty response"
            )

        # 5. Persist the completed conversation turn
        self.conversation_service.save_turn(
            conversation_id=conversation_id,
            user_content=message,
            assistant_content=answer,
        )

        return answer
