"""Initial schema: users, health_profiles, chat_history, audit_logs.

Revision ID: 20260330_0001
Revises:
Create Date: 2026-03-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260330_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("consent_flags", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "health_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("allergies", sa.JSON(), nullable=True),
        sa.Column("medications", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_health_profiles_user_id"),
    )
    op.create_index("ix_health_profiles_user_id", "health_profiles", ["user_id"], unique=False)

    op.create_table(
        "chat_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_history_user_id", "chat_history", ["user_id"], unique=False)
    op.create_index("ix_chat_history_timestamp", "chat_history", ["timestamp"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor", sa.String(length=512), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_timestamp", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_chat_history_timestamp", table_name="chat_history")
    op.drop_index("ix_chat_history_user_id", table_name="chat_history")
    op.drop_table("chat_history")

    op.drop_index("ix_health_profiles_user_id", table_name="health_profiles")
    op.drop_table("health_profiles")

    op.drop_table("users")
