
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        provider: str,
        title: str
    ) -> Conversation:
        conversation = Conversation(
            provider=provider,
            title=title
        )

        self.db.add(conversation)
        self.db.flush()

        return conversation

    def list_all(self) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .order_by(
                Conversation.updated_at.desc(),
                Conversation.id.desc()
            )
        )

        return list(self.db.scalars(stmt).all())

    def get(
        self,
        conversation_id: uuid.UUID
    ) -> Conversation | None:
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )

        return self.db.scalar(stmt)

    def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str
    ) -> Message:

        # Lock the conversation while allocating a sequence number.
        conversation = self.db.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .with_for_update()
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        # Find the last sequence number for this conversation.
        last_sequence = self.db.scalar(
            select(func.max(Message.sequence_number))
            .where(Message.conversation_id == conversation_id)
        ) or 0

        # Create the next message.
        message = Message(
            conversation_id=conversation_id,
            sequence_number=last_sequence + 1,
            role=role,
            content=content
        )

        self.db.add(message)
        self.db.flush()

        return message

    def delete(
        self,
        conversation: Conversation
    ) -> None:
        self.db.delete(conversation)
        
    
    def get_messages(
        self,
        conversation_id: uuid.UUID,
    ) -> list[Message]:

        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number.asc())
        )

        return list(self.db.scalars(stmt).all())

