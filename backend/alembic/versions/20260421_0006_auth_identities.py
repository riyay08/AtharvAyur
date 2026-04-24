"""User identity columns + webauthn_credentials + phone_otps.

Revision ID: 20260421_0006
Revises: 20260404_0005
Create Date: 2026-04-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260421_0006"
down_revision: Union[str, None] = "20260404_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("phone", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "phone_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("google_sub", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("display_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "primary_provider",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'anonymous'"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_phone", "users", ["phone"])
    op.create_unique_constraint("uq_users_google_sub", "users", ["google_sub"])
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_phone", "users", ["phone"], unique=False)
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=False)

    op.create_table(
        "webauthn_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("credential_id", sa.LargeBinary(), nullable=False),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("transports", sa.String(length=255), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("credential_id", name="uq_webauthn_credential_id"),
    )
    op.create_index(
        "ix_webauthn_credentials_user_id",
        "webauthn_credentials",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "phone_otps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "consumed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_phone_otps_phone", "phone_otps", ["phone"], unique=False)
    op.create_index(
        "ix_phone_otps_created_at", "phone_otps", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_phone_otps_created_at", table_name="phone_otps")
    op.drop_index("ix_phone_otps_phone", table_name="phone_otps")
    op.drop_table("phone_otps")

    op.drop_index("ix_webauthn_credentials_user_id", table_name="webauthn_credentials")
    op.drop_table("webauthn_credentials")

    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_constraint("uq_users_google_sub", "users", type_="unique")
    op.drop_constraint("uq_users_phone", "users", type_="unique")
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "primary_provider")
    op.drop_column("users", "display_name")
    op.drop_column("users", "google_sub")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "phone_verified")
    op.drop_column("users", "phone")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "email")
