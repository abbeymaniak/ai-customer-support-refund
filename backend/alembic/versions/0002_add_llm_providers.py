"""add llm_providers table and seed default providers

Revision ID: 0002_add_llm_providers
Revises: 0001_initial_schema
Create Date: 2026-09-23 22:15:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_llm_providers"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    llm_providers_table = op.create_table(
        "llm_providers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column("llm", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("llm_model", sa.String(length=64), nullable=False),
        sa.Column("api_key", sa.String(length=255), nullable=True),
        sa.Column("api_base", sa.String(length=255), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("timeout_seconds", sa.Float(), nullable=False, server_default=sa.text("3.0")),
        sa.Column(
            "updated_by", sa.String(length=128), nullable=True, server_default=sa.text("'system'")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_llm_providers_llm", "llm_providers", ["llm"], unique=True)
    op.create_index("idx_llm_providers_is_active", "llm_providers", ["is_active"])

    # Seed default rows for Ollama, OpenAI, and Gemini
    op.bulk_insert(
        llm_providers_table,
        [
            {
                "id": uuid.uuid4(),
                "llm": "ollama",
                "is_active": True,
                "llm_model": "llama3",
                "api_key": None,
                "api_base": "http://host.docker.internal:11434",
                "temperature": 0.0,
                "timeout_seconds": 3.0,
                "updated_by": "system_seed",
            },
            {
                "id": uuid.uuid4(),
                "llm": "openai",
                "is_active": False,
                "llm_model": "gpt-4o-mini",
                "api_key": None,
                "api_base": None,
                "temperature": 0.0,
                "timeout_seconds": 3.0,
                "updated_by": "system_seed",
            },
            {
                "id": uuid.uuid4(),
                "llm": "gemini",
                "is_active": False,
                "llm_model": "gemini-1.5-flash",
                "api_key": None,
                "api_base": None,
                "temperature": 0.0,
                "timeout_seconds": 3.0,
                "updated_by": "system_seed",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("idx_llm_providers_is_active", table_name="llm_providers")
    op.drop_index("idx_llm_providers_llm", table_name="llm_providers")
    op.drop_table("llm_providers")
