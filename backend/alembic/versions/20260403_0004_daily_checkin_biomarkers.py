"""Daily check-in: Ayurvedic biomarker fields (sleep, digestion, energy, movement).

Revision ID: 20260403_0004
Revises: 20260402_0003
Create Date: 2026-04-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260403_0004"
down_revision: Union[str, None] = "20260402_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("daily_check_ins", sa.Column("sleep_quality", sa.String(length=32), nullable=True))
    op.add_column("daily_check_ins", sa.Column("digestion", sa.String(length=32), nullable=True))
    op.add_column("daily_check_ins", sa.Column("energy_state", sa.String(length=32), nullable=True))
    op.add_column("daily_check_ins", sa.Column("movement", sa.String(length=32), nullable=True))

    op.execute(
        """
        UPDATE daily_check_ins SET
            sleep_quality = 'refreshed',
            digestion = 'calm',
            energy_state = 'grounded',
            movement = 'light'
        WHERE sleep_quality IS NULL
        """
    )

    op.alter_column("daily_check_ins", "sleep_quality", nullable=False)
    op.alter_column("daily_check_ins", "digestion", nullable=False)
    op.alter_column("daily_check_ins", "energy_state", nullable=False)
    op.alter_column("daily_check_ins", "movement", nullable=False)

    op.drop_column("daily_check_ins", "exercise")
    op.drop_column("daily_check_ins", "diet_quality")
    op.drop_column("daily_check_ins", "mood")


def downgrade() -> None:
    op.add_column("daily_check_ins", sa.Column("mood", sa.Integer(), nullable=True))
    op.add_column("daily_check_ins", sa.Column("diet_quality", sa.String(length=32), nullable=True))
    op.add_column("daily_check_ins", sa.Column("exercise", sa.Boolean(), nullable=True))

    op.execute(
        """
        UPDATE daily_check_ins SET
            mood = 3,
            diet_quality = 'mixed',
            exercise = false
        WHERE mood IS NULL
        """
    )

    op.alter_column("daily_check_ins", "mood", nullable=False)
    op.alter_column("daily_check_ins", "diet_quality", nullable=False)
    op.alter_column("daily_check_ins", "exercise", nullable=False)

    op.drop_column("daily_check_ins", "movement")
    op.drop_column("daily_check_ins", "energy_state")
    op.drop_column("daily_check_ins", "digestion")
    op.drop_column("daily_check_ins", "sleep_quality")
