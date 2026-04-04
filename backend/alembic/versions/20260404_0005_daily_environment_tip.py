"""Daily environment tip cache (per user per UTC day).

Revision ID: 20260404_0005
Revises: 20260403_0004
Create Date: 2026-04-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260404_0005"
down_revision: Union[str, None] = "20260403_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_environment_tips",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tip_date", sa.Date(), nullable=False),
        sa.Column("tip_title", sa.String(length=512), nullable=False),
        sa.Column("tip_description", sa.Text(), nullable=False),
        sa.Column("icon_name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "tip_date", name="uq_daily_env_tip_user_date"),
    )
    op.create_index("ix_daily_environment_tips_user_id", "daily_environment_tips", ["user_id"], unique=False)
    op.create_index("ix_daily_environment_tips_tip_date", "daily_environment_tips", ["tip_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_daily_environment_tips_tip_date", table_name="daily_environment_tips")
    op.drop_index("ix_daily_environment_tips_user_id", table_name="daily_environment_tips")
    op.drop_table("daily_environment_tips")
