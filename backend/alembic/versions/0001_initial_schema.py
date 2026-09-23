"""initial normalized schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-23 12:57:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Customers table
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("total_spent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("orders_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refunds_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("return_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "account_created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_customers_email", "customers", ["email"], unique=True)

    # 2. Orders table
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("order_date", sa.DateTime(), nullable=False, index=True),
        sa.Column("delivery_date", sa.DateTime(), nullable=True, index=True),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="delivered"),
        sa.Column(
            "items", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="[]"
        ),
        sa.Column(
            "shipping_address",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_orders_customer_id", "orders", ["customer_id"])
    op.create_index("idx_orders_order_number", "orders", ["order_number"], unique=True)
    op.create_index("idx_orders_status", "orders", ["status"])

    # 3. Order Items table
    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_final_sale", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("serial_number", sa.String(length=128), nullable=True),
        sa.Column("warranty_status", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_order_items_order_id", "order_items", ["order_id"])
    op.create_index("idx_order_items_product_id", "order_items", ["product_id"])
    op.create_index("idx_order_items_category", "order_items", ["category"])
    op.create_index("idx_order_items_is_final_sale", "order_items", ["is_final_sale"])

    # 4. Refund Requests table
    op.create_table(
        "refund_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_number", sa.String(length=64), nullable=False),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("item_id", sa.String(length=64), nullable=True),
        sa.Column("item_name", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_refund_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("reason_category", sa.String(length=64), nullable=False),
        sa.Column("customer_explanation", sa.Text(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column(
            "policy_checks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "llm_audit_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column("ai_decision", sa.String(length=32), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        sa.Column(
            "policy_evaluations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "llm_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column("human_override", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("override_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_refund_requests_request_number", "refund_requests", ["request_number"], unique=True
    )
    op.create_index("idx_refund_requests_customer_id", "refund_requests", ["customer_id"])
    op.create_index("idx_refund_requests_order_id", "refund_requests", ["order_id"])
    op.create_index("idx_refund_requests_status", "refund_requests", ["status"])
    op.create_index("idx_refund_requests_decision", "refund_requests", ["decision"])
    op.create_index("idx_refund_requests_created_at", "refund_requests", ["created_at"])

    # 5. Refund Items table
    op.create_table(
        "refund_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "refund_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("refund_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("order_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("refund_amount", sa.Float(), nullable=False),
        sa.Column(
            "item_condition", sa.String(length=64), nullable=False, server_default="unopened"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_refund_items_refund_request_id", "refund_items", ["refund_request_id"])
    op.create_index("idx_refund_items_order_item_id", "refund_items", ["order_item_id"])

    # 6. Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "refund_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("refund_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False, server_default="system"),
        sa.Column(
            "details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_logs_refund_request_id", "audit_logs", ["refund_request_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("refund_items")
    op.drop_table("refund_requests")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("customers")
