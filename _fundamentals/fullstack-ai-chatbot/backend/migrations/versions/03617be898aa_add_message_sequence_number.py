"""add message sequence number

Revision ID: 03617be898aa
Revises: 8fe5c6d6a00a
Create Date: 2026-11-15 11:55:13.361616

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03617be898aa'
down_revision: Union[str, Sequence[str], None] = '8fe5c6d6a00a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # 1. Add the column as nullable temporarily.
    op.add_column(
        "messages",
        sa.Column(
            "sequence_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    # 2. Assign sequence numbers to existing messages.
    op.execute("""
        WITH numbered_messages AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY conversation_id
                    ORDER BY
                        created_at ASC,
                        CASE
                            WHEN role = 'user' THEN 0
                            ELSE 1
                        END,
                        id ASC
                ) AS seq
            FROM messages
        )
        UPDATE messages AS m
        SET sequence_number = n.seq
        FROM numbered_messages AS n
        WHERE m.id = n.id
    """)

    # 3. Make the column required.
    op.alter_column(
        "messages",
        "sequence_number",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # 4. Prevent duplicate sequence numbers.
    op.create_unique_constraint(
        "uq_messages_conversation_sequence",
        "messages",
        ["conversation_id", "sequence_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_messages_conversation_sequence",
        "messages",
        type_="unique",
    )

    op.drop_column(
        "messages",
        "sequence_number",
    )

