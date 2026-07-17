"""v2.0 Phase 1: conversations, session_summaries, and additive columns.

- `conversations`: bounded chat sessions ('folders' for `chat_history` rows).
- `session_summaries`: Janitor-worker recaps, 3-sentence extraction per conversation.
- `chat_history.conversation_id`: nullable FK, historic rows are unaffected.
- `daily_check_ins.mood_score` / `.notes`: additive, nullable.
- `health_profiles.{vata,pitta,kapha}_score`: additive, nullable, backfilled from
  the existing `conditions -> prakriti_quiz -> dosha_distribution` JSON payload.

Revision ID: 20260716_0007
Revises: 20260421_0006
Create Date: 2026-07-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260716_0007"
down_revision: Union[str, None] = "20260421_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"], unique=False)
    op.create_index("ix_conversations_created_at", "conversations", ["created_at"], unique=False)

    op.create_table(
        "session_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_session_summaries_conversation_id", "session_summaries", ["conversation_id"], unique=False
    )
    op.create_index("ix_session_summaries_created_at", "session_summaries", ["created_at"], unique=False)

    op.add_column(
        "chat_history",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_chat_history_conversation_id",
        "chat_history",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_chat_history_conversation_id", "chat_history", ["conversation_id"], unique=False)

    op.add_column("daily_check_ins", sa.Column("mood_score", sa.Integer(), nullable=True))
    op.add_column("daily_check_ins", sa.Column("notes", sa.Text(), nullable=True))

    op.add_column("health_profiles", sa.Column("vata_score", sa.Integer(), nullable=True))
    op.add_column("health_profiles", sa.Column("pitta_score", sa.Integer(), nullable=True))
    op.add_column("health_profiles", sa.Column("kapha_score", sa.Integer(), nullable=True))

    # Backfill structured scores from the existing JSON quiz payload. `->` returns
    # NULL (not an error) when `conditions` isn't a JSON object or the path is
    # absent, so this is safe for rows with no quiz data / non-dict `conditions`.
    op.execute(
        """
        UPDATE health_profiles
        SET vata_score = (conditions -> 'prakriti_quiz' -> 'dosha_distribution' ->> 'vata')::integer,
            pitta_score = (conditions -> 'prakriti_quiz' -> 'dosha_distribution' ->> 'pitta')::integer,
            kapha_score = (conditions -> 'prakriti_quiz' -> 'dosha_distribution' ->> 'kapha')::integer
        WHERE conditions -> 'prakriti_quiz' -> 'dosha_distribution' IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column("health_profiles", "kapha_score")
    op.drop_column("health_profiles", "pitta_score")
    op.drop_column("health_profiles", "vata_score")

    op.drop_column("daily_check_ins", "notes")
    op.drop_column("daily_check_ins", "mood_score")

    op.drop_index("ix_chat_history_conversation_id", table_name="chat_history")
    op.drop_constraint("fk_chat_history_conversation_id", "chat_history", type_="foreignkey")
    op.drop_column("chat_history", "conversation_id")

    op.drop_index("ix_session_summaries_created_at", table_name="session_summaries")
    op.drop_index("ix_session_summaries_conversation_id", table_name="session_summaries")
    op.drop_table("session_summaries")

    op.drop_index("ix_conversations_created_at", table_name="conversations")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")
