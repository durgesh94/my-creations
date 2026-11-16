
import uuid

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.repositories.conversation_repository import (
    ConversationRepository,
)
from app.schemas.conversation import ConversationCreate

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    BaseMessage,
)


class ConversationService:

    # Initialize the service with a database session and repository.
    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversationRepository(db)

    # Create a new conversation with the given request data.
    def create(
        self,
        request: ConversationCreate
    ) -> Conversation:
        conversation = self.repo.create(
            provider=request.provider.value,
            title=request.title,
        )

        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    # List all conversations.
    def list_all(self) -> list[Conversation]:
        return self.repo.list_all()

    # Get a conversation by its ID.
    def get(
        self,
        conversation_id: uuid.UUID
    ) -> Conversation:
        conversation = self.repo.get(conversation_id)

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        return conversation

    # Delete a conversation by its ID.
    def delete(
        self,
        conversation_id: uuid.UUID
    ) -> None:
        conversation = self.get(conversation_id)

        self.repo.delete(conversation)
        self.db.commit()

    # Save a turn (user and assistant messages) for a conversation.
    def save_turn(
        self,
        conversation_id: uuid.UUID,
        user_content: str,
        assistant_content: str
    ) -> None:
        conversation = self.get(conversation_id)
        
        if conversation.title.casefold() == "new conversation":
            conversation.title = self.generate_title(user_content)

        self.repo.add_message(
            conversation_id,
            "user",
            user_content
        )

        self.repo.add_message(
            conversation_id,
            "assistant",
            assistant_content
        )

        # Update conversation ordering.
        conversation.updated_at = func.now()

        # Both messages are saved atomically.
        self.db.commit()
    
    # Generate a title for a conversation based on the first user message.
    @staticmethod
    def generate_title(message: str) -> str:
        title = " ".join(message.strip().split())

        if not title:
            return "New Conversation"

        if len(title) > 60:
            title = title[:57].rsplit(" ", 1)[0] + "..."

        return title
    
    # Get all messages for a conversation in LangGraph format.
    def get_langgraph_messages(
    self,
    conversation_id: uuid.UUID,
    ) -> list[BaseMessage]:

        # Validate that the conversation exists.
        self.get(conversation_id)

        db_messages = self.repo.get_messages(conversation_id)

        history: list[BaseMessage] = []

        for message in db_messages:
            if message.role == "user":
                history.append(
                    HumanMessage(content=message.content)
                )

            elif message.role == "assistant":
                history.append(
                    AIMessage(content=message.content)
                )

        return history


