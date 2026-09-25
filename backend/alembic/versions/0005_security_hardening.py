"""add risk_score, anomaly_flags, and error_context to refund_requests

Revision ID: 0005_security_hardening
Revises: 0004_add_security_logs
Create Date: 2026-09-25 07:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_security_hardening"
down_revision: str | None = "0004_add_security_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop legacy unique index on refund_items to allow duplicate claim conflict escalation tracking
    op.execute("DROP INDEX IF EXISTS uq_active_refund_item;")

    # 1. Add columns to refund_requests
    op.add_column(
        "refund_requests",
        sa.Column(
            "risk_score",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_refund_requests_risk_score",
        "refund_requests",
        ["risk_score"],
        unique=False,
    )
    op.add_column(
        "refund_requests",
        sa.Column(
            "anomaly_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "refund_requests",
        sa.Column(
            "error_context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("refund_requests", "error_context")
    op.drop_column("refund_requests", "anomaly_flags")
    op.drop_index("ix_refund_requests_risk_score", table_name="refund_requests")
    op.drop_column("refund_requests", "risk_score")
