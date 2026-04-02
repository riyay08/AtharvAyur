"""Add pgvector semantic memory to chat_history.

Revision ID: 20260331_0002
Revises: 20260330_0001
Create Date: 2026-03-31
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260331_0002"
down_revision: Union[str, None] = "20260330_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS embedding vector(768)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_chat_history_embedding_ivfflat
        ON chat_history USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chat_history_embedding_ivfflat")
    op.execute("ALTER TABLE chat_history DROP COLUMN IF EXISTS embedding")
