"""add security_logs table for audit and prompt injection tracking

Revision ID: 0004_add_security_logs
Revises: 0003_add_admin_auth
Create Date: 2026-09-24 17:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_add_security_logs"
down_revision: str | None = "0003_add_admin_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "security_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column(
            "severity", sa.String(length=20), nullable=False, server_default=sa.text("'high'")
        ),
        sa.Column("source_ip", sa.String(length=45), nullable=True),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("matched_pattern", sa.String(length=255), nullable=True),
        sa.Column("payload_preview", sa.String(length=500), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("order_number", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_security_logs_event_type", "security_logs", ["event_type"])
    op.create_index("ix_security_logs_severity", "security_logs", ["severity"])
    op.create_index("ix_security_logs_customer_email", "security_logs", ["customer_email"])
    op.create_index("ix_security_logs_order_number", "security_logs", ["order_number"])
    op.create_index("ix_security_logs_created_at", "security_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_security_logs_created_at", table_name="security_logs")
    op.drop_index("ix_security_logs_order_number", table_name="security_logs")
    op.drop_index("ix_security_logs_customer_email", table_name="security_logs")
    op.drop_index("ix_security_logs_severity", table_name="security_logs")
    op.drop_index("ix_security_logs_event_type", table_name="security_logs")
    op.drop_table("security_logs")
