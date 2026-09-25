"""add customer auth credentials and refresh token association

Revision ID: 0006_add_customer_auth
Revises: 0005_security_hardening
Create Date: 2026-09-25 21:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_add_customer_auth"
down_revision: str | None = "0005_security_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_CUSTOMER_PASSWORD_HASH = "$2b$12$eKZWf0D6LxbmHk161evm/.5u9N9HFhTFCn6azLziY41JzVBNB0qeC"


def upgrade() -> None:
    # 1. Add auth columns to customers table
    op.add_column(
        "customers",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            server_default=sa.text(f"'{DEFAULT_CUSTOMER_PASSWORD_HASH}'"),
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "last_login_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # 2. Alter refresh_tokens to allow polymorphic association (admin_users or customers)
    op.alter_column(
        "refresh_tokens",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("idx_refresh_tokens_customer_id", "refresh_tokens", ["customer_id"])

    # 3. Add check constraint ensuring exactly one owner is specified
    op.create_check_constraint(
        "ck_refresh_tokens_owner",
        "refresh_tokens",
        "(user_id IS NOT NULL AND customer_id IS NULL) OR (customer_id IS NOT NULL AND user_id IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_refresh_tokens_owner", "refresh_tokens", type_="check")
    op.drop_index("idx_refresh_tokens_customer_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "customer_id")
    op.alter_column(
        "refresh_tokens",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    op.drop_column("customers", "last_login_at")
    op.drop_column("customers", "is_active")
    op.drop_column("customers", "password_hash")
