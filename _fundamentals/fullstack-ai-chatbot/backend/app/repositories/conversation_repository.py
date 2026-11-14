from __future__ import annotations

import uuid

from sqlalchemy import select
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
        message = Message(
            conversation_id=conversation_id,
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
