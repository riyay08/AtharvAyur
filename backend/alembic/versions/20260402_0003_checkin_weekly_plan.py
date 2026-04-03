"""Daily check-ins and weekly plans.

Revision ID: 20260402_0003
Revises: 20260331_0002
Create Date: 2026-04-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260402_0003"
down_revision: Union[str, None] = "20260331_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_check_ins",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("mood", sa.Integer(), nullable=False),
        sa.Column("water_glasses", sa.Integer(), nullable=False),
        sa.Column("diet_quality", sa.String(length=32), nullable=False),
        sa.Column("exercise", sa.Boolean(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "check_in_date", name="uq_daily_check_ins_user_date"),
    )
    op.create_index("ix_daily_check_ins_user_id", "daily_check_ins", ["user_id"], unique=False)
    op.create_index("ix_daily_check_ins_check_in_date", "daily_check_ins", ["check_in_date"], unique=False)

    op.create_table(
        "weekly_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("tasks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "start_date", name="uq_weekly_plans_user_start"),
    )
    op.create_index("ix_weekly_plans_user_id", "weekly_plans", ["user_id"], unique=False)
    op.create_index("ix_weekly_plans_start_date", "weekly_plans", ["start_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_weekly_plans_start_date", table_name="weekly_plans")
    op.drop_index("ix_weekly_plans_user_id", table_name="weekly_plans")
    op.drop_table("weekly_plans")

    op.drop_index("ix_daily_check_ins_check_in_date", table_name="daily_check_ins")
    op.drop_index("ix_daily_check_ins_user_id", table_name="daily_check_ins")
    op.drop_table("daily_check_ins")
