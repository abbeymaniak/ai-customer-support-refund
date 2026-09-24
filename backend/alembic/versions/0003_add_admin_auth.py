"""add admin_users and refresh_tokens tables and seed default admin accounts

Revision ID: 0003_add_admin_auth
Revises: 0002_add_llm_providers
Create Date: 2026-09-24 12:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_add_admin_auth"
down_revision: str | None = "0002_add_llm_providers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create admin_users table
    admin_users_table = op.create_table(
        "admin_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default=sa.text("'agent'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_admin_users_email", "admin_users", ["email"], unique=True)

    # 2. Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("idx_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("idx_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("idx_refresh_tokens_revoked", "refresh_tokens", ["revoked"])

    # 3. Seed default admin accounts
    # admin@store.com / admin123 (role: admin)
    # lead@store.com / lead123 (role: agent)
    op.bulk_insert(
        admin_users_table,
        [
            {
                "id": uuid.uuid4(),
                "email": "admin@store.com",
                "password_hash": "$2b$12$9ua7iO66MzjehMDyrxlAbO6OfcOZhTAJumvPn.fmdCPg/2qvALjBe",
                "name": "Store Administrator",
                "role": "admin",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "email": "lead@store.com",
                "password_hash": "$2b$12$9NoplASyAhvXD8oxxhChJuWLaDB4Paqf6M86VDNoQILwDngTJupqS",
                "name": "Support Lead",
                "role": "agent",
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("admin_users")
