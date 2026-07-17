"""v2.0 Phase 3: Long-Term Memory — `user_memories` table (pgvector).

Durable, declarative facts about a user (e.g. "User is lactose intolerant"),
extracted by the Janitor worker from an ended conversation, alongside the
existing 3-sentence `session_summaries` recap. Semantically searchable via
`embedding`, same pattern as `chat_history.embedding` (see
20260331_0002_semantic_memory_pgvector).

Revision ID: 20260717_0008
Revises: 20260716_0007
Create Date: 2026-07-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0008"
down_revision: Union[str, None] = "20260716_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "user_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fact_text", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_memories_user_id", "user_memories", ["user_id"], unique=False)
    op.create_index("ix_user_memories_created_at", "user_memories", ["created_at"], unique=False)

    # `vector(768)` added via raw SQL (like chat_history.embedding) since
    # pgvector's SQLAlchemy type isn't reflected in `op.create_table`'s DDL model.
    op.execute("ALTER TABLE user_memories ADD COLUMN embedding vector(768)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_user_memories_embedding_ivfflat
        ON user_memories USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_memories_embedding_ivfflat")
    op.drop_index("ix_user_memories_created_at", table_name="user_memories")
    op.drop_index("ix_user_memories_user_id", table_name="user_memories")
    op.drop_table("user_memories")
