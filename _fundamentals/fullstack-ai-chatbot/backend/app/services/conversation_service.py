
import uuid

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.repositories.conversation_repository import (
    ConversationRepository,
)
from app.schemas.conversation import ConversationCreate


class ConversationService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversationRepository(db)

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

    def list_all(self) -> list[Conversation]:
        return self.repo.list_all()

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

    def delete(
        self,
        conversation_id: uuid.UUID
    ) -> None:
        conversation = self.get(conversation_id)

        self.repo.delete(conversation)
        self.db.commit()

    def save_turn(
        self,
        conversation_id: uuid.UUID,
        user_content: str,
        assistant_content: str
    ) -> None:
        conversation = self.get(conversation_id)

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
